import { useState } from 'react';
import { PatientQueue } from '@/components/dashboard/PatientQueue';
import { CapacityOverview } from '@/components/dashboard/CapacityCard';
import { DecisionFeed } from '@/components/dashboard/DecisionFeed';
import { PatientDetailPanel } from '@/components/dashboard/PatientDetailPanel';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Users, Zap } from 'lucide-react';
import { usePatients } from '@/hooks/usePatients';
import { useCapacity } from '@/hooks/useCapacity';
import { useDecisions } from '@/hooks/useDecisions';
import type { Patient, CapacityResponse, Decision } from '@/types/hospital';

// Type for decisions API response
interface DecisionsResponse {
  decisions: Decision[];
  total: number;
}

export default function Dashboard() {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const { data: patients, isLoading: patientsLoading } = usePatients();
  const { data: capacityData, isLoading: capacityLoading } = useCapacity();
  const { data: decisionsData, isLoading: decisionsLoading } = useDecisions();

  // Extract units from capacity response 
  const capacities = (capacityData as CapacityResponse)?.units ?? [];
  // Extract decisions array from response (backend returns {decisions: [], total: 0})
  const decisions = Array.isArray(decisionsData) ? decisionsData : ((decisionsData as DecisionsResponse)?.decisions ?? []);

  const handlePatientClick = (patient: Patient) => {
    setSelectedPatient(patient);
  };

  const handleCloseDetail = () => {
    setSelectedPatient(null);
  };

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Hospital Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time patient flow monitoring and AI decision insights
        </p>
      </div>

      <div className="grid h-[calc(100vh-12rem)] gap-6 lg:grid-cols-12">
        {/* Patient Queue - Left */}
        <div className="lg:col-span-4">
          <Card className="h-full border-border bg-card">
            <CardHeader className="border-b border-border pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="h-5 w-5 text-primary" />
                Patient Queue
                {patients && (
                  <span className="ml-auto text-sm font-normal text-muted-foreground">
                    {patients.length} patients
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(100%-5rem)] p-4">
              <PatientQueue
                patients={patients ?? []}
                selectedPatientId={selectedPatient?.id}
                onPatientClick={handlePatientClick}
                isLoading={patientsLoading}
              />
            </CardContent>
          </Card>
        </div>

        {/* Center - Capacity Overview + More */}
        <div className="space-y-6 lg:col-span-5">
          {/* Capacity Cards */}
          <div>
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <Activity className="h-5 w-5 text-primary" />
              Capacity Overview
            </h2>
            <CapacityOverview capacities={capacities ?? []} isLoading={capacityLoading} />
          </div>
        </div>

        {/* Decision Feed - Right */}
        <div className="lg:col-span-3">
          <Card className="h-full border-border bg-card">
            <CardHeader className="border-b border-border pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="h-5 w-5 text-primary" />
                Live Decisions
                <span className="ml-auto flex h-2 w-2 rounded-full bg-status-online animate-pulse-live" />
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(100%-5rem)] p-4">
              <DecisionFeed decisions={decisions ?? []} isLoading={decisionsLoading} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Patient Detail Slide-out */}
      {selectedPatient && (
        <PatientDetailPanel patient={selectedPatient} onClose={handleCloseDetail} />
      )}
    </div>
  );
}
