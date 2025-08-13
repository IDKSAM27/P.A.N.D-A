import os
import importlib
import inspect
from app.commands.base import CommandInterface

class CommandRegistry:
    def __init__(self):
        self._commands = {}
        self._discover_commands()

    def _discover_commands(self):
        commands_dir = os.path.join(os.path.dirname(__file__), '..', 'commands')
        for filename in os.listdir(commands_dir):
            if filename.endswith('.py') and not filename.startswith('__') and filename != 'base.py':
                module_name = f"app.commands.{filename[:-3]}"
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, CommandInterface) and obj is not CommandInterface:
                        command_instance = obj()
                        self._commands[command_instance.name] = command_instance

    def get_command(self, name: str) -> CommandInterface:
        return self._commands.get(name)

    def get_all_commands(self) -> dict:
        return self._commands

    def generate_llm_prompt(self) -> str:
        prompt = """
        You are an expert at routing a user's command to the correct internal tool.
        Based on the user's query, you must select the appropriate command and extract its specific parameters.

        Available commands:
        """
        for name, cmd in self._commands.items():
            prompt += f"\n---"
            prompt += f"\nCommand Name: \"{name}\"\n"
            prompt += f"Description: {cmd.description}\n"
            prompt += f"Trigger words: {', '.join(cmd.trigger_words)}\n"
            prompt += f"Parameters Schema: {cmd.pydantic_model.schema_json(indent=2)}\n"

        prompt += """
        ---
        CRITICAL RULES:
        1. You MUST respond with ONLY a single valid JSON object.
        2. The JSON object must have two top-level keys: "command_name" and "parameters".
        3. The "command_name" must be one of the exact command names listed above.
        4. The "parameters" object must be a valid JSON object that strictly conforms to that command's specified Parameters Schema.

        Example:
        User Query: "what is the total sales for espresso?"
        Your JSON Response:
        {
          "command_name": "aggregate_data",
          "parameters": {
            "agg_func": "sum",
            "target_column": "Sales",
            "group_by": ["Coffee_type"],
            "filters": {
              "Coffee_type": "Espresso"
            }
          }
        }
        """
        return prompt

# Create a single, shared instance of the registry
command_registry = CommandRegistry()
