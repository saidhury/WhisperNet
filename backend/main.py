import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import api 
from bindings import core_lib, ON_MESSAGE_RECEIVED_FUNC

UDP_PORT = 8888
c_callback_handler = ON_MESSAGE_RECEIVED_FUNC(api.handle_incoming_message)

app = FastAPI(title="WhisperNet Backend")

origins = [
    "http://localhost:5173",
    "http://12.0.0.1:5173",
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
    while True:
        discovery_message = '{"type": "DISCOVERY"}'
        broadcast_address = '192.168.56.255'.encode('utf-8')
        core_lib.send_udp_message(discovery_message.encode('utf-8'), broadcast_address, UDP_PORT)
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    print("Starting WhisperNet core...")
    api.loop = asyncio.get_running_loop()
    core_lib.start_udp_listener(UDP_PORT, c_callback_handler)
    asyncio.create_task(discover_peers_task())
    asyncio.create_task(api.check_stale_peers_task())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
