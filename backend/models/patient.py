"""
Patient models for AdaptiveCare hospital patient flow system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientStatus(str, Enum):
    """Current status of a patient in the hospital."""
    WAITING = "waiting"
    IN_TREATMENT = "in_treatment"
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    CRITICAL = "critical"


class AcuityLevel(int, Enum):
    """Emergency Severity Index (ESI) scale 1-5."""
    RESUSCITATION = 1  # Immediate life-saving intervention required
    EMERGENT = 2       # High risk situation
    URGENT = 3         # Stable but needs multiple resources
    LESS_URGENT = 4    # Stable, needs one resource
    NON_URGENT = 5     # Stable, no resources needed


class VitalSigns(BaseModel):
    """Patient vital signs measurement."""
    heart_rate: float = Field(..., ge=0, le=300, description="BPM")
    systolic_bp: float = Field(..., ge=0, le=300, description="mmHg")
    diastolic_bp: float = Field(..., ge=0, le=200, description="mmHg")
    spo2: float = Field(..., ge=0, le=100, description="Oxygen saturation %")
    temperature: float = Field(..., ge=30, le=45, description="Celsius")
    respiratory_rate: Optional[float] = Field(None, ge=0, le=60, description="Breaths/min")
    measured_at: datetime = Field(default_factory=datetime.now)

    @property
    def blood_pressure(self) -> str:
        """Return formatted blood pressure string."""
        return f"{self.systolic_bp:.0f}/{self.diastolic_bp:.0f}"

    def is_critical(self) -> bool:
        """Check if vitals indicate critical condition."""
        return (
            self.heart_rate < 40 or self.heart_rate > 150 or
            self.systolic_bp < 80 or self.systolic_bp > 200 or
            self.spo2 < 90 or
            self.temperature < 35 or self.temperature > 40
        )


class RiskFactors(BaseModel):
    """Risk factors contributing to patient risk score."""
    sepsis_probability: float = Field(0.0, ge=0, le=1)
    cardiac_risk: float = Field(0.0, ge=0, le=1)
    respiratory_risk: float = Field(0.0, ge=0, le=1)
    deterioration_trend: float = Field(0.0, ge=-1, le=1, description="Negative = improving, Positive = worsening")
    comorbidity_score: float = Field(0.0, ge=0, le=1)
    custom_factors: Dict[str, float] = Field(default_factory=dict)


class Patient(BaseModel):
    """Core patient model representing a patient in the hospital system."""
    id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., description="Patient full name")
    age: int = Field(..., ge=0, le=150)
    gender: str = Field(..., pattern="^(M|F|O)$", description="M/F/O")
    
    # Location and timing
    admission_time: datetime = Field(default_factory=datetime.now)
    current_location: str = Field(..., description="Current unit/bed")
    target_location: Optional[str] = Field(None, description="Recommended destination")
    
    # Medical information
    chief_complaint: str = Field(..., description="Primary reason for visit")
    diagnosis: Optional[str] = Field(None, description="Working diagnosis")
    comorbidities: List[str] = Field(default_factory=list)
    
    # Current state
    vitals: VitalSigns
    status: PatientStatus = PatientStatus.WAITING
    acuity_level: AcuityLevel = AcuityLevel.URGENT
    
    # Risk assessment (populated by Risk Monitor Agent)
    risk_score: float = Field(0.0, ge=0, le=100, description="Overall risk score 0-100")
    risk_factors: RiskFactors = Field(default_factory=RiskFactors)
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    notes: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    @property
    def wait_time_minutes(self) -> int:
        """Calculate current wait time in minutes."""
        return int((datetime.now() - self.admission_time).total_seconds() / 60)

    @property
    def is_high_risk(self) -> bool:
        """Check if patient is considered high risk."""
        return self.risk_score >= 70 or self.acuity_level <= AcuityLevel.EMERGENT

    def to_summary(self) -> Dict[str, Any]:
        """Return a summary dict for frontend display."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "status": self.status,
            "acuity_level": self.acuity_level,
            "risk_score": self.risk_score,
            "wait_time_minutes": self.wait_time_minutes,
            "current_location": self.current_location,
            "chief_complaint": self.chief_complaint,
            "is_critical": self.vitals.is_critical()
        }


class PatientQueue(BaseModel):
    """A queue of patients sorted by priority."""
    patients: List[Patient] = Field(default_factory=list)
    
    def get_sorted_by_risk(self) -> List[Patient]:
        """Return patients sorted by risk score (highest first)."""
        return sorted(self.patients, key=lambda p: p.risk_score, reverse=True)
    
    def get_sorted_by_acuity(self) -> List[Patient]:
        """Return patients sorted by acuity level (most urgent first)."""
        return sorted(self.patients, key=lambda p: p.acuity_level.value)
    
    def get_critical_patients(self) -> List[Patient]:
        """Return only critical/high-risk patients."""
        return [p for p in self.patients if p.is_high_risk or p.vitals.is_critical()]
