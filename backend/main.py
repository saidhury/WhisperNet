import sys
import os
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import uvicorn
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv 
from backend import api
from backend.bindings import core_lib, ON_MESSAGE_RECEIVED_FUNC
from backend import config

load_dotenv()

UDP_PORT = 8888
ACTUAL_UDP_PORT = 8888
MULTICAST_IP = b"239.255.255.250" # Modern Router-Friendly IP
c_callback_handler = ON_MESSAGE_RECEIVED_FUNC(api.handle_incoming_message)

app = FastAPI(title="WhisperNet Backend")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")

# Serve static frontend assets if the static directory exists
meipass = getattr(sys, "_MEIPASS", None)
if meipass:
    static_dir = os.path.abspath(os.path.join(meipass, "static"))
else:
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        if catchall.startswith("api") or catchall.startswith("ws"):
            return None
        local_path = os.path.join(static_dir, catchall)
        if os.path.exists(local_path) and os.path.isfile(local_path):
            return FileResponse(local_path)
        return FileResponse(os.path.join(static_dir, "index.html"))

async def discover_peers_task():
    """Sends out discovery packets using Broadcast, Multicast, and Localhost."""
    while True:
        discovery_payload = {
            "type": "DISCOVERY_REQUEST",
            "nickname": config.NICKNAME,
            "version": config.PROTOCOL_VERSION,
            "port": ACTUAL_UDP_PORT 
        }
        discovery_message = json.dumps(discovery_payload).encode("utf-8")
        
        # 1. Broadast via the new C++ function (shouts to whole subnet)
        core_lib.send_broadcast_message(discovery_message, UDP_PORT)

        # 2. Multicast via the new C++ Multicast feature (bypasses restrictive routers)
        core_lib.send_udp_message(discovery_message, MULTICAST_IP, UDP_PORT)
        
        # 3. Localhost (Guarantees loopback works if no internet connection exists)
        core_lib.send_udp_message(discovery_message, b"127.0.0.1", UDP_PORT)
        
        await asyncio.sleep(5)
        
@app.on_event("startup")
async def startup_event():
    global ACTUAL_UDP_PORT
    print("Starting WhisperNet core...")
    api.loop = asyncio.get_running_loop()

    # Start the core listener (Removed duplicate call)
    bound_port = core_lib.start_udp_listener(UDP_PORT, c_callback_handler)
    
    if bound_port > 0:
        ACTUAL_UDP_PORT = bound_port
        api.MY_LISTENING_PORT = bound_port 
        print(f"Successfully bound UDP listener to port: {ACTUAL_UDP_PORT}")

        # Join the Multicast group
        if core_lib.join_multicast_group(MULTICAST_IP):
            print(f"Successfully joined Multicast Group: {MULTICAST_IP.decode('utf-8')}")
        else:
            print("Warning: Failed to join Multicast Group.")
    else:
        print("CRITICAL: Failed to bind C++ UDP listener.")
    
    # Start tasks
    asyncio.create_task(discover_peers_task())
    asyncio.create_task(api.check_stale_peers_task()) 

    # Open default browser automatically if running in PyInstaller bundled mode
    if getattr(sys, "frozen", False):
        import webbrowser
        port = int(os.environ.get("API_PORT", 8000))
        
        async def open_browser():
            await asyncio.sleep(1.5)
            webbrowser.open(f"http://127.0.0.1:{port}")
            
        asyncio.create_task(open_browser())

@app.on_event("shutdown")
async def shutdown_event():
    print("Stopping WhisperNet core...")
    core_lib.stop_udp_listener()

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)