"""
Base agent class for AdaptiveCare multi-agent system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Callable
import asyncio

from backend.core.event_bus import EventBus
from backend.core.state_manager import StateManager
from backend.models.events import AgentEvent, EventType, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the AdaptiveCare system.
    
    Provides:
    - Event subscription and publishing
    - State management access
    - Lifecycle management
    - Logging infrastructure
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        event_bus: EventBus,
        state_manager: StateManager,
        name: Optional[str] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_type: Type of this agent
            event_bus: Event bus for inter-agent communication
            state_manager: Centralized state manager
            name: Optional custom name
        """
        self.agent_type = agent_type
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.name = name or agent_type.value
        self._is_running = False
        self._subscriptions: List[tuple] = []
        
        logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Process input and produce output.
        Must be implemented by subclasses.
        
        Args:
            input_data: Agent-specific input
            
        Returns:
            Agent-specific output
        """
        pass

    async def start(self) -> None:
        """Start the agent and subscribe to events."""
        if self._is_running:
            logger.warning(f"Agent {self.name} is already running")
            return
        
        self._is_running = True
        self._subscribe_to_events()
        await self.on_start()
        logger.info(f"Agent started: {self.name}")

    async def stop(self) -> None:
        """Stop the agent and unsubscribe from events."""
        if not self._is_running:
            return
        
        self._is_running = False
        self._unsubscribe_from_events()
        await self.on_stop()
        logger.info(f"Agent stopped: {self.name}")

    async def on_start(self) -> None:
        """Hook called when agent starts. Override in subclass."""
        pass

    async def on_stop(self) -> None:
        """Hook called when agent stops. Override in subclass."""
        pass

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events. Override in subclass to customize."""
        pass

    def _unsubscribe_from_events(self) -> None:
        """Unsubscribe from all events."""
        for event_type, callback in self._subscriptions:
            self.event_bus.unsubscribe(event_type, callback)
        self._subscriptions.clear()

    def subscribe(
        self, 
        event_type: EventType, 
        callback: Callable[[AgentEvent], Any],
        priority: int = 5
    ) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Handler function
            priority: Handler priority (1-10)
        """
        self.event_bus.subscribe(event_type, callback, priority)
        self._subscriptions.append((event_type, callback))
        logger.debug(f"{self.name} subscribed to {event_type}")

    async def emit_event(self, event: AgentEvent) -> None:
        """
        Emit an event to the event bus.
        
        Args:
            event: Event to publish
        """
        if not self._is_running:
            logger.warning(f"Agent {self.name} is not running, cannot emit event")
            return
        
        await self.event_bus.publish(event)
        logger.debug(f"{self.name} emitted {event.event_type}")

    async def store_output(self, key: str, value: Any) -> None:
        """
        Store output in state manager for other agents.
        
        Args:
            key: Output key
            value: Output value
        """
        await self.state_manager.store_agent_output(
            self.agent_type.value, key, value
        )

    def get_agent_output(self, agent_type: AgentType, key: str) -> Optional[Any]:
        """
        Get output from another agent.
        
        Args:
            agent_type: Type of agent
            key: Output key
            
        Returns:
            Stored output value or None
        """
        return self.state_manager.get_agent_output(agent_type.value, key)

    @property
    def is_running(self) -> bool:
        """Check if agent is currently running."""
        return self._is_running

    def __repr__(self) -> str:
        status = "running" if self._is_running else "stopped"
        return f"<{self.__class__.__name__} name={self.name} status={status}>"
