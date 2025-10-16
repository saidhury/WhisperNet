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

### Prerequisites
Ensure you have the following installed:
*   C++ Compiler (GCC/Clang/MSVC) & CMake
*   Python 3.8+
*   Node.js & npm

### Installation & Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/saidhury/WhisperNet.git
    cd whispernet
    ```

2.  **Build the C++ Core and run the dev environment:**
    ```bash
    # Make scripts executable (Linux/macOS)
    chmod +x scripts/*.sh

    # Build the core shared library
    ./scripts/build_core.sh

    # Auto-install dependencies and run backend/frontend
    ./scripts/run_dev.sh
    ```

3.  **Access the UI:**
    Open your browser to `http://localhost:5173`.

---

## 🎃 Hacktoberfest

We welcome contributions! If you are looking to participate in Hacktoberfest, check out the `Issues` tab for tasks labeled `good first issue`.

Please read `CONTRIBUTING.md` (coming soon) before submitting a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
