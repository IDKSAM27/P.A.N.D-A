import os
import pandas as pd
import json
from dotenv import load_dotenv

# --- Import our application components ---
from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline

def create_sample_dataframe() -> pd.DataFrame:
    """Creates a sample DataFrame for demonstration purposes."""
    data = {
        'Region': ['North', 'North', 'South', 'South', 'West', 'West', 'East', 'East'],
        'Product': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
        'Sales': [100, 150, 200, 250, 120, 180, 220, 280],
        'Year': [2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024]
    }
    df = pd.DataFrame(data)
    print("--- Sample DataFrame ---")
    print(df)
    print("------------------------\n")
    return df

def main():
    """
    Main function to initialize and run the voice data assistant pipeline.
    """
    # 1. Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env file.")
        print("Please create a .env file in the root directory and add your key.")
        return

    # 2. Load the data
    df = create_sample_dataframe()

    # 3. Instantiate components (Dependency Injection)
    # This is where we choose our concrete implementations
    try:
        llm_parser = OpenRouterParser(api_key=api_key)
        data_processor = PandasProcessor()
        pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)
    except ValueError as e:
        print(f"Error during initialization: {e}")
        return

    # 4. Define a sample command and run the pipeline
    # command = "What is the total sales for Product A?"
    command = "What are the average sales by region?"
    # command = "count the number of entries for the west region"

    result = pipeline.run(command, df)

    # 5. Display the result
    print("\n--- Final Result ---")
    print(f"Message: {result.message}")
    
    if result.result_type in ['table', 'value'] and result.data is not None:
        print("Data:")
        # Pretty print the data
        if isinstance(result.data, list) or isinstance(result.data, dict):
            print(json.dumps(result.data, indent=2))
        else:
            print(result.data)
    elif result.result_type == 'error':
        print(f"An error occurred: {result.message}")
    
    print("--------------------")


if __name__ == "__main__":
    main()
