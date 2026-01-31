"""
Risk Monitor Agent data models.
Defines risk assessment outputs and trend tracking structures.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TrendDirection(str, Enum):
    """Patient condition trend"""
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    RAPID_DETERIORATION = "rapid_deterioration"


class RiskLevel(str, Enum):
    """Risk level categories"""
    LOW = "low"              # 0-30
    MODERATE = "moderate"    # 31-60
    HIGH = "high"            # 61-80
    CRITICAL = "critical"    # 81-100


class VitalTrend(BaseModel):
    """Trend analysis for a single vital sign"""
    current_value: float
    previous_value: Optional[float] = None
    change_rate: float = 0.0  # Change per reading
    direction: TrendDirection = TrendDirection.STABLE
    out_of_range: bool = False
    critical: bool = False


class RiskFactorBreakdown(BaseModel):
    """Detailed breakdown of risk score components"""
    vital_signs_score: float = Field(0.0, ge=0, le=40, description="Max 40 points from vitals")
    deterioration_score: float = Field(0.0, ge=0, le=30, description="Max 30 points from trends")
    comorbidity_score: float = Field(0.0, ge=0, le=15, description="Max 15 points from comorbidities")
    acuity_score: float = Field(0.0, ge=0, le=15, description="Max 15 points from acuity level")
    
    @property
    def total_score(self) -> float:
        """Calculate total risk score (0-100)"""
        return min(100.0, self.vital_signs_score + self.deterioration_score + 
                   self.comorbidity_score + self.acuity_score)


class RiskAssessment(BaseModel):
    """
    Complete risk assessment output from Risk Monitor Agent.
    This is the contract that other agents will consume.
    """
    patient_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall risk
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_level: RiskLevel
    trend: TrendDirection
    
    # Breakdown
    risk_breakdown: RiskFactorBreakdown
    
    # Vital trends
    vital_trends: Dict[str, VitalTrend] = Field(default_factory=dict)
    
    # Flags and alerts
    needs_escalation: bool = False
    escalation_reason: Optional[str] = None
    critical_vitals: List[str] = Field(default_factory=list)
    
    # Context
    minutes_since_admission: Optional[int] = None
    previous_risk_score: Optional[float] = None
    risk_score_delta: float = 0.0  # Change from previous assessment
    
    # Recommendations
    recommended_monitoring_frequency: int = Field(15, description="Minutes between checks")
    
    @property
    def is_high_risk(self) -> bool:
        """Check if patient is high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @property
    def is_deteriorating(self) -> bool:
        """Check if patient is deteriorating"""
        return self.trend in [TrendDirection.DETERIORATING, TrendDirection.RAPID_DETERIORATION]
    
    def to_summary(self) -> Dict:
        """Convert to summary dict for display"""
        return {
            "patient_id": self.patient_id,
            "risk_score": round(self.risk_score, 1),
            "risk_level": self.risk_level.value,
            "trend": self.trend.value,
            "needs_escalation": self.needs_escalation,
            "critical_vitals": self.critical_vitals,
            "recommended_monitoring": f"{self.recommended_monitoring_frequency} min"
        }


class PatientRiskHistory(BaseModel):
    """Historical risk assessments for trend analysis"""
    patient_id: str
    assessments: List[RiskAssessment] = Field(default_factory=list, max_length=50)
    
    def add_assessment(self, assessment: RiskAssessment):
        """Add new assessment and maintain history limit"""
        self.assessments.append(assessment)
        if len(self.assessments) > 50:
            self.assessments.pop(0)
    
    @property
    def latest_assessment(self) -> Optional[RiskAssessment]:
        """Get most recent assessment"""
        return self.assessments[-1] if self.assessments else None
    
    @property
    def risk_trajectory(self) -> List[float]:
        """Get risk score trajectory over time"""
        return [a.risk_score for a in self.assessments]
