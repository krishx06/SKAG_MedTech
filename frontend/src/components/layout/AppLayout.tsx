import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Activity,
  Play,
  Bot,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useWebSocket, type ConnectionStatus } from '@/hooks/useWebSocket';
import { usePatientUpdates } from '@/hooks/usePatients';
import { useDecisionUpdates } from '@/hooks/useDecisions';
import { useCapacityUpdates } from '@/hooks/useCapacity';
import type { WebSocketEvent, Decision, RiskAssessment, UnitCapacity } from '@/types/hospital';
import { toast } from '@/hooks/use-toast';

interface AppLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/capacity', label: 'Capacity Intelligence', icon: Activity },
  { path: '/simulation', label: 'Simulation Control', icon: Play },
  { path: '/agents', label: 'Agent Status', icon: Bot },
];



export function AppLayout({ children }: AppLayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const { invalidatePatients, updatePatientRisk } = usePatientUpdates();
  const { addDecision } = useDecisionUpdates();
  const { invalidateCapacity } = useCapacityUpdates();

  const handleWebSocketMessage = (event: WebSocketEvent) => {
    switch (event.type) {
      case 'patient.arrival':
        invalidatePatients();
        break;
      case 'vitals.update':
        invalidatePatients();
        break;
      case 'risk_monitor.risk_calculated':
        const riskData = event.data as RiskAssessment;
        updatePatientRisk(riskData.patient_id, riskData);
        if (riskData.trajectory === 'critical') {
          toast({
            title: 'Critical Risk Alert',
            description: `Patient ${riskData.patient_id} has entered critical status`,
            variant: 'destructive',
          });
        }
        break;
      case 'capacity_intelligence.capacity_updated':
        invalidateCapacity();
        break;
      case 'escalation_decision.decision_made':
        const decision = event.data as Decision;
        addDecision(decision);
        break;
      default:
        break;
    }
  };

  const { status } = useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo/Header */}
        <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Activity className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-sidebar-foreground">AdaptiveCare</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="h-8 w-8 text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>


      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto scrollbar-thin">{children}</main>
    </div>
  );
}
