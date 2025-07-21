import pandas as pd
from app.interfaces.llm_interface import LLMInterface
from app.interfaces.processor_interface import ProcessorInterface
from app.models.result import Result
from app.models.intent import Intent

class CommandPipeline:
    """
    Orchestrates the process from natural language command to data result.
    
    This class connects the parsing and processing components, ensuring a smooth
    flow of data from user input to final output. It relies on abstractions
    (interfaces) for its components, making it highly modular and testable.
    """
    def __init__(self, llm_parser: LLMInterface, data_processor: ProcessorInterface):
        """
        Initializes the pipeline with dependency-injected components.

        By accepting interfaces as arguments, we adhere to the Dependency
        Inversion Principle, allowing us to swap implementations (e.g., use a
        different LLM or data processor) without changing this core logic.

        Args:
            llm_parser (LLMInterface): The component for parsing text to intent.
            data_processor (ProcessorInterface): The component for executing an intent.
        """
        self.llm_parser = llm_parser
        self.data_processor = data_processor

    def run(self, command: str, df: pd.DataFrame) -> Result:
        """
        Executes the full pipeline: parse command, then execute intent.

        Args:
            command (str): The user's natural language command.
            df (pd.DataFrame): The dataset to analyze.

        Returns:
            Result: The final result of the operation.
        """
        print(f"-> [Pipeline] Processing command: '{command}'")
        try:
            # Step 1: Parse the natural language command into a structured intent.
            # We provide the dataframe's column names to give the LLM context.
            df_columns = df.columns.tolist()
            intent = self.llm_parser.parse_command(command, df_columns)
            print(f"-> [Pipeline] LLM parsed intent: {intent.model_dump_json(indent=2)}")

            # Step 2: Execute the structured intent using the data processor.
            result = self.data_processor.execute(intent, df)
            print(f"-> [Pipeline] Processor executed. Result type: {result.result_type}")
            
            return result

        except Exception as e:
            # A top-level catch-all to ensure the pipeline always returns a Result object.
            error_message = f"An unexpected error occurred in the command pipeline: {e}"
            print(f"-> [Pipeline] ERROR: {error_message}")
            return Result(result_type='error', message=error_message)
