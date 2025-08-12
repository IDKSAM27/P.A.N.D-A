import os
import sys
import gradio as gr
import pandas as pd
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import application components
from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline
from app.audio.speech_recognition_handler import SpeechRecognitionHandler

# --- Initialization ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
audio_handler = SpeechRecognitionHandler()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

# --- SEPARATE UI LOGIC FUNCTIONS ---

def upload_csv(csv_file):
    """
    Handles only the CSV upload and stores the DataFrame in Gradio's state.
    """
    if csv_file is None:
        return None, "Please upload a valid CSV file."
    try:
        df = pd.read_csv(csv_file.name)
        message = f"Successfully loaded `{os.path.basename(csv_file.name)}`. Shape: {df.shape}. Ready for commands."
        print(f"-> [UI] {message}")
        return df, message
    except Exception as e:
        message = f"Error loading CSV: {e}"
        print(f"-> [UI] {message}")
        return None, message

def process_command(df_state, text_command, audio_command):
    """
    Handles only the command processing against the stored DataFrame.
    """
    # 1. Add print statements at the very top to confirm execution
    print("\n-> [UI] 'Process Command' button clicked. Starting command processing...")
    print(f"-> [UI] Received text_command: '{text_command}'")

    # 2. Check if a DataFrame is available from the state
    if df_state is None:
        message = "⚠️ Please upload a CSV file first."
        print(f"-> [UI] {message}")
        return message, None, None

    # 3. Determine which command to use (text or audio)
    command_to_process = ""
    if text_command and text_command.strip():
        command_to_process = text_command.strip()
    elif audio_command:
        transcribed_text = audio_handler.transcribe_audio(audio_command)
        if not transcribed_text:
            return "Could not understand audio. Please try again or type the command.", None, None
        command_to_process = transcribed_text
    else:
        return "⚠️ Please provide a command by typing or speaking.", None, None
    
    # 4. Run the main pipeline
    print(f"-> [UI] Handing off to pipeline with command: '{command_to_process}'")
    result = pipeline.run(command_to_process, df_state)

    # 5. Format and return the result for display
    if result.result_type == 'error':
        return result.message, None, None
    if result.result_type == 'table':
        result_df = pd.DataFrame(result.data)
        return result.message, result_df, None
    if result.result_type == 'value':
        return result.message, None, str(result.data)
    
    return "Completed.", None, None

# --- REVISED Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), title="P.A.N.D-A") as app:
    gr.Markdown("# P.A.N.D-A (Pandas Assistant for Natural Data Analysis)")
    gr.Markdown("Step 1: Upload a CSV. \nStep 2: Ask a question about the data.")
    
    # Use gr.State to hold the dataframe in memory for the session
    df_state = gr.State()

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Step 1: Upload Data")
            file_upload = gr.File(label="Upload CSV", file_types=[".csv"])
            
            gr.Markdown("### Step 2: Ask a Question")
            text_input = gr.Textbox(label="Type Command", placeholder="e.g., 'total sales by product'")
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Or Record Command")
            submit_btn = gr.Button("Process Command")
        
        with gr.Column(scale=2):
            gr.Markdown("### Results")
            output_message = gr.Textbox(label="Status / Message", interactive=False, lines=2)
            output_table = gr.DataFrame(label="Data Output", interactive=False)
            output_value = gr.Textbox(label="Value Output", interactive=False)

    # Wire up the components to the correct functions
    file_upload.upload(
        fn=upload_csv,
        inputs=[file_upload],
        outputs=[df_state, output_message]
    )
    
    submit_btn.click(
        fn=process_command,
        inputs=[df_state, text_input, audio_input],
        outputs=[output_message, output_table, output_value]
    )

if __name__ == "__main__":
    app.launch(share=False)
