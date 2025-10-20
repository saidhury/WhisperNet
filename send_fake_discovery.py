import socket
import json
from backend import config

PORT = 8888
BROADCAST_IP = "255.255.255.255"

message = {
    "type": "DISCOVERY",
    "nickname": "FakePeer",
    "version": config.PROTOCOL_VERSION,
}

payload = json.dumps(message).encode("utf-8")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print(f"Sending discovery packet to port {PORT}...")
sock.sendto(payload, (BROADCAST_IP, PORT))
print("Packet sent!")
sock.close()
