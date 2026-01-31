"""
Agents package for AdaptiveCare.
"""

from .base_agent import BaseAgent
# Temporarily commented out until Phase 3 integration
# from .escalation_decision import (
#     EscalationDecisionAgent,
#     AgentInput,
#     AgentOutput,
#     DecisionExplainer
# )

__all__ = [
    "BaseAgent",
    "AgentOutput",
    "DecisionExplainer"
]
