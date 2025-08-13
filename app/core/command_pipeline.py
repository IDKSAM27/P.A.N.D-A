import logging
import pandas as pd
from app.core.command_registry import command_registry

class CommandPipeline:
    def __init__(self, llm_parser):
        self.llm_parser = llm_parser

    def run(self, command: str, df: pd.DataFrame):
        logging.info(f"-> [Pipeline] Processing command: '{command}'")
        
        # Step 1: Parse the command to get the command name and parameters
        parsed_intent = self.llm_parser.parse_command(command)
        command_name = parsed_intent.get("command_name")
        parameters = parsed_intent.get("parameters", {})

        if not command_name:
            raise ValueError("LLM did not return a command_name.")

        # Step 2: Get the appropriate command module from the registry
        command_module = command_registry.get_command(command_name)
        if not command_module:
            raise ValueError(f"Command '{command_name}' not found in registry.")

        # Step 3: Validate the parameters against the command's specific model
        validated_params = command_module.pydantic_model(**parameters)
        logging.info(f"-> [Pipeline] Executing command '{command_name}' with validated params.")

        # Step 4: Execute the command
        result = command_module.execute(validated_params, df)
        logging.info(f"-> [Pipeline] Processor executed. Result type: {result.result_type}")
        return result
