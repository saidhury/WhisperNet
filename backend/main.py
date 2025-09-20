import uvicorn
import asyncio
from fastapi import FastAPI
import api 
from bindings import core_lib, ON_MESSAGE_RECEIVED_FUNC

UDP_PORT = 8888
c_callback_handler = ON_MESSAGE_RECEIVED_FUNC(api.handle_incoming_message)

app = FastAPI(title="WhisperNet Backend")

@app.on_event("startup")
async def startup_event():
    print("Starting WhisperNet core...")
    core_lib.start_udp_listener(UDP_PORT, c_callback_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
