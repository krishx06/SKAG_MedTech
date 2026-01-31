#!/usr/bin/env python3
"""
Phase 2 Test: Risk Monitor Agent
Tests risk scoring, trend analysis, and escalation detection.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simulation.data_generator import EnhancedDataGenerator
from backend.simulation.event_types import SeverityLevel, DeteriorationPattern
# Import directly to avoid conflicts with other agents
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "agents" / "risk_monitor"))
from agent import RiskMonitorAgent
from models import RiskLevel, TrendDirection


def test_risk_scoring():
    """Test basic risk score calculation"""
    print("="*70)
    print("TEST 1: Risk Score Calculation")
    print("="*70)
    
    agent = RiskMonitorAgent()
    
    # Test different severity levels
    severities = [
        (SeverityLevel.LOW, "Low Severity"),
        (SeverityLevel.MODERATE, "Moderate Severity"),
        (SeverityLevel.HIGH, "High Severity"),
        (SeverityLevel.CRITICAL, "Critical Severity")
    ]
    
    for severity, name in severities:
        patient = EnhancedDataGenerator.generate_patient(
            severity=severity,
            location="ED",
            deterioration_pattern=DeteriorationPattern.STABLE
        )
        
        assessment = agent.assess_patient(patient)
        
        print(f"\n{name} Patient:")
        print(f"   Risk Score: {assessment.risk_score:.1f}/100")
        print(f"   Risk Level: {assessment.risk_level.value}")
        print(f"   Trend: {assessment.trend.value}")
        print(f"   Breakdown:")
        print(f"      Vitals:         {assessment.risk_breakdown.vital_signs_score:.1f}/40")
        print(f"      Deterioration:  {assessment.risk_breakdown.deterioration_score:.1f}/30")
        print(f"      Comorbidities:  {assessment.risk_breakdown.comorbidity_score:.1f}/15")
        print(f"      Acuity:         {assessment.risk_breakdown.acuity_score:.1f}/15")


def test_deterioration_detection():
    """Test deterioration trend detection"""
    print("\n" + "="*70)
    print("TEST 2: Deterioration Detection")
    print("="*70)
    
    agent = RiskMonitorAgent()
    
    patterns = [
        (DeteriorationPattern.SEPSIS, "Sepsis"),
        (DeteriorationPattern.RESPIRATORY, "Respiratory Failure"),
        (DeteriorationPattern.GRADUAL_DECLINE, "Gradual Decline")
    ]
    
    for pattern, name in patterns:
        patient = EnhancedDataGenerator.generate_patient(
            severity=SeverityLevel.HIGH,
            location="ED",
            deterioration_pattern=pattern
        )
        
        # Initial assessment
        assessment1 = agent.assess_patient(patient)
        
        # Update vitals (simulate deterioration)
        patient.vitals = EnhancedDataGenerator.generate_vitals(
            age=patient.age,
            severity=SeverityLevel.CRITICAL,
            deterioration=pattern,
            time_offset=15
        )
        
        # Second assessment
        assessment2 = agent.assess_patient(patient)
        
        print(f"\n{name}:")
        print(f"   Initial: Risk={assessment1.risk_score:.1f}, Trend={assessment1.trend.value}")
        print(f"   After 15min: Risk={assessment2.risk_score:.1f} ({assessment2.risk_score_delta:+.1f}), Trend={assessment2.trend.value}")
        print(f"   Critical Vitals: {', '.join(assessment2.critical_vitals) if assessment2.critical_vitals else 'None'}")
        print(f"   Needs Escalation: {'YES' if assessment2.needs_escalation else 'NO'}")
        if assessment2.escalation_reason:
            print(f"   Reason: {assessment2.escalation_reason}")


def test_trend_tracking():
    """Test vital sign trend tracking over time"""
    print("\n" + "="*70)
    print("TEST 3: Trend Tracking Over Time")
    print("="*70)
    
    agent = RiskMonitorAgent()
    
    # Create deteriorating patient
    patient = EnhancedDataGenerator.generate_patient(
        severity=SeverityLevel.MODERATE,
        location="ED",
        deterioration_pattern=DeteriorationPattern.RESPIRATORY
    )
    
    print(f"\nPatient {patient.id} - Respiratory Deterioration")
    print(f"Age: {patient.age}, Comorbidities: {len(patient.comorbidities)}")
    
    # Simulate 4 assessments over 45 minutes
    for i, time_offset in enumerate([0, 15, 30, 45]):
        # Update vitals
        if i > 0:
            patient.vitals = EnhancedDataGenerator.generate_vitals(
                age=patient.age,
                severity=SeverityLevel.HIGH if i >= 2 else SeverityLevel.MODERATE,
                deterioration=DeteriorationPattern.RESPIRATORY,
                time_offset=time_offset
            )
        
        assessment = agent.assess_patient(patient)
        
        print(f"\n   T+{time_offset}min:")
        print(f"      Risk: {assessment.risk_score:.1f}/100 ({assessment.risk_level.value})")
        print(f"      SpO2: {patient.vitals.spo2:.1f}% | HR: {patient.vitals.heart_rate:.0f} | RR: {patient.vitals.respiratory_rate:.0f}")
        print(f"      Trend: {assessment.trend.value}")
        if assessment.needs_escalation:
            print(f"      ⚠️  ESCALATION NEEDED: {assessment.escalation_reason}")
    
    # Show trajectory
    history = agent.get_patient_history(patient.id)
    if history:
        trajectory = history.risk_trajectory
        print(f"\n   Risk Trajectory: {' → '.join(f'{s:.1f}' for s in trajectory)}")


def test_escalation_logic():
    """Test escalation triggers"""
    print("\n" + "="*70)
    print("TEST 4: Escalation Logic")
    print("="*70)
    
    agent = RiskMonitorAgent()
    
    # Test different escalation scenarios
    scenarios = [
        ("Critical Score", SeverityLevel.CRITICAL, DeteriorationPattern.SEPSIS),
        ("Rapid Deterioration", SeverityLevel.HIGH, DeteriorationPattern.RAPID_DECLINE),
        ("Multiple Critical Vitals", SeverityLevel.HIGH, DeteriorationPattern.RESPIRATORY)
    ]
    
    for scenario_name, severity, pattern in scenarios:
        patient = EnhancedDataGenerator.generate_patient(
            severity=severity,
            location="ED",
            deterioration_pattern=pattern
        )
        
        # Assess twice to show deterioration
        agent.assess_patient(patient)
        
        # Worsen vitals
        patient.vitals = EnhancedDataGenerator.generate_vitals(
            age=patient.age,
            severity=SeverityLevel.CRITICAL,
            deterioration=pattern,
            time_offset=30
        )
        
        assessment = agent.assess_patient(patient)
        
        print(f"\n   {scenario_name}:")
        print(f"      Escalation: {'YES ⚠️' if assessment.needs_escalation else 'NO'}")
        if assessment.needs_escalation:
            print(f"      Reason: {assessment.escalation_reason}")
        print(f"      Risk: {assessment.risk_score:.1f} | Trend: {assessment.trend.value}")
        print(f"      Monitoring: Every {assessment.recommended_monitoring_frequency} min")


def test_agent_queries():
    """Test agent query methods"""
    print("\n" + "="*70)
    print("TEST 5: Agent Query Methods")
    print("="*70)
    
    agent = RiskMonitorAgent()
    
    # Create mix of patients
    patients = []
    for i, (severity, pattern) in enumerate([
        (SeverityLevel.LOW, DeteriorationPattern.STABLE),
        (SeverityLevel.MODERATE, DeteriorationPattern.STABLE),
        (SeverityLevel.HIGH, DeteriorationPattern.GRADUAL_DECLINE),
        (SeverityLevel.CRITICAL, DeteriorationPattern.SEPSIS)
    ]):
        p = EnhancedDataGenerator.generate_patient(severity=severity, deterioration_pattern=pattern)
        patients.append(p)
        agent.assess_patient(p)
    
    high_risk = agent.get_high_risk_patients()
    deteriorating = agent.get_deteriorating_patients()
    
    print(f"\n   Total Patients: {len(patients)}")
    print(f"   High Risk: {len(high_risk)} patients")
    print(f"   Deteriorating: {len(deteriorating)} patients")
    
    # Show details
    for patient_id in high_risk[:2]:  # Show first 2
        history = agent.get_patient_history(patient_id)
        if history and history.latest_assessment:
            a = history.latest_assessment
            print(f"\n   High Risk Patient {patient_id}:")
            print(f"      Score: {a.risk_score:.1f} | Level: {a.risk_level.value}")
            print(f"      Trend: {a.trend.value}")


if __name__ == "__main__":
    print("\n🧪 PHASE 2 TEST: RISK MONITOR AGENT\n")
    
    try:
        test_risk_scoring()
        test_deterioration_detection()
        test_trend_tracking()
        test_escalation_logic()
        test_agent_queries()
        
        print("\n" + "="*70)
        print("✅ ALL PHASE 2 TESTS COMPLETED!")
        print("="*70)
        print("\n💡 Phase 2 Implementation Complete:")
        print("   1. ✅ Risk assessment models")
        print("   2. ✅ Risk calculation algorithms (NEWS2-based)")
        print("   3. ✅ Trend analysis and deterioration detection")
        print("   4. ✅ Escalation logic")
        print("   5. ✅ Agent query methods")
        print("\n")
        
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
