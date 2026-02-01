import { X, Clock, AlertTriangle, Heart, Activity, Thermometer } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import type { Patient } from '@/types/hospital';
import { getRiskBgColor, formatWaitTime } from '@/lib/display-utils';

interface PatientDetailPanelProps {
  patient: Patient | null;
  onClose: () => void;
}

function getAcuityLabel(level: number): string {
  switch (level) {
    case 1: return 'Resuscitation';
    case 2: return 'Emergent';
    case 3: return 'Urgent';
    case 4: return 'Less Urgent';
    case 5: return 'Non-Urgent';
    default: return `Acuity ${level}`;
  }
}

function getAcuityColor(level: number): string {
  switch (level) {
    case 1: return 'bg-red-600';
    case 2: return 'bg-orange-500';
    case 3: return 'bg-yellow-500';
    case 4: return 'bg-green-500';
    case 5: return 'bg-blue-500';
    default: return 'bg-gray-500';
  }
}

export function PatientDetailPanel({ patient, onClose }: PatientDetailPanelProps) {
  if (!patient) return null;

  const riskScore = patient.risk_score ?? 0;
  const isCritical = patient.is_critical || riskScore >= 80;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg animate-slide-in-right border-l border-border bg-background shadow-xl">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border p-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">{patient.name}</h2>
              {isCritical && (
                <Badge variant="destructive" className="animate-pulse">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  Critical
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {patient.age}y • {patient.current_location}
            </p>
            <p className="text-sm font-medium">{patient.chief_complaint}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            {/* Patient Info Card */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Patient Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Patient ID</span>
                    <p className="font-medium">{patient.id}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status</span>
                    <p className="font-medium capitalize">{patient.status}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Acuity Level</span>
                    <Badge className={cn(getAcuityColor(patient.acuity_level), 'text-white border-0 mt-1')}>
                      {getAcuityLabel(patient.acuity_level)}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Wait Time</span>
                    <div className="flex items-center gap-1 mt-1">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{formatWaitTime(patient.wait_time_minutes)}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk Assessment */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div
                    className={cn(
                      'flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold text-white',
                      getRiskBgColor(riskScore)
                    )}
                  >
                    {riskScore}
                  </div>
                  <div className="space-y-2">
                    <p className="font-medium">
                      {riskScore >= 80 ? 'High Risk' : riskScore >= 50 ? 'Moderate Risk' : 'Low Risk'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {riskScore >= 80
                        ? 'Requires immediate attention'
                        : riskScore >= 50
                          ? 'Monitor closely'
                          : 'Standard monitoring'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Current Status */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Current Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="flex flex-col items-center p-3 rounded-lg bg-secondary/50">
                    <Heart className="h-6 w-6 text-red-500 mb-2" />
                    <span className="text-xs text-muted-foreground">Location</span>
                    <span className="font-medium text-sm">{patient.current_location}</span>
                  </div>
                  <div className="flex flex-col items-center p-3 rounded-lg bg-secondary/50">
                    <Activity className="h-6 w-6 text-blue-500 mb-2" />
                    <span className="text-xs text-muted-foreground">Risk</span>
                    <span className="font-medium text-sm">{riskScore}%</span>
                  </div>
                  <div className="flex flex-col items-center p-3 rounded-lg bg-secondary/50">
                    <Thermometer className="h-6 w-6 text-orange-500 mb-2" />
                    <span className="text-xs text-muted-foreground">Acuity</span>
                    <span className="font-medium text-sm">{patient.acuity_level}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Chief Complaint Details */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Chief Complaint</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{patient.chief_complaint}</p>
                <Separator className="my-4" />
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    This patient has been waiting for <strong>{formatWaitTime(patient.wait_time_minutes)}</strong> and
                    has a risk score of <strong>{riskScore}</strong>.
                  </p>
                  {isCritical && (
                    <div className="flex items-center gap-2 p-2 rounded bg-red-500/10 text-red-500">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="text-sm font-medium">This patient requires immediate attention</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
