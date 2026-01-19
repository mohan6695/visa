#!/usr/bin/env python3
"""
Ollama MCP Server for KiloCode Integration
Provides AI tools using local Ollama Qwen model
Uses centralized configuration from config/ module
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add project root to path for centralized config
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ollama-mcp-server")

# Ollama configuration from centralized settings
OLLAMA_URL = settings.ollama_url
DEFAULT_MODEL = settings.ollama_model


class OllamaClient:
    """Client for interacting with local Ollama instance"""
    
    def __init__(self, base_url: str = OLLAMA_URL):
        self.base_url = base_url
    
    async def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate text using Ollama"""
        try:
            import httpx
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "response": response.json().get("response", ""),
                        "model": model
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "response": None
                    }
                    
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Chat completion using Ollama"""
        try:
            import httpx
            
            # Convert messages to a single prompt for non-chat models
            prompt = self._format_chat_prompt(messages)
            
            return await self.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages as a prompt"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"[{role.upper()}]: {content}")
        return "\n".join(formatted)
    
    async def embed(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            import httpx
            
            payload = {
                "model": model,
                "prompt": text
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json().get("embedding", [])
                else:
                    logger.error(f"Embedding API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ollama embed error: {e}")
            return []
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"List models error: {e}")
            return []


# Initialize MCP server
app = Server("ollama-mcp-server")
ollama_client = OllamaClient()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="generate_text",
            description="Generate text using local Ollama Qwen model",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to generate text from"
                    },
                    "model": {
                        "type": "string",
                        "description": "Ollama model to use",
                        "default": DEFAULT_MODEL
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for generation (0.0-1.0)",
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to generate",
                        "default": 1000
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="chat_completion",
            description="Chat completion using local Ollama Qwen model",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Chat messages array with role and content",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "model": {
                        "type": "string",
                        "description": "Ollama model to use",
                        "default": DEFAULT_MODEL
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for generation (0.0-1.0)",
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to generate",
                        "default": 1000
                    }
                },
                "required": ["messages"]
            }
        ),
        Tool(
            name="generate_embedding",
            description="Generate text embeddings using Ollama nomic-embed-text model",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to generate embedding for"
                    },
                    "model": {
                        "type": "string",
                        "description": "Embedding model to use",
                        "default": "nomic-embed-text"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="list_ollama_models",
            description="List available Ollama models on the local instance"
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "generate_text":
            result = await ollama_client.generate(
                prompt=arguments["prompt"],
                model=arguments.get("model", DEFAULT_MODEL),
                temperature=arguments.get("temperature", 0.7),
                max_tokens=arguments.get("max_tokens", 1000)
            )
            
            if result["success"]:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "generated_text": result["response"],
                        "model": result["model"]
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": result["error"]
                    }, indent=2)
                )]
        
        elif name == "chat_completion":
            messages = arguments["messages"]
            result = await ollama_client.chat(
                messages=messages,
                model=arguments.get("model", DEFAULT_MODEL),
                temperature=arguments.get("temperature", 0.7),
                max_tokens=arguments.get("max_tokens", 1000)
            )
            
            if result["success"]:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "response": result["response"],
                        "model": result["model"]
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": result["error"]
                    }, indent=2)
                )]
        
        elif name == "generate_embedding":
            embedding = await ollama_client.embed(
                text=arguments["text"],
                model=arguments.get("model", "nomic-embed-text")
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "embedding_dimensions": len(embedding),
                    "embedding": embedding[:10]  # First 10 values for preview
                }, indent=2)
            )]
        
        elif name == "list_ollama_models":
            models = await ollama_client.list_models()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "models": models
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }, indent=2)
            )]
    
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def main():
    """Main entry point"""
    logger.info("Starting Ollama MCP Server for KiloCode...")
    logger.info(f"Using Ollama at: {OLLAMA_URL}")
    logger.info(f"Default model: {DEFAULT_MODEL}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
