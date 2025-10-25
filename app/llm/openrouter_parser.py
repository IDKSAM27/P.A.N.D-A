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
        # Try dynamic prompt first
        system_prompt = command_registry.generate_llm_prompt()
        response_text = ""
        full_api_response = None  # For debugging
        
        try:
            logging.info("-> [LLM Parser] Sending request to OpenRouter...")
            response = requests.post(
                url=self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": command}],
                    "max_tokens": 500  # Limit to prevent overflow
                }
            )
            response.raise_for_status()
            full_api_response = response.json()
            logging.info(f"-> [LLM Parser] Full API response keys: {list(full_api_response.keys())}")  # Debug: Log structure
            
            if 'choices' not in full_api_response or not full_api_response['choices']:
                raise ValueError("Empty choices from API.")
            
            response_text = full_api_response['choices'][0]['message']['content']
            logging.info(f"-> [LLM Parser] Raw content length: {len(response_text)} chars")  # Debug: Check if empty
            
            if not response_text or response_text.strip() == "":
                raise ValueError("API returned empty content. Check API key/quota or try a paid model.")
            
            # Extract JSON (robust handling for partial responses)
            start_index = response_text.find('{')
            if start_index == -1:
                raise ValueError("No JSON object found in response.")
            end_index = response_text.rfind('}') + 1
            if end_index <= start_index:
                raise ValueError("Incomplete JSON object in response.")
            json_string = response_text[start_index:end_index]
            
            parsed_json = json.loads(json_string)
            logging.info(f"-> [LLM Parser] Successfully parsed response: {parsed_json}")
            return parsed_json

        except requests.exceptions.RequestException as e:
            logging.error(f"-> [LLM Parser] API request failed: {e}")
            raise ConnectionError(f"Failed to connect to OpenRouter API: {e}")
        except (ValueError, json.JSONDecodeError) as e:
            # Fallback: Use a simpler prompt and retry once
            logging.warning(f"-> [LLM Parser] Initial parse failed: {e}. Trying fallback prompt...")
            return self._parse_with_fallback(command)
        except Exception as e:
            logging.error(f"-> [LLM Parser] Unexpected error: {e}. Full response: {full_api_response}")
            raise ValueError(f"Could not parse the response from the LLM.")

    def _parse_with_fallback(self, command: str) -> dict:
        """Fallback with a simplified prompt (no schemas) to avoid token limits."""
        fallback_prompt = """
        You are an expert at routing a user's command to the correct tool.
        Available commands:
        - aggregate_data: For sums, averages, counts, top/lowest N. Trigger: total, sum, average, top, lowest.
        - plot_data: For charts/graphs. Trigger: plot, chart, visualize.
        - describe_data: For dataset summary. Trigger: describe, summary.

        Respond ONLY with JSON: {"command_name": "command_name", "parameters": {}}
        Example: {"command_name": "aggregate_data", "parameters": {"agg_func": "sum", "target_column": "Units Sold", "group_by": ["Day"]}}
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [{"role": "system", "content": fallback_prompt}, {"role": "user", "content": command}]
                }
            )
            response.raise_for_status()
            response_text = response.json()['choices'][0]['message']['content']
            
            if not response_text.strip():
                raise ValueError("Fallback also returned empty content.")
            
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_string = response_text[start_index:end_index]
            parsed_json = json.loads(json_string)
            logging.info(f"-> [LLM Parser] Fallback parsed: {parsed_json}")
            return parsed_json
        except Exception as e:
            logging.error(f"-> [LLM Parser] Fallback failed: {e}")
            raise ValueError("Both parsing attempts failed. Check your OpenRouter API key or try a different model.")
