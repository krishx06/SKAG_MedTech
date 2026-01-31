"""
SimPy-based hospital simulation engine.
Simulates patient arrivals and vital sign monitoring.
"""
import simpy
import asyncio
from typing import Optional, Callable, List
from datetime import datetime, timedelta
from backend.simulation.data_generator import DataGenerator
from backend.simulation.event_types import (
    PatientArrivalSimEvent,
    VitalsUpdateSimEvent,
    DeteriorationSimEvent,
    DeteriorationPattern,
    ArrivalMode,
    SeverityLevel
)
from backend.models.patient import Patient


class HospitalSimulator:
    """
    Discrete event simulator for hospital patient flow.
    Uses SimPy to orchestrate realistic patient arrivals and clinical events.
    """
    
    def __init__(
        self,
        event_callback: Optional[Callable] = None,
        time_scale: float = 1.0
    ):
        """
        Initialize simulator.
        
        Args:
            event_callback: Async function to call when events occur
            time_scale: Speed multiplier (1.0 = real-time, 10.0 = 10x faster)
        """
        self.env = simpy.Environment()
        self.event_callback = event_callback
        self.time_scale = time_scale
        self.patients: List[Patient] = []
        self.start_time = datetime.utcnow()
        self.loop = None  # Will be set when run_async is called
        self.pending_events = []  # Store events to process later
        
    def schedule_patient_arrival(
        self,
        delay_minutes: float,
        severity: SeverityLevel,
        location: str = "ED",
        deterioration: DeteriorationPattern = DeteriorationPattern.STABLE,
        arrival_mode: ArrivalMode = ArrivalMode.WALK_IN,
        chief_complaint: Optional[str] = None
    ):
        """
        Schedule a patient arrival.
        
        Args:
            delay_minutes: Minutes from simulation start
            severity: Patient severity level
            location: Arrival location
            deterioration: Deterioration pattern
            arrival_mode: How patient arrived
            chief_complaint: Optional specific complaint
        """
        self.env.process(
            self._patient_arrival_process(
                delay_minutes,
                severity,
                location,
                deterioration,
                arrival_mode,
                chief_complaint
            )
        )
    
    def _patient_arrival_process(
        self,
        delay: float,
        severity: SeverityLevel,
        location: str,
        deterioration: DeteriorationPattern,
        arrival_mode: ArrivalMode,
        chief_complaint: Optional[str]
    ):
        """Internal process for patient arrival"""
        yield self.env.timeout(delay)
        
        # Generate patient
        patient = DataGenerator.generate_patient(
            severity,
            location,
            deterioration,
            chief_complaint
        )
        
        self.patients.append(patient)
        
        # Emit arrival event
        event = PatientArrivalSimEvent(
            sim_time=self.env.now,
            timestamp=self.start_time + timedelta(minutes=self.env.now),
            patient_id=patient.id,
            arrival_mode=arrival_mode,
            severity=severity,
            chief_complaint=patient.chief_complaint,
            initial_vitals={
                "heart_rate": patient.vitals.heart_rate,
                "bp": patient.vitals.blood_pressure,
                "spo2": patient.vitals.spo2,
                "temp": patient.vitals.temperature
            },
            deterioration_pattern=deterioration
        )
        
        if self.event_callback:
            # Store event instead of trying to create async task
            self.pending_events.append(event)
        
        # Start monitoring this patient
        self.env.process(self._monitor_patient(patient, deterioration, severity))
    
    def _monitor_patient(
        self,
        patient: Patient,
        deterioration: DeteriorationPattern,
        severity: SeverityLevel
    ):
        """Monitor patient and emit periodic vitals updates"""
        
        # Emit vitals every 15 minutes
        for reading_num in range(1, 9):  # 8 readings over 2 hours
            yield self.env.timeout(15)
            
            # Generate new vitals based on deterioration and patient age
            new_vitals = DataGenerator.generate_vitals(
                age=patient.age,
                severity=severity,
                deterioration=deterioration,
                time_offset=reading_num * 15
            )
            
            # Update patient vitals
            patient.vitals = new_vitals
            patient.last_updated = datetime.now()
            
            # Emit vitals update event
            vitals_event = VitalsUpdateSimEvent(
                sim_time=self.env.now,
                timestamp=self.start_time + timedelta(minutes=self.env.now),
                patient_id=patient.id,
                heart_rate=int(new_vitals.heart_rate),
                blood_pressure_systolic=int(new_vitals.systolic_bp),
                blood_pressure_diastolic=int(new_vitals.diastolic_bp),
                oxygen_saturation=new_vitals.spo2,
                respiratory_rate=int(new_vitals.respiratory_rate) if new_vitals.respiratory_rate else 16,
                temperature=new_vitals.temperature,
                glasgow_coma_scale=15,  # Default GCS
                deterioration_indicator=deterioration.value if deterioration != DeteriorationPattern.STABLE else None
            )
            
            if self.event_callback:
                self.pending_events.append(vitals_event)
            
            # Check for deterioration
            if deterioration != DeteriorationPattern.STABLE:
                if new_vitals.spo2 < 88 or new_vitals.heart_rate > 130:
                    deterioration_event = DeteriorationSimEvent(
                        sim_time=self.env.now,
                        timestamp=self.start_time + timedelta(minutes=self.env.now),
                        patient_id=patient.id,
                        deterioration_type=deterioration,
                        severity_change=f"Vitals declining - O2: {new_vitals.spo2}%, HR: {new_vitals.heart_rate}",
                        trigger_vitals={
                            "spo2": new_vitals.spo2,
                            "hr": new_vitals.heart_rate,
                            "bp": f"{new_vitals.systolic_bp}/{new_vitals.diastolic_bp}"
                        },
                        needs_escalation=True
                    )
                    
                    if self.event_callback:
                        self.pending_events.append(deterioration_event)
    
    def run(self, until: Optional[float] = None):
        """
        Run simulation synchronously.
        
        Args:
            until: Simulation minutes to run (None = run until no events)
        """
        self.env.run(until=until)
    
    async def run_async(self, until: Optional[float] = None):
        """
        Run simulation asynchronously.
        
        Args:
            until: Simulation minutes to run
        """
        # Run simulation in thread executor (SimPy is not async)
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, self.run, until)
        
        # Process all pending events
        if self.event_callback:
            for event in self.pending_events:
                await self.event_callback(event)
    
    def get_current_patients(self) -> List[Patient]:
        """Get all patients in the simulation"""
        return self.patients.copy()
    
    def get_simulation_time(self) -> float:
        """Get current simulation time in minutes"""
        return self.env.now
