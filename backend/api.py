import asyncio
import ctypes
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import threading
import json
import time
import os
# from bindings import core_lib
from backend.bindings import core_lib
import ifaddr
from backend import config

BROADCAST_IP = '255.255.255.255'
PEER_TIMEOUT = int(os.getenv("PEER_TIMEOUT", "15"))
PEER_CHECK_INTERVAL = int(os.getenv("PEER_CHECK_INTERVAL", "5"))
MY_LISTENING_PORT = 8888

def get_all_own_ips():
    ips = []
    # 1. Use pure-Python ifaddr (no C compiler or dev headers required)
    try:
        adapters = ifaddr.get_adapters()
        for adapter in adapters:
            for ip in adapter.ips:
                if isinstance(ip.ip, str):
                    if ip.ip != '127.0.0.1':
                        ips.append(ip.ip)
    except Exception as e:
        print("Warning: Failed to retrieve adapters via ifaddr:", e)

    # 2. Add C++ primary routed IP via the new function
    ip_buffer = ctypes.create_string_buffer(64)
    if core_lib.get_local_ip(ip_buffer, 64):
        primary_ip = ip_buffer.value.decode('utf-8')
        if primary_ip not in ips and primary_ip != '127.0.0.1':
            ips.append(primary_ip)

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

def handle_incoming_message(message: bytes, sender_ip: bytes, sender_port: int):
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')

    try:
        data = json.loads(message.decode('utf-8', errors='ignore'))
        
        listening_port = data.get("port") if isinstance(data, dict) else None
        if listening_port is None:
            listening_port = sender_port

        is_self = (sender_ip_str in OWN_IPS or sender_ip_str == "127.0.0.1") and listening_port == MY_LISTENING_PORT
        if is_self: 
            return

        nickname = data.get("nickname") or data.get("sender_nick") or f"{sender_ip_str}:{listening_port}"
        peer_key = f"{sender_ip_str}:{listening_port}"
        
        if data.get("type") == "DISCOVERY_REQUEST":
            if data.get("version") != config.PROTOCOL_VERSION:
                return

            peer_updated = False
            
            with _peers_lock:
                if sender_ip_str != "127.0.0.1":
                    loopback_key = f"127.0.0.1:{listening_port}"
                    if loopback_key in discovered_peers:
                        discovered_peers.pop(loopback_key, None)
                        peer_updated = True
                elif sender_ip_str == "127.0.0.1":
                    has_lan_peer = any(
                        p["port"] == listening_port and p["ip"] != "127.0.0.1"
                        for p in discovered_peers.values()
                    )
                    if has_lan_peer:
                        return

                current_peer_data = discovered_peers.get(peer_key)
                if not current_peer_data or current_peer_data.get("nickname") != nickname:
                    peer_updated = True
                
                discovered_peers[peer_key] = {
                    "ip": sender_ip_str,
                    "port": listening_port,
                    "nickname": nickname,
                    "last_seen": time.monotonic()
                }

            if peer_updated:
                print(f"Discovered/updated peer: {peer_key} -> {nickname}")
                _broadcast_peer_update()

            # --- DISCOVERY HANDSHAKE REPLY ---
            # Send a direct unicast reply back to the sender's dynamic listening port
            reply_payload = {
                "type": "DISCOVERY_REPLY",
                "nickname": config.NICKNAME,
                "version": config.PROTOCOL_VERSION,
                "port": MY_LISTENING_PORT
            }
            core_lib.send_udp_message(
                json.dumps(reply_payload).encode("utf-8"),
                sender_ip_str.encode("utf-8"),
                listening_port
            )

        elif data.get("type") == "DISCOVERY_REPLY":
            if data.get("version") != config.PROTOCOL_VERSION:
                return

            peer_updated = False
            
            with _peers_lock:
                if sender_ip_str != "127.0.0.1":
                    loopback_key = f"127.0.0.1:{listening_port}"
                    if loopback_key in discovered_peers:
                        discovered_peers.pop(loopback_key, None)
                        peer_updated = True
                elif sender_ip_str == "127.0.0.1":
                    has_lan_peer = any(
                        p["port"] == listening_port and p["ip"] != "127.0.0.1"
                        for p in discovered_peers.values()
                    )
                    if has_lan_peer:
                        return

                current_peer_data = discovered_peers.get(peer_key)
                if not current_peer_data or current_peer_data.get("nickname") != nickname:
                    peer_updated = True
                
                discovered_peers[peer_key] = {
                    "ip": sender_ip_str,
                    "port": listening_port,
                    "nickname": nickname,
                    "last_seen": time.monotonic()
                }

            if peer_updated:
                print(f"Discovered/updated peer (via reply): {peer_key} -> {nickname}")
                _broadcast_peer_update()

        elif data.get("type") == "MESSAGE":
            update_message = {
                "type": "NEW_MESSAGE", 
                "payload": {"sender": peer_key, "content": data.get("content"), "sender_nick": nickname}
            }
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
            stale_keys = [key for key, data in discovered_peers.items() if current_time - data["last_seen"] > PEER_TIMEOUT]
            if stale_keys:
                print(f"Removing stale peers: {stale_keys}")
                for key in stale_keys:
                    discovered_peers.pop(key, None)
                stale_peers_found = True
        if stale_peers_found:
            _broadcast_peer_update()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/peers")
async def get_peers():
    with _peers_lock:
        return [
            {"ip": f"{data['ip']}:{data['port']}", "nickname": data["nickname"]} 
            for data in discovered_peers.values()
        ]

@router.post("/send")
async def send_message(message: dict):
    recipient_ip, content = message.get('recipient_ip'), message.get('content')
    if not recipient_ip or not content:
        return {"status": "error", "detail": "Missing recipient_ip or content"}
    
    # Extract IP and Port from the UI string key "IP:PORT"
    try:
        ip_part, port_part = recipient_ip.split(":")
        target_port = int(port_part)
    except ValueError:
        # Fallback to defaults if no port is present
        ip_part = recipient_ip
        target_port = 8888

    payload = {"type": "MESSAGE", "content": content, "port": MY_LISTENING_PORT}
    core_lib.send_udp_message(
        json.dumps(payload).encode('utf-8'), 
        ip_part.encode('utf-8'), 
        target_port
    )
    print(f"Sent message to {ip_part}:{target_port}: {content}")
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
        try:
            ip_part, port_part = sender_ip.split(":")
            port = int(port_part)
        except ValueError:
            ip_part = sender_ip
            port = 8888
        nickname = data.get('nickname') or sender_ip
        discovered_peers[sender_ip] = {
            "ip": ip_part,
            "port": port,
            "nickname": nickname,
            "last_seen": time.monotonic()
        }
        _broadcast_peer_update()
    return {"status": "ok"}

@router.post("/test/message")
async def test_message(data: dict):
    sender_ip, content = data.get('sender_ip'), data.get('content')
    update = {"type": "NEW_MESSAGE", "payload": {"sender": sender_ip, "content": content}}
    await manager.broadcast(json.dumps(update))
    return {"status": "ok"}