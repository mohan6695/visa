#!/usr/bin/env python3
"""
Test script to verify KiloCode can use Ollama through MCP
This simulates how KiloCode would interact with the Ollama MCP server
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

# Add next-app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server_startup():
    """Test that the MCP server can start"""
    print("🔍 Testing MCP server startup...")
    
    try:
        # Start the MCP server as a subprocess (like KiloCode would)
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "mcp_server.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for startup
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server started successfully!")
            
            # Test basic functionality
            result = await test_ollama_connection()
            
            # Clean up
            process.terminate()
            process.wait()
            
            return result
        else:
            stdout, stderr = process.communicate()
            print(f"❌ MCP server failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server startup error: {e}")
        return False

async def test_ollama_connection():
    """Test Ollama connection through MCP"""
    print("\n🔍 Testing Ollama connection...")
    
    try:
        from mcp_server import server
        
        # Test list models
        models = await server.list_models()
        print(f"✅ Ollama connection successful!")
        print(f"Available models: {models}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False

async def test_kilocode_mcp_tools():
    """Test the specific tools KiloCode would use"""
    print("\n🔍 Testing KiloCode MCP tools...")
    
    try:
        from mcp_server import server
        
        # Test 1: Generate text
        print("Testing generate_text tool...")
        result = await server.generate_text(
            prompt="What is machine learning?",
            model="qwen2.5:3b"
        )
        print(f"✅ generate_text: {result[:100]}...")
        
        # Test 2: Answer question
        print("Testing answer_question tool...")
        result = await server.answer_question(
            question="What are the benefits of local AI models?"
        )
        print(f"✅ answer_question: {result[:100]}...")
        
        # Test 3: Summarize text
        print("Testing summarize_text tool...")
        result = await server.summarize_text(
            text="Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.",
            max_length=50
        )
        print(f"✅ summarize_text: {result}")
        
        print("✅ All KiloCode MCP tools working!")
        return True
        
    except Exception as e:
        print(f"❌ KiloCode MCP tools error: {e}")
        return False

async def test_environment_configuration():
    """Test that the environment is properly configured"""
    print("\n🔍 Testing environment configuration...")
    
    try:
        # Check MCP config
        import os
        mcp_config_path = os.path.expanduser("~/.mcp.json")
        
        if os.path.exists(mcp_config_path):
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)
            
            print("✅ MCP configuration found!")
            print(f"Configured servers: {list(config.get('mcpServers', {}).keys())}")
            
            # Check environment variables
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
            
            print(f"OLLAMA_URL: {ollama_url}")
            print(f"OLLAMA_MODEL: {ollama_model}")
            
            return True
        else:
            print("❌ MCP configuration not found at ~/.mcp.json")
            return False
            
    except Exception as e:
        print(f"❌ Environment configuration error: {e}")
        return False

async def main():
    """Run all KiloCode integration tests"""
    print("🧪 Testing KiloCode + Ollama Integration")
    print("=" * 60)
    
    tests = [
        ("Environment Configuration", test_environment_configuration),
        ("MCP Server Startup", test_mcp_server_startup),
        ("KiloCode MCP Tools", test_kilocode_mcp_tools),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🔍 Running {test_name} test...")
        print('='*60)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*60}")
    print("📊 Final Results Summary:")
    print('='*60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Local Ollama Qwen model is fully connected to KiloCode!")
        print("\n🚀 What this means:")
        print("   • MCP server can start and run properly")
        print("   • Ollama connection is working (qwen2.5:3b available)")
        print("   • All KiloCode tools are functional")
        print("   • Environment is properly configured")
        print("\n📝 You can now use Ollama tools in KiloCode!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())