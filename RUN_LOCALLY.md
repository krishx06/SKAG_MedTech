# 🚀 Running AdaptiveCare Locally

## Quick Start (2 Terminals)

### Terminal 1: Backend (Python)
```bash
cd /Users/g.jaiswal/Documents/Hackron/SKAG_MedTech
source venv/bin/activate  # Activate virtual environment
python -m backend.run
```

**Wait for**: `AdaptiveCare backend started successfully`  
**URL**: http://localhost:8000

---

### Terminal 2: Frontend (React)
```bash
cd /Users/g.jaiswal/Documents/Hackron/SKAG_MedTech/frontend
npm run dev
```

**Wait for**: `Local: http://localhost:5173`  
**URL**: http://localhost:5173

---

## Testing the New Features

### 1️⃣ Test AI Scenario Generator

1. Open browser: http://localhost:5173
2. Navigate to **Simulation Control** (left sidebar)
3. Scroll to "🤖 AI Scenario Generator" card
4. Type a prompt:
   ```
   10 ICU beds, 9 filled, ambulance with 2 critical patients
   ```
5. Click "Generate Scenario"
6. See parsed scenario appear below
7. Click "START" to run it

### 2️⃣ Test Live Event Injection

1. Start a simulation first (any scenario)
2. Wait for simulation to be running
3. Scroll to "⚡ Inject Live Event" card (appears when running)
4. Type an event:
   ```
   ambulance with critical patient arrives now
   ```
5. Click "🚑 Inject Event Now"
6. Watch dashboard for new patient + decision!

### 3️⃣ Verify Real-Time Updates

1. Start simulation
2. Navigate to **Dashboard**
3. Watch for:
   - Patients appearing in queue
   - Capacity meters updating
   - **Decisions streaming** in right panel (Live Decisions)
4. Click on a decision card to see AI reasoning

---

## Troubleshooting

### Backend won't start
```bash
# Make sure you're in the project root
cd /Users/g.jaiswal/Documents/Hackron/SKAG_MedTech

# Activate venv
source venv/bin/activate

# Check Python version (need 3.8+)
python --version

# Run backend
python -m backend.run
```

### Frontend won't start
```bash
# Install dependencies if needed
npm install

# Then run
npm run dev
```

### No decisions appearing
1. Check backend terminal - should say "backend started successfully"
2. Check browser console (F12) for WebSocket errors
3. Try stopping and restarting simulation
4. Make sure you selected a scenario and clicked START

### Prompt scenario not working
- **With Gemini API**: Set `GOOGLE_API_KEY` in `.env` file
- **Without API**: Will use rule-based parser (still works!)

---

## Environment Variables (Optional)

Create `.env` file in project root:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here  # For AI scenario parsing
```

Without API key, the system uses rule-based parsing (works fine for demos).

---

## Quick Demo Flow

1. **Start both servers** (backend + frontend)
2. **Open**: http://localhost:5173
3. **Go to**: Simulation Control
4. **Try AI Generator**: 
   - Type: "10 ICU beds, 9 full, 2 ambulances coming"
   - Click Generate
5. **Start**: Click START button
6. **Go to**: Dashboard
7. **Watch**: Decisions appear in ~10-15 seconds
8. **Inject Event**: 
   - Back to Simulation Control
   - Type: "ambulance with critical patient"
   - Click Inject
9. **Return to Dashboard**: See new patient + decision!

**Total demo time**: 2-3 minutes ⚡

---

## For Hackathon Presentation

**Before presenting**:
- ✅ Test the full flow once
- ✅ Keep both servers running
- ✅ Have browser on Dashboard page
- ✅ Prepare 2-3 prompt examples

**During demo**:
- Use "Busy Thursday" scenario (best results)
- Or use AI Generator for wow factor
- Inject event mid-demo to show adaptability

🎯 **You're all set!**
