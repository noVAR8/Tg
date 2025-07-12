#!/usr/bin/env python3
"""
Backend API Testing Script for Telegram Bot
Tests all core API endpoints and integrations
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://3312ad11-8248-4d7e-86f5-1571a6d10e5d.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TelegramBotTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    async def test_basic_api(self):
        """Test basic API endpoint /api/"""
        try:
            async with self.session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "running":
                        self.log_test("Basic API", "PASS", "Server is running", data)
                        return True
                    else:
                        self.log_test("Basic API", "FAIL", "Server status not 'running'", data)
                        return False
                else:
                    self.log_test("Basic API", "FAIL", f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Basic API", "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def test_usersbox_integration(self):
        """Test usersbox API integration endpoint /api/test-usersbox"""
        try:
            async with self.session.post(f"{API_BASE}/test-usersbox") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        # Check if we got valid usersbox response
                        usersbox_data = data.get("data", {})
                        if usersbox_data.get("status") == "success":
                            balance_info = usersbox_data.get("data", {})
                            balance = balance_info.get("balance", 0)
                            is_active = balance_info.get("is_active", False)
                            
                            self.log_test("Usersbox Integration", "PASS", 
                                        f"API token works, balance: {balance}, active: {is_active}", 
                                        balance_info)
                            return True
                        else:
                            self.log_test("Usersbox Integration", "FAIL", 
                                        "Usersbox API returned error", usersbox_data)
                            return False
                    else:
                        self.log_test("Usersbox Integration", "FAIL", 
                                    "API endpoint returned error", data)
                        return False
                else:
                    self.log_test("Usersbox Integration", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Usersbox Integration", "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def test_webhook_setup(self):
        """Test webhook setup endpoint /api/set-webhook"""
        try:
            async with self.session.post(f"{API_BASE}/set-webhook") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        webhook_url = data.get("webhook_url")
                        telegram_response = data.get("telegram_response", {})
                        
                        if telegram_response.get("ok"):
                            self.log_test("Webhook Setup", "PASS", 
                                        f"Webhook set successfully to {webhook_url}", 
                                        telegram_response)
                            return True
                        else:
                            self.log_test("Webhook Setup", "FAIL", 
                                        "Telegram API rejected webhook", telegram_response)
                            return False
                    else:
                        self.log_test("Webhook Setup", "FAIL", 
                                    "Webhook setup failed", data)
                        return False
                else:
                    self.log_test("Webhook Setup", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Webhook Setup", "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def test_stats_endpoint(self):
        """Test stats endpoint /api/stats for database connectivity"""
        try:
            async with self.session.get(f"{API_BASE}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we got expected stats structure
                    required_fields = ["total_messages", "total_searches", "recent_messages", "recent_searches"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        total_messages = data.get("total_messages", 0)
                        total_searches = data.get("total_searches", 0)
                        
                        self.log_test("Stats Endpoint", "PASS", 
                                    f"Database connected, {total_messages} messages, {total_searches} searches", 
                                    data)
                        return True
                    else:
                        self.log_test("Stats Endpoint", "FAIL", 
                                    f"Missing fields: {missing_fields}", data)
                        return False
                else:
                    self.log_test("Stats Endpoint", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Stats Endpoint", "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def test_webhook_endpoint(self):
        """Test webhook endpoint /api/webhook with sample data"""
        try:
            # Sample Telegram update data
            sample_update = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Test",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "Test",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "/start"
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        self.log_test("Webhook Endpoint", "PASS", 
                                    "Webhook processes updates correctly", data)
                        return True
                    else:
                        self.log_test("Webhook Endpoint", "FAIL", 
                                    "Webhook returned error status", data)
                        return False
                else:
                    self.log_test("Webhook Endpoint", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Webhook Endpoint", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_phone_number_formatting(self):
        """Test phone number formatting with various formats"""
        try:
            # Test different phone number formats that should be normalized
            test_cases = [
                {
                    "input": "+7 929 847-04-21",
                    "expected": "+79298470421",
                    "description": "International format with spaces and dashes"
                },
                {
                    "input": "8-929-847-04-21", 
                    "expected": "+79298470421",
                    "description": "Russian format starting with 8"
                },
                {
                    "input": "79298470421",
                    "expected": "+79298470421", 
                    "description": "Russian format without +"
                },
                {
                    "input": "9298470421",
                    "expected": "+79298470421",
                    "description": "Mobile format without country code"
                },
                {
                    "input": "+7(929)847-04-21",
                    "expected": "+79298470421",
                    "description": "Format with parentheses"
                }
            ]
            
            all_passed = True
            results = []
            
            for case in test_cases:
                # Test via webhook with search command
                sample_update = {
                    "update_id": 123456790,
                    "message": {
                        "message_id": 2,
                        "from": {
                            "id": 987654321,
                            "is_bot": False,
                            "first_name": "Test",
                            "username": "testuser"
                        },
                        "chat": {
                            "id": 987654321,
                            "first_name": "Test", 
                            "username": "testuser",
                            "type": "private"
                        },
                        "date": 1640995200,
                        "text": f"/search {case['input']}"
                    }
                }
                
                async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "ok":
                            results.append({
                                "input": case['input'],
                                "description": case['description'],
                                "status": "processed"
                            })
                        else:
                            all_passed = False
                            results.append({
                                "input": case['input'],
                                "description": case['description'], 
                                "status": "failed",
                                "error": data
                            })
                    else:
                        all_passed = False
                        results.append({
                            "input": case['input'],
                            "description": case['description'],
                            "status": "http_error",
                            "error": f"HTTP {response.status}"
                        })
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            if all_passed:
                self.log_test("Phone Number Formatting", "PASS", 
                            f"All {len(test_cases)} phone formats processed correctly", results)
                return True
            else:
                self.log_test("Phone Number Formatting", "FAIL", 
                            "Some phone formats failed processing", results)
                return False
                
        except Exception as e:
            self.log_test("Phone Number Formatting", "FAIL", f"Test execution error: {str(e)}")
            return False

    async def test_usersbox_query_formatting(self):
        """Test that formatted queries work with usersbox API (no 400 errors)"""
        try:
            # Test the specific phone number mentioned in the review request
            test_phone = "+7 929 847-04-21"
            
            sample_update = {
                "update_id": 123456791,
                "message": {
                    "message_id": 3,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Test",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "Test",
                        "username": "testuser", 
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": test_phone  # Direct search without /search command
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        self.log_test("Usersbox Query Formatting", "PASS", 
                                    f"Phone number '{test_phone}' processed without 400 error", data)
                        return True
                    else:
                        self.log_test("Usersbox Query Formatting", "FAIL", 
                                    "Webhook returned error status", data)
                        return False
                else:
                    self.log_test("Usersbox Query Formatting", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
                    
        except Exception as e:
            self.log_test("Usersbox Query Formatting", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_error_handling_improvements(self):
        """Test improved error handling with helpful messages"""
        try:
            # Test with an invalid/empty search query
            sample_update = {
                "update_id": 123456792,
                "message": {
                    "message_id": 4,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Test",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "Test",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "/search"  # Empty search query
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        self.log_test("Error Handling", "PASS", 
                                    "Empty search query handled gracefully", data)
                        return True
                    else:
                        self.log_test("Error Handling", "FAIL", 
                                    "Webhook returned error for empty query", data)
                        return False
                else:
                    self.log_test("Error Handling", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
                    
        except Exception as e:
            self.log_test("Error Handling", "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Telegram Bot Backend Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 60)
        
        tests = [
            ("Basic API Health Check", self.test_basic_api),
            ("Usersbox API Integration", self.test_usersbox_integration),
            ("Webhook Setup", self.test_webhook_setup),
            ("Database Stats", self.test_stats_endpoint),
            ("Webhook Processing", self.test_webhook_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Test execution error: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend is working correctly.")
        elif passed > total // 2:
            print("⚠️  Most tests passed, but some issues found.")
        else:
            print("❌ Multiple critical issues found.")
        
        return self.test_results

async def main():
    """Main test runner"""
    async with TelegramBotTester() as tester:
        results = await tester.run_all_tests()
        
        # Save detailed results
        with open("/app/backend_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())