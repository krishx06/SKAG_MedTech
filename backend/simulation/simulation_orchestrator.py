"""
Simulation Orchestrator - Integrates simulation with Risk Monitor Agent

This module bridges the gap between the hospital simulation (Phase 1) and
the Risk Monitor Agent (Phase 2), enabling real-time risk assessment during
simulation execution.
"""
import asyncio
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import threading
from queue import Queue
import logging

from backend.simulation.hospital_sim import HospitalSimulator
from backend.simulation.scenarios.busy_thursday import BusyThursdayScenario
from backend.simulation.event_types import (
    PatientArrivalSimEvent,
    VitalsUpdateSimEvent,
    DeteriorationSimEvent
)
from backend.models.patient import Patient

# Import Risk Monitor directly to avoid dependency conflicts
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "risk_monitor"))
from agent import RiskMonitorAgent
sys.path.pop(0)

logger = logging.getLogger(__name__)


class SimulationOrchestrator:
    """
    Orchestrates hospital simulation and real-time risk monitoring.
    
    Responsibilities:
    - Run SimPy simulation in background thread
    - Feed patient events to Risk Monitor Agent
    - Maintain event queue for API/WebSocket broadcasting
    - Provide simulation control (start/stop)
    """
    
    def __init__(self, event_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize orchestrator.
        
        Args:
            event_callback: Optional callback function for broadcasting events
                           Called with event dict for WebSocket/API forwarding
        """
        self.simulation: Optional[HospitalSimulation] = None
        self.risk_monitor = RiskMonitorAgent()
        self.event_callback = event_callback
        self.event_queue: Queue = Queue()
        
        # Simulation state
        self.is_running = False
        self.simulation_thread: Optional[threading.Thread] = None
        self.patients: Dict[str, Patient] = {}
        
        # Statistics
        self.total_arrivals = 0
        self.total_assessments = 0
        self.start_time: Optional[datetime] = None
        
        logger.info("Simulation Orchestrator initialized")
    
    def start_simulation(
        self,
        scenario: str = "busy_thursday",
        duration: int = 120,
        arrival_rate: float = 12.5
    ) -> Dict[str, Any]:
        """
        Start hospital simulation with specified parameters.
        
        Args:
            scenario: Scenario name (currently supports "busy_thursday")
            duration: Simulation duration in minutes
            arrival_rate: Patient arrival rate (patients/hour)
        
        Returns:
            Status dict with simulation ID and parameters
        """
        if self.is_running:
            return {
                "status": "error",
                "message": "Simulation already running"
            }
        
        try:
            # Create simulator with event callback
            self.simulation = HospitalSimulator(
                event_callback=self._on_simulation_event,
                time_scale=1.0
            )
            
            # Setup scenario
            if scenario == "busy_thursday":
                BusyThursdayScenario.setup(self.simulation)
            else:
                raise ValueError(f"Unknown scenario: {scenario}")
            
            # Start simulation in background thread
            self.is_running = True
            self.start_time = datetime.now()
            self.simulation_thread = threading.Thread(
                target=self._run_simulation,
                args=(duration,),
                daemon=True
            )
            self.simulation_thread.start()
            
            logger.info(f"Started simulation: {scenario}, duration={duration}min")
            
            return {
                "status": "started",
                "scenario": scenario,
                "duration": duration,
                "arrival_rate": arrival_rate,
                "start_time": self.start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start simulation: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def stop_simulation(self) -> Dict[str, Any]:
        """
        Stop running simulation gracefully.
        
        Returns:
            Status dict with final statistics
        """
        if not self.is_running:
            return {
                "status": "error",
                "message": "No simulation running"
            }
        
        self.is_running = False
        
        # Wait for simulation thread to finish (with timeout)
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        logger.info(f"Stopped simulation. Duration: {duration:.1f}s, Arrivals: {self.total_arrivals}")
        
        return {
            "status": "stopped",
            "duration_seconds": duration,
            "total_arrivals": self.total_arrivals,
            "total_assessments": self.total_assessments,
            "patients": len(self.patients)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "total_arrivals": self.total_arrivals,
            "total_assessments": self.total_assessments,
            "active_patients": len(self.patients),
            "high_risk_patients": len(self.risk_monitor.get_high_risk_patients()),
            "deteriorating_patients": len(self.risk_monitor.get_deteriorating_patients())
        }
    
    def get_patients(self) -> List[Dict[str, Any]]:
        """Get all active patients with their latest risk assessments."""
        patients_with_risk = []
        
        for patient in self.patients.values():
            history = self.risk_monitor.get_patient_history(patient.id)
            latest_risk = history.latest_assessment if history else None
            
            patient_dict = {
                "id": patient.id,
                "age": patient.age,
                "gender": patient.gender,
                "acuity_level": patient.acuity_level,
                "chief_complaint": patient.chief_complaint,
                "comorbidities": patient.comorbidities,
                "vitals": {
                    "heart_rate": patient.vitals.heart_rate,
                    "systolic_bp": patient.vitals.systolic_bp,
                    "diastolic_bp": patient.vitals.diastolic_bp,
                    "spo2": patient.vitals.spo2,
                    "respiratory_rate": patient.vitals.respiratory_rate,
                    "temperature": patient.vitals.temperature
                },
                "admission_time": patient.admission_time.isoformat() if patient.admission_time else None
            }
            
            if latest_risk:
                patient_dict["risk"] = {
                    "score": latest_risk.risk_score,
                    "level": latest_risk.risk_level.value,
                    "trend": latest_risk.trend.value,
                    "needs_escalation": latest_risk.needs_escalation,
                    "critical_vitals": latest_risk.critical_vitals,
                    "monitoring_frequency": latest_risk.recommended_monitoring_frequency
                }
            
            patients_with_risk.append(patient_dict)
        
        return patients_with_risk
    
    def get_patient_risk(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get risk assessment for specific patient."""
        history = self.risk_monitor.get_patient_history(patient_id)
        if not history or not history.latest_assessment:
            return None
        
        assessment = history.latest_assessment
        return {
            "patient_id": patient_id,
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level.value,
            "trend": assessment.trend.value,
            "needs_escalation": assessment.needs_escalation,
            "escalation_reason": assessment.escalation_reason,
            "critical_vitals": assessment.critical_vitals,
            "vital_trends": {
                name: {
                    "current": trend.current_value,
                    "previous": trend.previous_value,
                    "change_rate": trend.change_rate,
                    "direction": trend.direction.value,
                    "critical": trend.critical
                }
                for name, trend in assessment.vital_trends.items()
            },
            "risk_breakdown": {
                "vitals": assessment.risk_breakdown.vital_signs_score,
                "deterioration": assessment.risk_breakdown.deterioration_score,
                "comorbidities": assessment.risk_breakdown.comorbidity_score,
                "acuity": assessment.risk_breakdown.acuity_score
            },
            "monitoring_frequency": assessment.recommended_monitoring_frequency,
            "timestamp": assessment.timestamp.isoformat()
        }
    
    def _run_simulation(self, duration: float):
        """Run simulation (called in background thread)."""
        try:
            # Run simulation
            self.simulation.run(until=duration)
            
            # Process all pending events from simulation
            logger.info(f"Simulation complete. Processing {len(self.simulation.pending_events)} events...")
            for event in self.simulation.pending_events:
                self._on_simulation_event(event)
            
            logger.info(f"Event processing complete. Total arrivals: {self.total_arrivals}, Assessments: {self.total_assessments}")
        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
        finally:
            self.is_running = False
    
    def _on_simulation_event(self, event):
        """Callback for simulation events - processes events from simulator."""
        try:
            # Handle different event types
            if isinstance(event, PatientArrivalSimEvent):
                self._handle_patient_arrival(event)
            elif isinstance(event, VitalsUpdateSimEvent):
                self._handle_vitals_update(event)
            elif isinstance(event, DeteriorationSimEvent):
                self._handle_deterioration(event)
        except Exception as e:
            logger.error(f"Error handling event: {e}", exc_info=True)
    
    def _handle_patient_arrival(self, event: PatientArrivalSimEvent):
        """Handle patient arrival event."""
        # Get patient from simulation
        sim_patients = self.simulation.get_current_patients()
        patient = next((p for p in sim_patients if p.id == event.patient_id), None)
        
        if not patient:
            logger.warning(f"Patient {event.patient_id} not found in simulation")
            return
        
        self.patients[patient.id] = patient
        self.total_arrivals += 1
        
        # Assess with Risk Monitor
        assessment = self.risk_monitor.assess_patient(patient)
        self.total_assessments += 1
        
        # Broadcast event
        event_data = {
            "type": "patient_arrival",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "patient_id": patient.id,
                "age": patient.age,
                "acuity": patient.acuity_level,
                "complaint": patient.chief_complaint,
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value
            }
        }
        self._broadcast_event(event_data)
        
        logger.debug(f"Patient arrival: {patient.id}, risk={assessment.risk_score:.1f}")
    
    def _handle_vitals_update(self, event: VitalsUpdateSimEvent):
        """Handle vitals update event."""
        # Get updated patient from simulation
        sim_patients = self.simulation.get_current_patients()
        patient = next((p for p in sim_patients if p.id == event.patient_id), None)
        
        if not patient:
            return
        
        # Update patient in registry
        self.patients[patient.id] = patient
        
        # Re-assess with Risk Monitor
        assessment = self.risk_monitor.assess_patient(patient)
        self.total_assessments += 1
        
        # Broadcast event
        event_data = {
            "type": "vitals_update",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "patient_id": patient.id,
                "vitals": {
                    "heart_rate": patient.vitals.heart_rate,
                    "spo2": patient.vitals.spo2,
                    "systolic_bp": patient.vitals.systolic_bp,
                    "respiratory_rate": patient.vitals.respiratory_rate,
                    "temperature": patient.vitals.temperature
                },
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value,
                "trend": assessment.trend.value
            }
        }
        self._broadcast_event(event_data)
        
        # If significant change, broadcast risk assessment separately
        if assessment.needs_escalation or assessment.risk_score_delta > 10:
            risk_event = {
                "type": "risk_assessment",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "patient_id": patient.id,
                    "risk_score": assessment.risk_score,
                    "risk_level": assessment.risk_level.value,
                    "trend": assessment.trend.value,
                    "needs_escalation": assessment.needs_escalation,
                    "escalation_reason": assessment.escalation_reason,
                    "critical_vitals": assessment.critical_vitals
                }
            }
            self._broadcast_event(risk_event)
    
    def _handle_deterioration(self, event: DeteriorationSimEvent):
        """Handle deterioration event."""
        # Get patient from simulation
        sim_patients = self.simulation.get_current_patients()
        patient = next((p for p in sim_patients if p.id == event.patient_id), None)
        
        if not patient:
            return
        
        # Assess with Risk Monitor
        assessment = self.risk_monitor.assess_patient(patient)
        
        # Broadcast deterioration event
        event_data = {
            "type": "deterioration",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "patient_id": patient.id,
                "pattern": event.deterioration_type.value,
                "risk_score": assessment.risk_score,
                "needs_escalation": assessment.needs_escalation,
                "escalation_reason": assessment.escalation_reason,
                "critical_vitals": assessment.critical_vitals
            }
        }
        self._broadcast_event(event_data)
        
        logger.warning(f"Deterioration: {patient.id}, pattern={event.deterioration_type.value}, risk={assessment.risk_score:.1f}")
    
    def _broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast event to callback and queue."""
        # Add to queue for API access
        self.event_queue.put(event_data)
        
        # Call callback if provided (for WebSocket broadcasting)
        if self.event_callback:
            try:
                self.event_callback(event_data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")


# Global orchestrator instance (singleton)
_orchestrator: Optional[SimulationOrchestrator] = None


def get_orchestrator() -> SimulationOrchestrator:
    """Get or create the global simulation orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SimulationOrchestrator()
    return _orchestrator


def set_event_callback(callback: Callable[[Dict[str, Any]], None]):
    """Set the event callback function (typically WebSocket broadcaster)."""
    orchestrator = get_orchestrator()
    orchestrator.event_callback = callback
