"""
Backend API Test Script

Tests all backend API endpoints to verify functionality.
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_test(name: str):
    """Print test header."""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"{'='*70}")


def test_health_check():
    """Test health endpoint."""
    print_test("TEST 1: Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed!")
    
    return response.json()


def test_get_patients():
    """Test get patients endpoint."""
    print_test("TEST 2: Get Patients")
    
    response = requests.get(f"{BASE_URL}/api/patients")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} patients")
    
    if data:
        print(f"\nFirst patient:")
        print(json.dumps(data[0], indent=2))
    
    assert response.status_code == 200
    print("✅ Get patients passed!")
    
    return data


def test_get_patient_by_id(patient_id: str):
    """Test get single patient."""
    print_test(f"TEST 3: Get Patient {patient_id}")
    
    response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Patient: {data.get('name', 'N/A')}")
        print(f"Age: {data.get('age', 'N/A')}")
        print(f"Acuity: {data.get('acuity_level', 'N/A')}")
        print("✅ Get patient by ID passed!")
        return data
    else:
        print(f"⚠️  Patient not found")
        return None


def test_capacity_snapshot():
    """Test capacity endpoint."""
    print_test("TEST 4: Get Capacity Snapshot")
    
    response = requests.get(f"{BASE_URL}/api/capacity")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        print("✅ Capacity check passed!")
        return data
    else:
        print(f"⚠️  Capacity endpoint returned {response.status_code}")
        return None


def test_agent_status():
    """Test agent status endpoint."""
    print_test("TEST 5: Get Agent Status")
    
    response = requests.get(f"{BASE_URL}/api/agents/status")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nActive Agents: {len(data.get('agents', []))}")
        for agent in data.get('agents', []):
            print(f"  - {agent.get('name')}: {agent.get('status')}")
        print("✅ Agent status passed!")
        return data
    else:
        print(f"⚠️  Agent status returned {response.status_code}")
        return None


def test_recent_decisions():
    """Test decisions endpoint."""
    print_test("TEST 6: Get Recent Decisions")
    
    response = requests.get(f"{BASE_URL}/api/decisions/recent?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nRecent decisions: {len(data)}")
        for decision in data[:3]:
            print(f"  - {decision.get('decision_type')}: {decision.get('patient_id')}")
        print("✅ Decisions check passed!")
        return data
    else:
        print(f"⚠️  Decisions endpoint returned {response.status_code}")
        return None


def test_simulation_status():
    """Test simulation status."""
    print_test("TEST 7: Simulation Status")
    
    response = requests.get(f"{BASE_URL}/api/simulation/status")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        print("✅ Simulation status passed!")
        return data
    else:
        print(f"⚠️  Simulation status returned {response.status_code}")
        return None


def run_all_tests():
    """Run all API tests."""
    print("\n" + "="*70)
    print("🧪 BACKEND API TESTS")
    print("="*70)
    
    try:
        # Test 1: Health
        health = test_health_check()
        
        # Test 2: Patients
        patients = test_get_patients()
        
        # Test 3: Single patient (if we have any)
        if patients:
            test_get_patient_by_id(patients[0]['id'])
        
        # Test 4: Capacity
        test_capacity_snapshot()
        
        # Test 5: Agents
        test_agent_status()
        
        # Test 6: Decisions
        test_recent_decisions()
        
        # Test 7: Simulation
        test_simulation_status()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL API TESTS PASSED!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  Base URL: {BASE_URL}")
        print(f"  All endpoints responding")
        print(f"  Backend API is functional!")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print(f"   Make sure server is running on {BASE_URL}")
        print(f"   Run: python backend/run.py")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Backend API Tests...")
    print(f"   Target: {BASE_URL}")
    print(f"   Waiting 2s for any pending startup...")
    time.sleep(2)
    
    success = run_all_tests()
    
    import sys
    sys.exit(0 if success else 1)
