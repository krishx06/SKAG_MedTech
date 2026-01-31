"""
LLM Reasoning module for AdaptiveCare.
Uses Claude API to generate human-readable explanations for decisions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.models.patient import Patient
from backend.models.decision import DecisionType, MCDAScore, UrgencyLevel
from backend.core.config import Config

logger = logging.getLogger(__name__)


class LLMReasoning:
    """
    LLM-powered reasoning for generating human-readable decision explanations.
    
    Uses Claude API to transform MCDA scores and patient context into
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
            api_key: Anthropic API key (defaults to config)
            model: Model name (defaults to config)
        """
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.model = model or Config.LLM_MODEL
        self.max_tokens = Config.LLM_MAX_TOKENS
        self.temperature = Config.LLM_TEMPERATURE
        self._client = None
        
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"LLM Reasoning initialized with model: {self.model}")
            except ImportError:
                logger.warning("anthropic package not installed, using fallback explanations")
        else:
            logger.warning("No API key provided, using fallback explanations")

    async def generate_explanation(
        self,
        patient: Patient,
        decision_type: DecisionType,
        mcda_score: MCDAScore,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable explanation for a decision.
        
        Args:
            patient: The patient the decision is for
            decision_type: Type of decision made
            mcda_score: MCDA scoring breakdown
            context: Additional context (capacity, recommendations, etc.)
            
        Returns:
            Human-readable explanation string
        """
        if not self._client:
            return self._generate_fallback_explanation(
                patient, decision_type, mcda_score, context
            )
        
        try:
            prompt = self._build_prompt(patient, decision_type, mcda_score, context)
            
            message = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            explanation = message.content[0].text.strip()
            logger.debug(f"Generated LLM explanation for patient {patient.id}")
            return explanation
            
        except Exception as e:
            logger.error(f"LLM API error: {e}, using fallback")
            return self._generate_fallback_explanation(
                patient, decision_type, mcda_score, context
            )

    def _build_prompt(
        self,
        patient: Patient,
        decision_type: DecisionType,
        mcda_score: MCDAScore,
        context: Dict[str, Any]
    ) -> str:
        """Build the prompt for Claude API."""
        
        # Get dominant factor
        dominant = mcda_score.get_dominant_factor()
        breakdown = mcda_score.get_breakdown()
        
        prompt = f"""You are a clinical decision support system explaining patient care decisions to hospital staff.

Generate a clear, concise explanation (2-3 sentences) for the following decision:

PATIENT:
- ID: {patient.id}
- Age: {patient.age}, Chief Complaint: {patient.chief_complaint}
- Acuity Level: ESI {patient.acuity_level} 
- Current Location: {patient.current_location}
- Wait Time: {patient.wait_time_minutes} minutes
- Risk Score: {patient.risk_score:.1f}/100

VITALS:
- Heart Rate: {patient.vitals.heart_rate} bpm
- Blood Pressure: {patient.vitals.blood_pressure}
- SpO2: {patient.vitals.spo2}%
- Temperature: {patient.vitals.temperature}°C

DECISION: {decision_type.upper()}

MCDA SCORE BREAKDOWN:
- Overall Score: {mcda_score.weighted_total:.2f}
- Risk Factor: {breakdown['risk']['raw']:.2f} (weighted: {breakdown['risk']['weighted']:.2f}, {breakdown['risk']['contribution']:.1f}% contribution)
- Capacity Factor: {breakdown['capacity']['raw']:.2f} (weighted: {breakdown['capacity']['weighted']:.2f}, {breakdown['capacity']['contribution']:.1f}% contribution)
- Wait Time Factor: {breakdown['wait_time']['raw']:.2f} (weighted: {breakdown['wait_time']['weighted']:.2f}, {breakdown['wait_time']['contribution']:.1f}% contribution)
- Resource Match: {breakdown['resource']['raw']:.2f} (weighted: {breakdown['resource']['weighted']:.2f}, {breakdown['resource']['contribution']:.1f}% contribution)
- Dominant Factor: {dominant}

CONTEXT:
- Available ICU beds: {context.get('icu_beds_available', 'N/A')}
- Available ER beds: {context.get('er_beds_available', 'N/A')}
- Flow recommendations: {context.get('flow_recommendations', [])}

Write a natural, clinical explanation that:
1. States the decision clearly
2. Explains the PRIMARY reason (focus on the dominant factor)
3. Mentions any critical secondary factors
4. Uses clinical terminology appropriately
5. Is actionable for staff

Example format: "Patient [ACTION] because [PRIMARY REASON]. [SECONDARY FACTORS if relevant]. Recommend [SPECIFIC ACTION]."
"""
        return prompt

    def _generate_fallback_explanation(
        self,
        patient: Patient,
        decision_type: DecisionType,
        mcda_score: MCDAScore,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate explanation without LLM (rule-based fallback).
        Used when API is unavailable.
        """
        dominant = mcda_score.get_dominant_factor()
        breakdown = mcda_score.get_breakdown()
        
        # Build explanation based on decision type and dominant factor
        reasons = []
        
        # Risk-based reasons
        if mcda_score.risk_score >= 0.7:
            reasons.append(f"risk score elevated to {patient.risk_score:.0f}%")
        if patient.vitals.is_critical():
            reasons.append("critical vital signs detected")
        if patient.risk_factors.sepsis_probability > 0.5:
            reasons.append(f"sepsis probability at {patient.risk_factors.sepsis_probability*100:.0f}%")
        
        # Capacity-based reasons
        if mcda_score.capacity_score >= 0.7:
            icu_beds = context.get('icu_beds_available', 0)
            if icu_beds > 0:
                reasons.append(f"ICU bed available ({icu_beds} open)")
        elif mcda_score.capacity_score < 0.3:
            reasons.append("limited bed availability")
        
        # Wait time reasons
        if mcda_score.wait_time_score >= 0.7:
            reasons.append(f"wait time ({patient.wait_time_minutes} min) exceeds threshold")
        
        # Resource reasons
        if mcda_score.resource_score < 0.5:
            reasons.append("resource constraints noted")
        
        # Build decision-specific explanation
        if decision_type == DecisionType.ESCALATE:
            action = "escalated to higher care level"
            if not reasons:
                reasons.append(f"MCDA score {mcda_score.weighted_total:.2f} exceeds escalation threshold")
        elif decision_type == DecisionType.OBSERVE:
            action = "recommended for continued monitoring"
            if not reasons:
                reasons.append("condition stable but requires ongoing observation")
        elif decision_type == DecisionType.DELAY:
            action = "placement delayed"
            if not reasons:
                reasons.append("awaiting resource availability")
        elif decision_type == DecisionType.REPRIORITIZE:
            action = "queue position adjusted"
            if not reasons:
                reasons.append("priority recalculated based on current factors")
        else:
            action = "decision pending"
            reasons.append("evaluation in progress")
        
        # Format the explanation
        reason_text = " AND ".join(reasons[:2]) if reasons else "multiple factors"
        
        explanation = f"Patient {action} because {reason_text}."
        
        # Add recommendation
        if decision_type == DecisionType.ESCALATE:
            target = context.get('target_unit', 'ICU')
            explanation += f" Recommend immediate transfer to {target}."
        elif decision_type == DecisionType.OBSERVE:
            explanation += " Continue monitoring with reassessment in 15 minutes."
        elif decision_type == DecisionType.DELAY:
            explanation += " Will reassess when resources become available."
        
        return explanation

    def extract_contributing_factors(
        self,
        patient: Patient,
        mcda_score: MCDAScore,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Extract list of contributing factors for display.
        
        Args:
            patient: Patient being evaluated
            mcda_score: MCDA score breakdown
            context: Additional context
            
        Returns:
            List of human-readable factor strings
        """
        factors = []
        breakdown = mcda_score.get_breakdown()
        
        # Risk factors
        if mcda_score.risk_score >= 0.5:
            factors.append(f"Risk score: {patient.risk_score:.0f}/100")
        if patient.vitals.is_critical():
            factors.append("Critical vitals detected")
        if patient.risk_factors.sepsis_probability > 0.3:
            factors.append(f"Sepsis risk: {patient.risk_factors.sepsis_probability*100:.0f}%")
        if patient.risk_factors.deterioration_trend > 0.2:
            factors.append("Worsening trend detected")
        
        # Capacity factors
        icu_beds = context.get('icu_beds_available', 0)
        if icu_beds > 0:
            factors.append(f"ICU beds available: {icu_beds}")
        elif icu_beds == 0 and mcda_score.capacity_score < 0.3:
            factors.append("No ICU beds available")
        
        # Wait time
        if patient.wait_time_minutes > 30:
            factors.append(f"Wait time: {patient.wait_time_minutes} minutes")
        
        # Acuity
        factors.append(f"Acuity level: ESI {patient.acuity_level}")
        
        return factors[:5]  # Limit to top 5 factors

    async def generate_batch_explanations(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate explanations for multiple decisions efficiently.
        
        Args:
            decisions: List of decision dicts with patient, type, score, context
            
        Returns:
            Dict mapping patient_id to explanation
        """
        explanations = {}
        
        for decision in decisions:
            patient_id = decision['patient'].id
            explanation = await self.generate_explanation(
                patient=decision['patient'],
                decision_type=decision['decision_type'],
                mcda_score=decision['mcda_score'],
                context=decision.get('context', {})
            )
            explanations[patient_id] = explanation
        
        return explanations
