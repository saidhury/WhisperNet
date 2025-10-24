import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import threading
import json
import socket
import time
from bindings import core_lib
import netifaces
import os
from backend import config

BROADCAST_IP = '255.255.255.255'
PEER_TIMEOUT = int(os.getenv("PEER_TIMEOUT", "15"))  # Seconds until a peer is considered stale
PEER_CHECK_INTERVAL = int(os.getenv("PEER_CHECK_INTERVAL", "5")) # How often to check for stale peers

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

discovered_peers: Dict[str, float] = {} # Maps IP to last_seen timestamp (monotonic)
discovered_peers_lock = threading.Lock()

def _update_peer_last_seen(ip: str) -> tuple[bool, list[str]]:
    """
    Updates a peer's last seen time and returns whether it was a new peer.
    Returns (is_new_peer, peers_snapshot) under lock.
    """
    is_new = False
    peers_snapshot = []
    with discovered_peers_lock:
        if ip not in discovered_peers:
            is_new = True
        discovered_peers[ip] = time.monotonic()
        if is_new:
            peers_snapshot = list(discovered_peers.keys())
    return is_new, peers_snapshot

def handle_incoming_message(message: bytes, sender_ip: bytes):
    global loop
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')
    message_str = message.decode('utf-8', errors='ignore')

    if sender_ip_str in OWN_IPS:
        return 
    
    print(f"UDP message received from {sender_ip_str}: {message_str}")

    try:
        data = json.loads(message_str)
        if data.get("type") == "DISCOVERY":
            peer_version = data.get("version")
            if peer_version and peer_version != config.PROTOCOL_VERSION:
                print(
                    f"Warning: Discovered peer at {sender_ip_str} with incompatible protocol version {peer_version}. Self is version {config.PROTOCOL_VERSION}."
                )

            peer_list_updated, peers_snapshot = _update_peer_last_seen(sender_ip_str)

            if peer_list_updated and loop:
                update_message = {
                    "type": "PEER_LIST_UPDATE",
                    "payload": peers_snapshot
                }
                fut = asyncio.run_coroutine_threadsafe(
                    manager.broadcast(json.dumps(update_message)), 
                    loop
                )
                # Log broadcast errors without breaking the UDP thread
                fut.add_done_callback(lambda f: (exc := f.exception()) and print(f"[broadcast error] {exc}"))

        elif data.get("type") == "MESSAGE":
             update_message = {
                "type": "NEW_MESSAGE",
                "payload": {"sender": sender_ip_str, "content": data.get("content")}
             }
             if loop:
                fut = asyncio.run_coroutine_threadsafe(
                    manager.broadcast(json.dumps(update_message)),
                    loop
                )
                # Log broadcast errors without breaking the UDP thread
                fut.add_done_callback(lambda f: (exc := f.exception()) and print(f"[broadcast error] {exc}"))

    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Error processing incoming message: {e}")

async def check_stale_peers_task():
    """Periodically checks for and removes stale peers."""
    while True:
        await asyncio.sleep(PEER_CHECK_INTERVAL)
        
        stale_peers_found = False
        peers_snapshot = []
        with discovered_peers_lock:
            current_time = time.monotonic()
            stale_peers = [
                ip for ip, last_seen in discovered_peers.items() 
                if current_time - last_seen > PEER_TIMEOUT
            ]

            if stale_peers:
                print(f"Removing stale peers: {stale_peers}")
                for peer in stale_peers:
                    discovered_peers.pop(peer, None)
                stale_peers_found = True
                peers_snapshot = list(discovered_peers.keys())

        if stale_peers_found:
            update_message = {
                "type": "PEER_LIST_UPDATE",
                "payload": peers_snapshot
            }
            await manager.broadcast(json.dumps(update_message))

@router.get("/health")
async def health_check():
    """
    A simple endpoint to confirm that the API service is running.
    """
    return {"status": "ok"}

@router.get("/peers")
async def get_peers():
    with discovered_peers_lock:
        return list(discovered_peers.keys())

@router.post("/send")
async def send_message(message: dict):
    recipient_ip = message.get('recipient_ip')
    content = message.get('content')

    if not recipient_ip or not content:
        return {"status": "error", "detail": "Missing recipient_ip or content"}

    udp_port = 8888

    payload = {
        "type": "MESSAGE",
        "content": content
    }
    
    message_bytes = json.dumps(payload).encode('utf-8')
    recipient_ip_bytes = recipient_ip.encode('utf-8')

    core_lib.send_udp_message(message_bytes, recipient_ip_bytes, udp_port)
    
    print(f"Sent message to {recipient_ip}: {content}")
    return {"status": "message sent"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f"New client connected: {websocket.client.host}")
    with discovered_peers_lock:
        peers_snapshot = list(discovered_peers.keys())
    initial_data = {
        "type": "PEER_LIST_UPDATE",
        "payload": peers_snapshot
    }
    await websocket.send_text(json.dumps(initial_data))
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected: {websocket.client.host}")

@router.post("/test/discover")
async def test_discover(data: dict):
    sender_ip = data.get('sender_ip')
    if sender_ip:
        peer_list_updated, peers_snapshot = _update_peer_last_seen(sender_ip)
        
        if peer_list_updated:
            update = {"type": "PEER_LIST_UPDATE", "payload": peers_snapshot}
            await manager.broadcast(json.dumps(update))
    return {"status": "ok"}

@router.post("/test/message")
async def test_message(data: dict):
    sender_ip = data.get('sender_ip')
    content = data.get('content')
    update = {"type": "NEW_MESSAGE", "payload": {"sender": sender_ip, "content": content}}
    await manager.broadcast(json.dumps(update))
    return {"status": "ok"}
