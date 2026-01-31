"""
FastAPI main application for AdaptiveCare backend.
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.core.config import Config
from backend.core.event_bus import get_event_bus
from backend.core.state_manager import get_state_manager
from backend.agents.escalation_decision import EscalationDecisionAgent, AgentInput
from backend.reasoning.decision_engine import DecisionEngine
from backend.reasoning.mcda import MCDACalculator
from backend.reasoning.llm_reasoning import LLMReasoning
from backend.models.patient import Patient, PatientStatus, AcuityLevel, VitalSigns, RiskFactors
from backend.models.hospital import CapacitySnapshot, Unit, Bed, BedType, BedStatus, StaffMember, StaffRole
from backend.models.decision import DecisionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
event_bus = None
state_manager = None
escalation_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global event_bus, state_manager, escalation_agent
    
    logger.info("Starting AdaptiveCare backend...")
    
    # Initialize core components
    event_bus = get_event_bus()
    state_manager = get_state_manager()
    
    # Initialize decision engine
    mcda = MCDACalculator()
    llm = LLMReasoning()
    decision_engine = DecisionEngine(mcda, llm)
    
    # Initialize escalation agent
    escalation_agent = EscalationDecisionAgent(
        event_bus=event_bus,
        state_manager=state_manager,
        decision_engine=decision_engine
    )
    await escalation_agent.start()
    
    # Initialize sample data for demo
    await _initialize_sample_data()
    
    logger.info("AdaptiveCare backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AdaptiveCare backend...")
    await escalation_agent.stop()
    event_bus.stop()
    logger.info("Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AdaptiveCare API",
    description="Multi-agent hospital patient flow system API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================
# Request/Response Models
# ========================

class PatientSummary(BaseModel):
    id: str
    name: str
    age: int
    status: str
    acuity_level: int
    risk_score: float
    wait_time_minutes: int
    current_location: str
    chief_complaint: str
    is_critical: bool


class DecisionSummary(BaseModel):
    id: str
    patient_id: str
    decision_type: str
    urgency: str
    priority_score: float
    reasoning: str
    timestamp: str


class CapacitySummary(BaseModel):
    total_beds: int
    total_available: int
    overall_occupancy_rate: float
    units: list


class SimulateRiskRequest(BaseModel):
    patient_id: str
    new_risk_score: float = Field(..., ge=0, le=100)
    risk_factors: Optional[dict] = None


class EvaluatePatientRequest(BaseModel):
    patient_id: str


# ========================
# API Endpoints
# ========================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AdaptiveCare API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "event_bus": "running" if event_bus else "not initialized",
            "state_manager": "running" if state_manager else "not initialized",
            "escalation_agent": "running" if escalation_agent and escalation_agent.is_running else "not running"
        },
        "config": {
            "debug": Config.DEBUG,
            "llm_configured": bool(Config.ANTHROPIC_API_KEY)
        }
    }


# ========================
# Patient Endpoints
# ========================

@app.get("/api/patients", response_model=List[PatientSummary])
async def get_patients(
    sort_by: str = Query("risk", regex="^(risk|acuity|wait_time|name)$"),
    limit: int = Query(50, ge=1, le=100)
):
    """Get all patients with optional sorting."""
    patients = state_manager.get_all_patients()
    
    # Sort
    if sort_by == "risk":
        patients.sort(key=lambda p: p.risk_score, reverse=True)
    elif sort_by == "acuity":
        patients.sort(key=lambda p: p.acuity_level)
    elif sort_by == "wait_time":
        patients.sort(key=lambda p: p.wait_time_minutes, reverse=True)
    elif sort_by == "name":
        patients.sort(key=lambda p: p.name)
    
    # Limit and convert
    return [PatientSummary(**p.to_summary()) for p in patients[:limit]]


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get detailed patient information."""
    patient = state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {
        "patient": patient.model_dump(),
        "decisions": [d.to_frontend_format() for d in state_manager.get_decisions(patient_id)]
    }


@app.get("/api/patients/{patient_id}/decisions")
async def get_patient_decisions(patient_id: str):
    """Get decision history for a patient."""
    patient = state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    decisions = state_manager.get_decisions(patient_id)
    return {
        "patient_id": patient_id,
        "decisions": [d.to_frontend_format() for d in decisions]
    }


# ========================
# Capacity Endpoints
# ========================

@app.get("/api/capacity")
async def get_capacity():
    """Get current hospital capacity snapshot."""
    capacity = state_manager.get_capacity()
    if not capacity:
        raise HTTPException(status_code=404, detail="No capacity data available")
    
    return capacity.to_summary()


@app.get("/api/capacity/{unit_id}")
async def get_unit_capacity(unit_id: str):
    """Get capacity for a specific unit."""
    capacity = state_manager.get_capacity()
    if not capacity:
        raise HTTPException(status_code=404, detail="No capacity data available")
    
    unit = capacity.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return unit.to_summary()


# ========================
# Decision Endpoints
# ========================

@app.get("/api/decisions")
async def get_decisions(
    limit: int = Query(20, ge=1, le=100),
    patient_id: Optional[str] = None
):
    """Get recent decisions."""
    if patient_id:
        decisions = state_manager.get_decisions(patient_id)
    else:
        decisions = state_manager.get_recent_decisions(limit)
    
    return {
        "decisions": [d.to_frontend_format() for d in decisions],
        "total": len(decisions)
    }


@app.get("/api/decisions/pending-review")
async def get_pending_review():
    """Get decisions requiring human review."""
    decisions = state_manager.get_pending_review_decisions()
    return {
        "decisions": [d.to_frontend_format() for d in decisions],
        "count": len(decisions)
    }


@app.post("/api/decisions/{decision_id}/acknowledge")
async def acknowledge_decision(decision_id: str, executed_by: str = "system"):
    """Mark a decision as executed/acknowledged."""
    success = await state_manager.mark_decision_executed(decision_id, executed_by)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return {"status": "acknowledged", "decision_id": decision_id}


# ========================
# Evaluation Endpoints
# ========================

@app.post("/api/evaluate")
async def evaluate_patient(request: EvaluatePatientRequest):
    """Trigger evaluation for a specific patient."""
    output = await escalation_agent.evaluate_patient_by_id(request.patient_id)
    if not output:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return output.to_dict()


@app.post("/api/evaluate/batch")
async def batch_evaluate(patient_ids: Optional[List[str]] = None):
    """Trigger batch evaluation for multiple or all patients."""
    result = await escalation_agent.batch_evaluate(patient_ids)
    return {
        "total_patients": result.total_patients,
        "evaluated": result.evaluated_patients,
        "escalations": result.escalations,
        "pending_review": result.pending_review,
        "processing_time_ms": result.processing_time_ms,
        "decisions": [d.to_dict() for d in result.decisions]
    }


# ========================
# Simulation Endpoints
# ========================

@app.post("/api/simulate/risk-spike")
async def simulate_risk_spike(request: SimulateRiskRequest):
    """Simulate a risk score change for testing."""
    patient = state_manager.get_patient(request.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    old_score = patient.risk_score
    
    # Update risk
    await state_manager.update_patient_risk(
        request.patient_id,
        request.new_risk_score,
        request.risk_factors
    )
    
    # Trigger re-evaluation
    output = await escalation_agent.evaluate_patient_by_id(request.patient_id)
    
    return {
        "patient_id": request.patient_id,
        "old_risk_score": old_score,
        "new_risk_score": request.new_risk_score,
        "decision": output.to_dict() if output else None
    }


@app.post("/api/simulate/capacity-change")
async def simulate_capacity_change(
    unit_id: str,
    beds_change: int = Query(..., ge=-10, le=10)
):
    """Simulate a capacity change in a unit."""
    capacity = state_manager.get_capacity()
    if not capacity:
        raise HTTPException(status_code=404, detail="No capacity data")
    
    unit = capacity.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Update beds
    old_available = unit.available_beds
    
    # Modify bed statuses
    change_count = abs(beds_change)
    for bed in unit.beds[:change_count]:
        if beds_change > 0:
            bed.status = BedStatus.AVAILABLE
        else:
            bed.status = BedStatus.OCCUPIED
    
    # Save updated capacity
    await state_manager.update_capacity(capacity)
    
    return {
        "unit_id": unit_id,
        "old_available": old_available,
        "new_available": unit.available_beds,
        "change": beds_change
    }


# ========================
# Stats Endpoints
# ========================

@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    return {
        "state": state_manager.get_state_summary(),
        "agent": escalation_agent.get_decision_stats() if escalation_agent else {}
    }


@app.get("/api/stats/decisions")
async def get_decision_stats():
    """Get decision statistics."""
    if not escalation_agent:
        raise HTTPException(status_code=503, detail="Agent not running")
    return escalation_agent.get_decision_stats()


# ========================
# Sample Data Initialization
# ========================

async def _initialize_sample_data():
    """Initialize sample data for demo purposes."""
    logger.info("Initializing sample data...")
    
    # Create sample patients
    sample_patients = [
        Patient(
            id="P001",
            name="John Smith",
            age=67,
            gender="M",
            current_location="ER-Bay-3",
            chief_complaint="Chest pain, shortness of breath",
            vitals=VitalSigns(
                heart_rate=102,
                systolic_bp=158,
                diastolic_bp=95,
                spo2=94,
                temperature=37.2
            ),
            acuity_level=AcuityLevel.EMERGENT,
            risk_score=78,
            risk_factors=RiskFactors(cardiac_risk=0.7, deterioration_trend=0.3)
        ),
        Patient(
            id="P002",
            name="Maria Garcia",
            age=45,
            gender="F",
            current_location="ER-Bay-7",
            chief_complaint="Severe abdominal pain",
            vitals=VitalSigns(
                heart_rate=88,
                systolic_bp=125,
                diastolic_bp=82,
                spo2=98,
                temperature=38.1
            ),
            acuity_level=AcuityLevel.URGENT,
            risk_score=52,
            risk_factors=RiskFactors(sepsis_probability=0.35)
        ),
        Patient(
            id="P003",
            name="Robert Chen",
            age=73,
            gender="M",
            current_location="ER-Bay-1",
            chief_complaint="Altered mental status, fever",
            vitals=VitalSigns(
                heart_rate=115,
                systolic_bp=95,
                diastolic_bp=60,
                spo2=91,
                temperature=39.2
            ),
            acuity_level=AcuityLevel.RESUSCITATION,
            risk_score=92,
            risk_factors=RiskFactors(sepsis_probability=0.85, deterioration_trend=0.6)
        ),
        Patient(
            id="P004",
            name="Emily Johnson",
            age=32,
            gender="F",
            current_location="ER-Bay-5",
            chief_complaint="Migraine, nausea",
            vitals=VitalSigns(
                heart_rate=75,
                systolic_bp=118,
                diastolic_bp=76,
                spo2=99,
                temperature=36.8
            ),
            acuity_level=AcuityLevel.LESS_URGENT,
            risk_score=15,
            risk_factors=RiskFactors()
        ),
        Patient(
            id="P005",
            name="James Wilson",
            age=58,
            gender="M",
            current_location="ER-Bay-2",
            chief_complaint="Diabetic emergency, confusion",
            vitals=VitalSigns(
                heart_rate=98,
                systolic_bp=140,
                diastolic_bp=88,
                spo2=96,
                temperature=36.5
            ),
            acuity_level=AcuityLevel.EMERGENT,
            risk_score=65,
            risk_factors=RiskFactors(deterioration_trend=0.2, comorbidity_score=0.5)
        ),
    ]
    
    for patient in sample_patients:
        await state_manager.add_patient(patient)
    
    # Create sample capacity
    icu_beds = [
        Bed(id=f"ICU-{i}", unit_id="ICU", bed_type=BedType.ICU, 
            status=BedStatus.OCCUPIED if i <= 8 else BedStatus.AVAILABLE)
        for i in range(1, 13)
    ]
    
    er_beds = [
        Bed(id=f"ER-Bay-{i}", unit_id="ER", bed_type=BedType.ER,
            status=BedStatus.OCCUPIED if i <= 6 else BedStatus.AVAILABLE)
        for i in range(1, 11)
    ]
    
    general_beds = [
        Bed(id=f"GEN-{i}", unit_id="GENERAL", bed_type=BedType.GENERAL,
            status=BedStatus.OCCUPIED if i <= 18 else BedStatus.AVAILABLE)
        for i in range(1, 25)
    ]
    
    icu_staff = [
        StaffMember(id=f"N-ICU-{i}", name=f"ICU Nurse {i}", role=StaffRole.NURSE, 
                    unit_id="ICU", current_load=4, max_load=6)
        for i in range(1, 5)
    ]
    
    capacity = CapacitySnapshot(
        units=[
            Unit(id="ICU", name="Intensive Care Unit", unit_type=BedType.ICU, 
                 beds=icu_beds, staff=icu_staff, pending_discharges=1),
            Unit(id="ER", name="Emergency Room", unit_type=BedType.ER, 
                 beds=er_beds, pending_discharges=2),
            Unit(id="GENERAL", name="General Ward", unit_type=BedType.GENERAL, 
                 beds=general_beds, pending_discharges=3)
        ],
        predicted_discharges_1h=2,
        predicted_admissions_1h=1
    )
    
    await state_manager.update_capacity(capacity)
    
    logger.info(f"Initialized {len(sample_patients)} patients and capacity data")


# WebSocket import (separate module)
from backend.api.websocket import router as ws_router
app.include_router(ws_router)
