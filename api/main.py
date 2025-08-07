import os
import sys
import pandas as pd
from dotenv import load_dotenv
import io
import uuid
import logging
import asyncio
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

# --- WebSocket and Logging Setup ---
class ConnectionManager:
    def __init__(self): self.active_connections: List[WebSocket] = []
    async def connect(self, ws: WebSocket): await ws.accept(); self.active_connections.append(ws)
    def disconnect(self, ws: WebSocket): self.active_connections.remove(ws)
    async def broadcast(self, msg: str): 
        for conn in self.active_connections: await conn.send_text(msg)
manager = ConnectionManager()

class WebSocketLogHandler(logging.Handler):
    def __init__(self, manager: ConnectionManager): super().__init__(); self.manager = manager
    def emit(self, record): asyncio.create_task(self.manager.broadcast(self.format(record)))
    
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), WebSocketLogHandler(manager)])
    
# --- Main Application Setup ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)
app = FastAPI(title="Voice Data Assistant API", version="1.3.2")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
dataframes_cache = {}

class CommandRequest(BaseModel):
    session_id: str
    command: str

def create_session(df: pd.DataFrame) -> dict:
    session_id = str(uuid.uuid4())
    dataframes_cache[session_id] = df
    return {
        "session_id": session_id,
        "columns": df.columns.tolist(),
        "shape": df.shape,
        "preview": df.head().to_dict(orient='records')
    }

# --- API Endpoints ---
@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        session_data = create_session(df)
        logging.info(f"-> [API] Uploaded '{file.filename}'. Session: {session_data['session_id']}")
        return session_data
    except Exception as e:
        logging.error(f"-> [API] Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sample_data")
async def load_sample_data():
    try:
        # --- DEFINITIVE FIX for File Path ---
        # Get the directory where this script (main.py) is located.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root.
        project_root = os.path.dirname(current_dir)
        # Construct the absolute path to the CSV file.
        sample_file_path = os.path.join(project_root, 'data', 'coffee.csv')
        
        logging.info(f"-> [API] Attempting to load sample data from: {sample_file_path}")
        
        df = pd.read_csv(sample_file_path)
        session_data = create_session(df)
        logging.info(f"-> [API] Loaded sample data. Session: {session_data['session_id']}")
        return session_data
    except FileNotFoundError:
        logging.error(f"-> [API] CRITICAL: Sample data file not found at expected path: {sample_file_path}")
        raise HTTPException(status_code=500, detail="Sample data file not found on server. Please check file location.")
    except Exception as e:
        logging.error(f"-> [API] Error loading sample data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=Result)
async def analyze_command(request: CommandRequest):
    session_id = request.session_id; command = request.command
    logging.info(f"-> [API] Received command for Session ID {session_id}: '{command}'")
    if session_id not in dataframes_cache:
        raise HTTPException(status_code=404, detail="Session ID not found.")
    df = dataframes_cache[session_id]
    try:
        result = pipeline.run(command, df)
        if result.result_type == 'error': raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        logging.error(f"-> [API] Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
