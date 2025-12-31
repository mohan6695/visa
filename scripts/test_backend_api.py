#!/usr/bin/env python3
"""
Test script for the Visa Platform Backend API
This script tests the core functionality of the backend API endpoints.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make an HTTP request and return the JSON response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    return await self._handle_response(response)
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"Unsupported method: {method}")
        
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {str(e)}", "status": "failed", "status_code": 0, "success": False}
    
    async def _handle_response(self, response) -> Dict[Any, Any]:
        """Handle HTTP response"""
        try:
            if response.content_type == 'application/json':
                data = await response.json()
            else:
                data = {"text": await response.text()}
            
            return {
                "status_code": response.status,
                "data": data,
                "success": 200 <= response.status < 300
            }
        except Exception as e:
            return {
                "status_code": response.status,
                "error": f"Failed to parse response: {str(e)}",
                "success": False
            }
    
    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("🩺 Testing Health Endpoints...")
        
        # Basic health check
        result = await self.make_request("GET", "/health")
        print(f"  ✓ GET /health: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        # Detailed health check
        result = await self.make_request("GET", "/health/detailed")
        print(f"  ✓ GET /health/detailed: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        # AI health check
        result = await self.make_request("GET", "/health/ai")
        print(f"  ✓ GET /health/ai: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        # Chat health check
        result = await self.make_request("GET", "/health/chat")
        print(f"  ✓ GET /health/chat: {result['status_code']} - {'✅' if result['success'] else '❌'}")
    
    async def test_ai_endpoints(self):
        """Test AI-related endpoints"""
        print("\n🤖 Testing AI Endpoints...")
        
        # Test AI question (this will fail without proper auth/DB setup, but should connect)
        test_data = {
            "question": "What is a visa?",
            "group_id": 1,
            "use_cache": False
        }
        
        result = await self.make_request("POST", "/api/v1/ai/answer", test_data)
        print(f"  ✓ POST /api/v1/ai/answer: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        if not result['success']:
            print(f"    Error: {result.get('data', {}).get('detail', 'Unknown error')}")
        
        # Test AI search
        search_result = await self.make_request("GET", "/api/v1/ai/search?query=visa&group_id=1")
        print(f"  ✓ GET /api/v1/ai/search: {search_result['status_code']} - {'✅' if search_result['success'] else '❌'}")
    
    async def test_chat_endpoints(self):
        """Test chat-related endpoints"""
        print("\n💬 Testing Chat Endpoints...")
        
        # Test chat history (will likely fail without auth, but should connect)
        result = await self.make_request("GET", "/api/v1/chat/history?community_id=1")
        print(f"  ✓ GET /api/v1/chat/history: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        if not result['success']:
            print(f"    Error: {result.get('data', {}).get('detail', 'Unknown error')}")
    
    async def test_ai_service_integration(self):
        """Test the AI service integration specifically"""
        print("\n🔧 Testing AI Service Integration...")
        
        # This should work if the backend can connect to AI providers
        result = await self.make_request("POST", "/health/test-ai")
        print(f"  ✓ POST /health/test-ai: {result['status_code']} - {'✅' if result['success'] else '❌'}")
        
        if result['success']:
            test_result = result['data'].get('test_result', {})
            print(f"    AI Response: {test_result.get('answer', 'No answer')[:100]}...")
            print(f"    Source: {test_result.get('source', 'unknown')}")
        else:
            print(f"    Error: {result.get('data', {}).get('detail', 'Unknown error')}")

async def main():
    """Run all tests"""
    print("🚀 Starting Visa Platform Backend API Tests")
    print("=" * 60)
    
    async with APITester() as tester:
        # Run all test suites
        await tester.test_health_endpoints()
        await tester.test_ai_endpoints()
        await tester.test_chat_endpoints()
        await tester.test_ai_service_integration()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("\nNotes:")
    print("- Some endpoints may fail due to missing authentication")
    print("- Database connections may fail if not properly configured")
    print("- AI endpoints require proper API keys to be configured")
    print("- This test mainly verifies API connectivity and basic responses")

if __name__ == "__main__":
    asyncio.run(main())