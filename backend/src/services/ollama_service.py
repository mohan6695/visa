"""Ollama service for local LLM integration with Qwen model"""

import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with local Ollama instance"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = "nomic-embed-text"  # Ollama embedding model
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Optional[Dict[str, Any]]:
        """Send chat completion request to Ollama"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Ollama request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            return None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Ollama's embedding endpoint"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text[:8192]  # Limit text length
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("embedding")
        except httpx.RequestError as e:
            logger.error(f"Ollama embedding request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama embedding response: {e}")
            return None
    
    async def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Optional[str]:
        """Generate text completion using Ollama"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            result = await self.chat(messages, temperature, max_tokens)
            if result and "message" in result:
                return result["message"].get("content", "")
            return None
        except Exception as e:
            logger.error(f"Ollama completion failed: {e}")
            return None
    
    async def check_health(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                ) as response:
                    async for chunk in response.aiter_lines():
                        data = json.loads(chunk)
                        if data.get("status") == "success":
                            return True
            return False
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False


# Singleton instance
_ollama_service: Optional[OllamaService] = None

def get_ollama_service() -> OllamaService:
    """Get or create Ollama service instance"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
