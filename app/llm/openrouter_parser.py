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

    def __init__(self, api_key: str, model_name: str = "google/gemma-7b-it"):
        if not api_key:
            raise ValueError("OpenRouter API key is required.") 

        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://openrouter.ai/api/v1/chat/completions" 

    def parse_command(self, command: str, df_columns: List[str]) -> Intent:
        """
        Sends the command to the OpenRouter API and parses the response.
        """
        system_prompt = self.build_system_prompt(df_columns)

        try:
            response = requests.post(
                url=self.api_url,
                header={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": command}
                    ],
                    "response_format": {"type": "json_object"}
                })
            )
            response.raise_for_status() # This will raise an HTTPError for bad responses (4xx, 5xx)

            response_json = response.json()
            intent_data = json.loads(response_json['choices'][0]['message']['content'])

            return Intent(**intent_data)
        
        except requests.exceptions.RequestException as e:
            print(f"Error calling OpenRouter API: {e}")
            # Depending on desired error handling, you might return a default intent
            # or re-raise the exception.
            raise
    
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing LLM response: {e}")
            raise

    
    