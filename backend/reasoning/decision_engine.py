"""
Decision engine for AdaptiveCare escalation system.
Combines MCDA scoring with LLM reasoning to produce actionable decisions.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.models.patient import Patient
from backend.models.hospital import CapacitySnapshot, BedType
from backend.models.decision import (
    DecisionType,
    UrgencyLevel,
    MCDAScore,
    EscalationDecision
)
from backend.reasoning.mcda import MCDACalculator
from backend.reasoning.llm_reasoning import LLMReasoning
from backend.reasoning.uncertainty import UncertaintyCalculator
from backend.core.config import Config

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Core decision engine that produces escalation decisions.
    
    Workflow:
    1. Calculate MCDA score for patient
    2. Determine decision type based on thresholds
    3. Calculate confidence level
    4. Generate LLM explanation
    5. Return complete decision
    """
    
    def __init__(
        self,
        mcda_calculator: Optional[MCDACalculator] = None,
        llm_reasoning: Optional[LLMReasoning] = None,
        uncertainty_calculator: Optional[UncertaintyCalculator] = None
    ):
        """
        Initialize the decision engine.
        
        Args:
            mcda_calculator: MCDA scoring engine
            llm_reasoning: LLM explanation generator
            uncertainty_calculator: Confidence scorer
        """
        self.mcda = mcda_calculator or MCDACalculator()
        self.llm = llm_reasoning or LLMReasoning()
        self.uncertainty = uncertainty_calculator or UncertaintyCalculator()
        
        # Get thresholds from config
        thresholds = Config.get_decision_thresholds()
        self.escalate_threshold = thresholds.escalate_threshold
        self.observe_threshold = thresholds.observe_threshold
        self.low_capacity_threshold = thresholds.low_capacity_threshold
        self.confidence_threshold = thresholds.confidence_threshold
        
        logger.info("Decision Engine initialized")

    async def evaluate_patient(
        self,
        patient: Patient,
        capacity: CapacitySnapshot,
        flow_recommendations: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> EscalationDecision:
        """
        Evaluate a patient and produce an escalation decision.
        
        Args:
            patient: Patient to evaluate
            capacity: Current hospital capacity
            flow_recommendations: Recommendations from Flow Orchestrator
            context: Additional context
            
        Returns:
            Complete EscalationDecision with reasoning
        """
        flow_recommendations = flow_recommendations or []
        context = context or {}
        
        logger.info(f"Evaluating patient {patient.id}")
        
        # 1. Calculate MCDA score
        mcda_score = self.mcda.compute_weighted_score(patient, capacity)
        
        # 2. Determine decision type
        decision_type = self._determine_decision_type(mcda_score, patient, capacity)
        
        # 3. Determine urgency
        urgency = self._determine_urgency(mcda_score, patient, decision_type)
        
        # 4. Calculate confidence
        confidence = self.uncertainty.calculate_confidence(
            mcda_score=mcda_score,
            data_freshness=datetime.now() - patient.last_updated,
            prediction_variance=context.get('prediction_variance', 0.1)
        )
        
        # 5. Build context for LLM
        llm_context = self._build_llm_context(capacity, flow_recommendations, context)
        
        # 6. Generate explanation
        reasoning = await self.llm.generate_explanation(
            patient=patient,
            decision_type=decision_type,
            mcda_score=mcda_score,
            context=llm_context
        )
        
        # 7. Extract contributing factors
        contributing_factors = self.llm.extract_contributing_factors(
            patient=patient,
            mcda_score=mcda_score,
            context=llm_context
        )
        
        # 8. Determine target unit
        target_unit = self._determine_target_unit(patient, capacity, decision_type)
        
        # 9. Generate recommended action
        recommended_action = self._generate_recommended_action(
            decision_type, urgency, target_unit, patient
        )
        
        # 10. Build and return decision
        decision = EscalationDecision(
            id=f"dec_{uuid.uuid4().hex[:12]}",
            patient_id=patient.id,
            timestamp=datetime.now(),
            decision_type=decision_type,
            urgency=urgency,
            priority_score=mcda_score.weighted_total * 100,
            mcda_breakdown=mcda_score,
            reasoning=reasoning,
            contributing_factors=contributing_factors,
            confidence=confidence,
            requires_human_review=confidence < self.confidence_threshold,
            recommended_action=recommended_action,
            target_unit=target_unit,
            context=llm_context
        )
        
        logger.info(
            f"Decision for {patient.id}: {decision_type.value} "
            f"(score: {mcda_score.weighted_total:.2f}, confidence: {confidence:.2f})"
        )
        
        return decision

    def _determine_decision_type(
        self,
        mcda_score: MCDAScore,
        patient: Patient,
        capacity: CapacitySnapshot
    ) -> DecisionType:
        """
        Determine the decision type based on MCDA score and thresholds.
        """
        score = mcda_score.weighted_total
        
        # Critical override: always escalate if vitals are critical
        if patient.vitals.is_critical():
            logger.debug(f"Critical vitals override for {patient.id}")
            return DecisionType.ESCALATE
        
        # High score = escalate
        if score >= self.escalate_threshold:
            return DecisionType.ESCALATE
        
        # Low capacity = delay (unless urgent)
        if mcda_score.capacity_score < self.low_capacity_threshold:
            if mcda_score.risk_score < 0.6:  # Not too high risk
                return DecisionType.DELAY
        
        # Medium score = observe
        if score >= self.observe_threshold:
            return DecisionType.OBSERVE
        
        # Check if reprioritization is needed
        if mcda_score.wait_time_score > 0.7 and mcda_score.risk_score < 0.5:
            return DecisionType.REPRIORITIZE
        
        # Default to observe
        return DecisionType.OBSERVE

    def _determine_urgency(
        self,
        mcda_score: MCDAScore,
        patient: Patient,
        decision_type: DecisionType
    ) -> UrgencyLevel:
        """Determine the urgency level of the decision."""
        
        # Critical conditions = immediate
        if patient.vitals.is_critical():
            return UrgencyLevel.IMMEDIATE
        
        if patient.acuity_level == 1:  # ESI 1
            return UrgencyLevel.IMMEDIATE
        
        # High risk escalation = urgent
        if decision_type == DecisionType.ESCALATE:
            if mcda_score.risk_score >= 0.8:
                return UrgencyLevel.IMMEDIATE
            elif mcda_score.risk_score >= 0.6:
                return UrgencyLevel.URGENT
            else:
                return UrgencyLevel.SOON
        
        # Observe with high wait time = soon
        if decision_type == DecisionType.OBSERVE:
            if mcda_score.wait_time_score >= 0.7:
                return UrgencyLevel.SOON
            return UrgencyLevel.ROUTINE
        
        # Default
        return UrgencyLevel.ROUTINE

    def _build_llm_context(
        self,
        capacity: CapacitySnapshot,
        flow_recommendations: List[str],
        additional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context dictionary for LLM explanation."""
        context = {
            "icu_beds_available": capacity.get_available_beds_by_type(BedType.ICU),
            "er_beds_available": capacity.get_available_beds_by_type(BedType.ER),
            "general_beds_available": capacity.get_available_beds_by_type(BedType.GENERAL),
            "overall_occupancy": capacity.overall_occupancy_rate,
            "predicted_discharges_1h": capacity.predicted_discharges_1h,
            "flow_recommendations": flow_recommendations,
        }
        context.update(additional_context)
        return context

    def _determine_target_unit(
        self,
        patient: Patient,
        capacity: CapacitySnapshot,
        decision_type: DecisionType
    ) -> Optional[str]:
        """Determine target unit for transfer/escalation."""
        
        if decision_type not in [DecisionType.ESCALATE, DecisionType.TRANSFER]:
            return None
        
        # Determine required type based on patient condition
        required_type = self._get_required_unit_type(patient)
        
        # Find available unit
        units = capacity.get_units_by_type(required_type)
        for unit in units:
            if unit.available_beds > 0:
                return unit.id
        
        # Try alternatives
        alternatives = self._get_alternative_types(required_type)
        for alt_type in alternatives:
            alt_units = capacity.get_units_by_type(alt_type)
            for unit in alt_units:
                if unit.available_beds > 0:
                    return unit.id
        
        return None

    def _get_required_unit_type(self, patient: Patient) -> BedType:
        """Get required unit type based on patient condition."""
        if patient.acuity_level <= 2:  # ESI 1-2
            return BedType.ICU
        elif patient.risk_factors.cardiac_risk > 0.5:
            return BedType.CARDIAC
        elif patient.acuity_level == 3:
            return BedType.ER
        else:
            return BedType.GENERAL

    def _get_alternative_types(self, primary: BedType) -> List[BedType]:
        """Get alternative unit types."""
        alternatives = {
            BedType.ICU: [BedType.CARDIAC, BedType.ER],
            BedType.CARDIAC: [BedType.ICU],
            BedType.ER: [BedType.GENERAL],
            BedType.GENERAL: [],
        }
        return alternatives.get(primary, [])

    def _generate_recommended_action(
        self,
        decision_type: DecisionType,
        urgency: UrgencyLevel,
        target_unit: Optional[str],
        patient: Patient
    ) -> str:
        """Generate specific recommended action string."""
        
        if decision_type == DecisionType.ESCALATE:
            if urgency == UrgencyLevel.IMMEDIATE:
                return f"IMMEDIATE transfer to {target_unit or 'higher care'}. Notify attending physician."
            elif urgency == UrgencyLevel.URGENT:
                return f"Transfer to {target_unit or 'higher care'} within 15 minutes."
            else:
                return f"Schedule transfer to {target_unit or 'appropriate unit'} when ready."
        
        elif decision_type == DecisionType.OBSERVE:
            if patient.risk_score >= 50:
                return "Continue monitoring. Reassess in 15 minutes. Alert if vitals change."
            else:
                return "Continue current care plan. Standard reassessment interval."
        
        elif decision_type == DecisionType.DELAY:
            return "Hold current position. Will notify when resources available."
        
        elif decision_type == DecisionType.REPRIORITIZE:
            return f"Queue position updated. Current priority score: {patient.risk_score:.0f}."
        
        else:
            return "Pending further evaluation."

    async def batch_evaluate(
        self,
        patients: List[Patient],
        capacity: CapacitySnapshot,
        context: Optional[Dict[str, Any]] = None
    ) -> List[EscalationDecision]:
        """
        Evaluate multiple patients and return sorted decisions.
        
        Args:
            patients: List of patients to evaluate
            capacity: Current capacity snapshot
            context: Additional context
            
        Returns:
            List of decisions sorted by priority (highest first)
        """
        decisions = []
        
        for patient in patients:
            decision = await self.evaluate_patient(
                patient=patient,
                capacity=capacity,
                context=context
            )
            decisions.append(decision)
        
        # Sort by priority (highest first)
        decisions.sort(key=lambda d: d.priority_score, reverse=True)
        
        logger.info(f"Batch evaluated {len(patients)} patients")
        return decisions
