import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import threading
import json
import time
import os
from bindings import core_lib
import netifaces
from backend import config

BROADCAST_IP = '255.255.255.255'
PEER_TIMEOUT = int(os.getenv("PEER_TIMEOUT", "15"))
PEER_CHECK_INTERVAL = int(os.getenv("PEER_CHECK_INTERVAL", "5"))

def get_all_own_ips():
    ips = []
    for interface in netifaces.interfaces():
        try:
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for addr_info in addresses[netifaces.AF_INET]:
                    ip = addr_info.get('addr')
                    if ip and ip != '127.0.0.1':
                        ips.append(ip)
        except ValueError:
            pass
    return ips

OWN_IPS = get_all_own_ips()
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

# Data structure to hold all peer info, combining both features
discovered_peers: Dict[str, Dict] = {} # Maps IP -> {"nickname": str, "last_seen": float}
_peers_lock = threading.Lock()

def _broadcast_peer_update():
    """Helper to safely build and broadcast the current peer list."""
    with _peers_lock:
        peers_payload = [{"ip": ip, "nickname": data["nickname"]} for ip, data in discovered_peers.items()]
    
    update_message = {"type": "PEER_LIST_UPDATE", "payload": peers_payload}
    
    if loop:
        fut = asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(update_message)), loop)
        fut.add_done_callback(lambda f: (exc := f.exception()) and print(f"[broadcast error] {exc}"))

def handle_incoming_message(message: bytes, sender_ip: bytes):
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')
    if sender_ip_str in OWN_IPS: return

    try:
        data = json.loads(message.decode('utf-8', errors='ignore'))
        
        if data.get("type") == "DISCOVERY":
            if data.get("version") != config.PROTOCOL_VERSION:
                print(f"Ignoring peer {sender_ip_str} with incompatible version.")
                return

            nickname = data.get("nickname") or sender_ip_str
            
            peer_updated = False
            with _peers_lock:
                current_peer_data = discovered_peers.get(sender_ip_str)
                if not current_peer_data or current_peer_data.get("nickname") != nickname:
                    peer_updated = True
                
                discovered_peers[sender_ip_str] = {
                    "nickname": nickname,
                    "last_seen": time.monotonic()
                }

            if peer_updated:
                print(f"Discovered/updated peer: {sender_ip_str} -> {nickname}")
                _broadcast_peer_update()

        elif data.get("type") == "MESSAGE":
            update_message = {"type": "NEW_MESSAGE", "payload": {"sender": sender_ip_str, "content": data.get("content")}}
            if loop:
                asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(update_message)), loop)

    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Error processing incoming message: {e}")

async def check_stale_peers_task():
    """Periodically checks for and removes stale peers."""
    while True:
        await asyncio.sleep(PEER_CHECK_INTERVAL)
        stale_peers_found = False
        with _peers_lock:
            current_time = time.monotonic()
            stale_peers = [ip for ip, data in discovered_peers.items() if current_time - data["last_seen"] > PEER_TIMEOUT]
            if stale_peers:
                print(f"Removing stale peers: {stale_peers}")
                for peer in stale_peers:
                    discovered_peers.pop(peer, None)
                stale_peers_found = True
        if stale_peers_found:
            _broadcast_peer_update()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/peers")
async def get_peers():
    with _peers_lock:
        return [{"ip": ip, "nickname": data["nickname"]} for ip, data in discovered_peers.items()]

@router.post("/send")
async def send_message(message: dict):
    # This endpoint remains largely the same
    recipient_ip, content = message.get('recipient_ip'), message.get('content')
    if not recipient_ip or not content:
        return {"status": "error", "detail": "Missing recipient_ip or content"}
    
    payload = {"type": "MESSAGE", "content": content}
    core_lib.send_udp_message(json.dumps(payload).encode('utf-8'), recipient_ip.encode('utf-8'), 8888)
    print(f"Sent message to {recipient_ip}: {content}")
    return {"status": "message sent"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    with _peers_lock:
        peers_payload = [{"ip": ip, "nickname": data["nickname"]} for ip, data in discovered_peers.items()]
    initial_data = {"type": "PEER_LIST_UPDATE", "payload": peers_payload}
    await websocket.send_text(json.dumps(initial_data))
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/test/discover")
async def test_discover(data: dict):
    # This test endpoint does not need to be thread-safe
    sender_ip = data.get('sender_ip')
    if sender_ip:
        nickname = data.get('nickname') or sender_ip
        discovered_peers[sender_ip] = {"nickname": nickname, "last_seen": time.monotonic()}
        _broadcast_peer_update()
    return {"status": "ok"}

@router.post("/test/message")
async def test_message(data: dict):
    sender_ip, content = data.get('sender_ip'), data.get('content')
    update = {"type": "NEW_MESSAGE", "payload": {"sender": sender_ip, "content": content}}
    await manager.broadcast(json.dumps(update))
    return {"status": "ok"}