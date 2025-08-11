# voice_data_assistant/app/llm/openrouter_parser.py

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
        """
        Parses the user command by making an API call to an LLM via OpenRouter.
        """
        system_prompt = self._build_system_prompt(df_columns)
        response_text = "" # Initialize to prevent reference before assignment in error handling
        
        try:
            logging.info("-> [LLM Parser] Sending request to OpenRouter...")
            response = requests.post(
                url=self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": command}
                    ]
                }
            )

            response.raise_for_status()
            
            response_text = response.json()['choices'][0]['message']['content']
            logging.info(f"-> [LLM Parser] Received raw response: {response_text}")
            
            # --- THE DEFINITIVE FIX ---
            # Correctly checks for markdown code blocks using valid string literals.
            clean_text = response_text.strip()
            # if clean_text.startswith("```
            #     clean_text = clean_text[7:-3].strip()
            if clean_text.startswith("```"):
                clean_text = clean_text[3:-3].strip()

            json_response = json.loads(clean_text)
            
            intent = Intent(**json_response)
            logging.info(f"-> [LLM Parser] Successfully parsed intent: {intent.model_dump_json(indent=2)}")
            return intent
            
        except requests.exceptions.RequestException as e:
            logging.error(f"-> [LLM Parser] API request failed: {e}")
            raise ConnectionError(f"Failed to connect to OpenRouter API: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"-> [LLM Parser] Failed to parse LLM response: {e}")
            raise ValueError(f"Could not parse the response from the LLM. Raw response: {response_text}")
        except Exception as e:
            logging.error(f"-> [LLM Parser] An unexpected error occurred: {e}")
            raise

    def _build_system_prompt(self, df_columns: List[str]) -> str:
        """
        Creates a detailed system prompt for the LLM.
        """
        return f"""
        You are an expert at parsing natural language commands into structured JSON format.
        Your task is to analyze the user's command and convert it into a JSON object.

        The user is working with a dataset that has the following columns:
        ---
        {', '.join(df_columns)}
        ---
        
        CRITICAL RULE: You MUST ONLY use the column names from the list above for the
        'target_column', 'group_by', and 'filters' fields. Do not invent or infer names.

        Analyze the user's command to determine the operation and fields.

        - 'operation': 'mean', 'sum', 'count', 'median', 'min', 'max', or 'plot'.
        - 'target_column': The column on which to perform the operation.
        - 'group_by': A list of columns to group the data by.
        - 'filters': A dictionary of filters to apply before the operation.
        - 'plot_type': If the operation is 'plot', specify the chart type (e.g., 'bar', 'line').
        - 'limit': The number of rows to return (e.g., for "top 5", limit is 5). Default is null.
        - 'sort_order': 'asc' for ascending (lowest) or 'desc' for descending (highest). Default is 'desc'.
        - 'description': A one-sentence summary of the command.

        You MUST respond with ONLY a valid JSON object. Do not include any explanatory text.
        
        Example for Top N query:
        Command: "show me the top 3 coffee types by sales"
        JSON output:
        ```
        {{
          "operation": "sum",
          "target_column": "Sales",
          "group_by": ["Coffee_type"],
          "filters": null,
          "plot_type": null,
          "limit": 3,
          "sort_order": "desc",
          "description": "Show the top 3 coffee types by sales."
        }}
        ```

        Example for Lowest N query:
        Command: "what are the 2 days with the lowest units sold"
        JSON output:
        ```
        {{
          "operation": "sum",
          "target_column": "Units Sold",
          "group_by": ["Day"],
          "filters": null,
          "plot_type": null,
          "limit": 2,
          "sort_order": "asc",
          "description": "Show the 2 days with the lowest units sold."
        }}
        ```
        """