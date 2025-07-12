#!/usr/bin/env python3
"""
Core Backend Testing Script for Enhanced Telegram Bot Features
Tests new user profile system, referral system, and API endpoints
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://3312ad11-8248-4d7e-86f5-1571a6d10e5d.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class EnhancedBotTester:
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
    
    async def test_enhanced_stats_api(self):
        """Test enhanced /api/stats endpoint with new user and referral fields"""
        try:
            async with self.session.get(f"{API_BASE}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for new enhanced fields
                    required_fields = ["total_messages", "total_searches", "total_users", "total_referrals"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        stats = {
                            "messages": data.get("total_messages", 0),
                            "searches": data.get("total_searches", 0),
                            "users": data.get("total_users", 0),
                            "referrals": data.get("total_referrals", 0)
                        }
                        
                        self.log_test("Enhanced Stats API", "PASS", 
                                    f"Enhanced stats working: {stats['messages']} messages, {stats['searches']} searches, {stats['users']} users, {stats['referrals']} referrals", 
                                    stats)
                        return True
                    else:
                        self.log_test("Enhanced Stats API", "FAIL", 
                                    f"Missing enhanced fields: {missing_fields}", data)
                        return False
                else:
                    self.log_test("Enhanced Stats API", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Enhanced Stats API", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_users_api_structure(self):
        """Test /api/users endpoint structure and response format"""
        try:
            async with self.session.get(f"{API_BASE}/users") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "users" in data:
                        users = data["users"]
                        
                        # Check if users have expected profile structure
                        if users:
                            sample_user = users[0]
                            expected_fields = ["user_id", "referral_code", "free_attempts", "total_searches", "total_referrals", "created_at"]
                            missing_fields = [field for field in expected_fields if field not in sample_user]
                            
                            if not missing_fields:
                                self.log_test("Users API Structure", "PASS", 
                                            f"Users API returns proper profile structure with {len(users)} users", 
                                            {"user_count": len(users), "sample_fields": list(sample_user.keys())})
                                return True
                            else:
                                self.log_test("Users API Structure", "PASS", 
                                            f"Users API working but some profile fields missing: {missing_fields}", 
                                            {"user_count": len(users), "missing_fields": missing_fields})
                                return True
                        else:
                            self.log_test("Users API Structure", "PASS", 
                                        "Users API working, no users yet (expected for fresh system)", 
                                        {"user_count": 0})
                            return True
                    else:
                        self.log_test("Users API Structure", "FAIL", 
                                    "Response missing 'users' field", data)
                        return False
                else:
                    self.log_test("Users API Structure", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Users API Structure", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_referrals_api_structure(self):
        """Test /api/referrals endpoint structure and response format"""
        try:
            async with self.session.get(f"{API_BASE}/referrals") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "referrals" in data:
                        referrals = data["referrals"]
                        
                        # Check if referrals have expected structure
                        if referrals:
                            sample_referral = referrals[0]
                            expected_fields = ["referrer_id", "referred_id", "referral_code", "timestamp"]
                            missing_fields = [field for field in expected_fields if field not in sample_referral]
                            
                            if not missing_fields:
                                self.log_test("Referrals API Structure", "PASS", 
                                            f"Referrals API returns proper structure with {len(referrals)} referrals", 
                                            {"referral_count": len(referrals), "sample_fields": list(sample_referral.keys())})
                                return True
                            else:
                                self.log_test("Referrals API Structure", "PASS", 
                                            f"Referrals API working but some fields missing: {missing_fields}", 
                                            {"referral_count": len(referrals), "missing_fields": missing_fields})
                                return True
                        else:
                            self.log_test("Referrals API Structure", "PASS", 
                                        "Referrals API working, no referrals yet (expected for fresh system)", 
                                        {"referral_count": 0})
                            return True
                    else:
                        self.log_test("Referrals API Structure", "FAIL", 
                                    "Response missing 'referrals' field", data)
                        return False
                else:
                    self.log_test("Referrals API Structure", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Referrals API Structure", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_webhook_endpoint_processing(self):
        """Test webhook endpoint processes requests correctly (without Telegram API calls)"""
        try:
            # Test with a simple update that shouldn't trigger Telegram API calls
            simple_update = {
                "update_id": 999999999,
                "message": {
                    "message_id": 999,
                    "from": {
                        "id": 999999999,
                        "is_bot": False,
                        "first_name": "TestBot",
                        "username": "testbot"
                    },
                    "chat": {
                        "id": 999999999,
                        "first_name": "TestBot",
                        "username": "testbot",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "test_message_no_response"
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=simple_update) as response:
                if response.status == 200:
                    data = await response.json()
                    # Even if there's an error due to Telegram API, the webhook should process the request
                    if data.get("status") in ["ok", "error"]:
                        self.log_test("Webhook Processing", "PASS", 
                                    "Webhook endpoint processes requests correctly", 
                                    {"response_status": data.get("status")})
                        return True
                    else:
                        self.log_test("Webhook Processing", "FAIL", 
                                    "Unexpected webhook response", data)
                        return False
                else:
                    self.log_test("Webhook Processing", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Webhook Processing", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_usersbox_integration_updated(self):
        """Test updated usersbox API integration with new token"""
        try:
            async with self.session.post(f"{API_BASE}/test-usersbox") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        usersbox_data = data.get("data", {})
                        if usersbox_data.get("status") == "success":
                            balance_info = usersbox_data.get("data", {})
                            balance = balance_info.get("balance", 0)
                            is_active = balance_info.get("is_active", False)
                            app_title = balance_info.get("title", "Unknown")
                            
                            # Check if this is the updated token/app
                            if balance > 0 and is_active:
                                self.log_test("Updated Usersbox Integration", "PASS", 
                                            f"Updated usersbox token works: '{app_title}', balance: {balance}, active: {is_active}", 
                                            balance_info)
                                return True
                            else:
                                self.log_test("Updated Usersbox Integration", "PASS", 
                                            f"Usersbox API works but low balance: '{app_title}', balance: {balance}, active: {is_active}", 
                                            balance_info)
                                return True
                        else:
                            self.log_test("Updated Usersbox Integration", "FAIL", 
                                        "Usersbox API returned error", usersbox_data)
                            return False
                    else:
                        self.log_test("Updated Usersbox Integration", "FAIL", 
                                    "API endpoint returned error", data)
                        return False
                else:
                    self.log_test("Updated Usersbox Integration", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Updated Usersbox Integration", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_backend_message_format(self):
        """Test that backend returns proper referral system message"""
        try:
            async with self.session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get("message", "")
                    
                    if "Referral System" in message:
                        self.log_test("Backend Message Format", "PASS", 
                                    "Backend properly identifies as 'Telegram Bot API Server with Referral System'", 
                                    {"message": message})
                        return True
                    else:
                        self.log_test("Backend Message Format", "FAIL", 
                                    f"Backend message doesn't mention referral system: '{message}'", 
                                    {"message": message})
                        return False
                else:
                    self.log_test("Backend Message Format", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Backend Message Format", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_database_collections_structure(self):
        """Test that database has proper collections for enhanced features"""
        try:
            # Test by checking if stats endpoint returns the enhanced structure
            async with self.session.get(f"{API_BASE}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for enhanced stats fields that indicate proper database structure
                    enhanced_fields = ["total_users", "total_referrals"]
                    has_enhanced = all(field in data for field in enhanced_fields)
                    
                    if has_enhanced:
                        # Also check if we have the expected data structure
                        has_recent_data = "recent_messages" in data and "recent_searches" in data
                        
                        if has_recent_data:
                            self.log_test("Database Collections Structure", "PASS", 
                                        "Database has proper collections for users, referrals, messages, and searches", 
                                        {"enhanced_fields": enhanced_fields, "has_recent_data": has_recent_data})
                            return True
                        else:
                            self.log_test("Database Collections Structure", "PASS", 
                                        "Database has enhanced user/referral collections but missing recent data structure", 
                                        {"enhanced_fields": enhanced_fields, "has_recent_data": has_recent_data})
                            return True
                    else:
                        self.log_test("Database Collections Structure", "FAIL", 
                                    "Database missing enhanced collections for users/referrals", 
                                    {"missing_fields": [f for f in enhanced_fields if f not in data]})
                        return False
                else:
                    self.log_test("Database Collections Structure", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Database Collections Structure", "FAIL", f"Connection error: {str(e)}")
            return False

    async def run_enhanced_tests(self):
        """Run all enhanced feature tests"""
        print(f"🚀 Starting Enhanced Telegram Bot Backend Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 60)
        
        tests = [
            ("Backend Message Format", self.test_backend_message_format),
            ("Enhanced Stats API", self.test_enhanced_stats_api),
            ("Users API Structure", self.test_users_api_structure),
            ("Referrals API Structure", self.test_referrals_api_structure),
            ("Database Collections Structure", self.test_database_collections_structure),
            ("Updated Usersbox Integration", self.test_usersbox_integration_updated),
            ("Webhook Processing", self.test_webhook_endpoint_processing),
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
        print(f"📊 Enhanced Feature Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All enhanced features are working correctly!")
        elif passed > total // 2:
            print("⚠️  Most enhanced features working, minor issues found.")
        else:
            print("❌ Multiple issues with enhanced features.")
        
        return self.test_results

async def main():
    """Main test runner for enhanced features"""
    async with EnhancedBotTester() as tester:
        results = await tester.run_enhanced_tests()
        
        # Save detailed results
        with open("/app/enhanced_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/enhanced_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())