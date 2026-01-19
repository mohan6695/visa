#!/usr/bin/env python3
"""
Test script for Ollama integration in KiloCode
This script tests the Ollama model and the AI service integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import the AI service
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from src.services.ai_service import AIService
from src.core.config import settings
from src.core.redis import get_redis
import redis.asyncio as redis

async def test_ollama_connection():
    """Test direct Ollama API connection"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                print("✅ Ollama connection successful!")
                print(f"Available models: {[m['name'] for m in models.get('models', [])]}")
                return True
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False

async def test_ollama_generation():
    """Test text generation with Ollama"""
    try:
        import httpx
        
        payload = {
            "model": "qwen2.5:3b",
            "prompt": "What are the benefits of using local AI models?",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Ollama text generation successful!")
                print(f"Response: {data['response'][:100]}...")
                return True
            else:
                print(f"❌ Generation failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

async def test_ai_service_integration():
    """Test the AI service with Ollama configuration"""
    try:
        # Check configuration
        print(f"AI Provider: {settings.AI_PROVIDER}")
        print(f"Ollama URL: {settings.OLLAMA_URL}")
        print(f"Ollama Model: {settings.OLLAMA_MODEL}")
        
        # Test if the service can be initialized
        redis_client = redis.from_url(settings.REDIS_URL)
        
        from src.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        ai_service = AIService(redis_client, embedding_service)
        print("✅ AI Service initialized successfully!")
        
        # Test a simple call
        result = await ai_service.call_ai_model(
            prompt="Hello, how are you?",
            model=settings.OLLAMA_MODEL,
            max_tokens=100
        )
        
        if result:
            print("✅ AI Service Ollama integration working!")
            print(f"Response: {result[:100]}...")
            return True
        else:
            print("❌ AI Service returned no response")
            return False
            
    except Exception as e:
        print(f"❌ AI Service integration error: {e}")
        return False

async def test_mcp_server():
    """Test the MCP server tools"""
    try:
        # Import the MCP server
        from mcp_server import server
        
        # Test list models
        models = await server.list_models()
        print("✅ MCP server - List models successful!")
        print(f"Models: {models}")
        
        # Test text generation
        result = await server.generate_text(
            prompt="What is artificial intelligence?",
            model="qwen2.5:3b"
        )
        print("✅ MCP server - Text generation successful!")
        print(f"Response: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Ollama Integration with KiloCode")
    print("=" * 50)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Ollama Generation", test_ollama_generation),
        ("AI Service Integration", test_ai_service_integration),
        ("MCP Server", test_mcp_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ollama integration is working perfectly!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())