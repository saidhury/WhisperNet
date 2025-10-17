import uvicorn
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import api
from dotenv import load_dotenv
from bindings import core_lib, ON_MESSAGE_RECEIVED_FUNC
from backend import config

load_dotenv() 

UDP_PORT = 8888
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

async def discover_peers_task():
    """Sends out a single discovery packet periodically."""
    while True:
        discovery_payload = {
            "type": "DISCOVERY",
            "nickname": config.NICKNAME,
            "version": config.PROTOCOL_VERSION, # <-- Must include version
        }
        discovery_message = json.dumps(discovery_payload)
        broadcast_address = api.BROADCAST_IP.encode('utf-8')
        core_lib.send_udp_message(
            discovery_message.encode("utf-8"), broadcast_address, UDP_PORT
        )
        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    """Starts all necessary background tasks."""
    print("Starting WhisperNet core...")
    api.loop = asyncio.get_running_loop()
    core_lib.start_udp_listener(UDP_PORT, c_callback_handler)
    
    # Start all tasks correctly
    asyncio.create_task(discover_peers_task())
    asyncio.create_task(api.check_stale_peers_task()) # <-- Restore this task


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)