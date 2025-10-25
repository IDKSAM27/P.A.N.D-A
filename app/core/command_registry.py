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
        Based on the user's query, select the appropriate command and extract its parameters.

        Available commands:
        """
        for name, cmd in self._commands.items():
            prompt += f"\n---\nCommand: \"{name}\"\n"
            prompt += f"Description: {cmd.description}\n"
            prompt += f"Triggers: {', '.join(cmd.trigger_words)}\n"
            prompt += f"Params (basic): {self._get_param_summary(cmd.pydantic_model)}\n"  # Short summary instead of full schema

        prompt += """
        ---
        RULES:
        1. Respond ONLY with valid JSON: {"command_name": "exact_name", "parameters": {param values}}
        2. Use exact command names.
        3. Parameters must match the command's requirements (e.g., aggregate_data needs 'agg_func' like 'sum').

        Example for "total units sold by day":
        {"command_name": "aggregate_data", "parameters": {"agg_func": "sum", "target_column": "Units Sold", "group_by": ["Day"]}}
        """
        return prompt

    def _get_param_summary(self, model_class) -> str:
        params = []
        for param_name, field in model_class.__fields__.items():
            try:
                param_type = getattr(field.annotation, "__name__", str(field.annotation))
            except Exception:
                param_type = "any"
            required = '' if field.default is not None else ' (required)'
            params.append(f"{param_name} ({param_type}){required}")
        return ', '.join(params)

# Create a single, shared instance of the registry
command_registry = CommandRegistry()
