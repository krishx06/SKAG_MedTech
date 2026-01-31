"""
Event models for inter-agent communication in AdaptiveCare.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the system."""
    # Agent updates
    RISK_UPDATE = "risk_update"
    CAPACITY_UPDATE = "capacity_update"
    FLOW_UPDATE = "flow_update"
    
    # Decisions
    DECISION_MADE = "decision_made"
    DECISION_EXECUTED = "decision_executed"
    
    # Patient events
    PATIENT_ADMITTED = "patient_admitted"
    PATIENT_DISCHARGED = "patient_discharged"
    PATIENT_TRANSFERRED = "patient_transferred"
    PATIENT_VITALS_UPDATED = "patient_vitals_updated"
    
    # System events
    SYSTEM_ALERT = "system_alert"
    SIMULATION_EVENT = "simulation_event"


class AgentType(str, Enum):
    """Types of agents in the system."""
    RISK_MONITOR = "risk_monitor"
    CAPACITY_INTELLIGENCE = "capacity_intelligence"
    FLOW_ORCHESTRATOR = "flow_orchestrator"
    ESCALATION_DECISION = "escalation_decision"
    SYSTEM = "system"


class AgentEvent(BaseModel):
    """Base event class for inter-agent communication."""
    id: str = Field(..., description="Unique event ID")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    source_agent: AgentType
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Optional metadata
    priority: int = Field(5, ge=1, le=10, description="Event priority 1-10 (10=highest)")
    correlation_id: Optional[str] = Field(None, description="ID linking related events")
    
    class Config:
        use_enum_values = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "payload": self.payload,
            "priority": self.priority,
            "correlation_id": self.correlation_id
        }


class RiskUpdateEvent(AgentEvent):
    """Event emitted by Risk Monitor Agent when patient risk changes."""
    event_type: EventType = EventType.RISK_UPDATE
    source_agent: AgentType = AgentType.RISK_MONITOR
    
    # Risk-specific payload
    patient_id: str
    old_score: float = Field(..., ge=0, le=100)
    new_score: float = Field(..., ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)
    trend: str = Field("stable", pattern="^(increasing|decreasing|stable)$")
    alert_triggered: bool = False

    @property
    def score_delta(self) -> float:
        """Change in risk score."""
        return self.new_score - self.old_score

    @property
    def is_significant_change(self) -> bool:
        """Check if change is significant (>10 points)."""
        return abs(self.score_delta) >= 10


class CapacityUpdateEvent(AgentEvent):
    """Event emitted by Capacity Intelligence Agent when capacity changes."""
    event_type: EventType = EventType.CAPACITY_UPDATE
    source_agent: AgentType = AgentType.CAPACITY_INTELLIGENCE
    
    # Capacity-specific payload
    unit_id: str
    unit_name: str
    availability_change: int = Field(..., description="Positive = more available, negative = less")
    new_available: int
    new_occupancy_rate: float = Field(..., ge=0, le=100)
    predicted_change_1h: int = Field(0, description="Predicted change in next hour")
    
    @property
    def is_critical_capacity(self) -> bool:
        """Check if capacity is critically low."""
        return self.new_available <= 1 or self.new_occupancy_rate >= 95


class FlowUpdateEvent(AgentEvent):
    """Event emitted by Flow Orchestrator Agent with flow recommendations."""
    event_type: EventType = EventType.FLOW_UPDATE
    source_agent: AgentType = AgentType.FLOW_ORCHESTRATOR
    
    # Flow-specific payload
    patient_id: str
    recommended_destination: str
    alternative_destinations: List[str] = Field(default_factory=list)
    estimated_wait_time: int = Field(..., ge=0, description="Minutes")
    flow_bottleneck: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)


class DecisionEvent(AgentEvent):
    """Event emitted by Escalation Decision Agent when a decision is made."""
    event_type: EventType = EventType.DECISION_MADE
    source_agent: AgentType = AgentType.ESCALATION_DECISION
    
    # Decision-specific payload (reference to full decision)
    decision_id: str
    patient_id: str
    decision_type: str
    priority_score: float
    reasoning_summary: str
    requires_acknowledgment: bool = False


class PatientEvent(AgentEvent):
    """Base event for patient-related changes."""
    patient_id: str
    patient_name: Optional[str] = None


class PatientAdmittedEvent(PatientEvent):
    """Event when a new patient is admitted."""
    event_type: EventType = EventType.PATIENT_ADMITTED
    source_agent: AgentType = AgentType.SYSTEM
    
    admission_unit: str
    chief_complaint: str
    acuity_level: int = Field(..., ge=1, le=5)


class PatientDischargedEvent(PatientEvent):
    """Event when a patient is discharged."""
    event_type: EventType = EventType.PATIENT_DISCHARGED
    source_agent: AgentType = AgentType.SYSTEM
    
    discharge_unit: str
    length_of_stay_hours: float
    destination: str = "home"  # home, transfer, AMA, deceased


class VitalsUpdateEvent(PatientEvent):
    """Event when patient vitals are updated."""
    event_type: EventType = EventType.PATIENT_VITALS_UPDATED
    source_agent: AgentType = AgentType.SYSTEM
    
    vitals: Dict[str, float]
    is_critical: bool = False


class SystemAlertEvent(AgentEvent):
    """System-wide alert event."""
    event_type: EventType = EventType.SYSTEM_ALERT
    source_agent: AgentType = AgentType.SYSTEM
    
    alert_level: str = Field("info", pattern="^(info|warning|error|critical)$")
    message: str
    affected_units: List[str] = Field(default_factory=list)
    action_required: bool = False


class SimulationEvent(AgentEvent):
    """Event for simulation control."""
    event_type: EventType = EventType.SIMULATION_EVENT
    source_agent: AgentType = AgentType.SYSTEM
    
    simulation_action: str  # start, stop, pause, scenario_trigger
    scenario_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
