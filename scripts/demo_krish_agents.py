#!/usr/bin/env python3
"""
AdaptiveCare Demo - Krish's Agents
===================================
Run this script to demonstrate:
1. Capacity Intelligence Agent - Hospital resource tracking
2. Flow Orchestrator Agent - Patient placement decisions with MCDA

Usage: python3 scripts/demo_krish_agents.py
"""

import sys
sys.path.insert(0, '/Users/krish/Desktop/SKAG_MedTech')

from datetime import datetime, timedelta

# Import Krish's agents
from backend.agents.capacity_intelligence import create_demo_capacity_agent
from backend.agents.flow_orchestrator import create_flow_orchestrator

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def print_section(text):
    print(f"\n--- {text} ---")

# =============================================================================
# EXAMPLE 1: Capacity Intelligence Agent
# =============================================================================
def demo_capacity_intelligence():
    print_header("CAPACITY INTELLIGENCE AGENT DEMO")
    
    print("""
    WHAT IT DOES:
    ┌─────────────────────────────────────────────────────────────┐
    │  Hospital Units     →    Capacity Agent    →   Assessment  │
    │  ─────────────────       ───────────────       ──────────── │
    │  • ICU (beds, staff)     Analyzes:             • Occupancy  │
    │  • Ward (beds, staff)    - Bed availability   • Score 0-100 │
    │  • ED (beds, staff)      - Staff workload     • Bottlenecks │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    # Initialize with demo data
    agent = create_demo_capacity_agent()
    
    print_section("Current Hospital Capacity")
    print(f"{'Unit':<10} {'Occupancy':<12} {'Staff Ratio':<15} {'Score':<10} {'Bottleneck'}")
    print("-" * 60)
    
    for unit in ["ICU", "Ward", "ED"]:
        assessment = agent.get_unit_assessment(unit)
        bottleneck = assessment.bottleneck_reason or "None"
        print(f"{unit:<10} {assessment.current_occupancy:>8.0%}     {assessment.staff_ratio:>6.1f} pts/nurse   {assessment.capacity_score:>5.0f}     {bottleneck}")
    
    print_section("Capacity Score Calculation (ICU Example)")
    icu = agent.get_unit_assessment("ICU")
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  CAPACITY SCORE = (Bed Score) + (Staff Score)               │
    │                                                             │
    │  Bed Score   = (1 - {icu.current_occupancy:.2f}) × 50 = {(1 - icu.current_occupancy) * 50:.1f}                    │
    │  Staff Score = min(staff_adequacy, 1.5) / 1.5 × 50          │
    │                                                             │
    │  ICU Capacity Score = {icu.capacity_score:.1f}/100                            │
    │  Interpretation: {'HIGH capacity' if icu.capacity_score > 60 else 'MEDIUM capacity' if icu.capacity_score > 40 else 'LOW capacity - bottleneck!'}                      │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    print_section("Find Best Unit for New Admission")
    best_unit = agent.find_best_unit_for_admission()
    print(f"  → Recommended unit: {best_unit}")
    print(f"  → Reason: Highest capacity score among available units")
    
    return agent


# =============================================================================
# EXAMPLE 2: Flow Orchestrator Agent with MCDA
# =============================================================================
def demo_flow_orchestrator(capacity_agent):
    print_header("FLOW ORCHESTRATOR AGENT DEMO")
    
    print("""
    WHAT IT DOES:
    ┌─────────────────────────────────────────────────────────────┐
    │  Patient + Capacity  →  MCDA Scoring  →  Flow Recommendation│
    │  ──────────────────     ────────────     ───────────────────│
    │  • Risk assessment       Criteria:        • Action: ADMIT   │
    │  • Capacity data         - Safety 35%     • Unit: ICU       │
    │  • Wait time             - Urgency 30%    • Confidence: 87% │
    │                          - Capacity 20%   • Alternatives    │
    │                          - Impact 15%                       │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    # Initialize flow agent
    flow_agent = create_flow_orchestrator()
    
    # Get capacity from capacity agent
    capacity_data = {
        unit: capacity_agent.get_unit_assessment(unit).to_dict() 
        for unit in ["ICU", "Ward", "ED"]
    }
    
    print_section("SCENARIO 1: Critical Patient (High Risk)")
    patient1 = {
        "acuity_level": 4,          # High acuity (1-5 scale)
        "wait_time_minutes": 120,    # Been waiting 2 hours
        "current_location": "ED",
        "chief_complaint": "Chest Pain",
        "age": 68,
        "trajectory": "deteriorating"
    }
    
    risk1 = {
        "risk_score": 82,
        "trajectory": "deteriorating",
        "factors": ["cardiac_risk", "age"]
    }
    
    print(f"""
    Patient Context:
    ├── Acuity Level: {patient1['acuity_level']} (HIGH)
    ├── Wait Time: {patient1['wait_time_minutes']} minutes
    ├── Location: {patient1['current_location']}
    ├── Complaint: {patient1['chief_complaint']}
    └── Trajectory: {patient1['trajectory'].upper()}
    
    Risk Assessment:
    ├── Risk Score: {risk1['risk_score']}/100
    └── Factors: {', '.join(risk1['factors'])}
    """)
    
    rec1 = flow_agent.get_recommendation(
        patient_id="P-CRITICAL-001",
        patient_context=patient1,
        capacity_assessments=capacity_data,
        risk_assessment=risk1
    )
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  MCDA SCORING BREAKDOWN                                     │
    │  ─────────────────────                                      │
    │  Safety:   {rec1.mcda_scores.safety:>6.1f}  (weight 35%) → {rec1.mcda_scores.safety * 0.35:>5.1f} contribution    │
    │  Urgency:  {rec1.mcda_scores.urgency:>6.1f}  (weight 30%) → {rec1.mcda_scores.urgency * 0.30:>5.1f} contribution    │
    │  Capacity: {rec1.mcda_scores.capacity:>6.1f}  (weight 20%) → {rec1.mcda_scores.capacity * 0.20:>5.1f} contribution    │
    │  Impact:   {rec1.mcda_scores.impact:>6.1f}  (weight 15%) → {rec1.mcda_scores.impact * 0.15:>5.1f} contribution    │
    │  ─────────────────────────────────────────────              │
    │  COMPOSITE SCORE: {rec1.mcda_scores.composite_score:>5.1f}                                  │
    │  PRIORITY LEVEL:  {rec1.priority_level:<10}                               │
    └─────────────────────────────────────────────────────────────┘
    
    ★ RECOMMENDATION:
    ├── Action: {rec1.recommended_action.value.upper()}
    ├── Unit: {rec1.recommended_unit or 'Best available'}
    ├── Confidence: {rec1.confidence:.0%}
    └── Reasoning: {rec1.reasoning}
    """)
    
    # Show alternatives
    if rec1.alternative_options:
        print("    Alternative Options:")
        for i, alt in enumerate(rec1.alternative_options[:3], 1):
            print(f"    {i}. {alt.unit} - Score: {alt.composite_viability_score:.0f}")
    
    print_section("SCENARIO 2: Routine Patient (Low Risk)")
    patient2 = {
        "acuity_level": 2,          # Lower acuity
        "wait_time_minutes": 30,
        "current_location": "ED",
        "chief_complaint": "Minor Injury",
        "age": 35,
        "trajectory": "stable"
    }
    
    risk2 = {
        "risk_score": 28,
        "trajectory": "stable"
    }
    
    print(f"""
    Patient Context:
    ├── Acuity Level: {patient2['acuity_level']} (LOW)
    ├── Wait Time: {patient2['wait_time_minutes']} minutes
    └── Trajectory: {patient2['trajectory'].upper()}
    
    Risk Assessment:
    └── Risk Score: {risk2['risk_score']}/100
    """)
    
    rec2 = flow_agent.get_recommendation(
        patient_id="P-ROUTINE-002",
        patient_context=patient2,
        capacity_assessments=capacity_data,
        risk_assessment=risk2
    )
    
    print(f"""
    ★ RECOMMENDATION:
    ├── Action: {rec2.recommended_action.value.upper()}
    ├── MCDA Score: {rec2.mcda_scores.composite_score:.1f}
    ├── Priority: {rec2.priority_level}
    └── Reasoning: {rec2.reasoning}
    """)
    
    return flow_agent


# =============================================================================
# EXAMPLE 3: What-If Scenario Analysis
# =============================================================================
def demo_what_if(flow_agent, capacity_agent):
    print_header("WHAT-IF SCENARIO ANALYSIS")
    
    print("""
    WHAT IT DOES:
    ┌─────────────────────────────────────────────────────────────┐
    │  Question: "What if we wait 30 minutes before admitting?"   │
    │                                                             │
    │  Simulator predicts:                                        │
    │  • Will capacity improve?                                   │
    │  • Will patient risk increase?                              │
    │  • Probability of better outcome if we wait                 │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    icu_score = capacity_agent.get_unit_assessment("ICU").capacity_score
    
    print_section("Comparing Wait Times")
    print(f"{'Wait Time':<15} {'Risk Level':<15} {'Probability Better':<20}")
    print("-" * 50)
    
    for wait_minutes in [0, 15, 30, 60]:
        scenario = flow_agent.run_what_if(
            patient_id="P-TEST-001",
            wait_minutes=wait_minutes,
            patient_context={"acuity_level": 3, "trajectory": "stable"},
            capacity_score=icu_score
        )
        print(f"{wait_minutes} min{'':<10} {scenario.risk_level:<15} {scenario.probability_of_better_outcome:.0%}")
    
    print(f"""
    Analysis:
    ├── Waiting longer may improve capacity availability
    ├── But patient risk may increase over time
    └── System balances these trade-offs automatically
    """)


# =============================================================================
# MAIN DEMO
# =============================================================================
if __name__ == "__main__":
    print("\n" + "🏥 " * 20)
    print("         ADAPTIVECARE - MULTI-AGENT HOSPITAL FLOW SYSTEM")
    print("                    Krish's Agent Demonstration")
    print("🏥 " * 20)
    
    # Run demos
    capacity_agent = demo_capacity_intelligence()
    flow_agent = demo_flow_orchestrator(capacity_agent)
    demo_what_if(flow_agent, capacity_agent)
    
    print_header("DEMO COMPLETE")
    print("""
    Summary of Krish's Implementation:
    
    ✅ Capacity Intelligence Agent
       - Real-time bed tracking
       - Staff workload monitoring
       - Availability prediction
       - Capacity scoring (0-100)
    
    ✅ Flow Orchestrator Agent
       - MCDA-based patient scoring
       - Placement recommendations
       - Alternative options ranking
       - What-if scenario simulation
    
    ✅ MCDA Reasoning Framework
       - 4 criteria: Safety, Urgency, Capacity, Impact
       - Configurable weights
       - Explainable priority levels
    
    Ready for integration with:
    - Risk Monitor Agent (Gayatri)
    - Escalation Decision Agent (Sneha)
    - EventBus + StateManager (Ashu)
    """)
