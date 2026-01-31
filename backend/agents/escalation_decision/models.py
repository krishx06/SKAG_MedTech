"""
Models for Escalation Decision Agent.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.models.patient import Patient
from backend.models.hospital import CapacitySnapshot
from backend.models.decision import EscalationDecision


class RiskAssessment(BaseModel):
    """Risk assessment data from Risk Monitor Agent."""
    patient_id: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_factors: Dict[str, float] = Field(default_factory=dict)
    trend: str = Field("stable", pattern="^(increasing|decreasing|stable)$")
    last_updated: datetime = Field(default_factory=datetime.now)
    alerts: List[str] = Field(default_factory=list)


class FlowRecommendation(BaseModel):
    """Flow recommendation from Flow Orchestrator Agent."""
    patient_id: str
    recommended_destination: str
    alternative_destinations: List[str] = Field(default_factory=list)
    estimated_wait_time: int = Field(0, ge=0)
    flow_bottleneck: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)


class AgentInput(BaseModel):
    """
    Input to the Escalation Decision Agent.
    Combines data from all upstream agents.
    """
    patient: Patient
    risk_data: Optional[RiskAssessment] = None
    capacity_data: CapacitySnapshot
    flow_recommendations: Optional[FlowRecommendation] = None
    
    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class AgentOutput(BaseModel):
    """
    Output from the Escalation Decision Agent.
    Contains the decision and any notifications.
    """
    decision: EscalationDecision
    should_notify: bool = False
    notification_targets: List[str] = Field(default_factory=list)
    
    # Additional metadata
    processing_time_ms: float = 0.0
    request_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision": self.decision.to_frontend_format(),
            "should_notify": self.should_notify,
            "notification_targets": self.notification_targets,
            "processing_time_ms": self.processing_time_ms,
            "request_id": self.request_id
        }


class BatchEvaluationRequest(BaseModel):
    """Request for batch patient evaluation."""
    patient_ids: List[str] = Field(default_factory=list)
    include_all: bool = False
    priority_filter: Optional[str] = None  # "high", "medium", "low"


class BatchEvaluationResult(BaseModel):
    """Result of batch patient evaluation."""
    decisions: List[AgentOutput] = Field(default_factory=list)
    total_patients: int = 0
    evaluated_patients: int = 0
    escalations: int = 0
    pending_review: int = 0
    processing_time_ms: float = 0.0
