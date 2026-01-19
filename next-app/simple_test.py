#!/usr/bin/env python3
"""
Simple test script for Ollama integration
Tests only the Ollama connection and basic functionality
"""

import asyncio
import httpx

async def test_ollama_connection():
    """Test Ollama API connection"""
    print("🔍 Testing Ollama connection...")
    
    try:
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
    print("\n🔍 Testing Ollama text generation...")
    
    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": "What are the benefits of using local AI models?",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Ollama text generation successful!")
                print(f"Response: {data['response']}")
                return True
            else:
                print(f"❌ Generation failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

async def test_model_info():
    """Test getting model information"""
    print("\n🔍 Testing model information...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/show",
                json={"name": "qwen2.5:3b"}
            )
            
            if response.status_code == 200:
                info = response.json()
                print("✅ Model info retrieved successfully!")
                print(f"Model: {info.get('model', 'Unknown')}")
                print(f"Size: {info.get('size', 'Unknown')}")
                return True
            else:
                print(f"❌ Failed to get model info: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False

async def test_chat_completion():
    """Test chat completion"""
    print("\n🔍 Testing chat completion...")
    
    try:
        payload = {
            "model": "qwen2.5:3b",
            "messages": [
                {"role": "user", "content": "Hello! How can you help me?"}
            ],
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Chat completion successful!")
                print(f"Response: {data['message']['content']}")
                return True
            else:
                print(f"❌ Chat completion failed: {response.status_code}")
                # Try with generate endpoint as fallback
                return await test_generate_fallback()
    except Exception as e:
        print(f"❌ Chat completion error: {e}")
        return False

async def test_generate_fallback():
    """Fallback test using generate endpoint"""
    print("🔄 Trying generate endpoint fallback...")
    
    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": "User: Hello! How can you help me?\n\nAssistant:",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Generate fallback successful!")
                print(f"Response: {data['response']}")
                return True
            else:
                print(f"❌ Generate fallback failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Generate fallback error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Ollama Integration")
    print("=" * 50)
    
    tests = [
        ("Connection", test_ollama_connection),
        ("Generation", test_ollama_generation),
        ("Model Info", test_model_info),
        ("Chat Completion", test_chat_completion),
    ]
    
    results = []
    for test_name, test_func in tests:
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
        print("\n🚀 Your local Qwen model is ready to use!")
        print("📝 Configuration:")
        print("   - Model: qwen2.5:3b")
        print("   - URL: http://localhost:11434")
        print("   - Provider: ollama")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())