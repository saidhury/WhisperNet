import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

loop = None

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
discovered_peers = set()

def handle_incoming_message(message: bytes, sender_ip: bytes):
    global loop
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')
    message_str = message.decode('utf-8', errors='ignore')
    print(f"UDP message received from {sender_ip_str}: {message_str}")
    try:
        data = json.loads(message_str)
        if data.get("type") == "DISCOVERY":
            if sender_ip_str not in discovered_peers:
                print(f"Discovered new peer: {sender_ip_str}")
                discovered_peers.add(sender_ip_str)
                update_message = {"type": "PEER_LIST_UPDATE", "payload": list(discovered_peers)}
                if loop:
                    asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(update_message)), loop)
    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Error processing incoming message: {e}")

@router.get("/peers")
async def get_peers():
    return list(discovered_peers)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    initial_data = {"type": "PEER_LIST_UPDATE", "payload": list(discovered_peers)}
    await websocket.send_text(json.dumps(initial_data))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
