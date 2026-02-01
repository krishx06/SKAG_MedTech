import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Bed, Users, Clock } from 'lucide-react';
import type { UnitCapacity } from '@/types/hospital';

interface CapacityCardProps {
  capacity: UnitCapacity;
  className?: string;
}

function getCapacityColor(occupancyRate: number): string {
  // occupancyRate is now 0-100
  if (occupancyRate < 50) return 'text-capacity-available';
  if (occupancyRate < 70) return 'text-capacity-moderate';
  return 'text-capacity-critical';
}

function getProgressColor(occupancyRate: number): string {
  if (occupancyRate < 50) return 'bg-capacity-available';
  if (occupancyRate < 70) return 'bg-capacity-moderate';
  return 'bg-capacity-critical';
}

function getUnitTypeColor(unitType: string): string {
  switch (unitType.toLowerCase()) {
    case 'icu':
      return 'bg-red-500/20 text-red-400';
    case 'er':
      return 'bg-orange-500/20 text-orange-400';
    case 'general':
      return 'bg-blue-500/20 text-blue-400';
    default:
      return 'bg-gray-500/20 text-gray-400';
  }
}

export function CapacityCard({ capacity, className }: CapacityCardProps) {
  const occupancyPercent = Math.round(capacity.occupancy_rate);
  const colorClass = getCapacityColor(capacity.occupancy_rate);
  const progressColor = getProgressColor(capacity.occupancy_rate);
  const occupiedBeds = capacity.total_beds - capacity.available_beds;

  return (
    <Card className={cn('bg-card border-border', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            {capacity.name}
          </CardTitle>
          <Badge className={cn('text-xs', getUnitTypeColor(capacity.unit_type))}>
            {capacity.id}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Occupancy Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Bed Occupancy</span>
            <span className={cn('font-medium', colorClass)}>{occupancyPercent}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cn('h-full transition-all', progressColor)}
              style={{ width: `${occupancyPercent}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Bed className="h-3 w-3" />
              Available Beds
            </div>
            <p className="text-xl font-bold">
              {capacity.available_beds}
              <span className="text-sm font-normal text-muted-foreground">
                /{capacity.total_beds}
              </span>
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Users className="h-3 w-3" />
              Staff Available
            </div>
            <p className="text-xl font-bold">
              {capacity.available_staff}
            </p>
          </div>
        </div>

        {/* Pending Discharges */}
        <div className="flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Pending Discharges</span>
          </div>
          <span className="text-lg font-bold text-green-500">
            {capacity.pending_discharges}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

interface CapacityOverviewProps {
  capacities: UnitCapacity[];
  isLoading?: boolean;
}

export function CapacityOverview({ capacities, isLoading }: CapacityOverviewProps) {
  // Show all units from the backend
  const mainUnits = capacities;

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse bg-card">
            <CardHeader className="pb-2">
              <div className="h-6 w-32 rounded bg-muted" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-2 w-full rounded bg-muted" />
              <div className="grid grid-cols-2 gap-4">
                <div className="h-12 rounded bg-muted" />
                <div className="h-12 rounded bg-muted" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {mainUnits.map((capacity) => (
        <CapacityCard key={capacity.id} capacity={capacity} />
      ))}
    </div>
  );
}
