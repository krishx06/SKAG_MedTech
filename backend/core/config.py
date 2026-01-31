"""
Configuration management for AdaptiveCare backend.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MCDAConfig(BaseModel):
    """MCDA weights configuration."""
    risk_weight: float = Field(0.4, ge=0, le=1)
    capacity_weight: float = Field(0.3, ge=0, le=1)
    wait_time_weight: float = Field(0.2, ge=0, le=1)
    resource_weight: float = Field(0.1, ge=0, le=1)


class DecisionThresholds(BaseModel):
    """Thresholds for decision making."""
    escalate_threshold: float = Field(0.75, ge=0, le=1)
    observe_threshold: float = Field(0.5, ge=0, le=1)
    low_capacity_threshold: float = Field(0.3, ge=0, le=1)
    confidence_threshold: float = Field(0.6, ge=0, le=1)
    
    # Risk thresholds
    high_risk_threshold: float = Field(70.0, ge=0, le=100)
    critical_risk_threshold: float = Field(85.0, ge=0, le=100)
    
    # Wait time thresholds (minutes)
    urgent_wait_time: int = Field(30, ge=0)
    critical_wait_time: int = Field(60, ge=0)


class LLMConfig(BaseModel):
    """LLM (Claude) configuration."""
    api_key: str = Field(default="")
    model: str = Field("claude-sonnet-4-20250514")
    max_tokens: int = Field(500)
    temperature: float = Field(0.3, ge=0, le=1)


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""
    host: str = Field("0.0.0.0")
    port: int = Field(8000)
    heartbeat_interval: int = Field(30)  # seconds


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field("sqlite:///./adaptivecare.db")
    echo: bool = Field(False)


class Config:
    """Main configuration class."""
    
    # Application
    APP_NAME: str = "AdaptiveCare"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    # LLM Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "500"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    
    # MCDA Weights
    RISK_WEIGHT: float = float(os.getenv("RISK_WEIGHT", "0.4"))
    CAPACITY_WEIGHT: float = float(os.getenv("CAPACITY_WEIGHT", "0.3"))
    WAIT_TIME_WEIGHT: float = float(os.getenv("WAIT_TIME_WEIGHT", "0.2"))
    RESOURCE_WEIGHT: float = float(os.getenv("RESOURCE_WEIGHT", "0.1"))
    
    # Decision Thresholds
    ESCALATE_THRESHOLD: float = float(os.getenv("ESCALATE_THRESHOLD", "0.75"))
    OBSERVE_THRESHOLD: float = float(os.getenv("OBSERVE_THRESHOLD", "0.5"))
    LOW_CAPACITY_THRESHOLD: float = float(os.getenv("LOW_CAPACITY_THRESHOLD", "0.3"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    HIGH_RISK_THRESHOLD: float = float(os.getenv("HIGH_RISK_THRESHOLD", "70.0"))
    CRITICAL_RISK_THRESHOLD: float = float(os.getenv("CRITICAL_RISK_THRESHOLD", "85.0"))
    
    # Timing
    AGENT_TICK_INTERVAL: float = float(os.getenv("AGENT_TICK_INTERVAL", "1.0"))  # seconds
    WEBSOCKET_HEARTBEAT: int = int(os.getenv("WEBSOCKET_HEARTBEAT", "30"))  # seconds
    
    @classmethod
    def get_mcda_weights(cls) -> MCDAConfig:
        """Get MCDA weights as config object."""
        return MCDAConfig(
            risk_weight=cls.RISK_WEIGHT,
            capacity_weight=cls.CAPACITY_WEIGHT,
            wait_time_weight=cls.WAIT_TIME_WEIGHT,
            resource_weight=cls.RESOURCE_WEIGHT
        )
    
    @classmethod
    def get_decision_thresholds(cls) -> DecisionThresholds:
        """Get decision thresholds as config object."""
        return DecisionThresholds(
            escalate_threshold=cls.ESCALATE_THRESHOLD,
            observe_threshold=cls.OBSERVE_THRESHOLD,
            low_capacity_threshold=cls.LOW_CAPACITY_THRESHOLD,
            confidence_threshold=cls.CONFIDENCE_THRESHOLD,
            high_risk_threshold=cls.HIGH_RISK_THRESHOLD,
            critical_risk_threshold=cls.CRITICAL_RISK_THRESHOLD
        )
    
    @classmethod
    def get_llm_config(cls) -> LLMConfig:
        """Get LLM configuration."""
        return LLMConfig(
            api_key=cls.ANTHROPIC_API_KEY,
            model=cls.LLM_MODEL,
            max_tokens=cls.LLM_MAX_TOKENS,
            temperature=cls.LLM_TEMPERATURE
        )
    
    @classmethod
    def get_websocket_config(cls) -> WebSocketConfig:
        """Get WebSocket configuration."""
        return WebSocketConfig(
            host=cls.HOST,
            port=cls.PORT,
            heartbeat_interval=cls.WEBSOCKET_HEARTBEAT
        )
    
    @classmethod
    def validate_required(cls) -> list:
        """Check for required configuration and return missing items."""
        missing = []
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        return missing
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return not cls.DEBUG
