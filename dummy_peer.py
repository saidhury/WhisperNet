import requests
import json
import time

BACKEND_URL = "http://localhost:8000/api"
FAKE_PEER_IP = "192.168.1.99"

def simulate_discovery():
    try:
        requests.post(f"{BACKEND_URL}/test/discover", json={"sender_ip": FAKE_PEER_IP})
        print(f"--> Sent fake discovery from {FAKE_PEER_IP}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the backend. Is it running? {e}")

def simulate_message(content):
    try:
        requests.post(f"{BACKEND_URL}/test/message", json={"sender_ip": FAKE_PEER_IP, "content": content})
        print(f"--> Sent fake message from {FAKE_PEER_IP}: {content}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the backend. Is it running? {e}")

def main():
    print("--- WhisperNet Final Test Peer ---")
    print(f"Will simulate a peer with IP: {FAKE_PEER_IP}")
    print("\nCommands:")
    print("  'discover' - Makes the fake peer appear in the main app.")
    print("  Anything else will be sent as a chat message from the fake peer.")
    print("  'exit' to quit.")
    print("-" * 34)

    while True:
        user_input = input("FinalTestPeer> ")
        if user_input.lower() == 'exit':
            break
        if user_input.lower() == 'discover':
            simulate_discovery()
        else:
            simulate_message(user_input)

if __name__ == "__main__":
    main()
