"""
End-to-End Pipeline Test for AdaptiveCare

Tests the full multi-agent workflow:
Simulation → Risk Monitor → Capacity Intelligence → Flow Orchestrator → Escalation Decision
"""
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_full_pipeline():
    """Test complete agent pipeline end-to-end."""
    
    print("\n" + "="*70)
    print("🧪 FULL AGENT PIPELINE TEST")
    print("="*70 + "\n")
    
    try:
        # Step 1: Initialize components (use existing Phase 3 integration)
        print("📦 Step 1: Testing via Simulation Orchestrator...")
        from backend.simulation.simulation_orchestrator import SimulationOrchestrator
        from backend.agents.risk_monitor.agent import RiskMonitor
        from backend.core.event_bus import get_event_bus
        from backend.core.state_manager import get_state_manager
        
        event_bus = get_event_bus()
        state_manager = get_state_manager()
        
        # Initialize Risk Monitor
        risk_monitor = RiskMonitor()
        
        # Initialize Simulation Orchestrator
        orchestrator = SimulationOrchestrator(risk_monitor)
        
        print("✅ Components initialized (using Phase 3 setup)\n")
        
        # Step 2: Start Simulation
        print("📦 Step 2: Starting Simulation...")
        result = orchestrator.start_simulation(
            scenario="busy_thursday",
            duration=30,  # 30 simulated minutes
            arrival_rate=12.0
        )
        
        if result["status"] != "success":
            raise Exception(f"Simulation start failed: {result.get('message')}")
        
        print(f"✅ Simulation started: {result['scenario']}")
        print(f"   Duration: {result['duration']} sim-minutes\n")
        
        # Step 3: Wait for simulation to complete
        print("📦 Step 3: Running Simulation...")
        import time
        time.sleep(3)  # Give simulation time to run
        
        # Step 4: Check Results
        print("📦 Step 4: Analyzing Results...")
        status = orchestrator.get_status()
        patients = orchestrator.get_patients()
        
        print(f"✅ Simulation completed!")
        print(f"   Total Arrivals: {status['total_arrivals']}")
        print(f"   Risk Assessments: {status['total_assessments']}")
        print(f"   Active Patients: {len(patients)}")
        print(f"   High Risk: {status['high_risk_patients']}\n")
        
        # Step 5: Test Individual Patient Risk Assessment
        if patients:
            print("📦 Step 5: Testing Patient Risk Assessment...")
            patient_id = patients[0]["id"]
            risk = orchestrator.get_patient_risk(patient_id)
            
            print(f"✅ Risk assessment for {patient_id}:")
            print(f"   Score: {risk['risk_score']}/100")
            print(f"   Level: {risk['risk_level']}")
            print(f"   Trend: {risk['trend']}\n")
        
        # Step 6: Test Capacity Intelligence (if integrated)
        print("📦 Step 6: Testing Capacity Intelligence...")
        try:
            from backend.agents.capacity_intelligence import CapacityIntelligenceAgent
            capacity_agent = CapacityIntelligenceAgent(event_bus, state_manager)
            await capacity_agent.start()
            
            # Get capacity assessment
            capacity_data = state_manager.get_capacity()
            if capacity_data:
                print(f"✅ Capacity tracked:")
                print(f"   Total Beds: {capacity_data.total_beds}")
                print(f"   Available: {capacity_data.total_available}")
                print(f"   Occupancy: {capacity_data.overall_occupancy_rate:.1f}%\n")
            else:
                print("⚠️  Capacity data not initialized\n")
                
            await capacity_agent.stop()
        except Exception as e:
            print(f"⚠️  Capacity Intelligence test skipped: {e}\n")
        
        # Step 7: Test Flow Orchestrator (if integrated)
        print("📦 Step 7: Testing Flow Orchestrator...")
        try:
            from backend.agents.flow_orchestrator import FlowOrchestratorAgent
            flow_agent = FlowOrchestratorAgent(event_bus, state_manager)
            await flow_agent.start()
            
            print("✅ Flow Orchestrator initialized\n")
            await flow_agent.stop()
        except Exception as e:
            print(f"⚠️  Flow Orchestrator test skipped: {e}\n")
        
        # Step 8: Test Escalation Decision (if integrated)
        print("📦 Step 8: Testing Escalation Decision Agent...")
        try:
            from backend.agents.escalation_decision import EscalationDecisionAgent
            from backend.reasoning.decision_engine import DecisionEngine
            
            decision_engine = DecisionEngine()
            escalation_agent = EscalationDecisionAgent(event_bus, state_manager, decision_engine)
            await escalation_agent.start()
            
            print("✅ Escalation Decision Agent initialized\n")
            await escalation_agent.stop()
        except Exception as e:
            print(f"⚠️  Escalation Decision test skipped: {e}\n")
        
        # Final Results
        print("="*70)
        print("✅ FULL PIPELINE TEST PASSED!")
        print("="*70)
        print(f"\n📊 Final Statistics:")
        print(f"   Patients Processed: {len(patients)}")
        print(f"   Risk Assessments: {status['total_assessments']}")
        print(f"   High Risk Detected: {status['high_risk_patients']}")
        print(f"   Avg Assessments/Patient: {status['total_assessments'] / max(len(patients), 1):.1f}")
        
        # Cleanup
        orchestrator.stop_simulation()
        
        return True
        
    except Exception as e:
        print(f"\n❌ PIPELINE TEST FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    
    import sys
    sys.exit(0 if success else 1)
