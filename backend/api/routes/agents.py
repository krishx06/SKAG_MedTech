"""
Agent status routes for AdaptiveCare API

Provides endpoints for monitoring AI agent status.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime

router = APIRouter()


# Default agent configurations  
DEFAULT_AGENTS = [
    {
        "agent_name": "RiskMonitor",
        "display_name": "Risk Monitor",
        "description": "Monitors patient risk levels and detects deterioration patterns",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "CapacityIntelligence", 
        "display_name": "Capacity Intelligence",
        "description": "Tracks bed availability and staff workload across units",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "FlowOrchestrator",
        "display_name": "Flow Orchestrator", 
        "description": "Optimizes patient flow and bed assignments",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "EscalationDecision",
        "display_name": "Escalation Decision",
        "description": "Makes AI-powered decisions for patient escalation",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    }
]


@router.get("/status")
async def get_agents_status() -> List[Dict[str, Any]]:
    """Get status of all AI agents."""
    # Return agent status list
    return DEFAULT_AGENTS


@router.get("/list")
async def list_agents():
    """List all registered agents."""
    return {
        "agents": [a["agent_name"] for a in DEFAULT_AGENTS],
        "count": len(DEFAULT_AGENTS)
    }


@router.get("/{agent_name}/status")
async def get_agent_status(agent_name: str) -> Dict[str, Any]:
    """Get status of a specific agent."""
    for agent in DEFAULT_AGENTS:
        if agent["agent_name"] == agent_name:
            return agent
    return {"error": f"Agent {agent_name} not found"}
