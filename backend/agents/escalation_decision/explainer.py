"""
Decision explainer for formatting decisions for frontend display.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.models.decision import EscalationDecision, DecisionType, UrgencyLevel

logger = logging.getLogger(__name__)


class DecisionExplainer:
    """
    Helper class for formatting and explaining decisions.
    
    Transforms raw decision data into frontend-friendly formats,
    extracts key insights, and provides visualization data.
    """
    
    def __init__(self):
        """Initialize the decision explainer."""
        logger.info("DecisionExplainer initialized")

    def format_for_frontend(self, decision: EscalationDecision) -> Dict[str, Any]:
        """
        Format a decision for frontend display.
        
        Args:
            decision: The decision to format
            
        Returns:
            Frontend-ready dictionary
        """
        mcda_viz = self._format_mcda_visualization(decision)
        
        return {
            "id": decision.id,
            "patient_id": decision.patient_id,
            "timestamp": decision.timestamp.isoformat(),
            
            # Decision details
            "decision": {
                "type": decision.decision_type.value,
                "type_label": self._get_decision_label(decision.decision_type),
                "urgency": decision.urgency.value,
                "urgency_label": self._get_urgency_label(decision.urgency),
                "color": decision.get_color_code(),
                "icon": self._get_decision_icon(decision.decision_type)
            },
            
            # Scores
            "scores": {
                "priority": round(decision.priority_score, 1),
                "confidence": round(decision.confidence * 100, 1),
                "confidence_label": self._get_confidence_label(decision.confidence)
            },
            
            # Reasoning
            "reasoning": {
                "summary": decision.reasoning,
                "factors": decision.contributing_factors,
                "dominant_factor": decision.mcda_breakdown.get_dominant_factor()
            },
            
            # MCDA breakdown for visualization
            "mcda": mcda_viz,
            
            # Action
            "action": {
                "recommended": decision.recommended_action,
                "target_unit": decision.target_unit,
                "requires_review": decision.requires_human_review
            },
            
            # Status
            "status": {
                "executed": decision.is_executed,
                "executed_at": decision.executed_at.isoformat() if decision.executed_at else None,
                "executed_by": decision.executed_by
            }
        }

    def _format_mcda_visualization(self, decision: EscalationDecision) -> Dict[str, Any]:
        """Format MCDA breakdown for chart visualization."""
        breakdown = decision.mcda_breakdown.get_breakdown()
        
        # Format for bar/radar chart
        factors = [
            {
                "name": "Risk",
                "key": "risk",
                "raw": round(breakdown["risk"]["raw"] * 100, 1),
                "weighted": round(breakdown["risk"]["weighted"] * 100, 1),
                "contribution": round(breakdown["risk"]["contribution"], 1),
                "weight": round(breakdown["risk"]["weight"] * 100, 1),
                "color": "#FF6B6B"
            },
            {
                "name": "Capacity",
                "key": "capacity",
                "raw": round(breakdown["capacity"]["raw"] * 100, 1),
                "weighted": round(breakdown["capacity"]["weighted"] * 100, 1),
                "contribution": round(breakdown["capacity"]["contribution"], 1),
                "weight": round(breakdown["capacity"]["weight"] * 100, 1),
                "color": "#4ECDC4"
            },
            {
                "name": "Wait Time",
                "key": "wait_time",
                "raw": round(breakdown["wait_time"]["raw"] * 100, 1),
                "weighted": round(breakdown["wait_time"]["weighted"] * 100, 1),
                "contribution": round(breakdown["wait_time"]["contribution"], 1),
                "weight": round(breakdown["wait_time"]["weight"] * 100, 1),
                "color": "#FFE66D"
            },
            {
                "name": "Resources",
                "key": "resource",
                "raw": round(breakdown["resource"]["raw"] * 100, 1),
                "weighted": round(breakdown["resource"]["weighted"] * 100, 1),
                "contribution": round(breakdown["resource"]["contribution"], 1),
                "weight": round(breakdown["resource"]["weight"] * 100, 1),
                "color": "#95E1D3"
            }
        ]
        
        return {
            "total_score": round(decision.mcda_breakdown.weighted_total * 100, 1),
            "factors": factors,
            "weights": decision.mcda_breakdown.weights_used.to_dict(),
            "dominant": decision.mcda_breakdown.get_dominant_factor()
        }

    def _get_decision_label(self, decision_type: DecisionType) -> str:
        """Get human-readable label for decision type."""
        labels = {
            DecisionType.ESCALATE: "Escalate Care",
            DecisionType.OBSERVE: "Continue Monitoring",
            DecisionType.DELAY: "Await Resources",
            DecisionType.REPRIORITIZE: "Adjust Priority",
            DecisionType.DISCHARGE: "Clear for Discharge",
            DecisionType.TRANSFER: "Transfer Unit"
        }
        return labels.get(decision_type, "Unknown")

    def _get_urgency_label(self, urgency: UrgencyLevel) -> str:
        """Get human-readable label for urgency level."""
        labels = {
            UrgencyLevel.IMMEDIATE: "Act Now",
            UrgencyLevel.URGENT: "Within 15 min",
            UrgencyLevel.SOON: "Within 1 hour",
            UrgencyLevel.ROUTINE: "When Available"
        }
        return labels.get(urgency, "Unknown")

    def _get_decision_icon(self, decision_type: DecisionType) -> str:
        """Get icon name for decision type."""
        icons = {
            DecisionType.ESCALATE: "arrow-up-circle",
            DecisionType.OBSERVE: "eye",
            DecisionType.DELAY: "clock",
            DecisionType.REPRIORITIZE: "list-ordered",
            DecisionType.DISCHARGE: "check-circle",
            DecisionType.TRANSFER: "arrow-right-circle"
        }
        return icons.get(decision_type, "help-circle")

    def _get_confidence_label(self, confidence: float) -> str:
        """Get human-readable label for confidence level."""
        if confidence >= 0.85:
            return "High Confidence"
        elif confidence >= 0.7:
            return "Good Confidence"
        elif confidence >= 0.5:
            return "Moderate Confidence"
        else:
            return "Low Confidence - Review Recommended"

    def get_contributing_factors(
        self, 
        decision: EscalationDecision
    ) -> List[Dict[str, Any]]:
        """
        Get detailed contributing factors with context.
        
        Args:
            decision: Decision to analyze
            
        Returns:
            List of factor dictionaries with details
        """
        factors = []
        breakdown = decision.mcda_breakdown.get_breakdown()
        
        # Add each significant factor
        for factor_key, factor_data in breakdown.items():
            if factor_data["contribution"] >= 15:  # Only significant factors
                factors.append({
                    "key": factor_key,
                    "name": self._factor_key_to_name(factor_key),
                    "score": factor_data["raw"],
                    "contribution": factor_data["contribution"],
                    "is_dominant": decision.mcda_breakdown.get_dominant_factor() == factor_key,
                    "description": self._get_factor_description(factor_key, factor_data["raw"])
                })
        
        # Sort by contribution
        factors.sort(key=lambda f: f["contribution"], reverse=True)
        
        return factors

    def _factor_key_to_name(self, key: str) -> str:
        """Convert factor key to display name."""
        names = {
            "risk": "Patient Risk",
            "capacity": "Bed Availability",
            "wait_time": "Wait Time",
            "resource": "Resource Match"
        }
        return names.get(key, key.replace("_", " ").title())

    def _get_factor_description(self, key: str, score: float) -> str:
        """Get contextual description for a factor score."""
        if key == "risk":
            if score >= 0.8:
                return "Critical risk level requiring immediate attention"
            elif score >= 0.6:
                return "Elevated risk, close monitoring needed"
            elif score >= 0.4:
                return "Moderate risk, standard observation"
            else:
                return "Low risk, stable condition"
        
        elif key == "capacity":
            if score >= 0.7:
                return "Good availability, resources accessible"
            elif score >= 0.4:
                return "Limited availability, may need alternatives"
            else:
                return "Capacity constrained, delays likely"
        
        elif key == "wait_time":
            if score >= 0.7:
                return "Extended wait exceeding guidelines"
            elif score >= 0.4:
                return "Wait time approaching threshold"
            else:
                return "Wait time within acceptable range"
        
        elif key == "resource":
            if score >= 0.7:
                return "Good resource match available"
            elif score >= 0.4:
                return "Partial resource match"
            else:
                return "Resource constraints noted"
        
        return "Score indicates moderate priority"

    def format_decision_feed_item(self, decision: EscalationDecision) -> Dict[str, Any]:
        """
        Format decision for the real-time decision feed.
        Compact format optimized for list display.
        """
        return {
            "id": decision.id,
            "patient_id": decision.patient_id,
            "timestamp": decision.timestamp.isoformat(),
            "relative_time": self._get_relative_time(decision.timestamp),
            "type": decision.decision_type.value,
            "type_label": self._get_decision_label(decision.decision_type),
            "urgency": decision.urgency.value,
            "color": decision.get_color_code(),
            "icon": self._get_decision_icon(decision.decision_type),
            "summary": self._truncate(decision.reasoning, 100),
            "priority": round(decision.priority_score, 0),
            "requires_action": decision.decision_type == DecisionType.ESCALATE,
            "requires_review": decision.requires_human_review
        }

    def _get_relative_time(self, timestamp) -> str:
        """Get relative time string (e.g., '2 min ago')."""
        from datetime import datetime
        
        now = datetime.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} min ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hr ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def batch_format_for_frontend(
        self, 
        decisions: List[EscalationDecision]
    ) -> List[Dict[str, Any]]:
        """Format multiple decisions for frontend."""
        return [self.format_for_frontend(d) for d in decisions]

    def batch_format_feed_items(
        self, 
        decisions: List[EscalationDecision]
    ) -> List[Dict[str, Any]]:
        """Format multiple decisions for feed display."""
        return [self.format_decision_feed_item(d) for d in decisions]
