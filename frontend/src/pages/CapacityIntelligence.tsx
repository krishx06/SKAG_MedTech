import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Activity, Bed, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import { useCapacity } from '@/hooks/useCapacity';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import type { UnitCapacity, CapacityResponse } from '@/types/hospital';

function getCapacityColorClass(occupancyPercent: number): string {
  if (occupancyPercent < 50) return 'bg-capacity-available';
  if (occupancyPercent < 70) return 'bg-capacity-moderate';
  return 'bg-capacity-critical';
}

function CapacityHeatmap({ capacities }: { capacities: UnitCapacity[] }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {capacities.map((capacity) => {
        const occupancyPercent = capacity.occupancy_rate;
        const isCritical = occupancyPercent >= 90;

        return (
          <Card
            key={capacity.id}
            className={cn(
              'relative overflow-hidden border-border transition-all hover:scale-105',
              isCritical && 'ring-2 ring-red-500'
            )}
          >
            <div
              className={cn(
                'absolute inset-0 opacity-20',
                getCapacityColorClass(occupancyPercent)
              )}
            />
            <CardContent className="relative p-4 text-center">
              <Badge
                variant="outline"
                className="mb-2 text-xs font-semibold"
              >
                {capacity.name}
              </Badge>
              <p className="text-3xl font-bold">{Math.round(occupancyPercent)}%</p>
              <p className="text-xs text-muted-foreground">Occupancy</p>
              <p className="mt-2 text-sm">
                {capacity.available_beds}/{capacity.total_beds} beds available
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

const timelineChartConfig: ChartConfig = {
  ED: { label: 'ED', color: 'hsl(var(--chart-1))' },
  ICU: { label: 'ICU', color: 'hsl(var(--chart-2))' },
  Ward: { label: 'Ward', color: 'hsl(var(--chart-3))' },
};

function PredictedAvailabilityChart() {
  // Generate mock predicted data for the next 24 hours
  const now = new Date();
  const data = Array.from({ length: 24 }, (_, i) => {
    const hour = new Date(now.getTime() + i * 60 * 60 * 1000);
    return {
      time: hour.toLocaleTimeString('en-US', { hour: '2-digit', hour12: false }),
      ED: Math.max(0, 10 - Math.floor(Math.random() * 5 + i * 0.2)),
      ICU: Math.max(0, 5 - Math.floor(Math.random() * 2 + i * 0.1)),
      Ward: Math.max(0, 20 - Math.floor(Math.random() * 8 + i * 0.3)),
    };
  });

  return (
    <ChartContainer config={timelineChartConfig} className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10 }}
            tickLine={false}
            className="text-muted-foreground"
          />
          <YAxis tick={{ fontSize: 10 }} tickLine={false} className="text-muted-foreground" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey="ED"
            stackId="1"
            stroke="var(--color-ED)"
            fill="var(--color-ED)"
            fillOpacity={0.4}
          />
          <Area
            type="monotone"
            dataKey="ICU"
            stackId="1"
            stroke="var(--color-ICU)"
            fill="var(--color-ICU)"
            fillOpacity={0.4}
          />
          <Area
            type="monotone"
            dataKey="Ward"
            stackId="1"
            stroke="var(--color-Ward)"
            fill="var(--color-Ward)"
            fillOpacity={0.4}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

function UnitBreakdownTable({ capacities }: { capacities: UnitCapacity[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full">
        <thead className="bg-secondary/50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Unit</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Beds</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Occupancy</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Staff</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Workload</th>
          </tr>
        </thead>
        <tbody>
          {capacities.map((cap) => {
            const occupiedBeds = cap.total_beds - cap.available_beds;
            const workloadPercent = Math.min(100, (cap.average_staff_load ?? 0) * 20);
            return (
              <tr key={cap.id} className="border-t border-border hover:bg-secondary/30">
                <td className="px-4 py-3">
                  <Badge variant="outline" className="font-medium">
                    {cap.name}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Bed className="h-4 w-4 text-muted-foreground" />
                    <span>{occupiedBeds}/{cap.total_beds}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-secondary">
                      <div
                        className={cn('h-full', getCapacityColorClass(cap.occupancy_rate))}
                        style={{ width: `${cap.occupancy_rate}%` }}
                      />
                    </div>
                    <span className="text-sm">{Math.round(cap.occupancy_rate)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span>{cap.available_staff ?? 0}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-secondary">
                      <div
                        className={cn(
                          'h-full',
                          workloadPercent > 80
                            ? 'bg-capacity-critical'
                            : workloadPercent > 60
                              ? 'bg-capacity-moderate'
                              : 'bg-capacity-available'
                        )}
                        style={{ width: `${workloadPercent}%` }}
                      />
                    </div>
                    <span className="text-sm">{(cap.average_staff_load ?? 0).toFixed(1)}</span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function CapacityIntelligence() {
  const { data: capacityData, isLoading } = useCapacity();

  // Extract units from capacity response
  const capacities = (capacityData as CapacityResponse)?.units ?? [];
  const criticalUnits = capacities.filter((c) => c.occupancy_rate >= 80);

  return (
    <div className="h-full overflow-auto p-6 scrollbar-thin">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Activity className="h-6 w-6 text-primary" />
          Capacity Intelligence
        </h1>
        <p className="text-muted-foreground">Hospital-wide capacity analysis and predictions</p>
      </div>

      {/* Critical Alerts */}
      {criticalUnits.length > 0 && (
        <Card className="mb-6 border-red-500 bg-red-500/10">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="font-medium text-red-500">
              {criticalUnits.length} unit(s) at critical capacity:{' '}
              {criticalUnits.map((u) => u.name).join(', ')}
            </span>
          </CardContent>
        </Card>
      )}

      <div className="space-y-6">
        {/* Capacity Heatmap */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Capacity Heatmap</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
                ))}
              </div>
            ) : capacities.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                No capacity data available
              </div>
            ) : (
              <CapacityHeatmap capacities={capacities} />
            )}
          </CardContent>
        </Card>

        {/* Predicted Availability */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5 text-primary" />
              Predicted Bed Availability (Next 24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <PredictedAvailabilityChart />
            <div className="mt-4 flex justify-center gap-6">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-[hsl(var(--chart-1))]" />
                <span className="text-sm">ED</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-[hsl(var(--chart-2))]" />
                <span className="text-sm">ICU</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-[hsl(var(--chart-3))]" />
                <span className="text-sm">Ward</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Unit Breakdown Table */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Unit Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-48 animate-pulse rounded-lg bg-muted" />
            ) : capacities.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                No capacity data available
              </div>
            ) : (
              <UnitBreakdownTable capacities={capacities} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
