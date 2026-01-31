"""
Risk calculation algorithms for patient risk scoring.
Implements clinical decision rules and trend analysis.
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from backend.models.patient import Patient, VitalSigns, AcuityLevel
from backend.agents.risk_monitor.models import (
    RiskLevel,
    TrendDirection,
    VitalTrend,
    RiskFactorBreakdown
)


class VitalScoreCalculator:
    """Calculate risk scores from vital signs"""
    
    # Scoring weights and thresholds based on NEWS2 (National Early Warning Score)
    VITAL_WEIGHTS = {
        "spo2": 3.0,           # Most critical
        "heart_rate": 2.5,
        "systolic_bp": 2.5,
        "respiratory_rate": 2.0,
        "temperature": 1.5
    }
    
    @staticmethod
    def score_spo2(spo2: float) -> float:
        """Score oxygen saturation (0-12 points)"""
        if spo2 >= 96:
            return 0
        elif spo2 >= 94:
            return 1
        elif spo2 >= 92:
            return 2
        elif spo2 >= 90:
            return 3
        elif spo2 >= 88:
            return 6
        elif spo2 >= 85:
            return 9
        else:
            return 12
    
    @staticmethod
    def score_heart_rate(hr: float) -> float:
        """Score heart rate (0-12 points)"""
        if 51 <= hr <= 90:
            return 0
        elif 41 <= hr <= 50 or 91 <= hr <= 110:
            return 1
        elif 111 <= hr <= 130:
            return 2
        elif hr <= 40 or 131 <= hr <= 150:
            return 6
        else:  # <40 or >150
            return 12
    
    @staticmethod
    def score_systolic_bp(sys_bp: float) -> float:
        """Score systolic blood pressure (0-12 points)"""
        if 111 <= sys_bp <= 219:
            return 0
        elif 101 <= sys_bp <= 110:
            return 1
        elif 91 <= sys_bp <= 100:
            return 2
        elif 81 <= sys_bp <= 90:
            return 6
        else:  # <=80 or >=220
            return 12
    
    @staticmethod
    def score_respiratory_rate(rr: Optional[float]) -> float:
        """Score respiratory rate (0-12 points)"""
        if rr is None:
            return 0
        
        if 12 <= rr <= 20:
            return 0
        elif 9 <= rr <= 11 or 21 <= rr <= 24:
            return 1
        elif rr <= 8 or 25 <= rr <= 29:
            return 2
        elif 30 <= rr <= 35:
            return 6
        else:  # <8 or >35
            return 12
    
    @staticmethod
    def score_temperature(temp: float) -> float:
        """Score temperature (0-6 points)"""
        if 36.1 <= temp <= 38.0:
            return 0
        elif 35.1 <= temp <= 36.0 or 38.1 <= temp <= 39.0:
            return 1
        elif 39.1 <= temp <= 40.0:
            return 2
        else:  # <=35 or >=40
            return 6
    
    @staticmethod
    def calculate_vital_score(vitals: VitalSigns) -> float:
        """Calculate overall vital signs risk score (0-40 points)"""
        scores = {
            "spo2": VitalScoreCalculator.score_spo2(vitals.spo2),
            "heart_rate": VitalScoreCalculator.score_heart_rate(vitals.heart_rate),
            "systolic_bp": VitalScoreCalculator.score_systolic_bp(vitals.systolic_bp),
            "respiratory_rate": VitalScoreCalculator.score_respiratory_rate(vitals.respiratory_rate),
            "temperature": VitalScoreCalculator.score_temperature(vitals.temperature)
        }
        
        # Weighted sum, normalized to 0-40
        weighted_sum = sum(scores[k] * VitalScoreCalculator.VITAL_WEIGHTS[k] / 12.0 for k in scores)
        return min(40.0, weighted_sum * 3.33)  # Scale to max 40


class TrendCalculator:
    """Analyze vital sign trends over time"""
    
    @staticmethod
    def analyze_vital_trend(
        current: float,
        previous: Optional[float],
        vital_name: str,
        critical_thresholds: Dict[str, Dict[str, float]]
    ) -> VitalTrend:
        """Analyze trend for a single vital sign"""
        
        trend = VitalTrend(current_value=current, previous_value=previous)
        
        if previous is None:
            return trend
        
        # Calculate change rate
        change = current - previous
        trend.change_rate = change
        
        # Determine trend direction based on vital type
        if vital_name == "spo2":
            # Lower is worse for SpO2
            if change < -3:
                trend.direction = TrendDirection.RAPID_DETERIORATION
            elif change < -1:
                trend.direction = TrendDirection.DETERIORATING
            elif change > 2:
                trend.direction = TrendDirection.IMPROVING
            
            trend.critical = current < critical_thresholds.get("spo2", {}).get("min", 88)
            trend.out_of_range = current < 92
        
        elif vital_name in ["heart_rate", "respiratory_rate"]:
            # Deviation from normal in either direction is bad
            abs_change = abs(change)
            if abs_change > 20:
                trend.direction = TrendDirection.RAPID_DETERIORATION
            elif abs_change > 10:
                trend.direction = TrendDirection.DETERIORATING
            elif abs_change < 5 and 60 <= current <= 100:  # Assuming HR
                trend.direction = TrendDirection.IMPROVING
            
            if vital_name == "heart_rate":
                trend.critical = current < 40 or current > 150
                trend.out_of_range = current < 50 or current > 120
            else:  # respiratory_rate
                trend.critical = current < 8 or current > 35
                trend.out_of_range = current < 10 or current > 25
        
        elif vital_name == "systolic_bp":
            # Low BP is more concerning
            if change < -15:
                trend.direction = TrendDirection.RAPID_DETERIORATION
            elif change < -10:
                trend.direction = TrendDirection.DETERIORATING
            elif change > 10 and current < 140:
                trend.direction = TrendDirection.IMPROVING
            
            trend.critical = current < 80 or current > 200
            trend.out_of_range = current < 90 or current > 180
        
        elif vital_name == "temperature":
            # High temp is concerning
            if change > 1.0:
                trend.direction = TrendDirection.RAPID_DETERIORATION
            elif abs(change) > 0.5:
                trend.direction = TrendDirection.DETERIORATING if current > 37.5 else TrendDirection.STABLE
            elif 36.5 <= current <= 37.5:
                trend.direction = TrendDirection.IMPROVING
            
            trend.critical = current < 35 or current > 40
            trend.out_of_range = current < 36 or current > 38.5
        
        return trend
    
    @staticmethod
    def calculate_deterioration_score(vital_trends: Dict[str, VitalTrend]) -> float:
        """Calculate deterioration score from trends (0-30 points)"""
        score = 0.0
        
        for vital_name, trend in vital_trends.items():
            # Points for critical values
            if trend.critical:
                score += 10.0
            elif trend.out_of_range:
                score += 5.0
            
            # Points for deterioration direction
            if trend.direction == TrendDirection.RAPID_DETERIORATION:
                score += 8.0
            elif trend.direction == TrendDirection.DETERIORATING:
                score += 4.0
            elif trend.direction == TrendDirection.IMPROVING:
                score -= 2.0  # Reward improvement
        
        return min(30.0, max(0.0, score))


class RiskScoreCalculator:
    """Main risk score calculator"""
    
    @staticmethod
    def calculate_comorbidity_score(patient: Patient) -> float:
        """Calculate risk from comorbidities (0-15 points)"""
        high_risk_conditions = ["CAD", "CHF", "COPD", "CKD", "Previous MI", "Stroke history"]
        
        num_comorbidities = len(patient.comorbidities)
        high_risk_count = sum(1 for c in patient.comorbidities if c in high_risk_conditions)
        
        # Base score from count
        score = min(10.0, num_comorbidities * 2.0)
        
        # Bonus for high-risk conditions
        score += high_risk_count * 1.0
        
        # Factor in patient risk factors
        score += patient.risk_factors.comorbidity_score * 5.0
        
        return min(15.0, score)
    
    @staticmethod
    def calculate_acuity_score(acuity_level: AcuityLevel) -> float:
        """Calculate score from acuity level (0-15 points)"""
        acuity_scores = {
            AcuityLevel.RESUSCITATION: 15.0,
            AcuityLevel.EMERGENT: 12.0,
            AcuityLevel.URGENT: 8.0,
            AcuityLevel.LESS_URGENT: 4.0,
            AcuityLevel.NON_URGENT: 0.0
        }
        return acuity_scores.get(acuity_level, 8.0)
    
    @staticmethod
    def determine_risk_level(score: float) -> RiskLevel:
        """Convert score to risk level"""
        if score >= 81:
            return RiskLevel.CRITICAL
        elif score >= 61:
            return RiskLevel.HIGH
        elif score >= 31:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    @staticmethod
    def determine_overall_trend(vital_trends: Dict[str, VitalTrend], risk_delta: float) -> TrendDirection:
        """Determine overall patient trend"""
        deteriorating_count = sum(
            1 for t in vital_trends.values() 
            if t.direction in [TrendDirection.DETERIORATING, TrendDirection.RAPID_DETERIORATION]
        )
        
        rapid_deteriorating = any(
            t.direction == TrendDirection.RAPID_DETERIORATION 
            for t in vital_trends.values()
        )
        
        improving_count = sum(
            1 for t in vital_trends.values()
            if t.direction == TrendDirection.IMPROVING
        )
        
        if rapid_deteriorating or deteriorating_count >= 3:
            return TrendDirection.RAPID_DETERIORATION
        elif deteriorating_count >= 2 or risk_delta > 10:
            return TrendDirection.DETERIORATING
        elif improving_count >= 3 or risk_delta < -10:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.STABLE
    
    @staticmethod
    def should_escalate(
        risk_score: float,
        trend: TrendDirection,
        vital_trends: Dict[str, VitalTrend]
    ) -> tuple[bool, Optional[str]]:
        """Determine if patient needs escalation"""
        
        # Critical score
        if risk_score >= 85:
            return True, f"Critical risk score: {risk_score:.1f}"
        
        # Rapid deterioration
        if trend == TrendDirection.RAPID_DETERIORATION:
            return True, "Rapid clinical deterioration detected"
        
        # Multiple critical vitals
        critical_vitals = [name for name, t in vital_trends.items() if t.critical]
        if len(critical_vitals) >= 2:
            return True, f"Multiple critical vitals: {', '.join(critical_vitals)}"
        
        # Single critical vital with deterioration
        if critical_vitals and trend == TrendDirection.DETERIORATING:
            return True, f"Critical {critical_vitals[0]} with ongoing deterioration"
        
        return False, None
    
    @staticmethod
    def recommend_monitoring_frequency(risk_level: RiskLevel, trend: TrendDirection) -> int:
        """Recommend vital signs monitoring frequency in minutes"""
        if risk_level == RiskLevel.CRITICAL or trend == TrendDirection.RAPID_DETERIORATION:
            return 5  # Continuous monitoring
        elif risk_level == RiskLevel.HIGH or trend == TrendDirection.DETERIORATING:
            return 10
        elif risk_level == RiskLevel.MODERATE:
            return 15
        else:
            return 30
