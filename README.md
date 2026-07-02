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

WhisperNet is a decentralized local area network messenger. It uses high-performance C++ networking to enable direct, serverless communication between devices on your local network (Wi-Fi or LAN). No internet connection or central servers are required.

## ✨ Features

*   **Fully Local & Private:** All communication is peer-to-peer and never leaves your local network.
*   **Automatic Discovery:** Instantly detects other WhisperNet users on the same subnet without manual setup.
*   **Zero Configuration:** Start chatting immediately without registering accounts or configuring servers.
*   **Retro Terminal Theme:** Retro, terminal-inspired user interface designed to scale seamlessly onto both desktop and mobile screens.

<img width="1914" height="1079" alt="image" src="https://github.com/user-attachments/assets/3f3456b7-5191-45e3-9c97-f8a38085630d" />

## 🚀 Quick Start (No Setup Required)

To start chatting right away, download the precompiled standalone executable for your operating system:

1. Go to the [Releases](https://github.com/saidhury/WhisperNet/releases) page.
2. Download the version for your system:
   - **Windows**: `whispernet.exe`
   - **Linux/macOS**: `whispernet`
3. Launch the downloaded file:
   - **Windows**: Double-click `whispernet.exe`
   - **Linux/macOS**: Set executable permissions (`chmod +x whispernet`) and run `./whispernet`
4. The application will start the background listener and automatically open your default browser to the web chat interface (`http://127.0.0.1:8000`).

## 🛠️ Developer & Build Guide

For guides on how to clone the repository, compile the C++ core from source, run the development server, or build custom standalone binaries, see [DEVELOPMENT.md](DEVELOPMENT.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
