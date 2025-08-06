import os
import sys
import pandas as pd
from dotenv import load_dotenv
import io
import uuid
import logging
from typing import List
import asyncio

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
        # --- FIX: Use create_task instead of asyncio.run() ---
        # This correctly schedules the async task on the running event loop.
        asyncio.create_task(self.manager.broadcast(log_entry))

# --- Configure Root Logger ---
log_handler = WebSocketLogHandler(manager)
log_formatter = logging.Formatter("[%(levelname)s] %(message)s")
log_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler(),
    log_handler
])

# --- Initialization ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

app = FastAPI(title="P.A.N.D-A API", version="1.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

dataframes_cache = {}

class CommandRequest(BaseModel):
    session_id: str
    command: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the P.A.N.D-A (Pandas Assistant for Natural Data-Analytics) API."}

# --- FIX: Re-added the full, correct code for this endpoint ---
@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        session_id = str(uuid.uuid4())
        dataframes_cache[session_id] = df
        
        logging.info(f"-> [API] Uploaded '{file.filename}'. Assigned Session ID: {session_id}")
        
        return {
            "message": f"File '{file.filename}' uploaded successfully.",
            "session_id": session_id,
            "columns": df.columns.tolist(),
            "shape": df.shape
        }
    except Exception as e:
        logging.error(f"-> [API] Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {e}")

@app.post("/analyze", response_model=Result)
async def analyze_command(request: CommandRequest):
    session_id = request.session_id
    command = request.command
    
    logging.info(f"-> [API] Received command for Session ID {session_id}: '{command}'")
    
    if session_id not in dataframes_cache:
        raise HTTPException(status_code=404, detail="Session ID not found.")
    
    df = dataframes_cache[session_id]
    
    try:
        result = pipeline.run(command, df)
        if result.result_type == 'error':
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        logging.error(f"-> [API] Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- WebSocket Endpoint ---
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logging.info("Frontend terminal connected.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Frontend terminal disconnected.")
