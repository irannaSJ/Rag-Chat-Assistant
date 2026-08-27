# llm/llm_client.py

import requests
from groq import Groq
import json

class LLMClient:
    def __init__(
        self,
        model_name: str = "phi3:mini",
        base_url: str = "http://localhost:11434"
    ):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False, 
            "options": {
                "temperature": 0.3,
                "num_predict":300  #tokens
            }
        }

        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()

    def generate_stream(self, prompt: str):
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "num_predict": 300
            }
        }

        response = requests.post(url, json=payload, stream=True, timeout=300)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    yield data["response"]
                if data.get("done"):
                    break
