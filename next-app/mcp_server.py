#!/usr/bin/env python3
"""
Ollama MCP Server for KiloCode Integration
Provides tools for interacting with local Ollama models including Qwen.
Compatible with MCP SDK 1.x
"""

import asyncio
import json
import httpx
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

class OllamaMCPServer:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.default_model = "qwen2.5:3b"
    
    async def call_ollama_api(self, model: str, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Make API call to local Ollama instance"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 1000),
                    "top_p": kwargs.get("top_p", 0.9),
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                else:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
                else:
                    return []
        except:
            return []
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/show",
                    json={"name": model}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to get model info: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    # Tool implementations
    async def generate_text(self, prompt: str, model: str = None, system_prompt{