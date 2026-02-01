"""
State manager for AdaptiveCare system.
Centralized state management for patients, capacity, and decisions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from backend.models.patient import Patient, PatientQueue
from backend.models.hospital import CapacitySnapshot, Unit
from backend.models.decision import EscalationDecision, DecisionHistory

logger = logging.getLogger(__name__)


class StateManager:
    """
    Central state management for all agents.
    
    Maintains:
    - Patient registry and queue
    - Hospital capacity state
    - Decision history
    - Agent outputs cache
    """
    
    def __init__(self):
        """Initialize the state manager."""
        self._patients: Dict[str, Patient] = {}
        self._capacity: Optional[CapacitySnapshot] = None
        self._decisions: DecisionHistory = DecisionHistory()
        self._agent_outputs: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._last_updated: Dict[str, datetime] = {}
        
        logger.info("StateManager initialized")

    # ========================
    # Patient Management
    # ========================
    
    async def add_patient(self, patient: Patient) -> None:
        """Add a new patient to the registry."""
        async with self._lock:
            self._patients[patient.id] = patient
            self._last_updated[f"patient_{patient.id}"] = datetime.now()
            logger.info(f"Added patient: {patient.id}")

    async def update_patient(self, patient: Patient) -> None:
        """Update an existing patient."""
        async with self._lock:
            patient.last_updated = datetime.now()
            self._patients[patient.id] = patient
            self._last_updated[f"patient_{patient.id}"] = datetime.now()
            logger.debug(f"Updated patient: {patient.id}")

    async def remove_patient(self, patient_id: str) -> Optional[Patient]:
        """Remove a patient from the registry."""
        async with self._lock:
            patient = self._patients.pop(patient_id, None)
            if patient:
                logger.info(f"Removed patient: {patient_id}")
            return patient

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID."""
        return self._patients.get(patient_id)

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return list(self._patients.values())

    def get_patient_queue(self) -> PatientQueue:
        """Get all patients as a queue."""
        return PatientQueue(patients=self.get_all_patients())

    def get_patients_by_location(self, location: str) -> List[Patient]:
        """Get patients in a specific location."""
        return [p for p in self._patients.values() if p.current_location == location]

    def get_high_risk_patients(self, threshold: float = 70.0) -> List[Patient]:
        """Get patients with risk score above threshold."""
        return [p for p in self._patients.values() if p.risk_score >= threshold]

    def get_patient_count(self) -> int:
        """Get total number of patients."""
        return len(self._patients)

    # ========================
    # Capacity Management
    # ========================
    
    async def update_capacity(self, snapshot: CapacitySnapshot) -> None:
        """Update the capacity snapshot."""
        async with self._lock:
            self._capacity = snapshot
            self._last_updated["capacity"] = datetime.now()
            logger.debug("Updated capacity snapshot")

    def get_capacity(self) -> Optional[CapacitySnapshot]:
        """Get current capacity snapshot."""
        return self._capacity

    def get_unit_capacity(self, unit_id: str) -> Optional[Unit]:
        """Get capacity for a specific unit."""
        if self._capacity:
            return self._capacity.get_unit(unit_id)
        return None

    def get_available_beds(self, unit_type: Optional[str] = None) -> int:
        """Get total available beds, optionally filtered by type."""
        if not self._capacity:
            return 0
        if unit_type:
            from backend.models.hospital import BedType
            try:
                bed_type = BedType(unit_type)
                return self._capacity.get_available_beds_by_type(bed_type)
            except ValueError:
                return 0
        return self._capacity.total_available

    # ========================
    # Decision Management
    # ========================
    
    async def add_decision(self, decision: EscalationDecision) -> None:
        """Add a decision to history (async)."""
        async with self._lock:
            self._decisions.add_decision(decision)
            self._last_updated[f"decision_{decision.id}"] = datetime.now()
            logger.info(f"Added decision: {decision.id} for patient {decision.patient_id}")
    
    def add_decision_sync(self, decision: EscalationDecision) -> None:
        """Add a decision to history (sync, for use from background threads)."""
        self._decisions.add_decision(decision)
        self._last_updated[f"decision_{decision.id}"] = datetime.now()
        logger.info(f"Added decision (sync): {decision.id} for patient {decision.patient_id}")

    def get_decisions(self, patient_id: Optional[str] = None) -> List[EscalationDecision]:
        """Get decisions, optionally filtered by patient."""
        if patient_id:
            return self._decisions.get_for_patient(patient_id)
        return self._decisions.decisions

    def get_recent_decisions(self, count: int = 10) -> List[EscalationDecision]:
        """Get most recent decisions."""
        return self._decisions.get_recent(count)

    def get_pending_review_decisions(self) -> List[EscalationDecision]:
        """Get decisions requiring human review."""
        return self._decisions.get_pending_review()

    async def mark_decision_executed(
        self, 
        decision_id: str, 
        executed_by: Optional[str] = None
    ) -> bool:
        """Mark a decision as executed."""
        async with self._lock:
            for decision in self._decisions.decisions:
                if decision.id == decision_id:
                    decision.is_executed = True
                    decision.executed_at = datetime.now()
                    decision.executed_by = executed_by
                    logger.info(f"Marked decision {decision_id} as executed")
                    return True
            return False

    # ========================
    # Agent Output Management
    # ========================
    
    async def store_agent_output(
        self, 
        agent_name: str, 
        key: str, 
        value: Any
    ) -> None:
        """Store output from an agent for cross-agent access."""
        async with self._lock:
            self._agent_outputs[agent_name][key] = {
                "value": value,
                "timestamp": datetime.now()
            }
            logger.debug(f"Stored output from {agent_name}: {key}")

    def get_agent_output(
        self, 
        agent_name: str, 
        key: str
    ) -> Optional[Any]:
        """Get stored output from an agent."""
        agent_data = self._agent_outputs.get(agent_name, {})
        output_data = agent_data.get(key)
        if output_data:
            return output_data["value"]
        return None

    def get_all_agent_outputs(self, agent_name: str) -> Dict[str, Any]:
        """Get all stored outputs from an agent."""
        agent_data = self._agent_outputs.get(agent_name, {})
        return {k: v["value"] for k, v in agent_data.items()}

    # ========================
    # Risk Assessment Storage
    # ========================
    
    async def update_patient_risk(
        self, 
        patient_id: str, 
        risk_score: float,
        risk_factors: Optional[Dict[str, float]] = None
    ) -> bool:
        """Update patient risk score from Risk Monitor Agent."""
        patient = self.get_patient(patient_id)
        if not patient:
            return False
        
        async with self._lock:
            patient.risk_score = risk_score
            if risk_factors:
                for key, value in risk_factors.items():
                    if hasattr(patient.risk_factors, key):
                        setattr(patient.risk_factors, key, value)
                    else:
                        patient.risk_factors.custom_factors[key] = value
            patient.last_updated = datetime.now()
            self._patients[patient_id] = patient
            logger.debug(f"Updated risk for patient {patient_id}: {risk_score}")
        return True

    # ========================
    # State Summary
    # ========================
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for debugging/monitoring."""
        return {
            "patients": {
                "total": self.get_patient_count(),
                "high_risk": len(self.get_high_risk_patients()),
                "last_updated": self._last_updated.get("patients")
            },
            "capacity": {
                "available_beds": self.get_available_beds() if self._capacity else 0,
                "total_beds": self._capacity.total_beds if self._capacity else 0,
                "occupancy_rate": self._capacity.overall_occupancy_rate if self._capacity else 0,
                "last_updated": self._last_updated.get("capacity")
            },
            "decisions": {
                "total": len(self._decisions.decisions),
                "pending_review": len(self.get_pending_review_decisions()),
                "recent_5": [d.id for d in self.get_recent_decisions(5)]
            },
            "agents": list(self._agent_outputs.keys())
        }

    async def clear_all(self) -> None:
        """Clear all state (for testing/reset)."""
        async with self._lock:
            self._patients.clear()
            self._capacity = None
            self._decisions = DecisionHistory()
            self._agent_outputs.clear()
            self._last_updated.clear()
            logger.info("All state cleared")


# Singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the singleton state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
