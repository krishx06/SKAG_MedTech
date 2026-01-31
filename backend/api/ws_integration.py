"""
WebSocket Integration for Simulation Orchestrator

Connects the simulation orchestrator to the WebSocket manager
for real-time event broadcasting to frontend clients.
"""
from backend.api.websocket import manager as ws_manager
from backend.simulation.simulation_orchestrator import set_event_callback


def broadcast_event(event_data: dict):
    """
    Callback function for simulation orchestrator to broadcast events via WebSocket.
    
    This function is called by the orchestrator whenever a simulation event occurs
    (patient arrival, vitals update, risk assessment, deterioration).
    """
    import asyncio
    
    # Create async task to broadcast
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_manager.broadcast(event_data))
    loop.close()


def initialize_websocket_integration():
    """
    Initialize WebSocket integration with simulation orchestrator.
    
    Call this during app startup to connect the orchestrator's event
    stream to the WebSocket broadcast system.
    """
    set_event_callback(broadcast_event)


# Export for use in main.py
__all__ = ['initialize_websocket_integration']
