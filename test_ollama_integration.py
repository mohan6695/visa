#!/usr/bin/env python3
"""
Test script for Ollama integration with KiloCode
Usage: python test_ollama_integration.py
"""
import sys
sys.path.insert(0, 'backend/src')

from services.ollama_client import OllamaClient, generate, chat_complete

def test_ollama():
    print("=" * 50)
    print("Ollama Integration Test")
    print("=" * 50)
    
    # Initialize client
    client = OllamaClient()
    
    # Test 1: List models
    print("\n[1] Available models:")
    models = client.list_models()
    for m in models:
        print(f"   - {m['name']}")
    
    # Test 2: Simple generation
    print("\n[2] Simple generation (2+2):")
    response = generate("What is 2+2?")
    print(f"   Response: {response}")
    
    # Test 3: Chat completion
    print("\n[3] Chat completion:")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    response = chat_complete(messages)
    print(f"   Response: {response}")
    
    # Test 4: Embeddings
    print("\n[4] Embeddings:")
    embedding = client.get_embedding("Hello, world!")
    print(f"   Dimension: {len(embedding)}")
    
    print("\n" + "=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)

if __name__ == "__main__":
    test_ollama()
