import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
from bindings import core_lib

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
                discovered_peers.add(sender_ip_str)
                update_message = {"type": "PEER_LIST_UPDATE", "payload": list(discovered_peers)}
                if loop: asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(update_message)), loop)
        elif data.get("type") == "MESSAGE":
             update_message = {"type": "NEW_MESSAGE", "payload": {"sender": sender_ip_str, "content": data.get("content")}}
             if loop: asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(update_message)), loop)
    except (json.JSONDecodeError, RuntimeError): pass

@router.post("/send")
async def send_message(message: dict):
    recipient_ip = message.get('recipient_ip')
    content = message.get('content')
    payload = {"type": "MESSAGE", "content": content}
    message_bytes = json.dumps(payload).encode('utf-8')
    core_lib.send_udp_message(message_bytes, recipient_ip.encode('utf-8'), 8888)
    return {"status": "message sent"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_text(json.dumps({"type": "PEER_LIST_UPDATE", "payload": list(discovered_peers)}))
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)
