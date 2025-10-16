# 🛰️ WhisperNet - A Local P2P Messenger

WhisperNet is a proof-of-concept local area network messenger. It uses UDP broadcasts for peer discovery, allowing for serverless communication between users on the same network.

## Architecture Overview

`Web UI (React) <--> Backend (FastAPI) <--> Core Engine (C++) <--> LAN Peers`

## Getting Started

1.  **Clone the repository.**
    `git clone <repo-url>`

2.  **Build the C++ Core.**
    `chmod +x scripts/*.sh`
    `./scripts/build_core.sh`

3.  **Run the development environment.**
    `./scripts/run_dev.sh`

4.  Open your browser to `http://localhost:5173` (or whatever port Vite uses).
