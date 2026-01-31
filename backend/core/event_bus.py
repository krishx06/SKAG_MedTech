"""
Event bus for inter-agent communication in AdaptiveCare.
Uses async pub/sub pattern for decoupled agent communication.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import uuid

from backend.models.events import EventType, AgentEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    Async event bus for inter-agent communication.
    
    Supports:
    - Publishing events to all subscribers
    - Subscribing to specific event types
    - Event history for debugging
    - Priority-based event handling
    """
    
    def __init__(self, max_history: int = 1000):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._event_history: List[AgentEvent] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
        self._is_running = True
        
        # Initialize subscriber lists for all event types
        for event_type in EventType:
            self._subscribers[event_type] = []
        
        logger.info("EventBus initialized")

    async def publish(self, event: AgentEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        if not self._is_running:
            logger.warning("EventBus is stopped, ignoring event")
            return
            
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        logger.debug(f"Publishing event: {event.event_type} from {event.source_agent}")
        
        # Get subscribers for this event type
        type_subscribers = self._subscribers.get(event.event_type, [])
        all_subscribers = type_subscribers + self._global_subscribers
        
        # Sort by priority if available
        all_subscribers_sorted = sorted(
            all_subscribers,
            key=lambda s: getattr(s, '_priority', 5),
            reverse=True
        )
        
        # Notify all subscribers
        tasks = []
        for callback in all_subscribers_sorted:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(self._safe_call(callback, event))
            else:
                # Wrap sync callback
                tasks.append(self._safe_call_sync(callback, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, callback: Callable, event: AgentEvent) -> None:
        """Safely call an async callback, catching exceptions."""
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}", exc_info=True)

    async def _safe_call_sync(self, callback: Callable, event: AgentEvent) -> None:
        """Safely call a sync callback."""
        try:
            callback(event)
        except Exception as e:
            logger.error(f"Error in sync event callback: {e}", exc_info=True)

    def subscribe(
        self, 
        event_type: EventType, 
        callback: Callable[[AgentEvent], Any],
        priority: int = 5
    ) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
            priority: Handler priority (1-10, 10 = highest)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Attach priority to callback for sorting
        callback._priority = priority  # type: ignore
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type} with priority {priority}")

    def subscribe_all(
        self, 
        callback: Callable[[AgentEvent], Any],
        priority: int = 5
    ) -> None:
        """
        Subscribe to all events.
        
        Args:
            callback: Function to call for any event
            priority: Handler priority (1-10, 10 = highest)
        """
        callback._priority = priority  # type: ignore
        if callback not in self._global_subscribers:
            self._global_subscribers.append(callback)
            logger.debug(f"Subscribed to all events with priority {priority}")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: The callback to remove
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from {event_type}")

    def unsubscribe_all(self, callback: Callable) -> None:
        """Remove a callback from all subscriptions."""
        if callback in self._global_subscribers:
            self._global_subscribers.remove(callback)
        
        for event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[AgentEvent]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
        
        Returns:
            List of events, most recent first
        """
        history = self._event_history.copy()
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        # Return most recent first
        history.reverse()
        return history[:limit]

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of subscribers for an event type or total."""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values()) + len(self._global_subscribers)

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")

    def stop(self) -> None:
        """Stop the event bus from processing events."""
        self._is_running = False
        logger.info("EventBus stopped")

    def start(self) -> None:
        """Start/resume the event bus."""
        self._is_running = True
        logger.info("EventBus started")


# Singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the singleton event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def create_event_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid.uuid4().hex[:12]}"
