# WhisperNet Developer Guide

This document contains instructions for setting up the development environment, running the developer server, testing multiple instances locally, and compiling/bundling standalone executables.

---

## 🧰 Development Prerequisites

To set up the development environment and compile the C++ core library, you need:

| Dependency | Minimum Version | Purpose |
|-------------|------------------|----------|
| **C++ Compiler** | GCC / Clang / MSVC | Compiles the C++ core library for UDP networking |
| **CMake** | 3.10+ | Generates C++ project build configurations |
| **Python** | 3.8+ | Runs the FastAPI API backend and tooling scripts |
| **Node.js (LTS)** | 18.x+ | Runs the React (Vite) frontend UI |
| **npm** | Included with Node.js | Installs frontend node package dependencies |

### Operating System Setup

*   **Linux / Ubuntu**
    ```bash
    sudo apt update
    sudo apt install build-essential cmake python3 python3-pip python3-venv python3-dev nodejs npm
    ```
*   **macOS**
    ```bash
    brew install cmake python node
    ```
*   **Windows**
    - Install Visual Studio Build Tools (select the *Desktop development with C++* workload).
    - Install Python 3.8+, Node.js LTS, and CMake. Make sure they are added to your system `PATH`.
*   **Android (via Termux)**
    Open Termux and run:
    ```bash
    pkg update
    pkg install clang cmake make python python-pip nodejs-lts git
    ```

---

## ⚙️ Running the Development Server

WhisperNet includes a platform-agnostic development runner that automatically handles CMake compilation, virtual environment setups, package dependencies, and starts both backend and frontend servers in parallel:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/saidhury/WhisperNet.git
    cd WhisperNet
    ```
2. **Launch the development runner**:
    ```bash
    python scripts/run_dev.py
    ```
3. **Access the interface**:
    Open your web browser and navigate to **[http://localhost:5173](http://localhost:5173)**.

---

## 👥 Running Multiple Local Instances (Multi-Instance Testing)

To test peer discovery and messaging on a single device, you can start multiple instances side-by-side on different ports. Use environment variables to configure each instance:

### Instance 1 (Alice)
*   **Windows (PowerShell)**:
    ```powershell
    $env:NICKNAME="Alice"; $env:API_PORT="8000"; $env:WEB_PORT="5173"; python scripts/run_dev.py
    ```
*   **Linux / macOS / Android**:
    ```bash
    NICKNAME=Alice API_PORT=8000 WEB_PORT=5173 python scripts/run_dev.py
    ```

### Instance 2 (Bob)
*   **Windows (PowerShell)**:
    ```powershell
    $env:NICKNAME="Bob"; $env:API_PORT="8001"; $env:WEB_PORT="5174"; python scripts/run_dev.py
    ```
*   **Linux / macOS / Android**:
    ```bash
    NICKNAME=Bob API_PORT=8001 WEB_PORT=5174 python scripts/run_dev.py
    ```

They will automatically discover each other locally using their unique port assignments.

---

## 📦 Building Standalone Executables (Release Bundling)

To package the application into a single, double-clickable executable (bundling the Python backend, React frontend static pages, and the C++ shared library):

1. Run the build release script:
   ```bash
   python scripts/build_release.py
   ```
2. The compiled standalone executable is generated in the root directory:
   - **Windows**: `whispernet.exe`
   - **Linux/macOS/Termux**: `whispernet`

---

## 🚀 How to Publish a GitHub Release

Follow these steps to upload the compiled binaries and publish a new release of WhisperNet on GitHub:

1. **Compile the standalone binary**:
   Run the build script on the target platform (e.g., Windows to build `.exe`, Linux to build a Linux binary) to generate the executable.
2. **Go to GitHub**:
   Navigate to the [saidhury/WhisperNet](https://github.com/saidhury/WhisperNet) repository on GitHub.
3. **Open the Releases page**:
   Click on the **Releases** tab on the right sidebar (or navigate to `/releases`).
4. **Draft a new release**:
   Click the **Draft a new release** button.
5. **Create a tag & title**:
   - Tag version: type a new version tag (e.g., `v1.0.0`) and select "Create new tag".
   - Release title: e.g., `WhisperNet v1.0.0 Release`.
6. **Upload the binaries**:
   Drag and drop your compiled standalone executable (`whispernet.exe` or `whispernet`) into the file uploader area under the description box.
7. **Publish**:
   Review the release details and click **Publish release**. Users will now be able to download and run the executable directly from your repository!
