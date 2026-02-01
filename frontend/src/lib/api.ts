/**
 * API Client for AdaptiveCare Backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Generic fetch wrapper with error handling
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

// API methods matching backend endpoints
export const api = {
    // Patients
    getPatients: () => fetchApi<any[]>('/api/patients'),
    getPatient: (id: string) => fetchApi<any>(`/api/patients/${id}`),
    getPatientVitals: (id: string) => fetchApi<any>(`/api/patients/${id}/vitals`),
    getPatientRisk: (id: string) => fetchApi<any>(`/api/patients/${id}/risk`),
    getPatientDecisions: (id: string) => fetchApi<any[]>(`/api/patients/${id}/decisions`),

    // Capacity
    getCapacity: () => fetchApi<any>('/api/capacity'),
    getUnitCapacity: (unitId: string) => fetchApi<any>(`/api/capacity/${unitId}`),
    getHospitalState: () => fetchApi<any>('/api/capacity'),

    // Decisions
    getDecisions: (limit?: number) => fetchApi<any>(`/api/decisions${limit ? `?limit=${limit}` : ''}`),
    getLatestDecisions: (limit?: number) => fetchApi<any>(`/api/decisions${limit ? `?limit=${limit}` : ''}`),
    getPendingReview: () => fetchApi<any[]>('/api/decisions/pending-review'),
    acknowledgeDecision: (id: string, executedBy?: string) =>
        fetchApi<any>(`/api/decisions/${id}/acknowledge`, {
            method: 'POST',
            body: JSON.stringify({ executed_by: executedBy || 'user' }),
        }),

    // Evaluation
    evaluatePatient: (patientId: string) =>
        fetchApi<any>('/api/evaluate', {
            method: 'POST',
            body: JSON.stringify({ patient_id: patientId }),
        }),
    batchEvaluate: (patientIds?: string[]) =>
        fetchApi<any>('/api/evaluate/batch', {
            method: 'POST',
            body: JSON.stringify({ patient_ids: patientIds }),
        }),

    // Simulation Control
    getSimulationStatus: () => fetchApi<any>('/api/simulation/status'),
    startSimulation: (scenario?: string, speed?: number) =>
        fetchApi<any>('/api/simulation/start', {
            method: 'POST',
            body: JSON.stringify({
                scenario: scenario || 'busy_thursday',
                duration: 120,
                arrival_rate: speed ? speed * 12.5 : 12.5
            }),
        }),
    stopSimulation: () =>
        fetchApi<any>('/api/simulation/stop', {
            method: 'POST',
        }),
    resetSimulation: () =>
        fetchApi<any>('/api/simulation/reset', {
            method: 'POST',
        }),

    // Simulation Events
    simulateRiskSpike: (patientId: string, newRiskScore: number, riskFactors?: Record<string, any>) =>
        fetchApi<any>('/api/simulate/risk-spike', {
            method: 'POST',
            body: JSON.stringify({
                patient_id: patientId,
                new_risk_score: newRiskScore,
                risk_factors: riskFactors,
            }),
        }),
    simulateCapacityChange: (unitId: string, bedsChange: number) =>
        fetchApi<any>(`/api/simulate/capacity-change?unit_id=${unitId}&beds_change=${bedsChange}`, {
            method: 'POST',
        }),

    // Stats
    getStats: () => fetchApi<any>('/api/stats'),
    getDecisionStats: () => fetchApi<any>('/api/stats/decisions'),

    // Agents
    getAgentStatus: () => fetchApi<any>('/api/agents/status'),
    getAgentsStatus: () => fetchApi<any[]>('/api/agents/status'),

    // Health
    healthCheck: () => fetchApi<any>('/health'),
    getHealth: () => fetchApi<any>('/health'),
};

export default api;

