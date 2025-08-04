# voice_data_assistant/api/main.py

import os
import sys
import pandas as pd
from dotenv import load_dotenv
import io
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the project root to the Python path to allow imports from `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our application components
from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline
from app.models.result import Result

# --- Initialization ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

# Create the FastAPI app instance
app = FastAPI(
    title="Voice Data Assistant API",
    description="An API to process natural language commands against a dataset.",
    version="1.1.0"
)

# --- CORS Middleware Configuration ---
# This allows the React frontend (running on localhost:3000) to communicate with the API
origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# --- End of CORS Configuration ---


# --- In-Memory Storage for Demo Purposes ---
dataframes_cache = {}

# --- Pydantic Models for Request Bodies ---
class CommandRequest(BaseModel):
    session_id: str
    command: str

# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Voice Data Assistant API. Use /docs to see endpoints."}


@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Uploads a CSV file, stores it in memory, and returns a session ID.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .csv file.")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        session_id = str(uuid.uuid4())
        dataframes_cache[session_id] = df
        
        print(f"-> [API] Uploaded '{file.filename}'. Assigned Session ID: {session_id}")
        
        return {
            "message": f"File '{file.filename}' uploaded successfully.",
            "session_id": session_id,
            "columns": df.columns.tolist(),
            "shape": df.shape
        }
    except Exception as e:
        print(f"-> [API] Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {e}")


@app.post("/analyze", response_model=Result)
async def analyze_command(request: CommandRequest):
    """
    Receives a command and a session_id, then processes the command
    against the corresponding uploaded dataframe.
    """
    session_id = request.session_id
    command = request.command
    
    print(f"-> [API] Received command for Session ID {session_id}: '{command}'")
    
    if session_id not in dataframes_cache:
        raise HTTPException(status_code=404, detail="Session ID not found. Please upload a file first.")
    
    df = dataframes_cache[session_id]
    
    try:
        result = pipeline.run(command, df)
        
        if result.result_type == 'error':
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
    except Exception as e:
        print(f"-> [API] Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
