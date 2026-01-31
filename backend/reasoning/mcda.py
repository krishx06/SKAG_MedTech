"""
Multi-Criteria Decision Analysis (MCDA) calculator for AdaptiveCare.
Implements weighted scoring for patient escalation decisions.
"""

import logging
from datetime import datetime
from typing import Optional

from backend.models.patient import Patient, AcuityLevel
from backend.models.hospital import CapacitySnapshot, BedType
from backend.models.decision import MCDAWeights, MCDAScore
from backend.core.config import Config

logger = logging.getLogger(__name__)


class MCDACalculator:
    """
    Multi-Criteria Decision Analysis calculator.
    
    Combines multiple factors into a weighted score:
    - Risk score (patient clinical risk)
    - Capacity score (resource availability)
    - Wait time score (urgency from waiting)
    - Resource score (patient-resource matching)
    """
    
    def __init__(self, weights: Optional[MCDAWeights] = None):
        """
        Initialize the MCDA calculator.
        
        Args:
            weights: Custom weights, or use defaults from config
        """
        if weights:
            self.weights = weights
        else:
            config_weights = Config.get_mcda_weights()
            self.weights = MCDAWeights(
                risk_weight=config_weights.risk_weight,
                capacity_weight=config_weights.capacity_weight,
                wait_time_weight=config_weights.wait_time_weight,
                resource_weight=config_weights.resource_weight
            )
        
        logger.info(f"MCDA Calculator initialized with weights: {self.weights.to_dict()}")

    def calculate_risk_score(self, patient: Patient) -> float:
        """
        Calculate normalized risk score (0-1).
        
        Considers:
        - Overall risk score from Risk Monitor Agent
        - Acuity level
        - Critical vitals
        - Risk factors
        
        Args:
            patient: Patient to evaluate
            
        Returns:
            Normalized risk score 0-1 (1 = highest risk)
        """
        # Base score from risk monitor (0-100 -> 0-1)
        base_score = patient.risk_score / 100.0
        
        # Acuity multiplier (ESI 1 = 1.0, ESI 5 = 0.2)
        acuity_multiplier = 1.0 - (patient.acuity_level - 1) * 0.2
        
        # Critical vitals boost
        vitals_boost = 0.15 if patient.vitals.is_critical() else 0.0
        
        # Risk factors contribution
        risk_factor_score = 0.0
        if patient.risk_factors:
            risk_factor_score = max(
                patient.risk_factors.sepsis_probability,
                patient.risk_factors.cardiac_risk,
                patient.risk_factors.respiratory_risk,
                abs(patient.risk_factors.deterioration_trend)
            ) * 0.2
        
        # Combine scores
        combined = (
            base_score * 0.5 +
            acuity_multiplier * 0.25 +
            vitals_boost +
            risk_factor_score
        )
        
        # Clamp to 0-1
        normalized = max(0.0, min(1.0, combined))
        
        logger.debug(f"Risk score for {patient.id}: {normalized:.3f}")
        return normalized

    def calculate_capacity_score(
        self, 
        capacity: CapacitySnapshot,
        target_unit_type: Optional[BedType] = None
    ) -> float:
        """
        Calculate capacity availability score (0-1).
        
        Higher score = more capacity available = better for decisions.
        
        Args:
            capacity: Current capacity snapshot
            target_unit_type: Specific unit type to check, or overall
            
        Returns:
            Normalized capacity score 0-1 (1 = high availability)
        """
        if not capacity or not capacity.units:
            logger.warning("No capacity data available")
            return 0.0
        
        if target_unit_type:
            # Score for specific unit type
            available = capacity.get_available_beds_by_type(target_unit_type)
            units = capacity.get_units_by_type(target_unit_type)
            total = sum(u.total_beds for u in units)
            
            if total == 0:
                return 0.0
            
            availability_ratio = available / total
        else:
            # Overall capacity score
            availability_ratio = capacity.total_available / capacity.total_beds if capacity.total_beds > 0 else 0.0
        
        # Factor in pending discharges (positive) and admissions (negative)
        pending_factor = (capacity.predicted_discharges_1h - capacity.predicted_admissions_1h) * 0.02
        
        # Calculate final score
        score = availability_ratio + pending_factor
        
        # Clamp to 0-1
        normalized = max(0.0, min(1.0, score))
        
        logger.debug(f"Capacity score: {normalized:.3f} (availability: {availability_ratio:.2f})")
        return normalized

    def calculate_wait_time_score(self, patient: Patient) -> float:
        """
        Calculate wait time urgency score (0-1).
        
        Longer wait times = higher urgency = higher score.
        Uses exponential decay with acuity-based thresholds.
        
        Args:
            patient: Patient to evaluate
            
        Returns:
            Normalized wait time score 0-1 (1 = urgent, long wait)
        """
        wait_minutes = patient.wait_time_minutes
        
        # Acuity-based thresholds (minutes)
        thresholds = {
            AcuityLevel.RESUSCITATION: 5,    # ESI 1: immediate
            AcuityLevel.EMERGENT: 15,         # ESI 2: within 15 min
            AcuityLevel.URGENT: 30,           # ESI 3: within 30 min
            AcuityLevel.LESS_URGENT: 60,      # ESI 4: within 1 hour
            AcuityLevel.NON_URGENT: 120       # ESI 5: within 2 hours
        }
        
        threshold = thresholds.get(patient.acuity_level, 60)
        
        # Calculate score using sigmoid-like curve
        # Score increases rapidly as wait time exceeds threshold
        if wait_minutes <= 0:
            score = 0.0
        elif wait_minutes >= threshold * 3:
            score = 1.0
        else:
            # Sigmoid curve centered at threshold
            import math
            x = (wait_minutes - threshold) / (threshold * 0.5)
            score = 1 / (1 + math.exp(-x))
        
        logger.debug(f"Wait time score for {patient.id}: {score:.3f} (waited {wait_minutes}min, threshold {threshold}min)")
        return score

    def calculate_resource_score(
        self, 
        patient: Patient, 
        capacity: CapacitySnapshot
    ) -> float:
        """
        Calculate resource matching score (0-1).
        
        How well do available resources match patient needs?
        
        Args:
            patient: Patient to evaluate
            capacity: Current capacity snapshot
            
        Returns:
            Normalized resource score 0-1 (1 = good match available)
        """
        if not capacity or not capacity.units:
            return 0.0
        
        # Determine required resource type based on patient
        required_type = self._determine_required_unit_type(patient)
        
        # Check availability of required resource type
        available = capacity.get_available_beds_by_type(required_type)
        
        if available == 0:
            # Check alternative types
            alternatives = self._get_alternative_types(required_type)
            for alt_type in alternatives:
                alt_available = capacity.get_available_beds_by_type(alt_type)
                if alt_available > 0:
                    return 0.5  # Partial match
            return 0.1  # No match, but system still running
        
        # Good match available
        if available >= 3:
            score = 1.0
        elif available >= 2:
            score = 0.9
        else:
            score = 0.75
        
        # Factor in staff availability
        units = capacity.get_units_by_type(required_type)
        if units:
            avg_staff_load = sum(u.average_staff_load for u in units) / len(units)
            staff_factor = 1.0 - (avg_staff_load / 100.0) * 0.3  # Up to 30% reduction for high load
            score *= staff_factor
        
        logger.debug(f"Resource score for {patient.id}: {score:.3f}")
        return max(0.0, min(1.0, score))

    def _determine_required_unit_type(self, patient: Patient) -> BedType:
        """Determine required unit type based on patient condition."""
        if patient.acuity_level == AcuityLevel.RESUSCITATION:
            return BedType.ICU
        elif patient.acuity_level == AcuityLevel.EMERGENT:
            if patient.risk_factors.cardiac_risk > 0.5:
                return BedType.CARDIAC
            elif patient.risk_factors.respiratory_risk > 0.5:
                return BedType.ICU
            return BedType.ICU
        elif patient.acuity_level == AcuityLevel.URGENT:
            return BedType.ER
        else:
            return BedType.GENERAL

    def _get_alternative_types(self, primary: BedType) -> list:
        """Get alternative unit types if primary is unavailable."""
        alternatives = {
            BedType.ICU: [BedType.CARDIAC, BedType.ER],
            BedType.CARDIAC: [BedType.ICU, BedType.ER],
            BedType.ER: [BedType.GENERAL],
            BedType.GENERAL: [BedType.ER],
            BedType.ISOLATION: [BedType.GENERAL],
            BedType.PEDIATRIC: [BedType.GENERAL]
        }
        return alternatives.get(primary, [BedType.GENERAL])

    def compute_weighted_score(
        self,
        patient: Patient,
        capacity: CapacitySnapshot,
        target_unit_type: Optional[BedType] = None
    ) -> MCDAScore:
        """
        Compute the full MCDA weighted score.
        
        Args:
            patient: Patient to evaluate
            capacity: Current capacity snapshot
            target_unit_type: Optional specific unit type to target
            
        Returns:
            Complete MCDAScore with breakdown
        """
        # Calculate individual scores
        risk_score = self.calculate_risk_score(patient)
        capacity_score = self.calculate_capacity_score(capacity, target_unit_type)
        wait_time_score = self.calculate_wait_time_score(patient)
        resource_score = self.calculate_resource_score(patient, capacity)
        
        # Apply weights
        weighted_risk = risk_score * self.weights.risk_weight
        weighted_capacity = capacity_score * self.weights.capacity_weight
        weighted_wait_time = wait_time_score * self.weights.wait_time_weight
        weighted_resource = resource_score * self.weights.resource_weight
        
        # Calculate total
        weighted_total = weighted_risk + weighted_capacity + weighted_wait_time + weighted_resource
        
        mcda_score = MCDAScore(
            risk_score=risk_score,
            capacity_score=capacity_score,
            wait_time_score=wait_time_score,
            resource_score=resource_score,
            weighted_risk=weighted_risk,
            weighted_capacity=weighted_capacity,
            weighted_wait_time=weighted_wait_time,
            weighted_resource=weighted_resource,
            weighted_total=weighted_total,
            weights_used=self.weights
        )
        
        logger.info(
            f"MCDA Score for {patient.id}: {weighted_total:.3f} "
            f"(R:{risk_score:.2f} C:{capacity_score:.2f} W:{wait_time_score:.2f} Rs:{resource_score:.2f})"
        )
        
        return mcda_score

    def update_weights(self, new_weights: MCDAWeights) -> None:
        """Update the MCDA weights."""
        if not new_weights.validate_sum():
            logger.warning("New weights don't sum to 1.0, normalizing...")
            total = (
                new_weights.risk_weight + 
                new_weights.capacity_weight + 
                new_weights.wait_time_weight + 
                new_weights.resource_weight
            )
            new_weights.risk_weight /= total
            new_weights.capacity_weight /= total
            new_weights.wait_time_weight /= total
            new_weights.resource_weight /= total
        
        self.weights = new_weights
        logger.info(f"Updated MCDA weights: {self.weights.to_dict()}")
