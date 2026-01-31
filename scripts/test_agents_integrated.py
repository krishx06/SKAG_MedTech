#!/usr/bin/env python3
"""
Test Capacity Intelligence and Flow Orchestrator Agents
Tests hospital capacity tracking and patient flow recommendations with synthetic data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simulation.data_generator import EnhancedDataGenerator
from backend.simulation.event_types import SeverityLevel, DeteriorationPattern

# Import agents using their full module paths to avoid conflicts
from backend.agents.capacity_intelligence.agent import CapacityIntelligenceAgent, create_demo_capacity_agent
from backend.agents.flow_orchestrator.agent import FlowOrchestratorAgent

# Import RiskMonitorAgent separately
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "agents" / "risk_monitor"))
from agent import RiskMonitorAgent
sys.path.pop(0)  # Remove after import


def test_capacity_intelligence():
    """Test Capacity Intelligence Agent with synthetic patients"""
    print("="*70)
    print("TEST 1: Capacity Intelligence Agent")
    print("="*70)
    
    # Create agent with demo data
    capacity_agent = create_demo_capacity_agent()
    
    print("\n📊 Initial Hospital Capacity:")
    status = capacity_agent.get_status_summary()
    print(f"   Total Beds: {status['hospital_total_beds']}")
    print(f"   Available: {status['hospital_available_beds']}")
    print(f"   Overall Occupancy: {status['hospital_occupancy']}")
    
    print("\n🏥 Unit-by-Unit Breakdown:")
    assessments = capacity_agent.get_all_assessments()
    for unit_name, assessment in assessments.items():
        print(f"\n   {unit_name}:")
        print(f"      Occupancy: {assessment.current_occupancy:.1%} ({assessment.total_bed_count - assessment.available_bed_count}/{assessment.total_bed_count})")
        print(f"      Capacity Score: {assessment.capacity_score:.1f}/100")
        print(f"      Staff Ratio: {assessment.staff_ratio:.1f} patients/staff")
        if assessment.available_bed_count > 0:
            print(f"      ✅ {assessment.available_bed_count} beds available")
        else:
            print(f"      ❌ No beds available")
        if assessment.bottleneck_reason:
            print(f"      ⚠️  Bottleneck: {assessment.bottleneck_reason}")
    
    # Test finding best unit for admission
    print("\n🔍 Finding Best Unit for New Admissions:")
    
    test_cases = [
        (["ICU"], "Critical patient needs ICU"),
        (["Ward", "Step-Down"], "Moderate patient, Ward/Step-Down preferred"),
        (None, "Any available unit")
    ]
    
    for preferred_units, description in test_cases:
        best_unit = capacity_agent.find_best_unit_for_admission(preferred_units)
        print(f"\n   {description}:")
        if best_unit:
            occupancy = capacity_agent.get_unit_occupancy(best_unit)
            print(f"      Recommended: {best_unit} (Occupancy: {occupancy:.1%})")
        else:
            print(f"      ⚠️  No available units")


def test_flow_orchestrator_with_synthetic_patients():
    """Test Flow Orchestrator with synthetic patient data"""
    print("\n" + "="*70)
    print("TEST 2: Flow Orchestrator with Synthetic Patients")
    print("="*70)
    
    # Create agents
    capacity_agent = create_demo_capacity_agent()
    risk_agent = RiskMonitorAgent()
    flow_agent = FlowOrchestratorAgent()
    
    # Set capacity data in flow agent
    capacity_assessments = capacity_agent.get_all_assessments()
    flow_agent.set_capacity_assessments(capacity_assessments)
    
    # Test with different severity patients
    test_patients = [
        (SeverityLevel.CRITICAL, DeteriorationPattern.SEPSIS, "Critical sepsis patient"),
        (SeverityLevel.HIGH, DeteriorationPattern.RESPIRATORY, "High-risk respiratory patient"),
        (SeverityLevel.MODERATE, DeteriorationPattern.STABLE, "Moderate stable patient"),
        (SeverityLevel.LOW, DeteriorationPattern.STABLE, "Low-risk patient")
    ]
    
    for severity, pattern, description in test_patients:
        # Generate synthetic patient
        patient = EnhancedDataGenerator.generate_patient(
            severity=severity,
            location="ED",
            deterioration_pattern=pattern
        )
        
        # Get risk assessment
        risk_assessment = risk_agent.assess_patient(patient)
        flow_agent.set_risk_assessment(patient.id, risk_assessment.model_dump())
        
        # Get flow recommendation
        patient_context = {
            "acuity": int(patient.acuity_level),
            "age": patient.age,
            "comorbidities": len(patient.comorbidities),
            "vitals": {
                "spo2": patient.vitals.spo2,
                "heart_rate": patient.vitals.heart_rate,
                "systolic_bp": patient.vitals.systolic_bp
            }
        }
        
        recommendation = flow_agent.get_recommendation(
            patient_id=patient.id,
            patient_context=patient_context,
            capacity_assessments=capacity_assessments,
            risk_assessment=risk_assessment.model_dump()
        )
        
        print(f"\n📋 {description} (ID: {patient.id}):")
        print(f"   Risk Score: {risk_assessment.risk_score:.1f}/100 ({risk_assessment.risk_level.value})")
        print(f"   Age: {patient.age} | Comorbidities: {len(patient.comorbidities)}")
        print(f"   Vitals: SpO2={patient.vitals.spo2:.1f}%, HR={patient.vitals.heart_rate:.0f}")
        print(f"\n   💡 Recommendation:")
        print(f"      Action: {recommendation.recommended_action.value}")
        if recommendation.recommended_unit:
            print(f"      Unit: {recommendation.recommended_unit}")
        print(f"      Confidence: {recommendation.confidence:.1%}")
        print(f"      Urgent: {'YES ⚠️' if recommendation.urgent else 'No'}")
        if recommendation.reasoning:
            print(f"      Reason: {recommendation.reasoning[:100]}...")


def test_what_if_scenarios():
    """Test what-if scenario analysis"""
    print("\n" + "="*70)
    print("TEST 3: What-If Scenario Analysis")
    print("="*70)
    
    flow_agent = FlowOrchestratorAgent()
    
    # Create a high-risk deteriorating patient
    patient = EnhancedDataGenerator.generate_patient(
        severity=SeverityLevel.HIGH,
        location="ED",
        deterioration_pattern=DeteriorationPattern.GRADUAL_DECLINE
    )
    
    patient_context = {
        "acuity": int(patient.acuity_level),
        "age": patient.age,
        "risk_score": 65,
        "trend": "deteriorating"
    }
    
    print(f"\n👤 Patient {patient.id} - High Risk, Deteriorating")
    print(f"   Age: {patient.age}, Risk Score: 65/100")
    print(f"   Current SpO2: {patient.vitals.spo2:.1f}%")
    
    print("\n🔮 What-If Scenarios:")
    
    wait_times = [0, 15, 30, 60]
    for wait_min in wait_times:
        outcome = flow_agent.run_what_if(
            patient_id=patient.id,
            wait_minutes=wait_min,
            patient_context=patient_context,
            capacity_score=60
        )
        
        print(f"\n   Wait {wait_min} minutes:")
        print(f"      Predicted Capacity: {outcome.predicted_capacity_score:.1f}")
        print(f"      Predicted Wait: {outcome.predicted_wait_for_bed} min")
        print(f"      Risk Level: {outcome.risk_level}")
        print(f"      Better Outcome Probability: {outcome.probability_of_better_outcome:.0%}")
        print(f"      Recommendation: {'⚠️ WAIT' if outcome.is_favorable else '✅ ACT NOW'}")


def test_integrated_workflow():
    """Test all agents working together"""
    print("\n" + "="*70)
    print("TEST 4: Integrated Multi-Agent Workflow")
    print("="*70)
    
    # Initialize all agents
    capacity_agent = create_demo_capacity_agent()
    risk_agent = RiskMonitorAgent()
    flow_agent = FlowOrchestratorAgent()
    
    # Set up capacity in flow agent
    capacity_assessments = capacity_agent.get_all_assessments()
    flow_agent.set_capacity_assessments(capacity_assessments)
    
    # Simulate 5 patient arrivals
    print("\n🚑 Simulating 5 Patient Arrivals:")
    
    severities = [
        SeverityLevel.CRITICAL,
        SeverityLevel.HIGH,
        SeverityLevel.HIGH,
        SeverityLevel.MODERATE,
        SeverityLevel.LOW
    ]
    
    for i, severity in enumerate(severities, 1):
        patient = EnhancedDataGenerator.generate_patient(
            severity=severity,
            location="ED"
        )
        
        # Step 1: Risk Monitor assesses patient
        risk = risk_agent.assess_patient(patient)
        
        # Step 2: Flow Orchestrator gets recommendation
        flow_agent.set_risk_assessment(patient.id, risk.model_dump())
        
        patient_context = {
            "acuity": int(patient.acuity_level),
            "age": patient.age
        }
        
        recommendation = flow_agent.get_recommendation(
            patient_id=patient.id,
            patient_context=patient_context,
            capacity_assessments=capacity_assessments,
            risk_assessment=risk.model_dump()
        )
        
        print(f"\n   Patient #{i} ({patient.id}):")
        print(f"      Severity: {severity.value} | Risk: {risk.risk_score:.1f}")
        print(f"      → {recommendation.recommended_action.value.upper()}", end="")
        if recommendation.recommended_unit:
            print(f" to {recommendation.recommended_unit}", end="")
        print(f" (Confidence: {recommendation.confidence:.0%})")


if __name__ == "__main__":
    print("\n🧪 TESTING CAPACITY INTELLIGENCE & FLOW ORCHESTRATOR\n")
    
    try:
        test_capacity_intelligence()
        test_flow_orchestrator_with_synthetic_patients()
        test_what_if_scenarios()
        test_integrated_workflow()
        
        print("\n" + "="*70)
        print("✅ ALL AGENT TESTS COMPLETED!")
        print("="*70)
        print("\n💡 Agents Tested:")
        print("   1. ✅ Capacity Intelligence Agent")
        print("   2. ✅ Flow Orchestrator Agent")
        print("   3. ✅ Risk Monitor Agent")
        print("   4. ✅ Integrated Multi-Agent Workflow")
        print("\n")
        
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
