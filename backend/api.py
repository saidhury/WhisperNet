import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
router = APIRouter()

def handle_incoming_message(message: bytes, sender_ip: bytes):
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')
    message_str = message.decode('utf-8', errors='ignore')
    print(f"UDP message received from {sender_ip_str}: {message_str}")
    # Logic will go here
    
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f"New client connected: {websocket.client.host}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected: {websocket.client.host}")
