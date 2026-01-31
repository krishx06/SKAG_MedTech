"""
Hospital and capacity models for AdaptiveCare system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class BedStatus(str, Enum):
    """Status of a hospital bed."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class BedType(str, Enum):
    """Type of hospital bed."""
    ICU = "icu"
    GENERAL = "general"
    ER = "er"
    ISOLATION = "isolation"
    PEDIATRIC = "pediatric"
    CARDIAC = "cardiac"


class StaffRole(str, Enum):
    """Hospital staff roles."""
    NURSE = "nurse"
    DOCTOR = "doctor"
    SPECIALIST = "specialist"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class Bed(BaseModel):
    """Individual hospital bed."""
    id: str = Field(..., description="Unique bed identifier")
    unit_id: str = Field(..., description="Parent unit ID")
    bed_type: BedType = BedType.GENERAL
    status: BedStatus = BedStatus.AVAILABLE
    patient_id: Optional[str] = Field(None, description="Current patient if occupied")
    expected_available: Optional[datetime] = Field(None, description="When bed will be free")
    
    def is_available(self) -> bool:
        """Check if bed is available for new patient."""
        return self.status == BedStatus.AVAILABLE


class StaffMember(BaseModel):
    """Hospital staff member."""
    id: str = Field(..., description="Unique staff identifier")
    name: str
    role: StaffRole
    unit_id: str = Field(..., description="Assigned unit")
    current_load: int = Field(0, ge=0, description="Current patient count")
    max_load: int = Field(6, gt=0, description="Maximum patient capacity")
    is_available: bool = Field(True, description="Currently on shift")
    specializations: List[str] = Field(default_factory=list)

    @property
    def load_percentage(self) -> float:
        """Return current load as percentage."""
        return (self.current_load / self.max_load) * 100 if self.max_load > 0 else 0

    @property
    def has_capacity(self) -> bool:
        """Check if staff member can take more patients."""
        return self.is_available and self.current_load < self.max_load


class Unit(BaseModel):
    """Hospital unit (e.g., ICU, ER, General Ward)."""
    id: str = Field(..., description="Unique unit identifier")
    name: str = Field(..., description="Display name")
    unit_type: BedType = Field(..., description="Primary bed type in this unit")
    beds: List[Bed] = Field(default_factory=list)
    staff: List[StaffMember] = Field(default_factory=list)
    pending_discharges: int = Field(0, ge=0, description="Patients pending discharge")
    pending_admissions: int = Field(0, ge=0, description="Patients waiting to be admitted")

    @property
    def total_beds(self) -> int:
        """Total number of beds in the unit."""
        return len(self.beds)

    @property
    def available_beds(self) -> int:
        """Number of available beds."""
        return sum(1 for bed in self.beds if bed.is_available())

    @property
    def occupied_beds(self) -> int:
        """Number of occupied beds."""
        return sum(1 for bed in self.beds if bed.status == BedStatus.OCCUPIED)

    @property
    def occupancy_rate(self) -> float:
        """Current occupancy rate as percentage."""
        if self.total_beds == 0:
            return 0.0
        return (self.occupied_beds / self.total_beds) * 100

    @property
    def available_staff(self) -> int:
        """Number of staff with capacity."""
        return sum(1 for s in self.staff if s.has_capacity)

    @property
    def average_staff_load(self) -> float:
        """Average load percentage across all staff."""
        if not self.staff:
            return 0.0
        return sum(s.load_percentage for s in self.staff) / len(self.staff)

    def get_available_bed(self) -> Optional[Bed]:
        """Get first available bed."""
        for bed in self.beds:
            if bed.is_available():
                return bed
        return None

    def to_summary(self) -> Dict:
        """Return summary for frontend."""
        return {
            "id": self.id,
            "name": self.name,
            "unit_type": self.unit_type,
            "total_beds": self.total_beds,
            "available_beds": self.available_beds,
            "occupancy_rate": round(self.occupancy_rate, 1),
            "pending_discharges": self.pending_discharges,
            "available_staff": self.available_staff,
            "average_staff_load": round(self.average_staff_load, 1)
        }


class CapacitySnapshot(BaseModel):
    """Point-in-time snapshot of hospital capacity."""
    timestamp: datetime = Field(default_factory=datetime.now)
    units: List[Unit] = Field(default_factory=list)
    
    # Predictions from Capacity Intelligence Agent
    predicted_discharges_1h: int = Field(0, description="Predicted discharges in next hour")
    predicted_admissions_1h: int = Field(0, description="Predicted admissions in next hour")
    predicted_bed_availability: Dict[str, int] = Field(
        default_factory=dict, 
        description="Predicted available beds by unit in 1 hour"
    )

    @property
    def total_beds(self) -> int:
        """Total beds across all units."""
        return sum(u.total_beds for u in self.units)

    @property
    def total_available(self) -> int:
        """Total available beds across all units."""
        return sum(u.available_beds for u in self.units)

    @property
    def overall_occupancy_rate(self) -> float:
        """Overall hospital occupancy rate."""
        if self.total_beds == 0:
            return 0.0
        return ((self.total_beds - self.total_available) / self.total_beds) * 100

    def get_unit(self, unit_id: str) -> Optional[Unit]:
        """Get unit by ID."""
        for unit in self.units:
            if unit.id == unit_id:
                return unit
        return None

    def get_units_by_type(self, bed_type: BedType) -> List[Unit]:
        """Get all units of a specific type."""
        return [u for u in self.units if u.unit_type == bed_type]

    def get_available_beds_by_type(self, bed_type: BedType) -> int:
        """Get total available beds of a specific type."""
        return sum(u.available_beds for u in self.get_units_by_type(bed_type))

    def to_summary(self) -> Dict:
        """Return summary for frontend."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_beds": self.total_beds,
            "total_available": self.total_available,
            "overall_occupancy_rate": round(self.overall_occupancy_rate, 1),
            "predicted_discharges_1h": self.predicted_discharges_1h,
            "predicted_admissions_1h": self.predicted_admissions_1h,
            "units": [u.to_summary() for u in self.units],
            "by_type": {
                bed_type.value: self.get_available_beds_by_type(bed_type)
                for bed_type in BedType
            }
        }
