import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { Decision } from '@/types/hospital';
import { getActionInfo, formatTimestamp } from '@/lib/display-utils';

interface DecisionItemProps {
  decision: Decision;
}

function DecisionItem({ decision }: DecisionItemProps) {
  const actionInfo = getActionInfo(decision.action);

  return (
    <Card className="border-border bg-card/50 p-3 animate-fade-in">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <Badge className={cn('text-xs font-bold', actionInfo.bgColor, actionInfo.color, 'border-0')}>
              {actionInfo.label}
            </Badge>
            <span className="text-sm font-medium text-foreground">
              {decision.patient_name || decision.patient_id}
            </span>
          </div>
          <p className="text-xs text-muted-foreground line-clamp-2">{decision.reasoning}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{decision.agent_name}</span>
            <span>•</span>
            <span>Confidence: {decision.confidence.toFixed(1)}%</span>
          </div>
        </div>
        <span className="shrink-0 text-xs text-muted-foreground">
          {formatTimestamp(decision.timestamp)}
        </span>
      </div>
    </Card>
  );
}

interface DecisionFeedProps {
  decisions: Decision[];
  isLoading?: boolean;
  autoScroll?: boolean;
}

export function DecisionFeed({ decisions, isLoading, autoScroll = true }: DecisionFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const safeDecisions = decisions ?? [];
  const prevLengthRef = useRef(safeDecisions.length);

  // Auto-scroll to top when new decisions arrive
  useEffect(() => {
    if (autoScroll && safeDecisions.length > prevLengthRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
    prevLengthRef.current = safeDecisions.length;
  }, [safeDecisions.length, autoScroll]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse bg-card/50 p-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-5 w-20 rounded bg-muted" />
                <div className="h-4 w-32 rounded bg-muted" />
              </div>
              <div className="h-4 w-full rounded bg-muted" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <ScrollArea className="h-full" ref={scrollRef}>
      <div className="space-y-3 pr-4">
        {safeDecisions.map((decision) => (
          <DecisionItem key={decision.decision_id} decision={decision} />
        ))}
        {safeDecisions.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            No decisions yet. Start the simulation to see AI decisions.
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
