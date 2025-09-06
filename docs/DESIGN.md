# WhisperNet Design Document (v0.1)

## Architecture

WhisperNet will use a three-tier architecture:
1.  **Core Engine (C++):** For high-performance UDP socket handling and cryptography.
2.  **Backend (Python/FastAPI):** To bridge the C++ core to a web interface.
3.  **Frontend (React):** A simple web UI for user interaction.

## Protocol
- **Discovery:** Peers will send a UDP broadcast packet containing a simple JSON message `{"type": "DISCOVERY"}` every 5 seconds to port 8888.
- **Messaging:** Messages will be sent via UDP unicast to a peer's IP address, also on port 8888.
