"""
Patient routes for AdaptiveCare API

Provides endpoints for accessing patient data with Risk Monitor assessments.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from backend.simulation.simulation_orchestrator import get_orchestrator

router = APIRouter()


@router.get("/")
async def list_patients():
    """Get all active patients with their latest risk assessments."""
    orchestrator = get_orchestrator()
    patients = orchestrator.get_patients()
    return patients


@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    """Get detailed patient information."""
    orchestrator = get_orchestrator()
    patients = orchestrator.get_patients()
    
    patient = next((p for p in patients if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient


@router.get("/{patient_id}/vitals")
async def get_patient_vitals(patient_id: str):
    """Get patient's current vital signs."""
    orchestrator = get_orchestrator()
    patients = orchestrator.get_patients()
    
    patient = next((p for p in patients if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient.get("vitals", {})


@router.get("/{patient_id}/risk")
async def get_patient_risk(patient_id: str):
    """Get patient's risk assessment from Risk Monitor."""
    orchestrator = get_orchestrator()
    risk = orchestrator.get_patient_risk(patient_id)
    
    if not risk:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    
    return risk

