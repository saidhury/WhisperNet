# WhisperNet

<p align="center">
  <img width="759" height="123" alt="image" src="https://github.com/user-attachments/assets/b2e31e3b-16a5-43e3-b828-a4e85e7d8a48" />
  <br>
  <strong>Serverless Local P2P Messenger</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Core-C++17-00599C?logo=c%2B%2B" alt="C++">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-React_Vite-61DAFB?logo=react" alt="React">
  <img src="https://img.shields.io/github/license/saidhury/WhisperNet" alt="License">
</p>

---

WhisperNet is a proof-of-concept local area network messenger. It utilizes a high-performance C++ core for UDP broadcasts and messaging, allowing for serverless, decentralized communication between users on the same network. No internet connection required.

## ✨ Features

*   **Serverless:** No central server required; fully peer-to-peer.
*   **Auto-Discovery:** Automatically finds other WhisperNet users on your LAN.
*   **Hybrid Architecture:** Combines raw C++ networking speed with a modern React UI.
*   **Retro UI:** Terminal-inspired interface.

<img width="1914" height="1079" alt="image" src="https://github.com/user-attachments/assets/3f3456b7-5191-45e3-9c97-f8a38085630d" />


## 🚀 Getting Started

### 🧰 Prerequisites

Before running WhisperNet, make sure you have the following dependencies installed:

| Dependency | Minimum Version | Purpose |
|-------------|------------------|----------|
| **C++ Compiler** | GCC / Clang / MSVC | Compiles the C++ core for UDP messaging |
| **CMake** | 3.10+ | Generates build files for the C++ core |
| **Python** | 3.8+ | Runs the FastAPI backend |
| **Node.js (LTS)** | 18.x+ | Runs the React (Vite) frontend |
| **npm** | Included with Node.js | Installs frontend dependencies |

**Quick setup tips:**
- **Linux / Ubuntu**
  ```bash
  sudo apt update
  sudo apt install build-essential cmake python3 python3-pip nodejs npm
- **macOS**
  ```bash
  brew install cmake python node
- **Windows**
  
  Install Visual Studio Build Tools (select Desktop development with C++).
  
  Install Python 3.8 or higher and Node.js LTS
  
  Make sure all tools are added to your PATH.

### ⚙️ Installation & Run

1. **Clone the repository**
    ```bash
    git clone https://github.com/saidhury/WhisperNet.git
    cd whispernet
    ```
    > Clones the repository from GitHub and enters the project directory.

2. **Make scripts executable (Linux/macOS only)**
    ```bash
    chmod +x scripts/*.sh
    ```
    > Grants execute permission to all shell scripts in the `scripts/` folder.  
    > Windows users can skip this step or use Git Bash.

3. **Build the C++ Core**
    ```bash
    ./scripts/build_core.sh
    ```
    > Runs CMake to compile the C++ networking core into a shared library (`.so` / `.dll`).  
    > This component handles UDP broadcast, discovery, and peer-to-peer messaging.

4. **Run the development environment**
    ```bash
    ./scripts/run_dev.sh
    ```
    > Installs all backend and frontend dependencies and launches both:
    > - FastAPI backend (Uvicorn server)
    > - React frontend (Vite dev server)

5. **Access the UI**
    Open your browser and navigate to **[http://localhost:5173](http://localhost:5173)**.

### ✅ Verification

After running `./scripts/run_dev.sh`, verify that everything started correctly:

1. **Check terminal output**
   - You should see backend logs like:
     ```
     INFO:     Uvicorn running on http://127.0.0.1:8000
     INFO:     Application startup complete.
     ```
   - And frontend logs like:
     ```
     VITE vX.Y.Z  ready in 300ms
     ➜  Local:   http://localhost:5173/
     ```
2. **Open the browser**
   - Visit **http://localhost:5173**
   - The WhisperNet UI should load (terminal-inspired chat interface).

3. **Test LAN connectivity**
   - Run WhisperNet on another device on the same network — both should discover each other automatically.

---

## 🎃 Hacktoberfest

We welcome contributions! If you are looking to participate in Hacktoberfest, check out the `Issues` tab for tasks labeled `good first issue`.

Please read `CONTRIBUTING.md` (coming soon) before submitting a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
