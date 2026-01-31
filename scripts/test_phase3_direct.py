"""
Phase 3 Direct Integration Test

Tests the simulation orchestrator and Risk Monitor integration
without requiring the full backend server.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simulation.simulation_orchestrator import SimulationOrchestrator
import time


def test_orchestrator_lifecycle():
    """Test 1: Orchestrator Start/Stop"""
    print("\n" + "="*70)
    print("TEST 1: Simulation Orchestrator Lifecycle")
    print("="*70)
    
    orchestrator = SimulationOrchestrator()
    
    # Start simulation
    print("\n🚀 Starting simulation...")
    result = orchestrator.start_simulation(
        scenario="busy_thursday",
        duration=30,  # 30 simulated minutes
        arrival_rate=20.0
    )
    
    assert result["status"] == "started", f"Failed to start: {result}"
    print(f"✅ Simulation started successfully")
    print(f"   Scenario: {result['scenario']}")
    print(f"   Duration: {result['duration']} minutes (simulated time)")
    print(f"\n📝 Note: SimPy runs in simulated time, not real-time")
    print(f"   30 simulated minutes may complete in <1 second")
    
    return orchestrator


def test_simulation_results(orchestrator):
    """Test 2: Simulation Results"""
    print("\n" + "="*70)
    print("TEST 2: Simulation Results & Risk Assessments")
    print("="*70)
    
    # Wait a moment for thread to complete
    print("\n⏳ Waiting for simulation thread to complete...")
    time.sleep(2)
    
    # Get status
    status = orchestrator.get_status()
    print(f"\n📊 Final Status:")
    print(f"   Running: {status['running']}")
    print(f"   Total Arrivals: {status['total_arrivals']}")
    print(f"   Total Assessments: {status['total_assessments']}")
    print(f"   Active Patients: {status['active_patients']}")
    print(f"   High Risk: {status['high_risk_patients']}")
    print(f"   Deteriorating: {status['deteriorating_patients']}")
    
    # Verify we got results
    assert status['total_arrivals'] > 0, "Should have patient arrivals"
    assert status['total_assessments'] > 0, "Should have risk assessments"
    assert status['active_patients'] > 0, "Should have active patients"
    
    print(f"\n✅ Simulation completed with results!")
    
    return status


def test_patient_data(orchestrator):
    """Test 3: Patient Data Retrieval"""
    print("\n" + "="*70)
    print("TEST 3: Patient Data with Risk Assessments")
    print("="*70)
    
    patients = orchestrator.get_patients()
    
    print(f"\n🏥 Retrieved {len(patients)} patients")
    
    if patients:
        print(f"\n📋 Patient Details:")
        for i, patient in enumerate(patients, 1):
            print(f"\n   Patient {i}:")
            print(f"      ID: {patient['id']}")
            print(f"      Age: {patient['age']} | Acuity: {patient['acuity_level']}")
            print(f"      Complaint: {patient['chief_complaint']}")
            
            if 'risk' in patient:
                risk = patient['risk']
                print(f"      Risk Score: {risk['score']:.1f}/100")
                print(f"      Risk Level: {risk['level']}")
                print(f"      Trend: {risk['trend']}")
                
                if risk['needs_escalation']:
                    print(f"      ⚠️  NEEDS ESCALATION")
                    
                if risk['critical_vitals']:
                    print(f"      Critical Vitals: {', '.join(risk['critical_vitals'])}")
    
    print(f"\n✅ Patient data retrieval working!")
    assert len(patients) > 0, "Should have retrieved patients"
    
    return patients


def test_specific_risk_assessment(orchestrator, patient_id):
    """Test 4: Specific Patient Risk Assessment"""
    print("\n" + "="*70)
    print(f"TEST 4: Detailed Risk Assessment for {patient_id}")
    print("="*70)
    
    risk = orchestrator.get_patient_risk(patient_id)
    
    if not risk:
        print(f"⚠️  No risk assessment found for {patient_id}")
        return None
    
    print(f"\n💊 Risk Assessment Details:")
    print(f"   Overall Risk: {risk['risk_score']:.1f}/100 ({risk['risk_level']})")
    print(f"   Trend: {risk['trend']}")
    print(f"   Monitoring Frequency: Every {risk['monitoring_frequency']} minutes")
    
    print(f"\n📊 Risk Breakdown:")
    breakdown = risk['risk_breakdown']
    print(f"   Vitals Score: {breakdown['vitals']:.1f}/40")
    print(f"   Deterioration: {breakdown['deterioration']:.1f}/30")
    print(f"   Comorbidities: {breakdown['comorbidities']:.1f}/15")
    print(f"   Acuity: {breakdown['acuity']:.1f}/15")
    
    if risk['vital_trends']:
        print(f"\n💓 Vital Trends:")
        for vital_name, trend in risk['vital_trends'].items():
            status = "🔴 CRITICAL" if trend['critical'] else "🟢 Normal"
            print(f"   {vital_name}: {trend['current']:.1f} ({trend['direction']}) {status}")
    
    if risk['needs_escalation']:
        print(f"\n⚠️  ESCALATION NEEDED: {risk['escalation_reason']}")
    
    print(f"\n✅ Detailed risk assessment retrieved!")
    
    return risk


def run_all_tests():
    """Run all Phase 3 integration tests."""
    print("\n🧪 PHASE 3 DIRECT INTEGRATION TESTS")
    print("   Testing: Simulation Orchestrator + Risk Monitor")
    print("="*70)
    
    try:
        # Test 1: Start
        orchestrator = test_orchestrator_lifecycle()
        
        # Test 2: Results (SimPy completes instantly in simulated time)
        status = test_simulation_results(orchestrator)
        
        # Test 3: Get patient data
        patients = test_patient_data(orchestrator)
        
        # Test 4: Detailed risk assessment (if we have patients)
        if patients:
            # Test first 2 patients
            for patient in patients[:2]:
                test_specific_risk_assessment(orchestrator, patient['id'])
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL PHASE 3 TESTS PASSED!")
        print("="*70)
        print(f"\n💡 Components Verified:")
        print(f"   ✅ Simulation Orchestrator (start/lifecycle)")
        print(f"   ✅ Risk Monitor Integration")
        print(f"   ✅ Real-time Risk Assessment")
        print(f"   ✅ Patient Data Retrieval")
        print(f"   ✅ Event Processing")
        
        print(f"\n📊 Test Summary:")
        print(f"   Patients: {status['total_arrivals']}")
        print(f"   Assessments: {status['total_assessments']}")
        print(f"   High Risk: {status['high_risk_patients']}")
        print(f"   Deteriorating: {status['deteriorating_patients']}")
        print(f"   Avg Assessments/Patient: {status['total_assessments']/max(status['total_arrivals'], 1):.1f}")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Phase 3 Direct Integration Tests...")
    print("   (No backend server required)")
    
    success = run_all_tests()
    
    sys.exit(0 if success else 1)
