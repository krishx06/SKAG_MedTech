"""
LLM-Powered Scenario Generator for AdaptiveCare

Parses natural language prompts to generate hospital simulation scenarios.
Example: "10 ICU beds, 9 filled, ambulance with 2 critical patients arriving"
"""
import logging
import os
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration from prompt."""
    # Capacity configuration
    icu_total_beds: int = 12
    icu_occupied_beds: int = 8
    ed_total_beds: int = 10
    ed_occupied_beds: int = 6
    ward_total_beds: int = 24
    ward_occupied_beds: int = 18
    
    # Patient arrivals
    initial_patients: int = 5
    incoming_ambulances: int = 0
    ambulance_patients: List[Dict[str, Any]] = None
    
    # Staff
    staff_shortage: bool = False
    icu_nurses: int = 4
    ed_nurses: int = 5
    
    # Dynamic events
    events: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.ambulance_patients is None:
            self.ambulance_patients = []
        if self.events is None:
            self.events = []


class PromptScenarioGenerator:
    """
    Generates simulation scenarios from natural language prompts using LLM.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the prompt scenario generator.
        
        Args:
            api_key: Google API key for Gemini (defaults to env variable)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Prompt Scenario Generator initialized with Gemini")
            except ImportError:
                logger.warning("google-generativeai not installed, using fallback parser")
        else:
            logger.warning("No Google API key, using rule-based parser")
    
    def parse_prompt(self, prompt: str) -> ScenarioConfig:
        """
        Parse natural language prompt into scenario configuration.
        
        Args:
            prompt: Natural language description of scenario
            
        Returns:
            ScenarioConfig with extracted parameters
            
        Examples:
            "10 ICU beds, 9 filled, ambulance with 2 critical patients"
            "Staff shortage with 2 nurses, 15 ED patients waiting"
            "Normal operations with 80% capacity"
        """
        if self._client:
            return self._parse_with_llm(prompt)
        else:
            return self._parse_with_rules(prompt)
    
    def _parse_with_llm(self, prompt: str) -> ScenarioConfig:
        """Parse prompt using Gemini LLM."""
        try:
            system_prompt = f"""You are a hospital simulation scenario parser. Extract parameters from natural language prompts.

Given a prompt, extract:
1. Bed capacity (ICU, ED, Ward) - total and occupied
2. Incoming patients (ambulances, critical cases)
3. Staff levels and shortages
4. Any special events

Respond ONLY with valid JSON in this format:
{{
  "icu_total_beds": 12,
  "icu_occupied_beds": 9,
  "ed_total_beds": 10,
  "ed_occupied_beds": 6,
  "ward_total_beds": 24,
  "ward_occupied_beds": 18,
  "initial_patients": 5,
  "incoming_ambulances": 1,
  "ambulance_patients": [
    {{"acuity": "critical", "complaint": "chest pain", "age": 65}}
  ],
  "staff_shortage": false,
  "icu_nurses": 4,
  "ed_nurses": 5,
  "events": []
}}

Use reasonable defaults for unspecified values.

User prompt: {prompt}

JSON response:"""

            response = self._client.generate_content(
                system_prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 500}
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in response (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                config_dict = json.loads(json_str)
                
                logger.info(f"LLM parsed scenario: {config_dict}")
                return ScenarioConfig(**config_dict)
            else:
                logger.warning("Could not extract JSON from LLM response, using fallback")
                return self._parse_with_rules(prompt)
                
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}, using rule-based fallback")
            return self._parse_with_rules(prompt)
    
    def _parse_with_rules(self, prompt: str) -> ScenarioConfig:
        """Fallback rule-based parser using regex."""
        config = ScenarioConfig()
        prompt_lower = prompt.lower()
        
        # Parse ICU beds
        icu_match = re.search(r'(\d+)\s*icu\s*beds?', prompt_lower)
        if icu_match:
            config.icu_total_beds = int(icu_match.group(1))
        
        icu_filled = re.search(r'(\d+)\s*(filled|occupied)', prompt_lower)
        if icu_filled:
            config.icu_occupied_beds = int(icu_filled.group(1))
        
        # Parse ED beds
        ed_match = re.search(r'(\d+)\s*ed\s*beds?', prompt_lower)
        if ed_match:
            config.ed_total_beds = int(ed_match.group(1))
        
        # Parse ambulances
        ambulance_match = re.search(r'ambulance[s]?\s*(?:with\s*)?(\d+)?\s*(critical|patients?)?', prompt_lower)
        if ambulance_match:
            count = int(ambulance_match.group(1)) if ambulance_match.group(1) else 1
            config.incoming_ambulances = count
            
            # Create critical patients
            is_critical = 'critical' in prompt_lower
            for i in range(count):
                config.ambulance_patients.append({
                    "acuity": "critical" if is_critical else "emergent",
                    "complaint": "Emergency arrival",
                    "age": 60 + i * 5
                })
        
        # Parse staff shortage
        if 'staff shortage' in prompt_lower or 'nurse shortage' in prompt_lower:
            config.staff_shortage = True
            config.icu_nurses = 2
            config.ed_nurses = 3
        
        # Parse patient count
        patient_match = re.search(r'(\d+)\s*patients?', prompt_lower)
        if patient_match and 'ambulance' not in prompt_lower:
            config.initial_patients = int(patient_match.group(1))
        
        logger.info(f"Rule-based parsed scenario: ICU={config.icu_occupied_beds}/{config.icu_total_beds}, "
                   f"Ambulances={config.incoming_ambulances}, Staff shortage={config.staff_shortage}")
        
        return config
    
    def generate_event_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse a prompt into a dynamic event that can be injected mid-simulation.
        
        Args:
            prompt: Event description (e.g., "ambulance with critical patient arrives now")
            
        Returns:
            Event dict with type and parameters
        """
        prompt_lower = prompt.lower()
        
        # Detect event type
        if 'ambulance' in prompt_lower:
            # Count patients
            count_match = re.search(r'(\d+)\s*patients?', prompt_lower)
            count = int(count_match.group(1)) if count_match.else 1
            
            is_critical = 'critical' in prompt_lower or 'emergency' in prompt_lower
            
            return {
                "type": "ambulance_arrival",
                "count": count,
                "patients": [{
                    "acuity_level": 1 if is_critical else 2,
                    "chief_complaint": "Emergency arrival - chest pain" if is_critical else "Emergency arrival",
                    "age": 60 + i * 5,
                    "vitals": {
                        "heart_rate": 110 + i * 5 if is_critical else 90 + i * 5,
                        "spo2": 88 if is_critical else 94,
                        "systolic_bp": 140 + i * 10,
                        "diastolic_bp": 90 + i * 5
                    }
                } for i in range(count)]
            }
        
        elif 'staff' in prompt_lower and ('shortage' in prompt_lower or 'call' in prompt_lower):
            return {
                "type": "staff_change",
                "shortage": 'shortage' in prompt_lower,
                "unit": "ICU" if 'icu' in prompt_lower else "ED"
            }
        
        elif 'bed' in prompt_lower and ('available' in prompt_lower or 'free' in prompt_lower):
            # Bed became available
            count_match = re.search(r'(\d+)\s*beds?', prompt_lower)
            count = int(count_match.group(1)) if count_match else 1
            
            return {
                "type": "capacity_change",
                "unit": "ICU" if 'icu' in prompt_lower else "ED",
                "beds_change": count
            }
        
        else:
            # Generic patient deterioration
            return {
                "type": "patient_deterioration",
                "severity": "high" if 'critical' in prompt_lower else "moderate"
            }


# Singleton instance
_generator: Optional[PromptScenarioGenerator] = None


def get_scenario_generator() -> PromptScenarioGenerator:
    """Get or create the global scenario generator."""
    global _generator
    if _generator is None:
        _generator = PromptScenarioGenerator()
    return _generator
