"""
Ollama Integration for KiloCode
Provides a client to interact with local Ollama models (qwen2.5:3b)
"""
import requests
import json
from typing import Optional, Dict, Any

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"

class OllamaClient:
    """Client for interacting with Ollama locally"""
    
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model = model
        self.base_url = base_url
    
    def generate(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate a response from the model"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured response using JSON mode"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return json.loads(response.json()["response"])
    
    def get_embedding(self, text: str) -> list:
        """Get embeddings for text using Ollama"""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["embedding"]
    
    def chat(self, messages: list, stream: bool = False) -> Dict[str, Any]:
        """Chat completion with messages format"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_models(self) -> list:
        """List available models"""
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("models", [])

# Global client instance
_client: Optional[OllamaClient] = None

def get_client(model: str = DEFAULT_MODEL) -> OllamaClient:
    """Get or create the Ollama client singleton"""
    global _client
    if _client is None or _client.model != model:
        _client = OllamaClient(model)
    return _client

def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Simple generation function"""
    client = get_client(model)
    return client.generate(prompt)["response"]

def chat_complete(messages: list, model: str = DEFAULT_MODEL) -> str:
    """Simple chat completion function"""
    client = get_client(model)
    return client.chat(messages)["message"]["content"]

def get_embeddings(texts: list, model: str = DEFAULT_MODEL) -> list:
    """Get embeddings for multiple texts"""
    client = get_client(model)
    return [client.get_embedding(text) for text in texts]

if __name__ == "__main__":
    # Test the integration
    client = OllamaClient()
    print("Available models:", client.list_models())
    print("\nTest generation:")
    print(generate("What is 2+2?"))
