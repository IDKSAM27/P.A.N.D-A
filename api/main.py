import os
import sys
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Add the project root to the Python path to allow imports from `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our application components
from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline
from app.models.intent import Intent # Though not used directly, good for context
from app.models.result import Result # Will be our response model

# --- Initialization ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

# Instantiate our core components
llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

# Create the FastAPI app instance
app = FastAPI(
    title="Voice Data Assistant API",
    description="An API to process natural language commands against a dataset.",
    version="1.0.0"
)

# For now, we'll use a hardcoded sample DataFrame for testing the API endpoint.
# In the next step, we'll replace this with a dynamic file upload mechanism.
def get_sample_dataframe() -> pd.DataFrame:
    """Creates a sample DataFrame for demonstration purposes."""
    data = {
        'Region': ['North', 'North', 'South', 'South', 'West', 'West', 'East', 'East'],
        'Product': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
        'Sales': [100, 150, 200, 250, 120, 180, 220, 280],
        'Year': [2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024]
    }
    return pd.DataFrame(data)

# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Voice Data Assistant API. Use the /docs endpoint to see the API documentation."}


@app.post("/analyze", response_model=Result)
async def analyze_command(command: str):
    """
    Receives a natural language command and processes it against the sample dataset.
    """
    try:
        df = get_sample_dataframe()
        print(f"-> [API] Received command: '{command}'")
        
        # Run the existing, tested pipeline
        result = pipeline.run(command, df)
        
        if result.result_type == 'error':
            # It's better to return a proper HTTP error for API clients
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
    except Exception as e:
        # Catch any unexpected errors from the pipeline
        print(f"-> [API] Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

