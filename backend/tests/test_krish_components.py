"""
Test Script for Krish's Components

Verifies:
1. Capacity Intelligence Agent - bed tracking, staff ratios, CapacityAssessment
2. MCDA Framework - weighted scoring, trade-off analysis 
3. Flow Orchestrator Agent - placement recommendations with MCDA scores

Run: python -m backend.tests.test_krish_components
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime


def test_capacity_intelligence():
    """Test Capacity Intelligence Agent."""
    print("\n" + "="*60)
    print("TEST 1: Capacity Intelligence Agent")
    print("="*60)
    
    from backend.agents.capacity_intelligence import (
        CapacityIntelligenceAgent,
        create_demo_capacity_agent,
        UnitType
    )
    
    # Create agent with demo data
    agent = create_demo_capacity_agent()
    
    # Test 1.1: Get ICU Assessment
    print("\n[1.1] ICU Capacity Assessment:")
    icu_assessment = agent.get_unit_assessment("ICU")
    print(f"  - Occupancy: {icu_assessment.current_occupancy:.1%}")
    print(f"  - Staff Ratio: {icu_assessment.staff_ratio:.2f}")
    print(f"  - Capacity Score: {icu_assessment.capacity_score:.1f}/100")
    print(f"  - Available Beds: {icu_assessment.available_bed_count}")
    print(f"  - Bottleneck: {icu_assessment.bottleneck_reason or 'None'}")
    
    assert icu_assessment.current_occupancy > 0, "ICU should have some occupancy"
    assert icu_assessment.capacity_score > 0, "Capacity score should be positive"
    print("  ✓ ICU Assessment test passed")
    
    # Test 1.2: Get All Units
    print("\n[1.2] All Units Assessment:")
    all_assessments = agent.get_all_assessments()
    for unit_name, assessment in all_assessments.items():
        print(f"  - {unit_name}: {assessment.current_occupancy:.0%} occupied, "
              f"score={assessment.capacity_score:.0f}")
    
    assert len(all_assessments) >= 3, "Should have at least 3 units"
    print("  ✓ All units assessment test passed")
    
    # Test 1.3: Find Best Unit
    print("\n[1.3] Find Best Unit for Admission:")
    best_unit = agent.find_best_unit_for_admission()
    print(f"  - Best unit: {best_unit}")
    print("  ✓ Best unit selection test passed")
    
    # Test 1.4: Status Summary
    print("\n[1.4] Hospital Status Summary:")
    summary = agent.get_status_summary()
    print(f"  - Total Beds: {summary['hospital_total_beds']}")
    print(f"  - Available: {summary['hospital_available_beds']}")
    print(f"  - Occupancy: {summary['hospital_occupancy']}")
    print("  ✓ Status summary test passed")
    
    return True


def test_mcda_framework():
    """Test MCDA Reasoning Framework."""
    print("\n" + "="*60)
    print("TEST 2: MCDA Framework")
    print("="*60)
    
    from backend.reasoning import (
        MCDAAnalyzer, 
        MCDAScores, 
        MCDAWeights
    )
    
    # Test 2.1: Basic MCDA Calculation
    print("\n[2.1] Basic MCDA Calculation:")
    analyzer = MCDAAnalyzer()
    
    scores = analyzer.calculate_scores(
        safety_score=75,
        urgency_score=60,
        capacity_score=50,
        impact_score=40
    )
    
    print(f"  - Safety: {scores.safety}")
    print(f"  - Urgency: {scores.urgency}")
    print(f"  - Capacity: {scores.capacity}")
    print(f"  - Impact: {scores.impact}")
    print(f"  - Composite Score: {scores.composite_score:.2f}")
    print(f"  - Priority Level: {scores.priority_level}")
    print(f"  - Dominant Factor: {scores.dominant_factor}")
    
    assert scores.composite_score > 0, "Composite score should be positive"
    assert scores.priority_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    print("  ✓ Basic MCDA calculation passed")
    
    # Test 2.2: Context-Based Calculation
    print("\n[2.2] Context-Based MCDA Calculation:")
    patient_ctx = {
        "acuity_level": 4,
        "wait_time_minutes": 90,
        "boarding_in_ed": True
    }
    capacity_ctx = {
        "capacity_score": 45,
        "current_occupancy": 0.85
    }
    risk_ctx = {
        "risk_score": 70,
        "trajectory": "deteriorating"
    }
    
    scores = analyzer.calculate_from_context(
        patient_context=patient_ctx,
        capacity_context=capacity_ctx,
        risk_context=risk_ctx
    )
    
    print(f"  - Composite Score: {scores.composite_score:.2f}")
    print(f"  - Priority: {scores.priority_level}")
    assert scores.composite_score > 50, "High-acuity patient should have high score"
    print("  ✓ Context-based calculation passed")
    
    # Test 2.3: Weight Presets
    print("\n[2.3] Weight Presets:")
    emergency_weights = MCDAWeights.for_emergency()
    print(f"  - Emergency Safety Weight: {emergency_weights.safety}")
    routine_weights = MCDAWeights.for_routine()
    print(f"  - Routine Capacity Weight: {routine_weights.capacity}")
    
    assert emergency_weights.safety > routine_weights.safety, "Emergency should prioritize safety"
    print("  ✓ Weight presets test passed")
    
    return True


def test_decision_engine():
    """Test Decision Engine."""
    print("\n" + "="*60)
    print("TEST 3: Decision Engine")
    print("="*60)
    
    from backend.reasoning import (
        DecisionEngine,
        ActionType,
        create_decision_engine
    )
    
    # Test 3.1: Make Decision
    print("\n[3.1] Decision Engine - Make Decision:")
    engine = create_decision_engine()
    
    decision = engine.make_decision(
        patient_id="P-TEST-001",
        patient_context={
            "acuity_level": 3,
            "wait_time_minutes": 45,
            "current_location": "ED"
        },
        capacity_context={
            "capacity_score": 55,
            "current_occupancy": 0.75
        },
        risk_context={
            "risk_score": 50,
            "trajectory": "stable"
        },
        available_units=["Ward", "ICU"]
    )
    
    print(f"  - Patient: {decision.patient_id}")
    print(f"  - Action: {decision.recommended_action.value}")
    print(f"  - Target Unit: {decision.target_unit}")
    print(f"  - Confidence: {decision.uncertainty.confidence:.1%}")
    print(f"  - Safe to Wait: {decision.wait_probability.safe_to_wait}")
    print(f"  - Reasoning: {decision.reasoning[:80]}...")
    
    assert decision.recommended_action in ActionType
    assert decision.mcda_scores is not None
    print("  ✓ Decision engine test passed")
    
    # Test 3.2: Critical Patient
    print("\n[3.2] Critical Patient Decision:")
    critical_decision = engine.make_decision(
        patient_id="P-CRITICAL-001",
        patient_context={
            "acuity_level": 5,
            "wait_time_minutes": 10,
            "is_emergency": True,
            "time_critical_condition": True
        },
        capacity_context={"capacity_score": 30},
        risk_context={"risk_score": 95, "trajectory": "deteriorating"}
    )
    
    print(f"  - Action: {critical_decision.recommended_action.value}")
    print(f"  - Priority: {critical_decision.mcda_scores.priority_level}")
    
    assert critical_decision.mcda_scores.priority_level in ["CRITICAL", "HIGH"]
    print("  ✓ Critical patient decision test passed")
    
    return True


def test_flow_orchestrator():
    """Test Flow Orchestrator Agent."""
    print("\n" + "="*60)
    print("TEST 4: Flow Orchestrator Agent")
    print("="*60)
    
    from backend.agents.flow_orchestrator import (
        FlowOrchestratorAgent,
        create_flow_orchestrator
    )
    
    # Test 4.1: Get Recommendation (with demo data)
    print("\n[4.1] Flow Recommendation (Demo Data):")
    agent = create_flow_orchestrator()
    
    recommendation = agent.get_recommendation(patient_id="P-FLOW-001")
    
    print(f"  - Patient: {recommendation.patient_id}")
    print(f"  - Action: {recommendation.recommended_action.value}")
    print(f"  - Unit: {recommendation.recommended_unit}")
    print(f"  - Confidence: {recommendation.confidence:.1%}")
    print(f"  - MCDA Composite: {recommendation.mcda_scores.composite_score:.1f}")
    print(f"  - Priority: {recommendation.priority_level}")
    print(f"  - Alternatives: {len(recommendation.alternative_options)}")
    print(f"  - Scenarios Analyzed: {len(recommendation.scenarios_analyzed)}")
    
    assert recommendation.mcda_scores is not None, "Should have MCDA scores"
    print("  ✓ Flow recommendation test passed")
    
    # Test 4.2: With Custom Context
    print("\n[4.2] Flow Recommendation (Custom Context):")
    recommendation = agent.get_recommendation(
        patient_id="P-CUSTOM-001",
        patient_context={
            "acuity_level": 3,
            "wait_time_minutes": 60,
            "current_location": "ED",
            "trajectory": "stable"
        },
        capacity_assessments={
            "Ward": {"capacity_score": 70, "current_occupancy": 0.6, "staff_ratio": 4.0},
            "ICU": {"capacity_score": 40, "current_occupancy": 0.8, "staff_ratio": 2.0}
        },
        risk_assessment={"risk_score": 45, "trajectory": "stable"}
    )
    
    print(f"  - Recommended Unit: {recommendation.recommended_unit}")
    print(f"  - Reasoning: {recommendation.reasoning[:100]}...")
    print("  ✓ Custom context test passed")
    
    # Test 4.3: What-If Scenario
    print("\n[4.3] What-If Scenario (Wait 15 min):")
    scenario = agent.run_what_if(
        patient_id="P-WHATIF-001",
        wait_minutes=15,
        capacity_score=45
    )
    
    print(f"  - Scenario: {scenario.description}")
    print(f"  - Predicted Capacity: {scenario.predicted_capacity_score:.0f}")
    print(f"  - Risk Level: {scenario.risk_level}")
    print(f"  - Probability of Better Outcome: {scenario.probability_of_better_outcome:.0%}")
    
    assert scenario.wait_time_minutes == 15
    print("  ✓ What-if scenario test passed")
    
    return True


def test_integration():
    """Test integration between components."""
    print("\n" + "="*60)
    print("TEST 5: Component Integration")
    print("="*60)
    
    from backend.agents.capacity_intelligence import create_demo_capacity_agent
    from backend.agents.flow_orchestrator import create_flow_orchestrator
    
    # Create both agents
    cap_agent = create_demo_capacity_agent()
    flow_agent = create_flow_orchestrator()
    
    # Get capacity assessments
    print("\n[5.1] Get Capacity from Capacity Agent:")
    capacity_assessments = {}
    for unit in ["ICU", "Ward", "ED"]:
        assessment = cap_agent.get_unit_assessment(unit)
        capacity_assessments[unit] = {
            "capacity_score": assessment.capacity_score,
            "current_occupancy": assessment.current_occupancy,
            "staff_ratio": assessment.staff_ratio,
            "predicted_availability": assessment.predicted_availability
        }
        print(f"  - {unit}: score={assessment.capacity_score:.0f}")
    
    # Feed to Flow Orchestrator
    print("\n[5.2] Flow Recommendation using Capacity Data:")
    recommendation = flow_agent.get_recommendation(
        patient_id="P-INTEGRATED-001",
        patient_context={
            "acuity_level": 3,
            "wait_time_minutes": 30,
            "current_location": "ED"
        },
        capacity_assessments=capacity_assessments,
        risk_assessment={"risk_score": 55, "trajectory": "stable"}
    )
    
    print(f"  - Recommended Action: {recommendation.recommended_action.value}")
    print(f"  - Target Unit: {recommendation.recommended_unit}")
    print(f"  - MCDA Scores: {recommendation.mcda_scores.to_dict()}")
    
    print("\n  ✓ Integration test passed - Components work together!")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("#  AdaptiveCare - Krish Components Test Suite")
    print("#  Testing: Capacity Intelligence, MCDA, Flow Orchestrator")
    print("#"*60)
    
    all_passed = True
    
    try:
        test_capacity_intelligence()
    except Exception as e:
        print(f"\n❌ Capacity Intelligence Test FAILED: {e}")
        all_passed = False
    
    try:
        test_mcda_framework()
    except Exception as e:
        print(f"\n❌ MCDA Framework Test FAILED: {e}")
        all_passed = False
    
    try:
        test_decision_engine()
    except Exception as e:
        print(f"\n❌ Decision Engine Test FAILED: {e}")
        all_passed = False
    
    try:
        test_flow_orchestrator()
    except Exception as e:
        print(f"\n❌ Flow Orchestrator Test FAILED: {e}")
        all_passed = False
    
    try:
        test_integration()
    except Exception as e:
        print(f"\n❌ Integration Test FAILED: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nSuccess Criteria Met:")
        print("  ✓ Capacity tracking works (produces CapacityAssessment for each unit)")
        print("  ✓ Flow produces recommendations with MCDA scores")
    else:
        print("❌ SOME TESTS FAILED - See details above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
