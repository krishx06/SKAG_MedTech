"""
Escalation Decision Agent for AdaptiveCare.
Final decision-making agent that consumes outputs from all other agents.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.escalation_decision.models import (
    AgentInput, 
    AgentOutput,
    RiskAssessment,
    FlowRecommendation,
    BatchEvaluationResult
)
from backend.agents.escalation_decision.explainer import DecisionExplainer
from backend.core.event_bus import EventBus, create_event_id
from backend.core.state_manager import StateManager
from backend.models.events import (
    EventType, 
    AgentType,
    RiskUpdateEvent,
    CapacityUpdateEvent,
    FlowUpdateEvent,
    DecisionEvent
)
from backend.models.patient import Patient
from backend.models.hospital import CapacitySnapshot
from backend.models.decision import EscalationDecision, DecisionType
from backend.reasoning.decision_engine import DecisionEngine
from backend.reasoning.mcda import MCDACalculator
from backend.reasoning.llm_reasoning import LLMReasoning

logger = logging.getLogger(__name__)


class EscalationDecisionAgent(BaseAgent):
    """
    Escalation Decision Agent.
    
    The final step in the multi-agent pipeline. Consumes:
    - Risk scores from Risk Monitor Agent
    - Capacity data from Capacity Intelligence Agent
    - Flow recommendations from Flow Orchestrator Agent
    
    Produces:
    - Escalation decisions (ESCALATE, OBSERVE, DELAY, REPRIORITIZE)
    - Human-readable explanations via LLM
    - Real-time decision events for frontend
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        state_manager: StateManager,
        decision_engine: Optional[DecisionEngine] = None,
        explainer: Optional[DecisionExplainer] = None
    ):
        """
        Initialize the Escalation Decision Agent.
        
        Args:
            event_bus: Event bus for communication
            state_manager: Centralized state manager
            decision_engine: Decision engine (created if not provided)
            explainer: Decision explainer (created if not provided)
        """
        super().__init__(
            agent_type=AgentType.ESCALATION_DECISION,
            event_bus=event_bus,
            state_manager=state_manager,
            name="EscalationDecisionAgent"
        )
        
        self.decision_engine = decision_engine or DecisionEngine()
        self.explainer = explainer or DecisionExplainer()
        
        # Track pending re-evaluations
        self._pending_evaluations: Dict[str, datetime] = {}
        
        logger.info("EscalationDecisionAgent initialized")

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process patient data and produce an escalation decision.
        
        Args:
            input_data: Combined input from all agents
            
        Returns:
            AgentOutput with decision and metadata
        """
        start_time = time.time()
        
        patient = input_data.patient
        capacity = input_data.capacity_data
        
        logger.info(f"Processing decision for patient {patient.id}")
        
        # Apply risk data if provided
        if input_data.risk_data:
            patient.risk_score = input_data.risk_data.risk_score
            # Update risk factors
            for key, value in input_data.risk_data.risk_factors.items():
                if hasattr(patient.risk_factors, key):
                    setattr(patient.risk_factors, key, value)
        
        # Build flow recommendations list
        flow_recs = []
        if input_data.flow_recommendations:
            flow_recs = input_data.flow_recommendations.recommendations
        
        # Build context
        context = input_data.context.copy()
        if input_data.flow_recommendations:
            context['recommended_destination'] = input_data.flow_recommendations.recommended_destination
            context['estimated_wait_time'] = input_data.flow_recommendations.estimated_wait_time
            context['flow_bottleneck'] = input_data.flow_recommendations.flow_bottleneck
        
        # Generate decision
        decision = await self.decision_engine.evaluate_patient(
            patient=patient,
            capacity=capacity,
            flow_recommendations=flow_recs,
            context=context
        )
        
        # Store decision in state manager
        await self.state_manager.add_decision(decision)
        
        # Determine if notification is needed
        should_notify = self._should_notify(decision)
        notification_targets = self._get_notification_targets(decision)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        output = AgentOutput(
            decision=decision,
            should_notify=should_notify,
            notification_targets=notification_targets,
            processing_time_ms=processing_time,
            request_id=input_data.request_id
        )
        
        # Emit decision event
        await self._emit_decision_event(decision)
        
        # Store output for other agents
        await self.store_output(f"decision_{patient.id}", decision.to_frontend_format())
        await self.store_output("latest_decision", decision.to_frontend_format())
        
        logger.info(
            f"Decision for {patient.id}: {decision.decision_type.value} "
            f"(processed in {processing_time:.1f}ms)"
        )
        
        return output

    async def evaluate_patient_by_id(self, patient_id: str) -> Optional[AgentOutput]:
        """
        Evaluate a patient by ID using current state.
        
        Args:
            patient_id: Patient ID to evaluate
            
        Returns:
            AgentOutput or None if patient not found
        """
        patient = self.state_manager.get_patient(patient_id)
        if not patient:
            logger.warning(f"Patient {patient_id} not found")
            return None
        
        capacity = self.state_manager.get_capacity()
        if not capacity:
            logger.warning("No capacity data available")
            return None
        
        # Get risk data from state
        risk_data = self.state_manager.get_agent_output(
            AgentType.RISK_MONITOR.value, 
            f"risk_{patient_id}"
        )
        
        # Get flow recommendations
        flow_data = self.state_manager.get_agent_output(
            AgentType.FLOW_ORCHESTRATOR.value,
            f"flow_{patient_id}"
        )
        
        input_data = AgentInput(
            patient=patient,
            capacity_data=capacity,
            risk_data=RiskAssessment(**risk_data) if risk_data else None,
            flow_recommendations=FlowRecommendation(**flow_data) if flow_data else None
        )
        
        return await self.process(input_data)

    async def batch_evaluate(
        self, 
        patient_ids: Optional[List[str]] = None
    ) -> BatchEvaluationResult:
        """
        Evaluate multiple patients.
        
        Args:
            patient_ids: Specific patients to evaluate, or all if None
            
        Returns:
            BatchEvaluationResult with all decisions
        """
        start_time = time.time()
        
        if patient_ids:
            patients = [
                self.state_manager.get_patient(pid) 
                for pid in patient_ids
            ]
            patients = [p for p in patients if p is not None]
        else:
            patients = self.state_manager.get_all_patients()
        
        capacity = self.state_manager.get_capacity()
        if not capacity:
            logger.warning("No capacity data for batch evaluation")
            return BatchEvaluationResult(
                total_patients=len(patients),
                evaluated_patients=0
            )
        
        results = []
        escalations = 0
        pending_review = 0
        
        for patient in patients:
            input_data = AgentInput(
                patient=patient,
                capacity_data=capacity
            )
            
            try:
                output = await self.process(input_data)
                results.append(output)
                
                if output.decision.decision_type == DecisionType.ESCALATE:
                    escalations += 1
                if output.decision.requires_human_review:
                    pending_review += 1
                    
            except Exception as e:
                logger.error(f"Error evaluating patient {patient.id}: {e}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchEvaluationResult(
            decisions=results,
            total_patients=len(patients),
            evaluated_patients=len(results),
            escalations=escalations,
            pending_review=pending_review,
            processing_time_ms=processing_time
        )

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events from other agents."""
        self.subscribe(EventType.RISK_UPDATE, self._on_risk_update, priority=8)
        self.subscribe(EventType.CAPACITY_UPDATE, self._on_capacity_update, priority=7)
        self.subscribe(EventType.FLOW_UPDATE, self._on_flow_update, priority=6)
        logger.info("EscalationDecisionAgent subscribed to events")

    async def _on_risk_update(self, event: RiskUpdateEvent) -> None:
        """
        Handle risk update from Risk Monitor Agent.
        Triggers re-evaluation if risk change is significant.
        """
        if not isinstance(event, RiskUpdateEvent):
            return
            
        patient_id = event.patient_id
        
        logger.debug(f"Received risk update for {patient_id}: {event.old_score} -> {event.new_score}")
        
        # Update patient risk in state
        await self.state_manager.update_patient_risk(
            patient_id,
            event.new_score,
            {f: 1.0 for f in event.risk_factors}  # Simplified
        )
        
        # Check if re-evaluation is needed
        if event.is_significant_change or event.alert_triggered:
            logger.info(f"Triggering re-evaluation for {patient_id} due to risk change")
            await self._schedule_evaluation(patient_id)

    async def _on_capacity_update(self, event: CapacityUpdateEvent) -> None:
        """
        Handle capacity update from Capacity Intelligence Agent.
        Re-evaluates patients waiting for that unit.
        """
        if not isinstance(event, CapacityUpdateEvent):
            return
            
        logger.debug(f"Received capacity update for unit {event.unit_id}")
        
        # If capacity increased, check for patients waiting for this unit
        if event.availability_change > 0:
            # Get patients that might benefit from this availability
            patients = self.state_manager.get_all_patients()
            for patient in patients:
                if patient.target_location == event.unit_id:
                    await self._schedule_evaluation(patient.id)

    async def _on_flow_update(self, event: FlowUpdateEvent) -> None:
        """
        Handle flow update from Flow Orchestrator Agent.
        Updates flow recommendations for patient.
        """
        if not isinstance(event, FlowUpdateEvent):
            return
            
        logger.debug(f"Received flow update for {event.patient_id}")
        
        # Store flow recommendation
        await self.store_output(f"flow_{event.patient_id}", {
            "recommended_destination": event.recommended_destination,
            "alternatives": event.alternative_destinations,
            "wait_time": event.estimated_wait_time,
            "recommendations": event.recommendations
        })

    async def _schedule_evaluation(self, patient_id: str) -> None:
        """Schedule a patient for re-evaluation."""
        # Debounce: don't re-evaluate too frequently
        last_eval = self._pending_evaluations.get(patient_id)
        now = datetime.now()
        
        if last_eval and (now - last_eval).total_seconds() < 5:
            return  # Too soon since last evaluation
        
        self._pending_evaluations[patient_id] = now
        await self.evaluate_patient_by_id(patient_id)

    async def _emit_decision_event(self, decision: EscalationDecision) -> None:
        """Emit a decision event to the event bus."""
        event = DecisionEvent(
            id=create_event_id(),
            source_agent=AgentType.ESCALATION_DECISION,
            decision_id=decision.id,
            patient_id=decision.patient_id,
            decision_type=decision.decision_type.value,
            priority_score=decision.priority_score,
            reasoning_summary=decision.reasoning[:100] + "..." if len(decision.reasoning) > 100 else decision.reasoning,
            requires_acknowledgment=decision.requires_human_review,
            priority=9 if decision.urgency.value == "immediate" else 5,
            payload=decision.to_frontend_format()
        )
        
        await self.emit_event(event)

    def _should_notify(self, decision: EscalationDecision) -> bool:
        """Determine if decision requires notification."""
        # Always notify for escalations and immediate urgency
        if decision.decision_type == DecisionType.ESCALATE:
            return True
        if decision.urgency.value == "immediate":
            return True
        if decision.requires_human_review:
            return True
        return False

    def _get_notification_targets(self, decision: EscalationDecision) -> List[str]:
        """Get list of roles/users to notify."""
        targets = []
        
        if decision.decision_type == DecisionType.ESCALATE:
            targets.append("charge_nurse")
            if decision.urgency.value == "immediate":
                targets.append("attending_physician")
        
        if decision.requires_human_review:
            targets.append("supervisor")
        
        if decision.target_unit:
            targets.append(f"unit_{decision.target_unit}")
        
        return targets

    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics about recent decisions."""
        recent = self.state_manager.get_recent_decisions(100)
        
        if not recent:
            return {
                "total_decisions": 0,
                "by_type": {},
                "avg_confidence": 0,
                "pending_review": 0
            }
        
        by_type = {}
        total_confidence = 0
        pending_review = 0
        
        for decision in recent:
            dtype = decision.decision_type.value
            by_type[dtype] = by_type.get(dtype, 0) + 1
            total_confidence += decision.confidence
            if decision.requires_human_review:
                pending_review += 1
        
        return {
            "total_decisions": len(recent),
            "by_type": by_type,
            "avg_confidence": total_confidence / len(recent),
            "pending_review": pending_review,
            "latest_decision_id": recent[0].id if recent else None
        }
