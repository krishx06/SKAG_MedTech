// AdaptiveCare Hospital System Types
// Matches the FastAPI backend data models

export type Gender = 'male' | 'female' | 'other';
export type LocationType = 'ED' | 'ICU' | 'Ward' | 'ED_Obs' | 'OR';
export type Trajectory = 'improving' | 'stable' | 'deteriorating' | 'critical';
export type ActionType = 'escalate' | 'observe' | 'delay' | 'transfer' | 'admit';

export interface VitalSigns {
  heart_rate: number;
  blood_pressure_systolic: number;
  blood_pressure_diastolic: number;
  oxygen_saturation: number;
  respiratory_rate: number;
  temperature: number;
  glasgow_coma_scale: number;
  timestamp: string;
}

export interface LabResult {
  test_name: string;
  value: number;
  unit: string;
  reference_range: string;
  is_abnormal: boolean;
  timestamp: string;
}

export interface Patient {
  id: string;
  patient_id?: string;
  name: string;
  age: number;
  gender?: Gender;
  status: string;
  acuity_level: number;
  risk_score: number;
  wait_time_minutes: number;
  chief_complaint: string;
  arrival_time?: string;
  current_location: string;
  vitals?: VitalSigns[];
  labs?: LabResult[];
  medical_history?: string[];
  is_critical: boolean;
}

export interface RiskAssessment {
  patient_id: string;
  risk_score: number; // 0-100
  trajectory: Trajectory;
  confidence: number; // 0-1
  contributing_factors: string[];
  timestamp?: string;
}

export interface UnitCapacity {
  id: string;
  name: string;
  unit_type: string;
  total_beds: number;
  available_beds: number;
  occupancy_rate: number; // 0-100 percentage
  pending_discharges: number;
  available_staff: number;
  average_staff_load: number;
}

export interface CapacityResponse {
  timestamp: string;
  total_beds: number;
  total_available: number;
  overall_occupancy_rate: number;
  predicted_discharges_1h: number;
  predicted_admissions_1h: number;
  units: UnitCapacity[];
  by_type: Record<string, number>;
}

export interface Decision {
  decision_id: string;
  patient_id: string;
  patient_name?: string;
  agent_name: string;
  action: ActionType;
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export interface MCDAScores {
  safety_score: number;
  urgency_score: number;
  capacity_score: number;
  impact_score: number;
  weighted_total: number;
}

export interface AgentStatus {
  agent_name: string;
  is_active: boolean;
  is_registered: boolean;
  last_decision_time?: string;
  decision_count: number;
}

export interface SimulationStatus {
  is_running: boolean;
  current_time: string;
  speed: number;
  scenario: string;
  event_count: number;
}

export interface HospitalState {
  patients: Patient[];
  capacity: UnitCapacity[];
  decisions: Decision[];
}

// WebSocket event types
export type WebSocketEventType =
  | 'patient.arrival'
  | 'vitals.update'
  | 'risk_monitor.risk_calculated'
  | 'capacity_intelligence.capacity_updated'
  | 'escalation_decision.decision_made'
  | 'simulation.tick';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: unknown;
}

// Patient with computed risk data for display
export interface PatientWithRisk extends Patient {
  risk_assessment?: RiskAssessment;
}

// API response types
export interface SystemInfo {
  name: string;
  version: string;
  status: string;
  agents: string[];
}

export interface HealthCheck {
  status: string;
  database: string;
  agents: Record<string, boolean>;
}
