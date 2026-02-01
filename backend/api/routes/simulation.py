"""
Simulation routes for AdaptiveCare API

Provides endpoints for controlling hospital simulation with
integrated Risk Monitor Agent.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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


@router.post("/generate-scenario")
async def generate_scenario_from_prompt(prompt: str):
    """
    Generate a simulation scenario from natural language prompt.
    
    Example prompts:
    - "10 ICU beds, 9 filled, ambulance with 2 critical patients"
    - "Staff shortage with 3 nurses, 15 ED patients waiting"
    - "Normal operations, then ambulance arrives with trauma patient"
    
    Returns the parsed scenario configuration.
    """
    try:
        from backend.simulation.prompt_scenario_generator import get_scenario_generator
        
        generator = get_scenario_generator()
        scenario_config = generator.parse_prompt(prompt)
        
        return {
            "status": "success",
            "prompt": prompt,
            "scenario": {
                "icu_beds": f"{scenario_config.icu_occupied_beds}/{scenario_config.icu_total_beds}",
                "ed_beds": f"{scenario_config.ed_occupied_beds}/{scenario_config.ed_total_beds}",
                "ward_beds": f"{scenario_config.ward_occupied_beds}/{scenario_config.ward_total_beds}",
                "initial_patients": scenario_config.initial_patients,
                "incoming_ambulances": scenario_config.incoming_ambulances,
                "ambulance_patients": scenario_config.ambulance_patients,
                "staff_shortage": scenario_config.staff_shortage,
                "staff": {
                    "icu_nurses": scenario_config.icu_nurses,
                    "ed_nurses": scenario_config.ed_nurses
                }
            },
            "config": scenario_config.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scenario: {str(e)}")


@router.post("/inject-event")
async def inject_event(prompt: str):
    """
    Inject a dynamic event into running simulation via natural language.
    
    Example prompts:
    - "ambulance with critical patient arrives now"
    - "staff shortage in ICU"
    - "2 ICU beds become available"
    - "patient deteriorates rapidly"
    
    The simulation must be running for this to work.
    """
    orchestrator = get_orchestrator()
    
    if not orchestrator.is_running:
        raise HTTPException(status_code=400, detail="Simulation is not running. Start simulation first.")
    
    try:
        from backend.simulation.prompt_scenario_generator import get_scenario_generator
        
        generator = get_scenario_generator()
        event = generator.generate_event_from_prompt(prompt)
        
        # Apply event to running simulation
        if event["type"] == "ambulance_arrival":
            # Add new patients to simulation
            for patient_data in event["patients"]:
                orchestrator._inject_ambulance_patient(patient_data)
        
        elif event["type"] == "staff_change":
            # Update staff levels (broadcast via WebSocket)
            orchestrator._broadcast_event({
                "type": "staff_change",
                "timestamp": datetime.now().isoformat(),
                "data": event
            })
        
        elif event["type"] == "capacity_change":
            # Update bed capacity
            orchestrator._broadcast_event({
                "type": "capacity_change",
                "timestamp": datetime.now().isoformat(),
                "data": event
            })
        
        return {
            "status": "injected",
            "prompt": prompt,
            "event": event,
            "message": f"Event injected into running simulation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inject event: {str(e)}")

