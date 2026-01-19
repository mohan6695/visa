#!/usr/bin/env python3
"""
Test script to verify Ollama Qwen model connection in KiloCode
"""
import asyncio
import httpx


async def test_ollama_connection():
    """Test if Ollama is running and Qwen model is available"""
    ollama_url = "http://localhost:11434"
    model_name = "qwen2.5:3b"  # Default model from config
    
    print(f"Testing Ollama connection to {ollama_url}")
    print(f"Model: {model_name}")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Check if Ollama is running
            print("\n[1] Checking if Ollama is running...")
            response = await client.get(f"{ollama_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"✓ Ollama is running!")
                print(f"  Available models: {[m['name'] for m in models]}")
                
                # Check if Qwen is available
                qwen_available = any("qwen" in m['name'].lower() for m in models)
                if qwen_available:
                    print(f"✓ Qwen model found!")
                else:
                    print(f"⚠ Qwen model not found. You may need to pull it:")
                    print(f"   Run: ollama pull {model_name}")
            else:
                print(f"✗ Ollama is not responding: {response.status_code}")
                return False
            
            # Test 2: Generate a simple response
            print("\n[2] Testing text generation with Qwen...")
            payload = {
                "model": model_name,
                "prompt": "Hello! What can you help me with? Respond briefly.",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 100
                }
            }
            
            response = await client.post(
                f"{ollama_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").strip()
                print(f"✓ Generation successful!")
                print(f"  Response: {response_text[:200]}...")
                print(f"  Eval count: {data.get('eval_count', 'N/A')} tokens")
                print(f"  Eval duration: {data.get('eval_duration', 'N/A')}ms")
            else:
                print(f"✗ Generation failed: {response.status_code} - {response.text}")
                return False
            
            # Test 3: Check if model is ready
            print("\n[3] Checking model status...")
            payload = {
                "model": model_name,
                "keep_alive": -1  # Keep model loaded
            }
            response = await client.post(
                f"{ollama_url}/api/show",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Model is ready!")
                print(f"  Model info: {data.get('model', 'N/A')}")
                print(f"  Size: {data.get('size', 'N/A')} bytes")
            else:
                print(f"⚠ Could not get model info: {response.status_code}")
            
            return True
            
    except httpx.ConnectError:
        print(f"✗ Cannot connect to Ollama at {ollama_url}")
        print("\nTo start Ollama:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Run: ollama serve")
        print("3. Run: ollama pull qwen2.5:3b")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_kilocode_integration():
    """Test integration with KiloCode's AI service"""
    print("\n" + "=" * 50)
    print("Testing KiloCode AI Service Integration")
    print("=" * 50)
    
    try:
        # Import KiloCode config
        import sys
        sys.path.insert(0, 'backend')
        
        from src.core.config import settings
        
        print(f"\nKiloCode Config:")
        print(f"  AI Provider: {settings.AI_PROVIDER}")
        print(f"  Ollama URL: {settings.OLLAMA_URL}")
        print(f"  Ollama Model: {settings.OLLAMA_MODEL}")
        
        # Check if AI_PROVIDER is set to 'ollama'
        if settings.AI_PROVIDER == "ollama":
            print("\n✓ AI_PROVIDER is set to 'ollama' - ready for local inference!")
        else:
            print(f"\n⚠ AI_PROVIDER is '{settings.AI_PROVIDER}', not 'ollama'")
            print("  To use Ollama, set AI_PROVIDER=ollama in your .env file")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading KiloCode config: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 50)
    print("Ollama Qwen Integration Test for KiloCode")
    print("=" * 50)
    
    # Test 1: Basic Ollama connection
    success1 = await test_ollama_connection()
    
    # Test 2: KiloCode integration
    success2 = await test_kilocode_integration()
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    if success1 and success2:
        print("✓ All tests passed! Ollama is ready to use with KiloCode.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return success1 and success2


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
