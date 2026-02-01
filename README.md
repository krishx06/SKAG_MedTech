# 🏥 AdaptiveCare

A **Multi-Agent Hospital Patient Flow Intelligence System** - featuring AI-powered patient prioritization, real-time capacity management, and explainable decision-making with LLM reasoning.

## 🎯 Overview

AdaptiveCare is an intelligent hospital management system that uses a multi-agent architecture to optimize patient flow, predict resource needs, and provide explainable escalation decisions. The system continuously monitors patient risk, hospital capacity, and makes data-driven recommendations with full transparency.

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│                  │     │                  │     │                  │     │                  │
│  Risk Monitor    │────▶│    Capacity      │────▶│     Flow         │────▶│   Escalation     │
│     Agent        │     │  Intelligence    │     │  Orchestrator    │     │    Decision      │
│                  │     │                  │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                        │                        │
        └────────────────────────┴────────────────────────┴────────────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │      Event Bus          │
                              │  (Real-time Updates)    │
                              └─────────────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │   Frontend Dashboard    │
                              │  (React + WebSocket)    │
                              └─────────────────────────┘
```

### Key Features

- **🔍 Risk Monitoring**: Continuous patient vital sign analysis with deterioration prediction
- **📊 Capacity Intelligence**: Real-time bed/staff tracking with availability forecasting
- **🔄 Flow Orchestration**: Optimal patient placement using MCDA (Multi-Criteria Decision Analysis)
- **⚡ Escalation Decisions**: AI-powered prioritization with LLM-generated explanations
- **📈 Real-time Dashboard**: Live visualization of hospital state and decisions
- **🎮 Hospital Simulation**: Realistic scenarios for testing and demonstration

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key (for LLM reasoning)

### 2. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/sneha31-debug/SKAG_MedTech.git
cd SKAG_MedTech

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Get key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Start Backend

```bash
cd backend
python run.py
```
Backend runs at: `http://localhost:8000`

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

## 📁 Project Structure

```
SKAG_MedTech/
├── backend/
│   ├── agents/                    # Multi-Agent System
│   │   ├── base_agent.py          # Abstract base class for all agents
│   │   ├── risk_monitor/          # Patient risk assessment
│   │   ├── capacity_intelligence/ # Resource tracking
│   │   ├── flow_orchestrator/     # Patient placement optimization
│   │   └── escalation_decision/   # Final decision with LLM reasoning
│   │
│   ├── api/                       # REST & WebSocket API
│   │   ├── main.py                # FastAPI app
│   │   └── routes/                # API endpoints
│   │
│   ├── core/                      # Core Infrastructure
│   │   ├── orchestrator.py        # Agent coordination
│   │   ├── event_bus.py           # Pub/sub messaging
│   │   ├── state_manager.py       # Shared state management
│   │   └── config.py              # Configuration
│   │
│   ├── reasoning/                 # Decision Intelligence
│   │   ├── decision_engine.py     # Core decision logic
│   │   ├── mcda.py                # Multi-Criteria Decision Analysis
│   │   ├── llm_reasoning.py       # Gemini API integration
│   │   └── uncertainty.py         # Confidence quantification
│   │
│   ├── simulation/                # Hospital Simulation
│   │   └── simulation_orchestrator.py
│   │
│   └── models/                    # Data Models
│       ├── patient.py             # Patient, VitalSigns, RiskFactors
│       ├── hospital.py            # Beds, Staff, Units
│       ├── decision.py            # Decision outputs
│       └── events.py              # Event types for pub/sub
│
├── frontend/                      # React Dashboard
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx      # Main overview
│       │   ├── AgentStatus.tsx    # Agent monitoring
│       │   ├── CapacityIntelligence.tsx
│       │   └── SimulationControl.tsx
│       │
│       └── components/
│           └── dashboard/
│               ├── PatientQueue.tsx
│               ├── CapacityCard.tsx
│               └── DecisionFeed.tsx
│
├── scripts/                       # Testing & Demo
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   └── demo_krish_agents.py
│
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🤖 Agent Architecture

### Base Agent Interface

```python
class BaseAgent(ABC):
    def __init__(self, agent_type, event_bus, state_manager):
        self.agent_type = agent_type
        self.event_bus = event_bus
        self.state_manager = state_manager
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input and produce output."""
        pass
    
    async def emit_event(self, event: AgentEvent) -> None:
        """Publish event to the event bus."""
        pass
```

### Agent Pipeline

| Agent | Purpose | Output |
|-------|---------|--------|
| **Risk Monitor** | Assess patient risk from vitals | RiskScore (0-100) + Trajectory |
| **Capacity Intelligence** | Track beds, staff, resources | CapacityAssessment per unit |
| **Flow Orchestrator** | Recommend optimal placements | FlowRecommendation + MCDA scores |
| **Escalation Decision** | Final decision with explanation | ActionType + LLM reasoning |

### Decision Flow

```
Patient Vitals Update
        │
        ▼
┌───────────────────┐
│   Risk Monitor    │ → risk_score: 78, trajectory: deteriorating
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Capacity       │ → ICU: 90% full, Ward: 65% full
│  Intelligence     │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│     Flow          │ → MCDA Analysis:
│  Orchestrator     │   - Safety: 0.85
└───────────────────┘   - Urgency: 0.78
        │               - Capacity: 0.45
        ▼
┌───────────────────┐
│   Escalation      │ → Action: ESCALATE to ICU
│    Decision       │   Reasoning: "Patient shows signs of
└───────────────────┘    deterioration requiring ICU-level care..."
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_api_key          # For LLM reasoning

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite:///./adaptivecare.db

# MCDA Weights (decision making)
RISK_WEIGHT=0.4
CAPACITY_WEIGHT=0.3
WAIT_TIME_WEIGHT=0.2
RESOURCE_WEIGHT=0.1

# Thresholds
ESCALATE_THRESHOLD=0.75
HIGH_RISK_THRESHOLD=70.0
CRITICAL_RISK_THRESHOLD=85.0

# LLM Configuration
LLM_MODEL=gemini-1.5-flash
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.3
```

### Adjust MCDA Weights

The Multi-Criteria Decision Analysis weights can be tuned in `.env`:

```bash
RISK_WEIGHT=0.4       # Patient clinical risk importance
CAPACITY_WEIGHT=0.3   # Resource availability importance
WAIT_TIME_WEIGHT=0.2  # Queue waiting time importance
RESOURCE_WEIGHT=0.1   # Staff/equipment importance
```

## 🧪 Testing

```bash
# Run all tests
cd scripts
python test_phase1.py   # Core infrastructure
python test_phase2.py   # Agent implementations
python test_phase3.py   # Full pipeline integration

# Run specific agent demo
python demo_krish_agents.py
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## 📡 API Endpoints

### Patients
- `GET /api/patients` - List all patients
- `GET /api/patients/{id}` - Get patient details
- `POST /api/patients` - Add new patient

### Decisions
- `GET /api/decisions` - Decision history
- `GET /api/decisions/{patient_id}` - Decisions for patient

### Agents
- `GET /api/agents/status` - All agent statuses
- `POST /api/agents/run` - Trigger agent pipeline

### Simulation
- `POST /api/simulation/start` - Start simulation
- `POST /api/simulation/stop` - Stop simulation
- `GET /api/simulation/status` - Current state

### WebSocket
- `ws://localhost:8000/ws` - Real-time decision stream

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **Pydantic** - Data validation and settings management
- **Google Gemini** - LLM for explainable reasoning
- **SimPy** - Discrete event simulation
- **SQLAlchemy** - Database ORM

### Frontend
- **React 18** + TypeScript
- **Vite** - Build tooling
- **TailwindCSS** - Styling
- **Radix UI** - Accessible components
- **Recharts** - Data visualization
- **React Query** - Server state management

## 👥 Team

| Member | Role |
|--------|------|
| **Ashu** | Orchestration, Event Bus, API layer, Integration |
| **Gayatri** | Risk Monitor Agent, Simulation System |
| **Krish** | Capacity Intelligence, Flow Orchestrator, MCDA , Frontend Dashboard|
| **Sneha** | Escalation Decision Agent |

## 📚 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Multi-Criteria Decision Analysis](https://en.wikipedia.org/wiki/Multiple-criteria_decision_analysis)

## 📄 License

MIT License - Feel free to use and modify!
