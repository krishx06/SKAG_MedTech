"""
LLM Reasoning module for AdaptiveCare.
Uses Google Gemini API to generate human-readable explanations for decisions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from backend.models.patient import Patient
from backend.models.decision import DecisionType, MCDAScores, RiskAssessment
from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMReasoning:
    """
    LLM-powered reasoning for generating human-readable decision explanations.
    
    Uses Google Gemini API to transform MCDA scores and patient context into
    clear, actionable explanations that clinical staff can understand.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LLM reasoning module.
        
        Args:
            api_key: Google API key (defaults to env variable)
            model: Model name (defaults to gemini-2.0-flash-exp)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self._client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
                logger.info(f"LLM Reasoning initialized with Gemini model: {self.model}")
            except ImportError:
                logger.warning("google-generativeai package not installed, using fallback explanations")
        else:
            logger.warning("No Google API key provided, using fallback explanations")

    async def generate_explanation(
        self,
        patient: Patient,
        action_type: ActionType,
        mcda_scores: Optional[MCDAScores],
        risk_assessment: Optional[RiskAssessment],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable explanation for a decision.
        
        Args:
            patient: The patient the decision is for
            action_type: Type of action recommended
            mcda_scores: MCDA scoring breakdown (optional)
            risk_assessment: Risk assessment data (optional)
            context: Additional context (capacity, recommendations, etc.)
            
        Returns:
            Human-readable explanation string
        """
        if not self._client:
            return self._generate_fallback_explanation(
                patient, action_type, mcda_scores, risk_assessment, context
            )
        
        try:
            prompt = self._build_prompt(patient, action_type, mcda_scores, risk_assessment, context)
            
            # Generate with Gemini
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
            
            response = self._client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            explanation = response.text.strip()
            logger.debug(f"Generated LLM explanation for patient {patient.patient_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}, using fallback")
            return self._generate_fallback_explanation(
                patient, action_type, mcda_scores, risk_assessment, context
            )

    def _build_prompt(
        self,
        patient: Patient,
        action_type: ActionType,
        mcda_scores: Optional[MCDAScores],
        risk_assessment: Optional[RiskAssessment],
        context: Dict[str, Any]
    ) -> str:
        """Build the prompt for Gemini API."""
        
        # Extract latest vitals
        vitals = patient.latest_vitals
        vitals_text = "No vitals available"
        if vitals:
            vitals_text = f"""- Heart Rate: {vitals.heart_rate} bpm
- Blood Pressure: {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg
- SpO2: {vitals.oxygen_saturation}%
- Respiratory Rate: {vitals.respiratory_rate} breaths/min
- Temperature: {vitals.temperature}°C
- GCS: {vitals.glasgow_coma_scale}/15"""

        # Risk assessment info
        risk_text = "No risk assessment available"
        if risk_assessment:
            risk_text = f"""- Risk Score: {risk_assessment.risk_score:.1f}/100
- Trajectory: {risk_assessment.trajectory.value}
- Contributing Factors: {', '.join(risk_assessment.contributing_factors[:3])}"""

        # MCDA scores info
        mcda_text = "No MCDA scores available"
        if mcda_scores:
            mcda_text = f"""- Overall Score: {mcda_scores.weighted_total:.2f}/100
- Safety: {mcda_scores.safety_score:.1f}
- Urgency: {mcda_scores.urgency_score:.1f}
- Capacity: {mcda_scores.capacity_score:.1f}
- Impact: {mcda_scores.impact_score:.1f}"""
        
        prompt = f"""You are a clinical decision support AI assistant. Generate a clear, professional explanation (2-3 sentences) for this patient care decision.

PATIENT INFORMATION:
- ID: {patient.patient_id}
- Name: {patient.name}
- Age: {patient.age}, Gender: {patient.gender.value if hasattr(patient.gender, 'value') else patient.gender}
- Chief Complaint: {patient.chief_complaint}
- Current Location: {patient.current_location.value if hasattr(patient.current_location, 'value') else patient.current_location}
- Medical History: {', '.join(patient.medical_history[:3]) if patient.medical_history else 'None noted'}

VITALS:
{vitals_text}

RISK ASSESSMENT:
{risk_text}

DECISION SCORES:
{mcda_text}

RECOMMENDED ACTION: {action_type.value.upper()}

CAPACITY CONTEXT:
- ICU beds available: {context.get('icu_beds_available', 'Unknown')}
- ED beds available: {context.get('ed_beds_available', 'Unknown')}
- Staff availability: {context.get('staff_availability', 'Normal')}

Generate a concise clinical explanation that:
1. States the recommended action clearly
2. Explains the PRIMARY clinical reason (focus on most critical factor)
3. Mentions any secondary concerns if critical
4. Uses appropriate medical terminology
5. Is actionable for clinical staff

Format: "Recommendation: [ACTION]. Rationale: [PRIMARY REASON]. [SECONDARY FACTOR if critical]. Next steps: [SPECIFIC ACTION]."

Keep it professional, clear, and under 100 words."""
        
        return prompt

    def _generate_fallback_explanation(
        self,
        patient: Patient,
        action_type: ActionType,
        mcda_scores: Optional[MCDAScores],
        risk_assessment: Optional[RiskAssessment],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate explanation without LLM (rule-based fallback).
        Used when API is unavailable.
        """
        reasons = []
        
        # Risk-based reasons
        if risk_assessment:
            if risk_assessment.risk_score >= 70:
                reasons.append(f"high risk score ({risk_assessment.risk_score:.0f}/100)")
            if risk_assessment.trajectory.value == "deteriorating":
                reasons.append("patient condition deteriorating")
            if risk_assessment.trajectory.value == "critical":
                reasons.append("CRITICAL patient status")
        
        # Vital signs
        vitals = patient.latest_vitals
        if vitals:
            if vitals.oxygen_saturation < 90:
                reasons.append(f"low oxygen saturation ({vitals.oxygen_saturation}%)")
            if vitals.heart_rate > 120:
                reasons.append(f"tachycardia ({vitals.heart_rate} bpm)")
            if vitals.blood_pressure_systolic < 90:
                reasons.append(f"hypotension ({vitals.blood_pressure_systolic} mmHg)")
            if vitals.glasgow_coma_scale < 13:
                reasons.append(f"altered mental status (GCS {vitals.glasgow_coma_scale})")
        
        # Capacity-based reasons
        if mcda_scores:
            if mcda_scores.capacity_score >= 70:
                icu_beds = context.get('icu_beds_available', 0)
                if icu_beds > 0:
                    reasons.append(f"bed available in target unit")
            elif mcda_scores.capacity_score < 30:
                reasons.append("limited bed availability")
        
        # Build decision-specific explanation
        if action_type == ActionType.ESCALATE:
            action = "escalate to higher level of care"
            if not reasons:
                reasons.append("clinical indicators warrant escalation")
            target = context.get('target_unit', 'ICU')
            next_step = f"Immediate transfer to {target} recommended."
            
        elif action_type == ActionType.OBSERVE:
            action = "continue monitoring"
            if not reasons:
                reasons.append("condition requires ongoing observation")
            next_step = "Reassess in 15-30 minutes."
            
        elif action_type == ActionType.DELAY:
            action = "delay placement"
            if not reasons:
                reasons.append("awaiting resource availability")
            next_step = "Reassess when resources become available."
            
        elif action_type == ActionType.REPRIORITIZE:
            action = "adjust priority level"
            if not reasons:
                reasons.append("clinical status changed")
            next_step = "Continue monitoring with updated priority."
            
        else:
            action = "pending evaluation"
            reasons.append("assessment in progress")
            next_step = "Complete evaluation."
        
        # Format the explanation
        reason_text = " AND ".join(reasons[:2]) if reasons else "clinical assessment"
        
        explanation = f"Recommendation: {action.capitalize()}. Rationale: {reason_text}. {next_step}"
        
        return explanation

    def extract_contributing_factors(
        self,
        patient: Patient,
        risk_assessment: Optional[RiskAssessment],
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Extract list of contributing factors for display.
        
        Args:
            patient: Patient being evaluated
            risk_assessment: Risk assessment data
            context: Additional context
            
        Returns:
            List of human-readable factor strings
        """
        factors = []
        
        # Risk factors
        if risk_assessment:
            if risk_assessment.risk_score >= 50:
                factors.append(f"Risk score: {risk_assessment.risk_score:.0f}/100")
            factors.append(f"Trajectory: {risk_assessment.trajectory.value}")
            factors.extend(risk_assessment.contributing_factors[:2])
        
        # Vital signs
        vitals = patient.latest_vitals
        if vitals:
            if vitals.oxygen_saturation < 92:
                factors.append(f"Low SpO2: {vitals.oxygen_saturation}%")
            if vitals.heart_rate > 110 or vitals.heart_rate < 50:
                factors.append(f"Abnormal HR: {vitals.heart_rate} bpm")
            if vitals.glasgow_coma_scale < 15:
                factors.append(f"GCS: {vitals.glasgow_coma_scale}")
        
        # Capacity
        icu_beds = context.get('icu_beds_available', 0)
        if icu_beds > 0:
            factors.append(f"ICU beds available: {icu_beds}")
        elif icu_beds == 0:
            factors.append("No ICU beds available")
        
        # Location and acuity
        factors.append(f"Location: {patient.current_location.value if hasattr(patient.current_location, 'value') else patient.current_location}")
        
        return factors[:5]  # Limit to top 5 factors

    async def generate_batch_explanations(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate explanations for multiple decisions efficiently.
        
        Args:
            decisions: List of decision dicts with patient, action, scores, context
            
        Returns:
            Dict mapping patient_id to explanation
        """
        explanations = {}
        
        for decision in decisions:
            patient_id = decision['patient'].patient_id
            explanation = await self.generate_explanation(
                patient=decision['patient'],
                action_type=decision['action_type'],
                mcda_scores=decision.get('mcda_scores'),
                risk_assessment=decision.get('risk_assessment'),
                context=decision.get('context', {})
            )
            explanations[patient_id] = explanation
        
        return explanations
