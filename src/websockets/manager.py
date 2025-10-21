# Create this new file at: Synapse-Backend/src/websockets/manager.py
from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        # Maps a client_id (e.g., user_id) to their WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"WebSocket connected for client: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"WebSocket disconnected for client: {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            print(f"Sent message to {client_id}: {message}")
        else:
            print(f"Could not send message: No active WebSocket for client {client_id}")

# Create a single, reusable instance for the application
connection_manager = ConnectionManager()