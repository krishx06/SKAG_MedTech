import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { Play, Pause, RotateCcw, Clock, Zap, Activity } from 'lucide-react';
import {
  useSimulationStatus,
  useStartSimulation,
  useStopSimulation,
  useResetSimulation,
} from '@/hooks/useSimulation';

const scenarios = [
  { 
    value: 'normal', 
    label: 'Normal Operations',
    description: 'Baseline hospital operations with typical patient flow (5-8 patients/hour). ICU at 67% capacity, adequate staffing. First decisions in ~15-20 seconds.'
  },
  { 
    value: 'busy_thursday', 
    label: 'Busy Thursday',
    description: 'High-volume evening shift with 12-15 patients/hour. Multiple high-acuity cases, 2-3 patients requiring escalation. First decisions in ~10-15 seconds. Best for demos!'
  },
  { 
    value: 'high_ed', 
    label: 'High ED Volume',
    description: 'Emergency department surge with 15-20 patients/hour. Extended wait times, capacity strain. Tests agent prioritization under pressure. Rapid decisions within 5-10 seconds.'
  },
  { 
    value: 'staff_shortage', 
    label: 'Staff Shortage',
    description: 'Reduced nursing staff (50% capacity). Normal patient volume but limited resources. Demonstrates resource-constrained decision making. Decisions in ~15-20 seconds.'
  },
];

const speedOptions = [
  { value: 1, label: '1x' },
  { value: 2, label: '2x' },
  { value: 5, label: '5x' },
  { value: 10, label: '10x' },
];

export default function SimulationControl() {
  const [selectedScenario, setSelectedScenario] = useState('normal');
  const [speed, setSpeed] = useState(1);
  const [promptText, setPromptText] = useState('');
  const [eventPrompt, setEventPrompt] = useState('');
  const [generatedScenario, setGeneratedScenario] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);

  const { data: status, isLoading } = useSimulationStatus();
  const startMutation = useStartSimulation();
  const stopMutation = useStopSimulation();
  const resetMutation = useResetSimulation();

  // Backend returns 'running' not 'is_running'
  const isRunning = status?.running ?? false;
  const totalArrivals = status?.total_arrivals ?? 0;
  const activePatients = status?.active_patients ?? 0;
  const uptime = status?.uptime_seconds ?? 0;

  const handleStart = () => {
    startMutation.mutate({ scenario: selectedScenario, speed });
  };

  const handleStop = () => {
    stopMutation.mutate();
  };

  const handleReset = () => {
    resetMutation.mutate();
  };

  const handleGenerateScenario = async () => {
    if (!promptText.trim()) return;
    
    setIsGenerating(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/simulation/generate-scenario?prompt=${encodeURIComponent(promptText)}`
      , {
        method: 'POST'
      });
      const data = await response.json();
      setGeneratedScenario(data.scenario);
    } catch (error) {
      console.error('Failed to generate scenario:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInjectEvent = async () => {
    if (!eventPrompt.trim()) return;
    
    setIsInjecting(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/simulation/inject-event?prompt=${encodeURIComponent(eventPrompt)}`,
        { method: 'POST' }
      );
      const data = await response.json();
      alert(`Event injected: ${data.message}`);
      setEventPrompt('');
    } catch (error) {
      console.error('Failed to inject event:', error);
      alert('Failed to inject event. Make sure simulation is running.');
    } finally {
      setIsInjecting(false);
    }
  };

  const formatSimulationTime = (timeStr?: string) => {
    if (!timeStr) return '--:--:--';
    try {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return timeStr;
    }
  };

  return (
    <div className="h-full overflow-auto p-6 scrollbar-thin">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Play className="h-6 w-6 text-primary" />
          Simulation Control
        </h1>
        <p className="text-muted-foreground">Control and configure hospital simulation scenarios</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Control Panel */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Simulation Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Control Buttons */}
            <div className="flex gap-3">
              {isRunning ? (
                <Button
                  size="lg"
                  variant="destructive"
                  className="flex-1"
                  onClick={handleStop}
                  disabled={stopMutation.isPending}
                >
                  <Pause className="mr-2 h-5 w-5" />
                  Stop
                </Button>
              ) : (
                <Button
                  size="lg"
                  className="flex-1 bg-status-online hover:bg-status-online/90"
                  onClick={handleStart}
                  disabled={startMutation.isPending}
                >
                  <Play className="mr-2 h-5 w-5" />
                  Start
                </Button>
              )}
              <Button
                size="lg"
                variant="outline"
                onClick={handleReset}
                disabled={resetMutation.isPending || isRunning}
              >
                <RotateCcw className="mr-2 h-5 w-5" />
                Reset
              </Button>
            </div>

            {/* Active Indicator */}
            <div className="flex items-center justify-center gap-3 rounded-lg bg-secondary/50 p-4">
              <div
                className={cn(
                  'h-4 w-4 rounded-full',
                  isRunning
                    ? 'bg-status-online animate-pulse-live'
                    : 'bg-status-offline'
                )}
              />
              <span className="text-lg font-medium">
                {isRunning ? 'Simulation Running' : 'Simulation Paused'}
              </span>
            </div>

            {/* Scenario Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Scenario</label>
              <Select
                value={selectedScenario}
                onValueChange={setSelectedScenario}
                disabled={isRunning}
              >
                <SelectTrigger className="bg-secondary">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {scenarios.map((scenario) => (
                    <SelectItem key={scenario.value} value={scenario.value}>
                      <div>
                        <div className="font-medium">{scenario.label}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">{scenario.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Scenario Description */}
              <div className="rounded-lg bg-secondary/50 p-3 border border-border">
                <p className="text-sm text-muted-foreground">
                  {scenarios.find(s => s.value === selectedScenario)?.description}
                </p>
              </div>
            </div>

            {/* Speed Control */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Simulation Speed</label>
                <Badge variant="secondary">{speed}x</Badge>
              </div>
              <Slider
                value={[speed]}
                onValueChange={([v]) => setSpeed(v)}
                min={1}
                max={10}
                step={1}
                disabled={isRunning}
                className="py-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1x</span>
                <span>5x</span>
                <span>10x</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Status Display */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Simulation Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
                ))}
              </div>
            ) : (
              <>
                {/* Current Time - show uptime */}
                <div className="rounded-lg bg-secondary/50 p-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    Simulation Uptime
                  </div>
                  <p className="mt-1 text-3xl font-bold font-mono">
                    {uptime > 0
                      ? `${Math.floor(uptime / 60)}:${String(Math.floor(uptime % 60)).padStart(2, '0')}`
                      : '--:--'}
                  </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-secondary/50 p-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Activity className="h-4 w-4" />
                      Total Arrivals
                    </div>
                    <p className="mt-1 text-2xl font-bold">{totalArrivals}</p>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Zap className="h-4 w-4" />
                      Active Patients
                    </div>
                    <p className="mt-1 text-2xl font-bold">{activePatients}</p>
                  </div>
                </div>

                {/* Active Scenario */}
                <div className="rounded-lg border border-border p-4">
                  <div className="text-sm text-muted-foreground">Active Scenario</div>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant="outline" className="text-sm">
                      {scenarios.find((s) => s.value === (status?.scenario ?? selectedScenario))
                        ?.label ?? 'Normal Operations'}
                    </Badge>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Prompt-Based Scenario Generation */}
      <Card className="mt-6 border-border bg-card">
        <CardHeader>
          <CardTitle className="text-lg">🤖 AI Scenario Generator</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Describe your scenario in natural language</label>
            <Textarea
              placeholder="Example: 10 ICU beds, 9 filled, ambulance with 2 critical patients arriving..."
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="min-h-[80px] bg-secondary"
              disabled={isRunning}
            />
          </div>
          <Button 
            onClick={handleGenerateScenario} 
            disabled={isGenerating || !promptText.trim() || isRunning}
            className="w-full"
          >
            {isGenerating ? 'Generating...' : 'Generate Scenario'}
          </Button>
          
          {generatedScenario && (
            <div className="rounded-lg border border-border bg-secondary/50 p-4">
              <p className="text-sm font-medium mb-2">Generated Scenario:</p>
              <div className="space-y-1 text-sm">
                <p>• ICU: {generatedScenario.icu_beds}</p>
                <p>• ED: {generatedScenario.ed_beds}</p>
                <p>• Initial Patients: {generatedScenario.initial_patients}</p>
                {generatedScenario.incoming_ambulances > 0 && (
                  <p>• Incoming Ambulances: {generatedScenario.incoming_ambulances}</p>
                )}
                {generatedScenario.staff_shortage && (
                  <p className="text-yellow-500">⚠️ Staff Shortage</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dynamic Event Injection */}
      {isRunning && (
        <Card className="mt-6 border-border bg-card border-primary/50">
          <CardHeader>
            <CardTitle className="text-lg">⚡ Inject Live Event</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Add event to running simulation</label>
              <Textarea
                placeholder="Example: ambulance with critical patient arrives now..."
                value={eventPrompt}
                onChange={(e) => setEventPrompt(e.target.value)}
                className="min-h-[60px] bg-secondary"
              />
            </div>
            <Button 
              onClick={handleInjectEvent}
              disabled={isInjecting || !eventPrompt.trim()}
              className="w-full bg-status-online hover:bg-status-online/90"
            >
              {isInjecting ? 'Injecting...' : '🚑 Inject Event Now'}
            </Button>
            <p className="text-xs text-muted-foreground">
              Try: "ambulance with 2 critical patients" or "staff shortage in ICU"
            </p>
          </CardContent>
        </Card>
      )}

      {/* Quick Info */}
      <Card className="mt-6 border-border bg-card">
        <CardContent className="p-4">
          <div className="flex items-start gap-4 text-sm text-muted-foreground">
            <div className="flex-1">
              <p className="font-medium text-foreground">How it works</p>
              <p className="mt-1">
                The simulation generates realistic patient arrivals, vital sign changes, and
                triggers AI agents to make decisions. Start the simulation to see the hospital
                system respond in real-time.
              </p>
              <p className="mt-2 font-medium text-foreground">AI-Powered Scenarios</p>
              <p className="mt-1">
                Use natural language to describe any hospital scenario. Our AI will parse it and configure the simulation automatically.
              </p>
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">Available Scenarios</p>
              <ul className="mt-1 space-y-1">
                <li>• Normal: Baseline operations with typical patient flow</li>
                <li>• High ED Volume: Surge in emergency admissions</li>
                <li>• Staff Shortage: Reduced nursing staff availability</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
