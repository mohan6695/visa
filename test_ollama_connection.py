#!/usr/bin/env python3
"""Test script to verify Ollama Qwen model connection in KiloCode"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src.services.ollama_service import get_ollama_service, OllamaService
from src.core.config import settings


async def test_ollama_connection():
    """Test Ollama connection with Qwen model"""
    print("=" * 60)
    print("Ollama Qwen Model Connection Test")
    print("=" * 60)
    
    # Display current configuration
    print("\n📋 Current Configuration:")
    print(f"   OLLAMA_URL: {settings.OLLAMA_URL}")
    print(f"   OLLAMA_MODEL: {settings.OLLAMA_MODEL}")
    print(f"   AI_PROVIDER: {settings.AI_PROVIDER}")
    
    # Create service instance
    ollama_service = get_ollama_service()
    
    # Test 1: Health check
    print("\n🔍 Test 1: Health Check")
    print("-" * 40)
    is_healthy = await ollama_service.check_health()
    if is_healthy:
        print("✅ Ollama service is healthy!")
    else:
        print("❌ Ollama service is not responding!")
        print("   Make sure Ollama is running: `ollama serve`")
        return False
    
    # Test 2: List available models
    print("\n🔍 Test 2: Available Models")
    print("-" * 40)
    models = await ollama_service.list_models()
    if models:
        print("✅ Available models:")
        for model in models:
            print(f"   - {model}")
    else:
        print("⚠️  No models found or error listing models")
    
    # Test 3: Check if Qwen model is available
    print("\n🔍 Test 3: Qwen Model Check")
    print("-" * 40)
    expected_model = settings.OLLAMA_MODEL
    qwen_available = any(expected_model in model for model in models)
    if qwen_available:
        print(f"✅ Qwen model '{expected_model}' is available!")
    else:
        print(f"⚠️  Qwen model '{expected_model}' not found in available models")
        print(f"   Available: {models}")
        print(f"   To download: `ollama pull {expected_model}`")
    
    # Test 4: Generate a simple completion (if Qwen is available)
    if qwen_available:
        print("\n🔍 Test 4: Generate Completion with Qwen")
        print("-" * 40)
        test_prompt = "What is the capital of France? Answer briefly."
        print(f"   Prompt: {test_prompt}")
        
        response = await ollama_service.generate_completion(
            prompt=test_prompt,
            system_prompt="You are a helpful assistant. Answer concisely.",
            temperature=0.3,
            max_tokens=100
        )
        
        if response:
            print(f"✅ Response: {response}")
        else:
            print("❌ Failed to generate completion")
            return False
    else:
        print("\n⏭️  Skipping completion test (Qwen model not available)")
    
    print("\n" + "=" * 60)
    print("✅ Ollama connection test completed!")
    print("=" * 60)
    
    return True


async def test_in_kilocode_ai_service():
    """Test the integration through KiloCode's AI service"""
    print("\n" + "=" * 60)
    print("Testing KiloCode AI Service Integration")
    print("=" * 60)
    
    # Update config to use ollama
    import os
    os.environ["AI_PROVIDER"] = "ollama"
    settings.AI_PROVIDER = "ollama"
    
    try:
        from src.services.optimized_ai_service import OptimizedAIService
        ai_service = OptimizedAIService()
        
        print("\n📋 Testing AI Service with Ollama provider")
        print(f"   Provider: {ai_service.provider}")
        
        # Test a simple query
        response = await ai_service.get_response(
            messages=[{"role": "user", "content": "Say hello in one word!"}],
            context=None
        )
        
        if response:
            print(f"✅ AI Service Response: {response}")
        else:
            print("⚠️  AI Service returned empty response")
            
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(test_ollama_connection())
    
    if success:
        asyncio.run(test_in_kilocode_ai_service())
    
    print("\n📝 Next Steps:")
    print("   1. If Ollama is not running, start it with: ollama serve")
    print("   2. If Qwen model is not installed, download with: ollama pull qwen2.5:3b")
    print("   3. Set AI_PROVIDER=ollama in your .env file")
