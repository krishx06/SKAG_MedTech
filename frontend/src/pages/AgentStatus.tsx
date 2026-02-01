import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '../lib/utils';
import { Bot, Activity, Eye, ArrowRightLeft, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { useAgentsStatus } from '@/hooks/useAgents';
import { formatDateTime } from '../lib/display-utils';

interface AgentInfo {
  name: string;
  displayName: string;
  description: string;
  icon: typeof Bot;
  color: string;
}

const agentInfoMap: Record<string, AgentInfo> = {
  RiskMonitor: {
    name: 'RiskMonitor',
    displayName: 'Risk Monitor',
    description: 'Monitors patient risk levels and detects deterioration patterns',
    icon: AlertTriangle,
    color: 'text-risk-high',
  },
  CapacityIntelligence: {
    name: 'CapacityIntelligence',
    displayName: 'Capacity Intelligence',
    description: 'Tracks bed availability and staff workload across units',
    icon: Activity,
    color: 'text-chart-1',
  },
  FlowOrchestrator: {
    name: 'FlowOrchestrator',
    displayName: 'Flow Orchestrator',
    description: 'Optimizes patient flow and bed assignments',
    icon: ArrowRightLeft,
    color: 'text-chart-4',
  },
  EscalationDecision: {
    name: 'EscalationDecision',
    displayName: 'Escalation Decision',
    description: 'Makes AI-powered decisions for patient escalation',
    icon: Eye,
    color: 'text-chart-2',
  },
};

function AgentCard({
  agentName,
  isActive,
  isRegistered,
  lastDecisionTime,
  decisionCount,
}: {
  agentName: string;
  isActive: boolean;
  isRegistered: boolean;
  lastDecisionTime?: string;
  decisionCount: number;
}) {
  const info = agentInfoMap[agentName] ?? {
    name: agentName,
    displayName: agentName,
    description: 'AI Agent',
    icon: Bot,
    color: 'text-muted-foreground',
  };

  const Icon = info.icon;

  return (
    <Card className={cn('border-border bg-card transition-all', isActive && 'ring-1 ring-primary')}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-lg bg-secondary',
                info.color
              )}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base">{info.displayName}</CardTitle>
              <p className="text-xs text-muted-foreground">{info.description}</p>
            </div>
          </div>
          <div
            className={cn(
              'h-3 w-3 rounded-full',
              isActive ? 'bg-status-online animate-pulse-live' : 'bg-status-offline'
            )}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Badges */}
        <div className="flex gap-2">
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              isActive
                ? 'border-status-online text-status-online'
                : 'border-status-offline text-status-offline'
            )}
          >
            {isActive ? (
              <>
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Active
              </>
            ) : (
              <>
                <XCircle className="mr-1 h-3 w-3" />
                Inactive
              </>
            )}
          </Badge>
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              isRegistered
                ? 'border-primary text-primary'
                : 'border-muted-foreground text-muted-foreground'
            )}
          >
            {isRegistered ? 'Registered' : 'Not Registered'}
          </Badge>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 rounded-lg bg-secondary/50 p-3">
          <div>
            <p className="text-xs text-muted-foreground">Decisions Made</p>
            <p className="text-xl font-bold">{decisionCount}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Last Decision</p>
            <p className="text-sm font-medium">
              {lastDecisionTime ? formatDateTime(lastDecisionTime) : 'Never'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AgentStatus() {
  const { data: agents, isLoading, error } = useAgentsStatus();

  const activeCount = agents?.filter((a) => a.is_active).length ?? 0;
  const totalDecisions = agents?.reduce((sum, a) => sum + a.decision_count, 0) ?? 0;

  return (
    <div className="h-full overflow-auto p-6 scrollbar-thin">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Bot className="h-6 w-6 text-primary" />
          Agent Status
        </h1>
        <p className="text-muted-foreground">Monitor all AI agents in the hospital system</p>
      </div>

      {/* Summary Stats */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Agents</p>
            <p className="text-3xl font-bold">{agents?.length ?? 4}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Active Agents</p>
            <p className="text-3xl font-bold text-status-online">{activeCount}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Decisions</p>
            <p className="text-3xl font-bold">{totalDecisions}</p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Cards Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse border-border bg-card">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-muted" />
                  <div className="space-y-2">
                    <div className="h-5 w-32 rounded bg-muted" />
                    <div className="h-3 w-48 rounded bg-muted" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-20 rounded-lg bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-6 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-destructive" />
            <p className="mt-2 text-destructive">
              Failed to load agent status. Make sure the backend is running.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {agents?.map((agent) => (
            <AgentCard
              key={agent.agent_name}
              agentName={agent.agent_name}
              isActive={agent.is_active}
              isRegistered={agent.is_registered}
              lastDecisionTime={agent.last_decision_time}
              decisionCount={agent.decision_count}
            />
          )) ?? (
              // Fallback static cards when no data
              <>
                {Object.values(agentInfoMap).map((info) => (
                  <AgentCard
                    key={info.name}
                    agentName={info.name}
                    isActive={false}
                    isRegistered={false}
                    decisionCount={0}
                  />
                ))}
              </>
            )}
        </div>
      )}
    </div>
  );
}
