import os
import sys
import gradio as gr
import pandas as pd
from dotenv import load_dotenv

# Add the project root to the Python path to solve module import issues
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

df_cache = None

def process_data_and_command(csv_file, text_command, audio_command):
    """
    The main function that Gradio will call. It processes the uploaded file
    and a command (either text or voice) to produce an output.
    """
    global df_cache
    command_to_process = ""

    # 1. Load and cache the DataFrame if a new file is uploaded
    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file.name)
            df_cache = df
            upload_message = f"Successfully loaded `{os.path.basename(csv_file.name)}`. Shape: {df.shape}. Ready for commands."
            return upload_message, None, None
        except Exception as e:
            return f"Error loading CSV: {e}", None, None

    if df_cache is None:
        return "Please upload a CSV file first.", None, None

    # --- UPDATED LOGIC: Prioritize Text Input ---
    # If the user typed a command, use it.
    if text_command and text_command.strip():
        command_to_process = text_command.strip()
        print(f"-> [UI] Using manual text command: '{command_to_process}'")
    # Otherwise, if audio was provided, use that.
    elif audio_command:
        print("-> [UI] No text command found, processing audio input.")
        transcribed_text = audio_handler.transcribe_audio(audio_command)
        if not transcribed_text:
            return "Could not understand the audio. Please try again or type the command.", None, None
        command_to_process = transcribed_text
    # If neither was provided, return an error.
    else:
        return "Please provide a command by typing or speaking.", None, None

    # Run the main pipeline with the determined command
    result = pipeline.run(command_to_process, df_cache)

    # 4. Format and return the result for display
    if result.result_type == 'error':
        return result.message, None, None
    
    if result.result_type == 'table':
        result_df = pd.DataFrame(result.data)
        return result.message, result_df, None
    
    if result.result_type == 'value':
        return result.message, None, str(result.data)

    return "Completed.", None, None


# --- UPDATED Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), title="Voice Data Assistant") as app:
    gr.Markdown("# P.A.N.D-A (Pandas Assistant for Natural Data-Analytics)")
    gr.Markdown("Upload a CSV, then ask a question by typing in the text box or recording your voice.")

    with gr.Row():
        with gr.Column(scale=1):
            file_upload = gr.File(label="Upload CSV", file_types=[".csv"])
            
            # --- NEW: Manual Text Input ---
            text_input = gr.Textbox(
                label="Manual Command",
                placeholder="Type your command here (e.g., 'total sales by product')",
                lines=2
            )
            
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Or Record Voice Command")
            submit_btn = gr.Button("Process Command")
        
        with gr.Column(scale=2):
            gr.Markdown("### Results")
            output_message = gr.Textbox(label="Status / Message", interactive=False, lines=2)
            output_table = gr.DataFrame(label="Data Output", interactive=False)
            output_value = gr.Textbox(label="Value Output", interactive=False)

    # Update the click function to include the new text input
    submit_btn.click(
        fn=process_data_and_command,
        inputs=[file_upload, text_input, audio_input],
        outputs=[output_message, output_table, output_value]
    )

if __name__ == "__main__":
    app.launch(share=False)
