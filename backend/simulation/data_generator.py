"""
Enhanced synthetic data generator for hospital simulation.
Uses medical reference data for realistic age/gender-specific vital signs and comorbidity patterns.
"""
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
from backend.models.patient import Patient, VitalSigns, PatientStatus, AcuityLevel, RiskFactors
from backend.simulation.event_types import (
    DeteriorationPattern,
    SeverityLevel
)


class EnhancedDataGenerator:
    """Generates realistic hospital data using medical reference data"""
    
    # Load medical reference data
    _ref_data_path = Path(__file__).parent / "medical_reference_data.json"
    with open(_ref_data_path) as f:
        MEDICAL_REF = json.load(f)
    
    CHIEF_COMPLAINTS = [
        "Chest pain",
        "Shortness of breath",
        "Abdominal pain",
        "Fever",
        "Headache",
        "Trauma - MVA",
        "Fall injury",
        "Altered mental status",
        "Seizure",
        "Syncope",
        "Severe bleeding",
        "Sepsis",
        "Stroke symptoms",
        "Diabetic emergency",
        "Respiratory failure - COPD exacerbation"
    ]
    
    FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", 
                   "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas",
                   "Linda", "Charles", "Barbara", "Joseph", "Elizabeth"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson",
                  "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee"]
    
    @staticmethod
    def get_age_group(age: int) -> str:
        """Determine age group from age"""
        for group, ranges in EnhancedDataGenerator.MEDICAL_REF["age_groups"].items():
            if ranges["min"] <= age <= ranges["max"]:
                return group
        return "middle_aged"
    
    @staticmethod
    def generate_patient_id() -> str:
        """Generate unique patient ID"""
        return f"PT{random.randint(10000, 99999)}"
    
    @staticmethod
    def generate_name() -> str:
        """Generate random patient name"""
        first = random.choice(EnhancedDataGenerator.FIRST_NAMES)
        last = random.choice(EnhancedDataGenerator.LAST_NAMES)
        return f"{first} {last}"
    
    @staticmethod
    def generate_age(severity: SeverityLevel) -> int:
        """Generate age based on severity (older patients tend to be sicker)"""
        if severity == SeverityLevel.CRITICAL:
            return random.randint(65, 90)
        elif severity == SeverityLevel.HIGH:
            return random.randint(50, 80)
        elif severity == SeverityLevel.MODERATE:
            return random.randint(35, 70)
        else:
            return random.randint(18, 60)
    
    @staticmethod
    def severity_to_acuity(severity: SeverityLevel) -> AcuityLevel:
        """Map severity level to acuity level"""
        mapping = {
            SeverityLevel.CRITICAL: AcuityLevel.RESUSCITATION,
            SeverityLevel.HIGH: AcuityLevel.EMERGENT,
            SeverityLevel.MODERATE: AcuityLevel.URGENT,
            SeverityLevel.LOW: AcuityLevel.LESS_URGENT
        }
        return mapping.get(severity, AcuityLevel.URGENT)
    
    @staticmethod
    def generate_comorbidities(age: int, chief_complaint: str) -> List[str]:
        """Generate realistic comorbidities based on age and complaint"""
        age_group = EnhancedDataGenerator.get_age_group(age)
        comorbidities = []
        
        # Get prevalence-based comorbidities
        comorbidity_data = EnhancedDataGenerator.MEDICAL_REF["comorbidity_correlations"]
        
        for condition, data in comorbidity_data.items():
            prevalence = data["prevalence_by_age"].get(age_group, 0.1)
            if random.random() < prevalence:
                comorbidities.append(condition)
                
                # Add correlated conditions with reduced probability
                for related in data.get("often_with", []):
                    if related not in comorbidities and random.random() < 0.3:
                        comorbidities.append(related)
        
        return comorbidities[:4]  # Limit to 4 major comorbidities
    
    @staticmethod
    def generate_vitals(
        age: int,
        severity: SeverityLevel,
        deterioration: DeteriorationPattern = DeteriorationPattern.STABLE,
        time_offset: int = 0
    ) -> VitalSigns:
        """Generate age-appropriate vital signs with deterioration patterns"""
        
        age_group = EnhancedDataGenerator.get_age_group(age)
        vital_ranges = EnhancedDataGenerator.MEDICAL_REF["vital_ranges"][age_group]
        
        # Start with normal ranges for the age group
        if severity == SeverityLevel.CRITICAL:
            hr_base = random.randint(
                vital_ranges["heart_rate"]["normal_max"],
                vital_ranges["heart_rate"]["critical_high"]
            )
            sys_base = random.randint(
                vital_ranges["systolic_bp"]["critical_low"],
                vital_ranges["systolic_bp"]["normal_min"]
            )
            spo2_base = random.uniform(
                vital_ranges["spo2"]["critical_low"],
                vital_ranges["spo2"]["normal_min"] - 2
            )
            rr_base = random.randint(
                vital_ranges["respiratory_rate"]["normal_max"] + 5,
                vital_ranges["respiratory_rate"]["critical_high"]
            )
        elif severity == SeverityLevel.HIGH:
            hr_base = random.randint(
                vital_ranges["heart_rate"]["normal_max"] - 5,
                vital_ranges["heart_rate"]["normal_max"] + 20
            )
            sys_base = random.randint(
                vital_ranges["systolic_bp"]["normal_min"] - 10,
                vital_ranges["systolic_bp"]["normal_min"] + 10
            )
            spo2_base = random.uniform(
                vital_ranges["spo2"]["normal_min"] - 4,
                vital_ranges["spo2"]["normal_min"]
            )
            rr_base = random.randint(
                vital_ranges["respiratory_rate"]["normal_max"],
                vital_ranges["respiratory_rate"]["normal_max"] + 8
            )
        elif severity == SeverityLevel.MODERATE:
            hr_base = random.randint(
                vital_ranges["heart_rate"]["normal_min"] + 10,
                vital_ranges["heart_rate"]["normal_max"]
            )
            sys_base = random.randint(
                vital_ranges["systolic_bp"]["normal_min"],
                vital_ranges["systolic_bp"]["normal_max"] + 10
            )
            spo2_base = random.uniform(
                vital_ranges["spo2"]["normal_min"],
                vital_ranges["spo2"]["normal_max"] - 2
            )
            rr_base = random.randint(
                vital_ranges["respiratory_rate"]["normal_min"] + 2,
                vital_ranges["respiratory_rate"]["normal_max"] + 4
            )
        else:  # LOW
            hr_base = random.randint(
                vital_ranges["heart_rate"]["normal_min"],
                vital_ranges["heart_rate"]["normal_max"]
            )
            sys_base = random.randint(
                vital_ranges["systolic_bp"]["normal_min"],
                vital_ranges["systolic_bp"]["normal_max"]
            )
            spo2_base = random.uniform(
                vital_ranges["spo2"]["normal_min"],
                vital_ranges["spo2"]["normal_max"]
            )
            rr_base = random.randint(
                vital_ranges["respiratory_rate"]["normal_min"],
                vital_ranges["respiratory_rate"]["normal_max"]
            )
        
        dia_base = int(sys_base * 0.65)  # Diastolic typically ~65% of systolic
        temp_base = random.uniform(
            vital_ranges["temperature"]["normal_min"],
            vital_ranges["temperature"]["normal_max"]
        )
        
        # Apply deterioration patterns using reference data
        if deterioration != DeteriorationPattern.STABLE and deterioration.value in EnhancedDataGenerator.MEDICAL_REF["deterioration_vital_patterns"]:
            pattern = EnhancedDataGenerator.MEDICAL_REF["deterioration_vital_patterns"][deterioration.value]
            
            # Calculate deterioration factor based on time
            deterioration_factor = min(time_offset / 60.0, 1.0)  # Max deterioration at 60 min
            
            # Apply pattern-specific changes
            if "heart_rate" in pattern:
                hr_change = pattern["heart_rate"]["magnitude"]
                variability = pattern["heart_rate"]["variability"]
                hr_base = hr_base * hr_change * (1 + random.uniform(-variability, variability))
            
            if "systolic_bp" in pattern:
                sys_change = pattern["systolic_bp"]["magnitude"]
                variability = pattern["systolic_bp"]["variability"]
                sys_base = sys_base * sys_change * (1 + random.uniform(-variability, variability))
            
            if "spo2" in pattern:
                spo2_change = pattern["spo2"]["magnitude"]
                variability = pattern["spo2"]["variability"]
                spo2_base = spo2_base * spo2_change * (1 + random.uniform(-variability, variability))
                spo2_base = max(75, spo2_base)  # Don't go below 75%
            
            if "respiratory_rate" in pattern:
                rr_change = pattern["respiratory_rate"]["magnitude"]
                variability = pattern["respiratory_rate"]["variability"]
                rr_base = rr_base * rr_change * (1 + random.uniform(-variability, variability))
            
            if "temperature" in pattern:
                temp_change = pattern["temperature"]["magnitude"]
                variability = pattern["temperature"]["variability"]
                temp_base = temp_base * temp_change * (1 + random.uniform(-variability, variability))
        
        return VitalSigns(
            heart_rate=max(30, min(200, hr_base)),
            systolic_bp=max(60, min(250, sys_base)),
            diastolic_bp=max(40, min(150, dia_base)),
            spo2=round(max(70, min(100, spo2_base)), 1),
            respiratory_rate=max(6, min(50, rr_base)) if rr_base else None,
            temperature=round(max(34, min(42, temp_base)), 1),
            measured_at=datetime.now() + timedelta(minutes=time_offset)
        )
    
    @staticmethod
    def generate_patient(
        severity: SeverityLevel,
        location: str = "ED",
        deterioration_pattern: DeteriorationPattern = DeteriorationPattern.STABLE,
        chief_complaint: str = None
    ) -> Patient:
        """Generate a complete patient with realistic data"""
        
        patient_id = EnhancedDataGenerator.generate_patient_id()
        age = EnhancedDataGenerator.generate_age(severity)
        
        # Select or use provided chief complaint
        if not chief_complaint:
            chief_complaint = random.choice(EnhancedDataGenerator.CHIEF_COMPLAINTS)
        
        # Generate realistic comorbidities
        comorbidities = EnhancedDataGenerator.generate_comorbidities(age, chief_complaint)
        
        # Generate age-appropriate vitals
        initial_vitals = EnhancedDataGenerator.generate_vitals(age, severity, deterioration_pattern, 0)
        
        # Generate risk factors based on complaint and deterioration
        risk_factors = RiskFactors()
        
        complaint_data = EnhancedDataGenerator.MEDICAL_REF["complaint_severity_mapping"].get(
            chief_complaint, {}
        )
        
        for risk_type in complaint_data.get("risk_factors", []):
            if risk_type == "sepsis_probability":
                risk_factors.sepsis_probability = random.uniform(0.3, 0.7) if deterioration_pattern == DeteriorationPattern.SEPSIS else random.uniform(0.1, 0.3)
            elif risk_type == "cardiac_risk":
                risk_factors.cardiac_risk = random.uniform(0.4, 0.8)
            elif risk_type == "respiratory_risk":
                risk_factors.respiratory_risk = random.uniform(0.3, 0.7) if deterioration_pattern == DeteriorationPattern.RESPIRATORY else random.uniform(0.1, 0.3)
            elif risk_type == "deterioration_trend":
                risk_factors.deterioration_trend = random.uniform(0.3, 0.8)
        
        # Set comorbidity score based on number and severity
        risk_factors.comorbidity_score = min(1.0, len(comorbidities) * 0.2)
        
        if deterioration_pattern != DeteriorationPattern.STABLE:
            risk_factors.deterioration_trend = random.uniform(0.5, 1.0)
        
        return Patient(
            id=patient_id,
            name=EnhancedDataGenerator.generate_name(),
            age=age,
            gender=random.choice(["M", "F", "O"]),
            chief_complaint=chief_complaint,
            admission_time=datetime.now(),
            current_location=location,
            vitals=initial_vitals,
            comorbidities=comorbidities,
            acuity_level=EnhancedDataGenerator.severity_to_acuity(severity),
            status=PatientStatus.WAITING,
            risk_factors=risk_factors,
            notes=[]
        )


# Backwards compatibility - use EnhancedDataGenerator as DataGenerator
DataGenerator = EnhancedDataGenerator
