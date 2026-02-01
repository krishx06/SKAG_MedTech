from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core import state_manager
from backend.models.decision import EscalationDecision


router = APIRouter()


@router.get("/", response_model=List[Decision])
async def list_decisions(patient_id: Optional[str] = None, limit: int = 100):
    return await state_manager.get_decisions(patient_id=patient_id, limit=limit)


@router.get("/latest")
async def get_latest_decisions(limit: int = 20):
    decisions = await state_manager.get_decisions(limit=limit)
    return decisions


@router.get("/patient/{patient_id}", response_model=List[Decision])
async def get_patient_decisions(patient_id: str, limit: int = 50):
    return await state_manager.get_decisions(patient_id=patient_id, limit=limit)


@router.get("/patient/{patient_id}/escalation")
async def get_patient_escalation(patient_id: str):
    from backend.models import EscalationDecision
    escalation = await state_manager.get_agent_output("EscalationDecisionAgent", patient_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation decision not found")
    return escalation


@router.get("/patient/{patient_id}/flow")
async def get_patient_flow(patient_id: str):
    flow = await state_manager.get_flow_recommendation(patient_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow recommendation not found")
    return flow
