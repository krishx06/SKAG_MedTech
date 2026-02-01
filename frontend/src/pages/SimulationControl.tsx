import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
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
  { value: 'normal', label: 'Normal Operations' },
  { value: 'busy_thursday', label: 'Busy Thursday' },
  { value: 'high_ed', label: 'High ED Volume' },
  { value: 'staff_shortage', label: 'Staff Shortage' },
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
                      {scenario.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
