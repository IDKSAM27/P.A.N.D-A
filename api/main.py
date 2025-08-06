import os
import sys
import pandas as pd
from dotenv import load_dotenv
import io
import uuid
import logging
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline
from app.models.result import Result

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Custom Logging Handler for WebSockets ---
class WebSocketLogHandler(logging.Handler):
    def __init__(self, manager: ConnectionManager):
        super().__init__()
        self.manager = manager

    def emit(self, record):
        log_entry = self.format(record)
        # We need to run the async broadcast in a non-async context
        import asyncio
        asyncio.run(self.manager.broadcast(log_entry))

# --- Configure Root Logger ---
# This captures logs from your entire application and sends them to the WebSocket
log_handler = WebSocketLogHandler(manager)
log_formatter = logging.Formatter("[%(levelname)s] %(message)s")
log_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler(), # This will keep logging to the console as well
    log_handler            # This adds our custom WebSocket handler
])

# --- Initialization ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

app = FastAPI(title="Voice Data Assistant API", version="1.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

dataframes_cache = {}

class CommandRequest(BaseModel):
    session_id: str
    command: str

# --- API Endpoints ---
@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    # ... (this endpoint code remains the same)
    logging.info(f"-> [API] Uploaded '{file.filename}'. Assigned Session ID: {session_id}")


@app.post("/analyze", response_model=Result)
async def analyze_command(request: CommandRequest):
    # ... (this endpoint code remains the same)
    logging.info(f"-> [API] Received command for Session ID {session_id}: '{command}'")


# --- WebSocket Endpoint ---
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logging.info("Frontend terminal connected.")
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Frontend terminal disconnected.")

