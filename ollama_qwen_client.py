"""
Ollama Qwen Client for KiloCode Integration
Provides a simple interface to use local Ollama Qwen models
"""

import requests
import json
from typing import Optional, Dict, Any

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"

class OllamaClient:
    """Client for interacting with local Ollama Qwen models"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate a response from the model"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """Chat completion with conversation history"""
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except:
            return []


# Convenience functions for easy use in KiloCode
def qwen_complete(prompt: str, **kwargs) -> str:
    """Simple completion using Qwen"""
    client = OllamaClient()
    result = client.generate(prompt, **kwargs)
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("response", "")

def qwen_chat(messages: list, **kwargs) -> str:
    """Chat completion using Qwen"""
    client = OllamaClient()
    result = client.chat(messages, **kwargs)
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("message", {}).get("content", "")


if __name__ == "__main__":
    # Quick test
    client = OllamaClient()
    print(f"Ollama available: {client.is_available()}")
    print(f"Models: {[m['name'] for m in client.list_models()]}")
    
    # Test generation
    response = client.generate("Explain H1B visa in 2 sentences")
    print(f"\nQwen Response: {response.get('response', response)}")
