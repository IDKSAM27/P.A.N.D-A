import os
import gradio as gr
import pandas as pd
from dotenv import load_dotenv

# Import application components
from app.llm.openrouter_parser import OpenRouterParser
from app.processing.pandas_processor import PandasProcessor
from app.core.command_pipeline import CommandPipeline
from app.audio.speech_recognition_handler import SpeechRecognitionHandler

# --- Initialization ---
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Check for API key
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")

# Instantiate our components
llm_parser = OpenRouterParser(api_key=api_key)
data_processor = PandasProcessor()
audio_handler = SpeechRecognitionHandler()
pipeline = CommandPipeline(llm_parser=llm_parser, data_processor=data_processor)

# Global variable to hold the DataFrame
# Gradio's state management can be done this way for simplicity
df_cache = None

def process_data_and_command(csv_file, audio_command):
    """
    The main function that Gradio will call. It processes the uploaded file
    and the voice command to produce an output.
    """
    global df_cache

    # 1. Load and cache the DataFrame if a new file is uploaded
    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file.name)
            df_cache = df
            upload_message = f"Successfully loaded `{os.path.basename(csv_file.name)}`. Shape: {df.shape}. Ready for commands."
            return upload_message, None, None # Return message, clear outputs
        except Exception as e:
            return f"Error loading CSV: {e}", None, None

    # 2. Check if a DataFrame is available
    if df_cache is None:
        return "Please upload a CSV file first.", None, None

    # 3. Process the audio command
    if audio_command is None:
        return "Please record a command.", None, None

    # Transcribe audio to text
    transcribed_text = audio_handler.transcribe_audio(audio_command)
    if not transcribed_text:
        return "Could not understand the audio. Please try again.", None, None

    # Run the main pipeline
    result = pipeline.run(transcribed_text, df_cache)

    # 4. Format and return the result for display
    if result.result_type == 'error':
        return result.message, None, None
    
    if result.result_type == 'table':
        # Convert list of dicts to DataFrame for display
        result_df = pd.DataFrame(result.data)
        return result.message, result_df, None
    
    if result.result_type == 'value':
        return result.message, None, str(result.data)

    return "Completed.", None, None


# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), title="Voice Data Assistant") as app:
    gr.Markdown("# P.A.N.D-A (Pandas Assistant for Natural Data-Analytics)")
    gr.Markdown("Upload a CSV file, then use your voice to ask questions about the data.")

    with gr.Row():
        with gr.Column(scale=1):
            file_upload = gr.File(label="Upload CSV", file_types=[".csv"])
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Voice Command")
            submit_btn = gr.Button("Process Command")
        
        with gr.Column(scale=2):
            gr.Markdown("### Results")
            output_message = gr.Textbox(label="Status / Message", interactive=False)
            output_table = gr.DataFrame(label="Data Output", interactive=False)
            output_value = gr.Textbox(label="Value Output", interactive=False)

    submit_btn.click(
        fn=process_data_and_command,
        inputs=[file_upload, audio_input],
        outputs=[output_message, output_table, output_value]
    )

if __name__ == "__main__":
    app.launch(share=False) # Set share=True to get a public link
