"""
Risk Monitor Agent - Continuously assesses patient risk and tracks deterioration.
Main agent implementation for Phase 2.
"""
from typing import Dict, Optional
from datetime import datetime
from backend.models.patient import Patient
from backend.agents.risk_monitor.models import (
    RiskAssessment,
    RiskFactorBreakdown,
    PatientRiskHistory,
    RiskLevel,
    TrendDirection
)
from backend.agents.risk_monitor.calculators import (
    VitalScoreCalculator,
    TrendCalculator,
    RiskScoreCalculator
)


class RiskMonitorAgent:
    """
    Risk Monitor Agent - Tracks patient conditions and calculates risk scores.
    
    Responsibilities:
    - Calculate risk scores (0-100) from patient vitals and history
    - Track deterioration trends over time
    - Flag patients needing escalation
    - Recommend monitoring frequencies
    """
    
    def __init__(self):
        """Initialize Risk Monitor Agent"""
        self.patient_histories: Dict[str, PatientRiskHistory] = {}
        self.vital_calculator = VitalScoreCalculator()
        self.trend_calculator = TrendCalculator()
        self.risk_calculator = RiskScoreCalculator()
    
    def assess_patient(self, patient: Patient) -> RiskAssessment:
        """
        Perform complete risk assessment for a patient.
        
        Args:
            patient: Patient object with current vitals and history
        
        Returns:
            RiskAssessment with score, trends, and recommendations
        """
        # Get or create patient history
        if patient.id not in self.patient_histories:
            self.patient_histories[patient.id] = PatientRiskHistory(patient_id=patient.id)
        
        history = self.patient_histories[patient.id]
        previous_assessment = history.latest_assessment
        
        # Calculate vital signs score (0-40 points)
        vital_score = self.vital_calculator.calculate_vital_score(patient.vitals)
        
        # Analyze vital trends
        vital_trends = self._analyze_vital_trends(patient, previous_assessment)
        
        # Calculate deterioration score (0-30 points)
        deterioration_score = self.trend_calculator.calculate_deterioration_score(vital_trends)
        
        # Calculate comorbidity score (0-15 points)
        comorbidity_score = self.risk_calculator.calculate_comorbidity_score(patient)
        
        # Calculate acuity score (0-15 points)
        acuity_score = self.risk_calculator.calculate_acuity_score(patient.acuity_level)
        
        # Create risk breakdown
        breakdown = RiskFactorBreakdown(
            vital_signs_score=vital_score,
            deterioration_score=deterioration_score,
            comorbidity_score=comorbidity_score,
            acuity_score=acuity_score
        )
        
        # Calculate total risk score
        risk_score = breakdown.total_score
        
        # Determine risk level
        risk_level = self.risk_calculator.determine_risk_level(risk_score)
        
        # Calculate risk delta
        previous_score = previous_assessment.risk_score if previous_assessment else risk_score
        risk_delta = risk_score - previous_score
        
        # Determine overall trend
        trend = self.risk_calculator.determine_overall_trend(vital_trends, risk_delta)
        
        # Check if escalation needed
        needs_escalation, escalation_reason = self.risk_calculator.should_escalate(
            risk_score, trend, vital_trends
        )
        
        # Get critical vitals list
        critical_vitals = [
            name for name, vital_trend in vital_trends.items() 
            if vital_trend.critical
        ]
        
        # Recommend monitoring frequency
        monitoring_freq = self.risk_calculator.recommend_monitoring_frequency(risk_level, trend)
        
        # Calculate time since admission
        minutes_since_admission = int(
            (datetime.now() - patient.admission_time).total_seconds() / 60
        ) if patient.admission_time else None
        
        # Create risk assessment
        assessment = RiskAssessment(
            patient_id=patient.id,
            risk_score=risk_score,
            risk_level=risk_level,
            trend=trend,
            risk_breakdown=breakdown,
            vital_trends=vital_trends,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason,
            critical_vitals=critical_vitals,
            minutes_since_admission=minutes_since_admission,
            previous_risk_score=previous_score,
            risk_score_delta=risk_delta,
            recommended_monitoring_frequency=monitoring_freq
        )
        
        # Store in history
        history.add_assessment(assessment)
        
        return assessment
    
    def _analyze_vital_trends(
        self,
        patient: Patient,
        previous_assessment: Optional[RiskAssessment]
    ) -> Dict[str, any]:
        """Analyze trends for all vital signs"""
        from backend.agents.risk_monitor.models import VitalTrend
        
        current_vitals = patient.vitals
        trends = {}
        
        # Get previous vital values if available
        previous_vitals = {}
        if previous_assessment and previous_assessment.vital_trends:
            previous_vitals = {
                name: trend.current_value 
                for name, trend in previous_assessment.vital_trends.items()
            }
        
        # Critical thresholds
        thresholds = {
            "spo2": {"min": 88},
            "heart_rate": {"min": 40, "max": 150},
            "systolic_bp": {"min": 80, "max": 200},
            "respiratory_rate": {"min": 8, "max": 35},
            "temperature": {"min": 35, "max": 40}
        }
        
        # Analyze each vital
        trends["spo2"] = self.trend_calculator.analyze_vital_trend(
            current_vitals.spo2,
            previous_vitals.get("spo2"),
            "spo2",
            thresholds
        )
        
        trends["heart_rate"] = self.trend_calculator.analyze_vital_trend(
            current_vitals.heart_rate,
            previous_vitals.get("heart_rate"),
            "heart_rate",
            thresholds
        )
        
        trends["systolic_bp"] = self.trend_calculator.analyze_vital_trend(
            current_vitals.systolic_bp,
            previous_vitals.get("systolic_bp"),
            "systolic_bp",
            thresholds
        )
        
        if current_vitals.respiratory_rate is not None:
            trends["respiratory_rate"] = self.trend_calculator.analyze_vital_trend(
                current_vitals.respiratory_rate,
                previous_vitals.get("respiratory_rate"),
                "respiratory_rate",
                thresholds
            )
        
        trends["temperature"] = self.trend_calculator.analyze_vital_trend(
            current_vitals.temperature,
            previous_vitals.get("temperature"),
            "temperature",
            thresholds
        )
        
        return trends
    
    def get_patient_history(self, patient_id: str) -> Optional[PatientRiskHistory]:
        """Get risk assessment history for a patient"""
        return self.patient_histories.get(patient_id)
    
    def get_high_risk_patients(self) -> list[str]:
        """Get list of patient IDs with high risk"""
        high_risk = []
        for patient_id, history in self.patient_histories.items():
            latest = history.latest_assessment
            if latest and latest.is_high_risk:
                high_risk.append(patient_id)
        return high_risk
    
    def get_deteriorating_patients(self) -> list[str]:
        """Get list of patient IDs that are deteriorating"""
        deteriorating = []
        for patient_id, history in self.patient_histories.items():
            latest = history.latest_assessment
            if latest and latest.is_deteriorating:
                deteriorating.append(patient_id)
        return deteriorating
    
    def reset_history(self):
        """Clear all patient histories (for testing)"""
        self.patient_histories.clear()
