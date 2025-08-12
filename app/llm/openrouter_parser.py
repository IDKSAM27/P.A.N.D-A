import os
import json
import logging
import requests
from typing import List
from app.interfaces.llm_interface import LLMInterface
from app.models.intent import Intent

class OpenRouterParser(LLMInterface):
    """
    An intent parser that uses the OpenRouter API to understand natural language commands.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key for OpenRouter is required.")
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def parse_command(self, command: str, df_columns: List[str]) -> Intent:
        system_prompt = self._build_system_prompt(df_columns)
        response_text = ""
        try:
            logging.info("-> [LLM Parser] Sending request to OpenRouter...")
            response = requests.post(
                url=self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": command}]
                }
            )
            response.raise_for_status()
            response_text = response.json()['choices'][0]['message']['content']
            logging.info(f"-> [LLM Parser] Received raw response: {response_text}")

            try:
                start_index = response_text.index('{')
                end_index = response_text.rindex('}') + 1
                json_string = response_text[start_index:end_index]
                json_response = json.loads(json_string)
            except (ValueError, json.JSONDecodeError):
                clean_text = response_text.strip()
                
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:-3].strip()
                json_response = json.loads(clean_text)

            intent = Intent(**json_response)
            logging.info(f"-> [LLM Parser] Successfully parsed intent: {intent.model_dump_json(indent=2)}")
            return intent
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to OpenRouter API: {e}")
        except Exception:
            raise ValueError(f"Could not parse the response from the LLM. Raw response: {response_text}")

    def _build_system_prompt(self, df_columns: List[str]) -> str:
        """
        Creates a detailed system prompt for the LLM.
        """
        return f"""
        You are an expert at parsing natural language commands into structured JSON format for a pandas backend.
        Your task is to analyze the user's command and convert it into a JSON object.

        The user is working with a dataset that has the following columns:
        ---
        {', '.join(df_columns)}
        ---
        
        CRITICAL RULES:
        1. You MUST ONLY use the column names from the list above.
        2. For ranking queries (e.g., "top 5", "lowest 3"), the 'operation' MUST be 'sum'.

        VALID OPERATIONS:
        - Aggregations: 'sum', 'mean', 'median', 'min', 'max', 'count'
        - Plotting: 'plot'
        - General Info: 'describe', 'info'
        - Specific Counts: 'value_counts'

        Analyze the command to determine the operation and its parameters.

        - 'operation': The specific operation to perform.
        - 'target_column': The column for the operation. Required for most operations.
        - 'group_by': A list of columns to group by. Used for aggregations and plots.
        - 'limit': The number of rows for "top/lowest" queries.
        - 'sort_order': 'asc' for lowest, 'desc' for highest.
        - 'plot_type': 'bar' or 'line' if operation is 'plot'.
        - 'description': A one-sentence summary of what you are doing.

        You MUST respond with ONLY a valid JSON object. Do not include any explanatory text.
        
        EXAMPLES:

        Command: "give me a description of the dataset"
        JSON:
        ```
        {{
          "operation": "describe",
          "target_column": null,
          "group_by": null,
          "filters": null,
          "plot_type": null,
          "limit": null,
          "sort_order": "desc",
          "description": "Provide a statistical summary of the dataset."
        }}
        ```

        Command: "how many different coffee types are there?"
        JSON:
        ```
        {{
          "operation": "value_counts",
          "target_column": "Coffee_type",
          "group_by": null,
          "filters": null,
          "plot_type": null,
          "limit": null,
          "sort_order": "desc",
          "description": "Count the occurrences of each unique coffee type."
        }}
        ```

        Command: "show the top 3 days by total sales"
        JSON:
        ```
        {{
          "operation": "sum",
          "target_column": "Sales",
          "group_by": ["Day"],
          "filters": null,
          "plot_type": null,
          "limit": 3,
          "sort_order": "desc",
          "description": "Show the top 3 days by total sales."
        }}
        ```
        """
