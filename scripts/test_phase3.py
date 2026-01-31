"""
Phase 3 Integration Test Script

Tests the complete Phase 3 integration:
- Simulation Orchestrator
- Risk Monitor integration
- REST API endpoints
- Real-time event processing
"""
import sys
import time
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE = "http://localhost:8000"


def test_api_health():
    """Test 1: API Health Check"""
    print("\n" + "="*70)
    print("TEST 1: API Health Check")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    
    data = response.json()
    print(f"✅ API Status: {data['status']}")
    print(f"   Components: {data.get('components', {})}")


def test_start_simulation():
    """Test 2: Start Simulation"""
    print("\n" + "="*70)
    print("TEST 2: Start Simulation with Risk Monitor")
    print("="*70)
    
    payload = {
        "scenario": "busy_thursday",
        "duration": 60,  # 1 hour for testing
        "arrival_rate": 15.0
    }
    
    response = requests.post(f"{API_BASE}/api/simulation/start", json=payload)
    assert response.status_code == 200, f"Failed to start: {response.status_code}"
    
    data = response.json()
    print(f"✅ Simulation started")
    print(f"   Scenario: {data.get('scenario')}")
    print(f"   Duration: {data.get('duration')} minutes")
    print(f"   Arrival Rate: {data.get('arrival_rate')} patients/hour")
    
    return data


def test_simulation_status():
    """Test 3: Get Simulation Status"""
    print("\n" + "="*70)
    print("TEST 3: Simulation Status")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/simulation/status")
    assert response.status_code == 200
    
    status = response.json()
    print(f"✅ Simulation Running: {status['running']}")
    print(f"   Total Arrivals: {status['total_arrivals']}")
    print(f"   Total Assessments: {status['total_assessments']}")
    print(f"   Active Patients: {status['active_patients']}")
    print(f"   High Risk Patients: {status['high_risk_patients']}")
    print(f"   Deteriorating Patients: {status['deteriorating_patients']}")
    
    return status


def test_get_patients():
    """Test 4: Get All Patients"""
    print("\n" + "="*70)
    print("TEST 4: Get All Patients")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/patients")
    assert response.status_code == 200
    
    patients = response.json()
    print(f"✅ Retrieved {len(patients)} patients")
    
    if patients:
        print("\n   Sample Patient:")
        p = patients[0]
        print(f"   ID: {p['id']}")
        print(f"   Age: {p['age']} | Acuity: {p['acuity_level']}")
        print(f"   Complaint: {p['chief_complaint']}")
        if 'risk' in p:
            print(f"   Risk Score: {p['risk']['score']:.1f}/100")
            print(f"   Risk Level: {p['risk']['level']}")
            print(f"   Trend: {p['risk']['trend']}")
    
    return patients


def test_patient_risk(patient_id: str):
    """Test 5: Get Patient Risk Assessment"""
    print("\n" + "="*70)
    print(f"TEST 5: Get Risk Assessment for Patient {patient_id}")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/patients/{patient_id}/risk")
    
    if response.status_code == 404:
        print(f"⚠️  No risk assessment yet for {patient_id}")
        return None
    
    assert response.status_code == 200
    
    risk = response.json()
    print(f"✅ Risk Assessment Retrieved")
    print(f"   Risk Score: {risk['risk_score']:.1f}/100")
    print(f"   Risk Level: {risk['risk_level']}")
    print(f"   Trend: {risk['trend']}")
    print(f"   Needs Escalation: {'YES ⚠️' if risk['needs_escalation'] else 'No'}")
    
    if risk['critical_vitals']:
        print(f"   Critical Vitals: {', '.join(risk['critical_vitals'])}")
    
    if risk['escalation_reason']:
        print(f"   Escalation Reason: {risk['escalation_reason']}")
    
    return risk


def test_stop_simulation():
    """Test 6: Stop Simulation"""
    print("\n" + "="*70)
    print("TEST 6: Stop Simulation")
    print("="*70)
    
    response = requests.post(f"{API_BASE}/api/simulation/stop")
    assert response.status_code == 200
    
    data = response.json()
    print(f"✅ Simulation stopped")
    print(f"   Duration: {data.get('duration_seconds', 0):.1f} seconds")
    print(f"   Total Arrivals: {data.get('total_arrivals', 0)}")
    print(f"   Total Assessments: {data.get('total_assessments', 0)}")
    
    return data


def run_phase3_tests():
    """Run all Phase 3 integration tests."""
    print("\n🧪 PHASE 3 INTEGRATION TESTS - Backend API & Real-Time Integration")
    print("="*70)
    
    try:
        # Test 1: Health Check
        test_api_health()
        
        # Test 2: Start Simulation
        start_result = test_start_simulation()
        
        # Wait for some patients to arrive
        print("\n⏳ Waiting 10 seconds for patients to arrive...")
        time.sleep(10)
        
        # Test 3: Check Status
        status = test_simulation_status()
        
        # Test 4: Get Patients
        patients = test_get_patients()
        
        # Test 5: Get Risk Assessment (if we have patients)
        if patients:
            print(f"\n📊 Testing risk assessments for first 3 patients...")
            for patient in patients[:3]:
                test_patient_risk(patient['id'])
                time.sleep(1)
        
        # Wait a bit more to accumulate data
        print("\n⏳ Waiting another 10 seconds for more  data...")
        time.sleep(10)
        
        # Re-check status
        final_status = test_simulation_status()
        
        # Test 6: Stop Simulation
        stop_result = test_stop_simulation()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL PHASE 3 TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📈 Summary:")
        print(f"   • Patients Processed: {stop_result.get('total_arrivals', 0)}")
        print(f"   • Risk Assessments: {stop_result.get('total_assessments', 0)}")
        print(f"   • Simulation Duration: {stop_result.get('duration_seconds', 0):.1f}s")
        print(f"\n💡 Phase 3 Components Verified:")
        print(f"   ✅ Simulation Orchestrator")
        print(f"   ✅ Risk Monitor Integration")
        print(f"   ✅ REST API Endpoints")
        print(f"   ✅ Real-time Patient Processing")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to API at {API_BASE}")
        print(f"   Make sure the backend server is running:")
        print(f"   cd backend && python run.py")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n" + "🚀 Starting Phase 3 Integration Tests...")
    print(f"📍 API Base URL: {API_BASE}")
    print("\n⚠️  IMPORTANT: Make sure the backend server is running!")
    print("   Run in another terminal: cd backend && python run.py")
    
    input("\nPress Enter when ready to start tests...")
    
    success = run_phase3_tests()
    
    sys.exit(0 if success else 1)
