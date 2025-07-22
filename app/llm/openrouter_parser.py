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
    # Using a known free and stable model as the default.
    def __init__(self, api_key: str, model_name: str = "meta-llama/llama-3-8b-instruct:free"):
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        self.api_key = api_key
        self.model_name = model_name
        # The API URL is correct as per the documentation.
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def parse_command(self, command: str, df_columns: List[str]) -> Intent:
        """
        Sends the command to the OpenRouter API and parses the response.
        """
        system_prompt = self._build_system_prompt(df_columns)
        
        request_body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                url=self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(request_body)
            )
            
            # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
            response.raise_for_status()
            
            response_json = response.json()
            intent_data = json.loads(response_json['choices'][0]['message']['content'])
            
            return Intent(**intent_data)

        except requests.exceptions.HTTPError as e:
            # Provide more detailed error information for debugging.
            print(f"HTTP Error calling OpenRouter API: {e}")
            print(f"Response Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Network error calling OpenRouter API: {e}")
            raise
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing LLM response: {e}")
            raise

    def _build_system_prompt(self, df_columns: List[str]) -> str:
        """
        Creates a detailed system prompt for the LLM.
        """
        return f"""
        You are an expert at parsing natural language commands into structured JSON format.
        Your task is to analyze the user's command and convert it into a JSON object that
        conforms to the specified schema.

        The user is working with a dataset that has the following columns:
        {', '.join(df_columns)}

        Analyze the user's command to determine the operation, target column(s), grouping,
        and any filters.

        Possible operations are: 'mean', 'sum', 'count', 'median', 'min', 'max', 'plot'.
        
        - For plotting, set 'operation' to 'plot' and use the 'description' field to describe the plot request.
        - The 'target_column' is the column on which the main aggregation is performed (e.g., 'sales' in "average sales").
        - The 'group_by' field should be a list of columns for aggregation (e.g., ['region'] in "by region").
        - The 'filters' should be a dictionary of key-value pairs (e.g., {{"product_category": "electronics"}}).
        - Provide a brief, one-sentence 'description' of the task.

        You MUST respond with ONLY a valid JSON object. Do not include any explanatory text.
        Example command: "What is the total revenue for shoes in New York?"
        Example JSON output:
        {{
          "operation": "sum",
          "target_column": "revenue",
          "group_by": null,
          "filters": {{
            "product_category": "shoes",
            "state": "New York"
          }},
          "description": "Calculate the sum of revenue for shoes in New York."
        }}
        """
