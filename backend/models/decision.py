"""
Decision models for AdaptiveCare escalation system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Types of escalation decisions."""
    ESCALATE = "escalate"           # Move patient to higher care level (e.g., ER -> ICU)
    OBSERVE = "observe"             # Continue monitoring, no immediate action
    DELAY = "delay"                 # Wait for resources to become available
    REPRIORITIZE = "reprioritize"   # Change queue position based on new information
    DISCHARGE = "discharge"         # Patient ready for discharge
    TRANSFER = "transfer"           # Transfer to different unit at same level


class UrgencyLevel(str, Enum):
    """Urgency of the decision."""
    IMMEDIATE = "immediate"     # Act now
    URGENT = "urgent"           # Within 15 minutes
    SOON = "soon"               # Within 1 hour
    ROUTINE = "routine"         # When convenient


class MCDAWeights(BaseModel):
    """Weights for Multi-Criteria Decision Analysis."""
    risk_weight: float = Field(0.4, ge=0, le=1, description="Weight for patient risk score")
    capacity_weight: float = Field(0.3, ge=0, le=1, description="Weight for capacity availability")
    wait_time_weight: float = Field(0.2, ge=0, le=1, description="Weight for wait time penalty")
    resource_weight: float = Field(0.1, ge=0, le=1, description="Weight for resource matching")

    def validate_sum(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = self.risk_weight + self.capacity_weight + self.wait_time_weight + self.resource_weight
        return abs(total - 1.0) < 0.001

    def to_dict(self) -> Dict[str, float]:
        """Return as dictionary."""
        return {
            "risk": self.risk_weight,
            "capacity": self.capacity_weight,
            "wait_time": self.wait_time_weight,
            "resource": self.resource_weight
        }


class MCDAScore(BaseModel):
    """MCDA scoring breakdown for a decision."""
    # Individual normalized scores (0-1)
    risk_score: float = Field(..., ge=0, le=1, description="Normalized risk score")
    capacity_score: float = Field(..., ge=0, le=1, description="Normalized capacity score")
    wait_time_score: float = Field(..., ge=0, le=1, description="Normalized wait time score")
    resource_score: float = Field(..., ge=0, le=1, description="Normalized resource match score")
    
    # Weighted scores
    weighted_risk: float = Field(..., ge=0, le=1)
    weighted_capacity: float = Field(..., ge=0, le=1)
    weighted_wait_time: float = Field(..., ge=0, le=1)
    weighted_resource: float = Field(..., ge=0, le=1)
    
    # Final score
    weighted_total: float = Field(..., ge=0, le=1, description="Final weighted score")
    
    # Weights used
    weights_used: MCDAWeights = Field(default_factory=MCDAWeights)

    def get_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Return full breakdown for visualization."""
        return {
            "risk": {
                "raw": self.risk_score,
                "weight": self.weights_used.risk_weight,
                "weighted": self.weighted_risk,
                "contribution": (self.weighted_risk / self.weighted_total * 100) if self.weighted_total > 0 else 0
            },
            "capacity": {
                "raw": self.capacity_score,
                "weight": self.weights_used.capacity_weight,
                "weighted": self.weighted_capacity,
                "contribution": (self.weighted_capacity / self.weighted_total * 100) if self.weighted_total > 0 else 0
            },
            "wait_time": {
                "raw": self.wait_time_score,
                "weight": self.weights_used.wait_time_weight,
                "weighted": self.weighted_wait_time,
                "contribution": (self.weighted_wait_time / self.weighted_total * 100) if self.weighted_total > 0 else 0
            },
            "resource": {
                "raw": self.resource_score,
                "weight": self.weights_used.resource_weight,
                "weighted": self.weighted_resource,
                "contribution": (self.weighted_resource / self.weighted_total * 100) if self.weighted_total > 0 else 0
            }
        }

    def get_dominant_factor(self) -> str:
        """Return the factor with highest contribution."""
        factors = {
            "risk": self.weighted_risk,
            "capacity": self.weighted_capacity,
            "wait_time": self.weighted_wait_time,
            "resource": self.weighted_resource
        }
        return max(factors, key=factors.get)


class EscalationDecision(BaseModel):
    """Complete escalation decision with reasoning."""
    id: str = Field(..., description="Unique decision ID")
    patient_id: str = Field(..., description="Patient this decision is for")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Decision details
    decision_type: DecisionType
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    priority_score: float = Field(..., ge=0, le=100, description="Priority score 0-100")
    
    # MCDA breakdown
    mcda_breakdown: MCDAScore
    
    # Reasoning (LLM-generated)
    reasoning: str = Field(..., description="Human-readable explanation")
    contributing_factors: List[str] = Field(default_factory=list, description="Key factors")
    
    # Confidence
    confidence: float = Field(..., ge=0, le=1, description="Decision confidence 0-1")
    requires_human_review: bool = Field(False, description="Flag for low-confidence decisions")
    
    # Action details
    recommended_action: str = Field(..., description="Specific action to take")
    target_unit: Optional[str] = Field(None, description="Target unit for transfer/escalation")
    target_bed: Optional[str] = Field(None, description="Specific bed if assigned")
    
    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Status tracking
    is_executed: bool = Field(False, description="Whether action has been taken")
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None

    class Config:
        use_enum_values = True

    def to_frontend_format(self) -> Dict[str, Any]:
        """Format for frontend display."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "timestamp": self.timestamp.isoformat(),
            "decision_type": self.decision_type,
            "urgency": self.urgency,
            "priority_score": round(self.priority_score, 1),
            "reasoning": self.reasoning,
            "contributing_factors": self.contributing_factors,
            "confidence": round(self.confidence * 100, 1),
            "requires_human_review": self.requires_human_review,
            "recommended_action": self.recommended_action,
            "target_unit": self.target_unit,
            "mcda_breakdown": self.mcda_breakdown.get_breakdown(),
            "dominant_factor": self.mcda_breakdown.get_dominant_factor(),
            "is_executed": self.is_executed
        }

    def get_color_code(self) -> str:
        """Return color code for frontend based on decision type and urgency."""
        if self.decision_type == DecisionType.ESCALATE:
            if self.urgency == UrgencyLevel.IMMEDIATE:
                return "#FF0000"  # Red
            return "#FF6B00"  # Orange
        elif self.decision_type == DecisionType.OBSERVE:
            return "#FFD700"  # Yellow
        elif self.decision_type == DecisionType.DELAY:
            return "#87CEEB"  # Light blue
        elif self.decision_type == DecisionType.REPRIORITIZE:
            return "#9370DB"  # Purple
        else:
            return "#90EE90"  # Light green


class DecisionHistory(BaseModel):
    """Collection of decisions for tracking and analysis."""
    decisions: List[EscalationDecision] = Field(default_factory=list)

    def add_decision(self, decision: EscalationDecision):
        """Add a decision to history."""
        self.decisions.append(decision)

    def get_for_patient(self, patient_id: str) -> List[EscalationDecision]:
        """Get all decisions for a patient."""
        return [d for d in self.decisions if d.patient_id == patient_id]

    def get_recent(self, count: int = 10) -> List[EscalationDecision]:
        """Get most recent decisions."""
        sorted_decisions = sorted(self.decisions, key=lambda d: d.timestamp, reverse=True)
        return sorted_decisions[:count]

    def get_pending_review(self) -> List[EscalationDecision]:
        """Get decisions requiring human review."""
        return [d for d in self.decisions if d.requires_human_review and not d.is_executed]
