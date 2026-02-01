"""
Simulation routes for AdaptiveCare API

Provides endpoints for controlling hospital simulation with
integrated Risk Monitor Agent.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.simulation.simulation_orchestrator import get_orchestrator

router = APIRouter()


class SimulationStartRequest(BaseModel):
    """Request to start simulation."""
    scenario: str = Field(default="busy_thursday", description="Scenario name")
    duration: int = Field(default=120, ge=1, le=1440, description="Duration in minutes")
    arrival_rate: float = Field(default=12.5, gt=0, le=100, description="Arrival rate (patients/hour)")


class SimulationControl(BaseModel):
    speed: Optional[float] = 1.0


@router.get("/status")
async def get_simulation_status():
    """Get current simulation status and statistics."""
    orchestrator = get_orchestrator()
    return orchestrator.get_status()


@router.post("/start")
async def start_simulation(request: SimulationStartRequest = SimulationStartRequest()):
    """
    Start hospital simulation with Risk Monitor integration.
    
    The simulation runs in the background and continuously feeds
    patient events to the Risk Monitor Agent.
    """
    orchestrator = get_orchestrator()
    
    result = orchestrator.start_simulation(
        scenario=request.scenario,
        duration=request.duration,
        arrival_rate=request.arrival_rate
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to start"))
    
    return result


@router.post("/stop")
async def stop_simulation():
    """Stop the running simulation gracefully."""
    orchestrator = get_orchestrator()
    
    result = orchestrator.stop_simulation()
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "No simulation running"))
    
    return result


@router.post("/reset")
async def reset_simulation():
    """Reset simulation to initial state, clearing all data."""
    orchestrator = get_orchestrator()
    
    # Stop if running
    if orchestrator.is_running:
        orchestrator.stop_simulation()
    
    # Reset state
    orchestrator.patients.clear()
    orchestrator.total_arrivals = 0
    orchestrator.total_assessments = 0
    orchestrator.start_time = None
    orchestrator.simulation = None
    
    return {
        "status": "reset",
        "message": "Simulation reset to initial state"
    }


@router.get("/hospital")
async def get_hospital_state():
    """Get current hospital state with all patients."""
    orchestrator = get_orchestrator()
    patients = orchestrator.get_patients()
    status = orchestrator.get_status()
    
    return {
        "status": status,
        "patients": patients,
        "patient_count": len(patients)
    }


@router.get("/capacity/{unit}")
async def get_unit_capacity(unit: str):
    """Get capacity for a specific unit."""
    # This will be enhanced when Capacity Intelligence integration is complete
    raise HTTPException(status_code=501, detail="Capacity endpoint not yet integrated")

