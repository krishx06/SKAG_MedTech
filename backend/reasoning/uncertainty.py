"""
Uncertainty and confidence calculation for AdaptiveCare decisions.
"""

import logging
from datetime import timedelta
from typing import Optional

from backend.models.decision import MCDAScore
from backend.core.config import Config

logger = logging.getLogger(__name__)


class UncertaintyCalculator:
    """
    Calculate confidence levels and uncertainty for decisions.
    
    Factors affecting confidence:
    - Data freshness (stale data = lower confidence)
    - Prediction variance (high variance = lower confidence)
    - MCDA score distribution (balanced = higher confidence)
    - Factor consistency (consistent signals = higher confidence)
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        max_data_age_minutes: int = 30
    ):
        """
        Initialize uncertainty calculator.
        
        Args:
            confidence_threshold: Threshold below which to flag for human review
            max_data_age_minutes: Maximum age for data to be considered fresh
        """
        self.confidence_threshold = confidence_threshold
        self.max_data_age_minutes = max_data_age_minutes
        
        logger.info("Uncertainty Calculator initialized")

    def calculate_confidence(
        self,
        mcda_score: MCDAScore,
        data_freshness: timedelta,
        prediction_variance: float = 0.0,
        data_completeness: float = 1.0
    ) -> float:
        """
        Calculate overall confidence in a decision.
        
        Args:
            mcda_score: The MCDA score for the decision
            data_freshness: Age of the most recent data
            prediction_variance: Variance in predictions (0-1)
            data_completeness: Proportion of data available (0-1)
            
        Returns:
            Confidence score 0-1 (1 = high confidence)
        """
        # 1. Data freshness factor (100% if < 5 min, decays to 50% at max age)
        age_minutes = data_freshness.total_seconds() / 60
        if age_minutes <= 5:
            freshness_factor = 1.0
        elif age_minutes >= self.max_data_age_minutes:
            freshness_factor = 0.5
        else:
            # Linear decay
            freshness_factor = 1.0 - (age_minutes - 5) / (self.max_data_age_minutes - 5) * 0.5
        
        # 2. Prediction variance factor (lower variance = higher confidence)
        variance_factor = 1.0 - (prediction_variance * 0.4)  # Max 40% reduction
        
        # 3. Data completeness factor
        completeness_factor = 0.5 + (data_completeness * 0.5)  # Min 50%
        
        # 4. Score clarity factor (clear-cut scores = higher confidence)
        score_clarity = self._calculate_score_clarity(mcda_score)
        
        # 5. Factor consistency (consistent signals = higher confidence)
        consistency = self._calculate_factor_consistency(mcda_score)
        
        # Combine factors
        confidence = (
            freshness_factor * 0.25 +
            variance_factor * 0.15 +
            completeness_factor * 0.15 +
            score_clarity * 0.25 +
            consistency * 0.20
        )
        
        # Ensure bounds
        confidence = max(0.0, min(1.0, confidence))
        
        logger.debug(
            f"Confidence: {confidence:.2f} "
            f"(fresh:{freshness_factor:.2f}, var:{variance_factor:.2f}, "
            f"complete:{completeness_factor:.2f}, clarity:{score_clarity:.2f}, "
            f"consistency:{consistency:.2f})"
        )
        
        return confidence

    def _calculate_score_clarity(self, mcda_score: MCDAScore) -> float:
        """
        Calculate how clear-cut the MCDA score is.
        
        Scores very close to thresholds have lower clarity.
        """
        score = mcda_score.weighted_total
        
        # Get thresholds
        thresholds = Config.get_decision_thresholds()
        escalate = thresholds.escalate_threshold
        observe = thresholds.observe_threshold
        
        # Distance from nearest threshold
        distances = [
            abs(score - escalate),
            abs(score - observe),
            abs(score - 0.0),
            abs(score - 1.0)
        ]
        min_distance = min(distances)
        
        # Convert distance to clarity (further from threshold = clearer)
        # Max possible distance is 0.5, so normalize
        clarity = min(min_distance / 0.15, 1.0)  # Normalize to 15% distance
        
        return clarity

    def _calculate_factor_consistency(self, mcda_score: MCDAScore) -> float:
        """
        Calculate how consistent the individual factors are.
        
        If all factors point in same direction, consistency is high.
        If factors conflict, consistency is lower.
        """
        scores = [
            mcda_score.risk_score,
            mcda_score.capacity_score,
            mcda_score.wait_time_score,
            mcda_score.resource_score
        ]
        
        # Calculate variance of scores
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        
        # Lower variance = higher consistency
        # Max variance is 0.25 (if scores are 0 and 1)
        consistency = 1.0 - (variance / 0.25)
        
        # Add bonus for all-high or all-low scenarios
        if all(s >= 0.6 for s in scores) or all(s <= 0.4 for s in scores):
            consistency = min(1.0, consistency + 0.1)
        
        return max(0.0, min(1.0, consistency))

    def should_escalate_to_human(self, confidence: float) -> bool:
        """
        Determine if decision should be escalated to human review.
        
        Args:
            confidence: Confidence score
            
        Returns:
            True if human review is recommended
        """
        return confidence < self.confidence_threshold

    def get_uncertainty_reasons(
        self,
        mcda_score: MCDAScore,
        data_freshness: timedelta,
        prediction_variance: float = 0.0
    ) -> list:
        """
        Get human-readable reasons for uncertainty.
        
        Returns:
            List of uncertainty reason strings
        """
        reasons = []
        
        age_minutes = data_freshness.total_seconds() / 60
        
        # Check data freshness
        if age_minutes > 15:
            reasons.append(f"Patient data is {age_minutes:.0f} minutes old")
        
        # Check prediction variance
        if prediction_variance > 0.3:
            reasons.append("High variance in capacity predictions")
        
        # Check score clarity
        clarity = self._calculate_score_clarity(mcda_score)
        if clarity < 0.5:
            reasons.append("Score is close to decision threshold")
        
        # Check factor consistency
        consistency = self._calculate_factor_consistency(mcda_score)
        if consistency < 0.5:
            reasons.append("Conflicting signals from different factors")
        
        # Check for missing dominant signal
        breakdown = mcda_score.get_breakdown()
        max_contribution = max(
            breakdown['risk']['contribution'],
            breakdown['capacity']['contribution'],
            breakdown['wait_time']['contribution'],
            breakdown['resource']['contribution']
        )
        if max_contribution < 35:  # No clear dominant factor
            reasons.append("No single dominant factor in decision")
        
        return reasons

    def calculate_decision_stability(
        self,
        current_score: MCDAScore,
        previous_scores: list = None
    ) -> float:
        """
        Calculate how stable a decision is over time.
        
        Args:
            current_score: Current MCDA score
            previous_scores: List of recent MCDA scores
            
        Returns:
            Stability score 0-1 (1 = very stable)
        """
        if not previous_scores or len(previous_scores) < 2:
            return 0.8  # Default moderate stability with limited data
        
        # Calculate variance of recent scores
        all_scores = [s.weighted_total for s in previous_scores] + [current_score.weighted_total]
        mean = sum(all_scores) / len(all_scores)
        variance = sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
        
        # Check for trend changes (oscillation = lower stability)
        changes = [all_scores[i+1] - all_scores[i] for i in range(len(all_scores)-1)]
        sign_changes = sum(1 for i in range(len(changes)-1) if changes[i] * changes[i+1] < 0)
        oscillation_penalty = sign_changes * 0.1
        
        # Calculate stability
        stability = 1.0 - min(variance * 4, 0.5) - oscillation_penalty
        
        return max(0.0, min(1.0, stability))
