# voice_data_assistant/app/llm/openrouter_parser.py

import os
import json
import requests
from typing import List
from app.interfaces.llm_interface import LLMInterface
from app.models.intent import Intent

class OpenRouterParser(LLMInterface):
    """
    An LLM parser that uses the OpenRouter API to extract intent.
    """
    def __init__(self, api_key: str, model_name: str = "mistralai/mistral-7b-instruct"):
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def parse_command(self, command: str, df_columns: List[str]) -> Intent:
        """
        Sends the command to the OpenRouter API and parses the response.
        """
        system_prompt = self._build_system_prompt(df_columns)
        
        request_body = { "model": self.model_name, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": command}] }
        raw_content = ""
        try:
            response = requests.post(
                url=self.api_url,
                headers={ "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "HTTP-Referer": "http://localhost", "X-Title": "Voice Data Assistant" },
                data=json.dumps(request_body)
            )
            response.raise_for_status()
            
            response_json = response.json()
            raw_content = response_json['choices'][0]['message']['content']
            
            json_start_index = raw_content.find('{')
            json_end_index = raw_content.rfind('}')
            
            if json_start_index == -1 or json_end_index == -1:
                raise json.JSONDecodeError("Could not find a valid JSON object in the LLM response.", raw_content, 0)

            json_string = raw_content[json_start_index : json_end_index + 1]
            intent_data = json.loads(json_string)

            # --- FIX: ADDED SAFETY NET FOR 'group_by' FIELD ---
            # If the LLM returns a string instead of a list for group_by, fix it here.
            if 'group_by' in intent_data and isinstance(intent_data['group_by'], str):
                print("-> [Parser] Correcting 'group_by' from string to list.")
                intent_data['group_by'] = [intent_data['group_by']]
            # --- END OF FIX ---
            
            return Intent(**intent_data)

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error calling OpenRouter API: {e}\nResponse Body: {e.response.text}")
            raise
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing LLM response: {e}\nRaw content from LLM: {raw_content}")
            raise

    def _build_system_prompt(self, df_columns: List[str]) -> str:
        # --- FIX: IMPROVED PROMPT FOR 'group_by' ---
        return f"""
        You are an expert at parsing natural language commands into structured JSON format.
        Your task is to analyze the user's command and convert it into a JSON object.

        The user is working with a dataset that has the following columns:
        {', '.join(df_columns)}

        Analyze the user's command to determine the operation, target column(s), grouping, and any filters.

        - 'operation': 'mean', 'sum', 'count', 'median', 'min', 'max', or 'plot'.
        - 'target_column': The column for the operation (e.g., 'Sales').
        - 'group_by': MUST BE A LIST of column names to group by. For a single column, use a list like ["Region"].
        - 'filters': A dictionary of filters, e.g., {{"Year": "2023"}}.
        - 'description': A one-sentence summary of the command.

        You MUST respond with ONLY a valid JSON object. Do not include any explanatory text.
        
        Example command: "average sales by region"
        Example JSON output:
        {{
          "operation": "mean",
          "target_column": "Sales",
          "group_by": ["Region"],
          "filters": null,
          "description": "Calculate the average sales grouped by region."
        }}
        """
