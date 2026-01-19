#!/usr/bin/env python3
"""Simple Ollama MCP Server for KiloCode Integration"""

import asyncio
import json
import sys
import httpx

async def main():
    """Main function for stdio-based MCP communication"""
    ollama_url = "http://localhost:11434"
    default_model = "qwen2.5:3b"
    
    async def call_ollama(prompt, model=None, temperature=0.7, max_tokens=1000):
        model = model or default_model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{ollama_url}/api/generate", json=payload)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return f"Error: {response.status_code}"
    
    # Read requests from stdin line by line
    reader = asyncio.StreamReader()
    
    async def read_stdin():
        line = await reader.readline()
        return line.decode().strip()
    
    while True:
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=30)
            if not line:
                break
            
            request = json.loads(line.decode())
            method = request.get("method", "")
            params = request.get("params", {})
            
            if method == "list_tools":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "generate_text",
                                "description": "Generate text using Ollama",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {"type": "string"},
                                        "model": {"type": "string"},
                                        "temperature": {"type": "number"},
                                        "max_tokens": {"type": "integer"}
                                    },
                                    "required": ["prompt"]
                                }
                            },
                            {
                                "name": "answer_question",
                                "description": "Answer a question",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string"},
                                        "context": {"type": "string"}
                                    },
                                    "required": ["question"]
                                }
                            }
                        ]
                    }
                }
                print(json.dumps(response), flush=True)
            
            elif method == "call_tool":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "generate_text":
                    result = await call_ollama(
                        arguments.get("prompt", ""),
                        arguments.get("model"),
                        arguments.get("temperature", 0.7),
                        arguments.get("max_tokens", 1000)
                    )
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": result}
                    }
                    print(json.dumps(response), flush=True)
                
                elif tool_name == "answer_question":
                    question = arguments.get("question", "")
                    context = arguments.get("context", "")
                    if context:
                        prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
                    else:
                        prompt = f"Question: {question}\n\nAnswer:"
                    result = await call_ollama(prompt)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": result}
                    }
                    print(json.dumps(response), flush=True)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
                    print(json.dumps(response), flush=True)
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32600, "message": f"Unknown method: {method}"}
                }
                print(json.dumps(response), flush=True)
        
        except asyncio.TimeoutError:
            continue
        except json.JSONDecodeError:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Invalid JSON"}
            }
            print(json.dumps(response), flush=True)
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
