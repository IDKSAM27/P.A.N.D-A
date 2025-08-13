# This file becomes much simpler!
import json
import logging
import requests
from app.core.command_registry import command_registry

class OpenRouterParser:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key for OpenRouter is required.")
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def parse_command(self, command: str) -> dict:
        system_prompt = command_registry.generate_llm_prompt()
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
            
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_string = response_text[start_index:end_index]
            
            parsed_json = json.loads(json_string)
            logging.info(f"-> [LLM Parser] Successfully parsed response: {parsed_json}")
            return parsed_json

        except Exception as e:
            logging.error(f"-> [LLM Parser] Failed to parse LLM response: {e}. Raw text: {response_text}")
            raise ValueError(f"Could not parse the response from the LLM.")
