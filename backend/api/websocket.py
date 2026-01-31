"""
WebSocket handler for real-time updates to frontend.
"""

import logging
import asyncio
import json
from typing import List, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core.event_bus import get_event_bus
from backend.core.state_manager import get_state_manager
from backend.models.events import EventType, AgentEvent, DecisionEvent

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        self._subscribed_to_events = False

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Subscribe to events if first connection
        if not self._subscribed_to_events:
            self._subscribe_to_events()

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, default=str)
        
        disconnected = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def send_to_client(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")
            await self.disconnect(websocket)

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events for broadcasting."""
        event_bus = get_event_bus()
        
        # Subscribe to decision events
        event_bus.subscribe(EventType.DECISION_MADE, self._on_decision_event, priority=10)
        
        # Subscribe to other events for real-time updates
        event_bus.subscribe(EventType.RISK_UPDATE, self._on_risk_update, priority=10)
        event_bus.subscribe(EventType.CAPACITY_UPDATE, self._on_capacity_update, priority=10)
        event_bus.subscribe(EventType.PATIENT_ADMITTED, self._on_patient_event, priority=10)
        event_bus.subscribe(EventType.PATIENT_DISCHARGED, self._on_patient_event, priority=10)
        
        self._subscribed_to_events = True
        logger.info("WebSocket manager subscribed to events")

    async def _on_decision_event(self, event: DecisionEvent) -> None:
        """Handle decision events and broadcast to clients."""
        message = {
            "type": "decision",
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": {
                "decision_id": event.decision_id,
                "patient_id": event.patient_id,
                "decision_type": event.decision_type,
                "priority_score": event.priority_score,
                "reasoning": event.reasoning_summary,
                "requires_acknowledgment": event.requires_acknowledgment,
                "full_decision": event.payload
            }
        }
        await self.broadcast(message)

    async def _on_risk_update(self, event: AgentEvent) -> None:
        """Handle risk update events."""
        message = {
            "type": "risk_update",
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.payload
        }
        await self.broadcast(message)

    async def _on_capacity_update(self, event: AgentEvent) -> None:
        """Handle capacity update events."""
        message = {
            "type": "capacity_update",
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.payload
        }
        await self.broadcast(message)

    async def _on_patient_event(self, event: AgentEvent) -> None:
        """Handle patient events (admitted, discharged)."""
        message = {
            "type": "patient_update",
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.payload
        }
        await self.broadcast(message)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.
    
    Clients receive:
    - Decision events (new decisions, updates)
    - Risk updates
    - Capacity changes
    - Patient events
    
    Clients can send:
    - Subscription preferences
    - Ping/pong for keepalive
    """
    await manager.connect(websocket)
    
    # Send initial state
    try:
        await _send_initial_state(websocket)
    except Exception as e:
        logger.error(f"Failed to send initial state: {e}")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await _handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_to_client(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


async def _send_initial_state(websocket: WebSocket) -> None:
    """Send initial state to newly connected client."""
    state_manager = get_state_manager()
    
    # Get current state
    patients = state_manager.get_all_patients()
    capacity = state_manager.get_capacity()
    recent_decisions = state_manager.get_recent_decisions(10)
    
    initial_state = {
        "type": "initial_state",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "patients": [p.to_summary() for p in patients],
            "capacity": capacity.to_summary() if capacity else None,
            "recent_decisions": [d.to_frontend_format() for d in recent_decisions],
            "stats": state_manager.get_state_summary()
        }
    }
    
    await manager.send_to_client(websocket, initial_state)


async def _handle_client_message(websocket: WebSocket, message: dict) -> None:
    """Handle incoming messages from clients."""
    msg_type = message.get("type", "")
    
    if msg_type == "ping":
        await manager.send_to_client(websocket, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    elif msg_type == "subscribe":
        # Handle subscription preferences
        channels = message.get("channels", [])
        await manager.send_to_client(websocket, {
            "type": "subscribed",
            "channels": channels
        })
    
    elif msg_type == "request_state":
        # Re-send current state
        await _send_initial_state(websocket)
    
    elif msg_type == "request_patient":
        # Send specific patient data
        patient_id = message.get("patient_id")
        if patient_id:
            state_manager = get_state_manager()
            patient = state_manager.get_patient(patient_id)
            if patient:
                await manager.send_to_client(websocket, {
                    "type": "patient_data",
                    "data": patient.to_summary()
                })
    
    else:
        await manager.send_to_client(websocket, {
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "active_connections": manager.connection_count,
        "subscribed_to_events": manager._subscribed_to_events
    }
