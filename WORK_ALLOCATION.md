# AdaptiveCare System - Work Allocation

Multi-Agent Hospital Patient Flow Intelligence System

---

## Team Work Division

### Allocation Strategy

Each person owns a vertical slice (agent + related components), with Ashu owning the horizontal integration layer.

| Person | Primary Ownership | Secondary |
|--------|------------------|-----------|
| Ashu | Orchestration, Event Bus, API layer, Integration | Base Agent, State Manager |
| Gayatri | Risk Monitor Agent + Simulation System | Data generation |
| Krish | Capacity Intelligence + Flow Orchestrator Agents | MCDA reasoning |
| Sneha | Escalation Decision Agent + Frontend Dashboard | LLM reasoning integration |

### Rationale

1. **Ashu**: Owns the glue - orchestration, APIs, event communication. Builds the foundation that everyone else depends on.

2. **Gayatri**: Risk Monitor is the first agent in the pipeline. Simulation feeds all agents. She creates the data reality.

3. **Krish**: Capacity and Flow are tightly coupled (Flow needs Capacity data). Owns resource optimization logic and MCDA.

4. **Sneha**: Escalation is the final decision agent and needs strong UX to show reasoning. Connects backend intelligence to user interface.

Each person works in distinct folders to minimize merge conflicts. Shared models are defined by Ashu first, then imported by others.

---

## Ashu

### Responsibilities
- System orchestration and agent coordination
- API layer and WebSocket infrastructure
- Event-driven architecture (Event Bus)
- Shared state management
- Base agent abstraction
- Database setup and repositories
- Integration testing framework

### Folders Owned
```
backend/core/*
backend/api/*
backend/models/*
backend/db/*
backend/agents/base_agent.py
backend/utils/*
scripts/*
```

### Implementation Plan

**Phase 1: Foundation (Hours 0-4)**
1. `backend/models/patient.py` - Patient data model (everyone imports this)
2. `backend/models/hospital.py` - Bed, Staff, Resource models
3. `backend/models/decision.py` - Decision output structure
4. `backend/models/events.py` - Event types for pub/sub
5. `backend/agents/base_agent.py` - Abstract base class:
   ```python
   class BaseAgent(ABC):
       @abstractmethod
       async def observe(self, context: dict) -> dict
       @abstractmethod
       async def decide(self, observations: dict) -> Decision
   ```

**Phase 2: Core Systems (Hours 5-10)**
6. `backend/core/event_bus.py` - Pub/sub for agent communication
7. `backend/core/state_manager.py` - Shared state (Redis-backed)
8. `backend/core/orchestrator.py` - Main orchestration logic
9. `backend/db/connection.py` - PostgreSQL connection pool
10. `backend/db/repositories/patient_repo.py` - Patient CRUD

**Phase 3: API Layer (Hours 11-16)**
11. `backend/api/main.py` - FastAPI app setup
12. `backend/api/routes/patients.py` - Patient endpoints
13. `backend/api/routes/decisions.py` - Decision history/logs
14. `backend/api/routes/simulation.py` - Simulation control
15. `backend/api/routes/agents.py` - Agent status/metrics
16. `backend/api/websocket.py` - Real-time decision stream

**Phase 4: Integration (Hours 17-22)**
17. `backend/run.py` - Server startup script
18. `scripts/setup_db.py` - Database initialization
19. Integration tests for full agent pipeline

### Integration Points
- Provides: Base models, event bus, state manager, database access
- Consumes: All agent implementations
- Coordination: Defines interfaces first. Everyone codes to those contracts.

---

## Gayatri - Risk Monitor Agent + Simulation

### Responsibilities
- Risk Monitor Agent (patient risk assessment)
- Hospital simulation engine
- Synthetic data generation
- Demo scenario creation
- Real-time patient vital streaming

### Folders Owned
```
backend/agents/risk_monitor/*
backend/simulation/*
```

### Implementation Plan

**Phase 1: Simulation Foundation (Hours 0-6)**
1. `backend/simulation/event_types.py` - Define simulation events:
   - PatientArrival, VitalsUpdate, LabResult, BedChange, StaffShift

2. `backend/simulation/data_generator.py` - Synthetic data:
   - Realistic patient profiles
   - Vital sign streams (heart rate, BP, O2, GCS)
   - Lab results with realistic delays
   - Deterioration patterns

3. `backend/simulation/hospital_sim.py` - Discrete event simulator:
   - SimPy-based event engine
   - Time progression and event emission
   - Scenario playback

4. `backend/simulation/scenarios/busy_thursday.py` - Demo scenario:
   - 15 ED patients, 2 deteriorating
   - ICU at 90% capacity
   - Incoming ambulance

**Phase 2: Risk Monitor Agent (Hours 7-14)**
5. `backend/agents/risk_monitor/models.py` - RiskScore, VitalSigns, RiskTrajectory
6. `backend/agents/risk_monitor/calculators.py` - Dynamic risk scoring, trend tracking
7. `backend/agents/risk_monitor/agent.py` - BaseAgent implementation

**Phase 3: Integration (Hours 15-20)**
8. Connect simulation to Event Bus
9. Test Risk Monitor with simulated patients
10. Create API endpoint for simulation control

### Data Contract
```python
class RiskAssessment:
    patient_id: str
    risk_score: float  # 0-100
    trajectory: RiskTrajectory  # improving/stable/deteriorating
    confidence: float
    contributing_factors: List[str]
```

---

## Krish - Capacity Intelligence + Flow Orchestrator + MCDA

### Responsibilities
- Capacity Intelligence Agent (resource tracking)
- Flow Orchestrator Agent (patient placement optimization)
- Multi-Criteria Decision Analysis (MCDA) reasoning
- Scenario simulation (what-if analysis)

### Folders Owned
```
backend/agents/capacity_intelligence/*
backend/agents/flow_orchestrator/*
backend/reasoning/mcda.py
backend/reasoning/decision_engine.py
```

### Implementation Plan

**Phase 1: Capacity Intelligence (Hours 0-6)**
1. `backend/agents/capacity_intelligence/models.py` - BedStatus, StaffWorkload, UnitCapacity
2. `backend/agents/capacity_intelligence/trackers.py` - Real-time bed/staff tracking, availability prediction
3. `backend/agents/capacity_intelligence/agent.py` - BaseAgent implementation

**Phase 2: MCDA Reasoning (Hours 7-12)**
4. `backend/reasoning/mcda.py`:
   - Weighting system: Safety, Urgency, Capacity, Impact scores
   - Scoring algorithms and trade-off analysis

5. `backend/reasoning/decision_engine.py`:
   - Core decision logic
   - Uncertainty quantification
   - Safe-to-wait probability calculations

**Phase 3: Flow Orchestrator (Hours 13-20)**
6. `backend/agents/flow_orchestrator/models.py` - FlowDecision, PlacementOption, ScenarioOutcome
7. `backend/agents/flow_orchestrator/scenarios.py` - What-if scenario simulator
8. `backend/agents/flow_orchestrator/agent.py` - BaseAgent implementation using MCDA

### Data Contracts
```python
class CapacityAssessment:
    unit: str  # ICU, Ward, ED
    current_occupancy: float
    staff_ratio: float
    capacity_score: float  # 0-100
    predicted_availability: Optional[datetime]

class FlowRecommendation:
    patient_id: str
    recommended_action: ActionType
    alternative_options: List[PlacementOption]
    confidence: float
    mcda_scores: MCDAScores
```

---

## Sneha - Escalation Decision Agent + Frontend

### Responsibilities
- Escalation Decision Agent (final decision maker)
- LLM-based explanation generation
- Complete React frontend
- Real-time dashboard
- Scenario simulator UI

### Folders Owned
```
backend/agents/escalation_decision/*
backend/reasoning/llm_reasoning.py
frontend/*
```

### Implementation Plan

**Phase 1: Escalation Agent (Hours 0-7)**
1. `backend/agents/escalation_decision/models.py` - EscalationDecision, ActionType enum
2. `backend/agents/escalation_decision/explainer.py` - Human-readable justifications
3. `backend/reasoning/llm_reasoning.py` - Claude API integration, prompt engineering
4. `backend/agents/escalation_decision/agent.py` - BaseAgent implementation

**Phase 2: Frontend Foundation (Hours 8-14)**
5. Setup React + TypeScript + Vite
6. `frontend/src/services/api.ts` - API client
7. `frontend/src/services/websocket.ts` - WebSocket for real-time updates
8. `frontend/src/store/store.ts` - Redux store
9. `frontend/src/types/*` - TypeScript types matching backend

**Phase 3: Core Components (Hours 15-21)**
10. `PatientQueue.tsx` - List with risk scores, color-coded urgency
11. `CapacityView.tsx` - Bed occupancy, staff workload visualization
12. `DecisionFeed.tsx` - Real-time decision stream with reasoning
13. `ScenarioSimulator.tsx` - Simulation control UI
14. `ReasoningExplainer.tsx` - MCDA scores and decision factors
15. `MetricsPanel.tsx` - Key metrics and live charts

**Phase 4: Polish (Hours 22-23)**
16. Responsive design, error handling, loading states

### Data Contract
```python
class EscalationDecision:
    patient_id: str
    action: ActionType  # Escalate, Observe, Delay, Reprioritize
    reasoning: str  # LLM-generated
    mcda_breakdown: MCDAScores
    confidence: float
    alternatives: List[AlternativeAction]
    timestamp: datetime
```

---

## Agent Interfaces and Contracts

### Core Agent Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from models.decision import Decision

class BaseAgent(ABC):
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state = state_manager
    
    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant data from current hospital state."""
        pass
    
    @abstractmethod
    async def decide(self, observations: Dict[str, Any]) -> Decision:
        """Make a decision based on observations."""
        pass
    
    async def execute(self, context: Dict[str, Any]) -> Decision:
        observations = await self.observe(context)
        decision = await self.decide(observations)
        await self.event_bus.publish(f"{self.__class__.__name__}.decision", decision)
        return decision
```

---

## Shared Data Models

### Patient Model
```python
class VitalSigns(BaseModel):
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    oxygen_saturation: float
    respiratory_rate: int
    temperature: float
    glasgow_coma_scale: int
    timestamp: datetime

class Patient(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    chief_complaint: str
    arrival_time: datetime
    current_location: str  # ED, ICU, Ward
    vitals: List[VitalSigns]
    labs: List[LabResult]
    medical_history: List[str]
    current_medications: List[str]
```

### Decision Model
```python
class ActionType(str, Enum):
    ESCALATE = "escalate"
    OBSERVE = "observe"
    DELAY = "delay"
    REPRIORITIZE = "reprioritize"

class Decision(BaseModel):
    decision_id: str
    patient_id: str
    agent_name: str
    action: ActionType
    confidence: float  # 0-1
    reasoning: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

---

## Agent Communication Flow

```
Simulation (Gayatri)
    | VitalsUpdate event
    v
Event Bus (Ashu)
    |
    v
Risk Monitor (Gayatri) --> RiskAssessment --> State Manager
    
Capacity Intelligence (Krish) --> CapacityAssessment --> State Manager

Flow Orchestrator (Krish)
    reads: RiskAssessment + CapacityAssessment
    outputs: FlowRecommendation --> State Manager

Escalation Decision (Sneha)
    reads: RiskAssessment + CapacityAssessment + FlowRecommendation
    outputs: EscalationDecision --> Event Bus --> WebSocket --> Frontend
```

---

## Event Bus Message Format

```python
class Event(BaseModel):
    event_type: str
    timestamp: datetime
    source: str  # agent name or "simulation"
    patient_id: Optional[str]
    payload: Dict[str, Any]

# Event types:
# simulation.vitals_update
# risk_monitor.risk_calculated
# capacity_intelligence.capacity_updated
# flow_orchestrator.recommendation_ready
# escalation_decision.decision_made
```

---

## Initial Handoff Sequence

**Minutes 0-10 (Ashu)**
- Create repo structure
- Define all models in backend/models/
- Implement BaseAgent
- Create event_bus.py and state_manager.py (in-memory versions first)
- Commit and push

**Minutes 10-15 (Everyone)**
- Pull Ashu's commit
- Create agent folder structure
- Implement basic agent skeleton (empty observe/decide)
- Commit

**Minutes 15-30 (Parallel)**
- Gayatri: Start simulation data generation
- Krish: Start MCDA framework
- Sneha: Start frontend setup + Escalation agent structure
- Ashu: Start API routes

---

## Success Criteria

| Person | Done When |
|--------|-----------|
| Ashu | System boots, agents can communicate, API responds |
| Gayatri | Simulation generates patients, Risk agent produces scores |
| Krish | Capacity tracking works, Flow produces recommendations |
| Sneha | Frontend shows live data, Escalation makes final decisions |

---

## Integration Checklist

- [ ] All agents implement BaseAgent interface
- [ ] All agents publish decisions to Event Bus
- [ ] Frontend receives WebSocket updates
- [ ] Simulation triggers full agent pipeline
- [ ] Demo scenario runs end-to-end
- [ ] Decisions include explanations
- [ ] UI shows real-time updates

---

## File Ownership Quick Reference

| File/Folder | Owner |
|-------------|-------|
| backend/core/* | Ashu |
| backend/api/* | Ashu |
| backend/models/* | Ashu |
| backend/db/* | Ashu |
| backend/agents/base_agent.py | Ashu |
| backend/agents/risk_monitor/* | Gayatri |
| backend/simulation/* | Gayatri |
| backend/agents/capacity_intelligence/* | Krish |
| backend/agents/flow_orchestrator/* | Krish |
| backend/reasoning/mcda.py | Krish |
| backend/reasoning/decision_engine.py | Krish |
| backend/agents/escalation_decision/* | Sneha |
| backend/reasoning/llm_reasoning.py | Sneha |
| frontend/* | Sneha |
| scripts/* | Ashu |
| docs/* | Everyone (respective sections) |