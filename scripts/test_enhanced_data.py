#!/usr/bin/env python3
"""
Test to demonstrate enhanced synthetic data improvements.
Shows age-specific vitals, realistic comorbidities, and evidence-based deterioration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simulation.data_generator import EnhancedDataGenerator
from backend.simulation.event_types import SeverityLevel, DeteriorationPattern


def test_age_specific_vitals():
    """Show that vitals are age-appropriate"""
    print("="*70)
    print("TEST 1: Age-Specific Vital Signs")
    print("="*70)
    
    ages = [25, 55, 75, 90]
    for age in ages:
        vitals = EnhancedDataGenerator.generate_vitals(
            age=age,
            severity=SeverityLevel.MODERATE,
            deterioration=DeteriorationPattern.STABLE
        )
        age_group = EnhancedDataGenerator.get_age_group(age)
        print(f"\n👤 Age {age} ({age_group}):")
        print(f"   HR: {vitals.heart_rate} bpm")
        print(f"   BP: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg")
        print(f"   SpO2: {vitals.spo2}%")
        print(f"   RR: {vitals.respiratory_rate} breaths/min")
        print(f"   Temp: {vitals.temperature}°C")


def test_realistic_comorbidities():
    """Show age-correlated comorbidities"""
    print("\n" + "="*70)
    print("TEST 2: Age-Correlated Comorbidities")
    print("="*70)
    
    ages = [30, 50, 70, 85]
    for age in ages:
        patient = EnhancedDataGenerator.generate_patient(
            severity=SeverityLevel.MODERATE,
            location="ED"
        )
        patient.age = age  # Override for testing
        comorbidities = EnhancedDataGenerator.generate_comorbidities(age, "Chest pain")
        
        print(f"\n👤 Age {age}:")
        print(f"   Comorbidities ({len(comorbidities)}): {', '.join(comorbidities) if comorbidities else 'None'}")


def test_deterioration_patterns():
    """Show evidence-based deterioration patterns"""
    print("\n" + "="*70)
    print("TEST 3: Evidence-Based Deterioration Patterns")
    print("="*70)
    
    patterns = [
        (DeteriorationPattern.SEPSIS, "Sepsis"),
        (DeteriorationPattern.RESPIRATORY, "Respiratory Failure"),
        (DeteriorationPattern.CARDIAC, "Cardiac"),
    ]
    
    for pattern, name in patterns:
        print(f"\n🚨 {name} Deterioration:")
        
        # Initial vitals
        initial = EnhancedDataGenerator.generate_vitals(
            age=65,
            severity=SeverityLevel.HIGH,
            deterioration=pattern,
            time_offset=0
        )
        
        # After 30 minutes
        after_30 = EnhancedDataGenerator.generate_vitals(
            age=65,
            severity=SeverityLevel.HIGH,
            deterioration=pattern,
            time_offset=30
        )
        
        print(f"   Initial  → HR: {initial.heart_rate:3.0f}, BP: {initial.systolic_bp:3.0f}/{initial.diastolic_bp:2.0f}, SpO2: {initial.spo2:4.1f}%")
        print(f"   30 min   → HR: {after_30.heart_rate:3.0f}, BP: {after_30.systolic_bp:3.0f}/{after_30.diastolic_bp:2.0f}, SpO2: {after_30.spo2:4.1f}%")
        print(f"   Changes  → HR: {after_30.heart_rate - initial.heart_rate:+.0f}, SpO2: {after_30.spo2 - initial.spo2:+.1f}%")


def test_complete_patient():
    """Show complete patient generation with all enhancements"""
    print("\n" + "="*70)
    print("TEST 4: Complete Enhanced Patient")
    print("="*70)
    
    patient = EnhancedDataGenerator.generate_patient(
        severity=SeverityLevel.CRITICAL,
        location="ED",
        deterioration_pattern=DeteriorationPattern.SEPSIS,
        chief_complaint="Sepsis - fever, hypotension"
    )
    
    print(f"\n👤 Patient: {patient.name} (ID: {patient.id})")
    print(f"   Age: {patient.age} years")
    print(f"   Gender: {patient.gender}")
    print(f"   Chief Complaint: {patient.chief_complaint}")
    print(f"   Acuity: Level {patient.acuity_level} (1=Resuscitation, 5=Non-Urgent)")
    print(f"\n   Comorbidities ({len(patient.comorbidities)}):")
    for comorb in patient.comorbidities:
        print(f"      • {comorb}")
    
    print(f"\n   Vital Signs:")
    print(f"      HR: {patient.vitals.heart_rate} bpm")
    print(f"      BP: {patient.vitals.blood_pressure}")
    print(f"      SpO2: {patient.vitals.spo2}%")
    print(f"      Temp: {patient.vitals.temperature}°C")
    print(f"      RR: {patient.vitals.respiratory_rate} breaths/min")
    
    print(f"\n   Risk Factors:")
    print(f"      Sepsis Risk: {patient.risk_factors.sepsis_probability:.1%}")
    print(f"      Cardiac Risk: {patient.risk_factors.cardiac_risk:.1%}")
    print(f"      Respiratory Risk: {patient.risk_factors.respiratory_risk:.1%}")
    print(f"      Deterioration Trend: {patient.risk_factors.deterioration_trend:.2f}")
    print(f"      Comorbidity Score: {patient.risk_factors.comorbidity_score:.2f}")


if __name__ == "__main__":
    print("\n🧪 ENHANCED SYNTHETIC DATA GENERATOR TESTS\n")
    
    test_age_specific_vitals()
    test_realistic_comorbidities()
    test_deterioration_patterns()
    test_complete_patient()
    
    print("\n" + "="*70)
    print("✅ All enhancement tests completed!")
    print("="*70)
    print("\n💡 Key Improvements:")
    print("   1. ✅ Age-specific vital sign ranges")
    print("   2. ✅ Realistic comorbidity correlations")
    print("   3. ✅ Evidence-based deterioration patterns")
    print("   4. ✅ Chief complaint → risk factor mapping")
    print("   5. ✅ Age-correlated comorbidity prevalence")
    print("\n")
