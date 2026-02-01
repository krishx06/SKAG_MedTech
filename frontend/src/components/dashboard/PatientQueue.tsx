import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TrendingUp, TrendingDown, Minus, Clock, AlertTriangle } from 'lucide-react';
import type { Patient } from '@/types/hospital';
import {
  getRiskBgColor,
  formatWaitTime,
} from '@/lib/display-utils';

interface PatientCardProps {
  patient: Patient;
  onClick?: () => void;
  isSelected?: boolean;
}

function getRiskColor(score: number): string {
  if (score >= 80) return 'bg-red-500';
  if (score >= 60) return 'bg-orange-500';
  if (score >= 40) return 'bg-yellow-500';
  return 'bg-green-500';
}

function getAcuityColor(level: number): string {
  switch (level) {
    case 1: return 'bg-red-500 text-white';
    case 2: return 'bg-orange-500 text-white';
    case 3: return 'bg-yellow-500 text-black';
    case 4: return 'bg-green-500 text-white';
    default: return 'bg-gray-500 text-white';
  }
}

export function PatientCard({ patient, onClick, isSelected }: PatientCardProps) {
  const riskScore = patient.risk_score ?? 0;
  const isCritical = patient.is_critical || riskScore >= 80;

  return (
    <Card
      className={cn(
        'cursor-pointer border-border bg-card p-4 transition-all hover:bg-accent',
        isSelected && 'ring-2 ring-primary',
        isCritical && 'border-red-500 border-2'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Patient Info */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground">{patient.name}</h3>
            <span className="text-sm text-muted-foreground">{patient.age}y</span>
            {isCritical && <AlertTriangle className="h-4 w-4 text-red-500" />}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={getAcuityColor(patient.acuity_level)}>
              Acuity {patient.acuity_level}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {patient.current_location}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground line-clamp-1">
            {patient.chief_complaint}
          </p>
        </div>

        {/* Risk Score */}
        <div className="flex flex-col items-end gap-2">
          <div
            className={cn(
              'flex h-12 w-12 items-center justify-center rounded-full text-sm font-bold text-white',
              getRiskColor(riskScore)
            )}
          >
            {Math.round(riskScore)}
          </div>
          <span className="text-xs text-muted-foreground">Risk</span>
        </div>
      </div>

      {/* Wait Time */}
      <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" />
        <span>Wait: {formatWaitTime(patient.wait_time_minutes)}</span>
        <span className="ml-auto text-xs">Status: {patient.status}</span>
      </div>
    </Card>
  );
}

interface PatientQueueProps {
  patients: Patient[];
  selectedPatientId?: string | null;
  onPatientClick: (patient: Patient) => void;
  isLoading?: boolean;
}

export function PatientQueue({
  patients,
  selectedPatientId,
  onPatientClick,
  isLoading,
}: PatientQueueProps) {
  // Sort by risk score (highest first)
  const sortedPatients = [...patients].sort((a, b) => {
    return (b.risk_score ?? 0) - (a.risk_score ?? 0);
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <Card key={i} className="animate-pulse bg-card p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-5 w-32 rounded bg-muted" />
                <div className="h-4 w-24 rounded bg-muted" />
              </div>
              <div className="h-10 w-10 rounded-full bg-muted" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-3 pr-4">
        {sortedPatients.map((patient) => (
          <PatientCard
            key={patient.id}
            patient={patient}
            isSelected={patient.id === selectedPatientId}
            onClick={() => onPatientClick(patient)}
          />
        ))}
        {sortedPatients.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            No patients in queue
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
