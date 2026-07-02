import os
import sys
import subprocess
import hashlib
import time

def get_hash(filepath):
    if not os.path.exists(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)

    print("=== Ensuring backend virtualenv exists ===")
    venv_dir = os.path.join("backend", ".venv")
    
    # Determine paths inside virtualenv
    if os.name == "nt":
        venv_python = os.path.abspath(os.path.join(venv_dir, "Scripts", "python.exe"))
        venv_pip = os.path.abspath(os.path.join(venv_dir, "Scripts", "pip.exe"))
    else:
        venv_python = os.path.abspath(os.path.join(venv_dir, "bin", "python"))
        venv_pip = os.path.abspath(os.path.join(venv_dir, "bin", "pip"))

    if not os.path.exists(venv_python):
        print("Creating virtual environment...")
        if os.path.exists(venv_dir):
            import shutil
            shutil.rmtree(venv_dir, ignore_errors=True)
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Install Python dependencies if needed
    req_file = os.path.join("backend", "requirements.txt")
    req_hash_file = os.path.join(venv_dir, ".requirements_hash")
    current_req_hash = get_hash(req_file)
    prev_req_hash = ""
    if os.path.exists(req_hash_file):
        with open(req_hash_file, "r") as f:
            prev_req_hash = f.read().strip()

    if current_req_hash != prev_req_hash:
        print("Installing/updating Python packages...")
        subprocess.run([venv_pip, "install", "-r", req_file], check=True)
        with open(req_hash_file, "w") as f:
            f.write(current_req_hash)
    else:
        print("Python dependencies up-to-date.")

    print("=== Configuring and compiling C++ Core Library ===")
    subprocess.run(["cmake", "-S", "core", "-B", "build/core"], check=True)
    subprocess.run(["cmake", "--build", "build/core", "--config", "Debug"], check=True)

    # Install Frontend dependencies if needed
    pkg_file = os.path.join("webui", "package.json")
    node_hash_file = os.path.join("webui", ".node_deps_hash")
    node_modules_dir = os.path.join("webui", "node_modules")
    current_pkg_hash = get_hash(pkg_file)
    prev_pkg_hash = ""
    if os.path.exists(node_hash_file):
        with open(node_hash_file, "r") as f:
            prev_pkg_hash = f.read().strip()

    if not os.path.isdir(node_modules_dir) or current_pkg_hash != prev_pkg_hash:
        print("Installing/updating frontend npm packages...")
        # Use shell=True for npm/npx on Windows
        subprocess.run("npm install", cwd="webui", shell=True, check=True)
        with open(node_hash_file, "w") as f:
            f.write(current_pkg_hash)
    else:
        print("Frontend dependencies up-to-date.")

    # Ports configurations
    api_port = os.getenv("API_PORT", "8000")
    web_port = os.getenv("WEB_PORT", "5173")
    nickname = os.getenv("NICKNAME", "DefaultUser")

    print(f"=== Starting WhisperNet for {nickname} (API Port: {api_port}, Web UI Port: {web_port}) ===")

    # Setup environment variables for subprocesses
    env = os.environ.copy()
    env["API_PORT"] = api_port
    env["WEB_PORT"] = web_port
    env["NICKNAME"] = nickname

    # Start backend
    backend_cmd = [venv_python, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", api_port]
    backend_proc = subprocess.Popen(backend_cmd, cwd="backend", env=env)

    # Wait a few seconds for backend to start up
    print("Waiting for backend to spin up...")
    time.sleep(3)

    # Start frontend
    frontend_cmd = f"npx vite --port {web_port}"
    frontend_proc = subprocess.Popen(frontend_cmd, cwd="webui", env=env, shell=True)

    print("\nWhisperNet Dev processes started.")
    print("Press Ctrl+C to terminate.")

    # Handle graceful exit
    procs = [backend_proc, frontend_proc]
    try:
        while True:
            # Poll processes to make sure they are still alive
            for p in procs:
                if p.poll() is not None:
                    print(f"Subprocess terminated with exit code {p.returncode}")
                    return
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dev processes...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("All processes cleaned up.")

if __name__ == "__main__":
    main()
