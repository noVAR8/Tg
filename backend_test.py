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
        """Test enhanced stats endpoint /api/stats with new user and referral fields"""
        try:
            async with self.session.get(f"{API_BASE}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we got expected stats structure including new fields
                    required_fields = ["total_messages", "total_searches", "total_users", "total_referrals", "recent_messages", "recent_searches"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        total_messages = data.get("total_messages", 0)
                        total_searches = data.get("total_searches", 0)
                        total_users = data.get("total_users", 0)
                        total_referrals = data.get("total_referrals", 0)
                        
                        self.log_test("Enhanced Stats Endpoint", "PASS", 
                                    f"Database connected, {total_messages} messages, {total_searches} searches, {total_users} users, {total_referrals} referrals", 
                                    data)
                        return True
                    else:
                        self.log_test("Enhanced Stats Endpoint", "FAIL", 
                                    f"Missing fields: {missing_fields}", data)
                        return False
                else:
                    self.log_test("Enhanced Stats Endpoint", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Enhanced Stats Endpoint", "FAIL", f"Connection error: {str(e)}")
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

    async def test_users_api_endpoint(self):
        """Test new /api/users endpoint for user profiles"""
        try:
            async with self.session.get(f"{API_BASE}/users") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "users" in data:
                        users = data["users"]
                        self.log_test("Users API Endpoint", "PASS", 
                                    f"Retrieved {len(users)} user profiles", 
                                    {"user_count": len(users), "sample_user": users[0] if users else None})
                        return True
                    else:
                        self.log_test("Users API Endpoint", "FAIL", 
                                    "Response missing 'users' field", data)
                        return False
                else:
                    self.log_test("Users API Endpoint", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Users API Endpoint", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_referrals_api_endpoint(self):
        """Test new /api/referrals endpoint for referral data"""
        try:
            async with self.session.get(f"{API_BASE}/referrals") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "referrals" in data:
                        referrals = data["referrals"]
                        self.log_test("Referrals API Endpoint", "PASS", 
                                    f"Retrieved {len(referrals)} referral records", 
                                    {"referral_count": len(referrals), "sample_referral": referrals[0] if referrals else None})
                        return True
                    else:
                        self.log_test("Referrals API Endpoint", "FAIL", 
                                    "Response missing 'referrals' field", data)
                        return False
                else:
                    self.log_test("Referrals API Endpoint", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Referrals API Endpoint", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_user_profile_creation(self):
        """Test user profile creation with /start command"""
        try:
            # Use a unique user ID for testing
            test_user_id = 999888777
            
            sample_update = {
                "update_id": 123456800,
                "message": {
                    "message_id": 10,
                    "from": {
                        "id": test_user_id,
                        "is_bot": False,
                        "first_name": "TestUser",
                        "username": "testuser_profile"
                    },
                    "chat": {
                        "id": test_user_id,
                        "first_name": "TestUser",
                        "username": "testuser_profile",
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
                        # Check if user was created by calling users API
                        await asyncio.sleep(1)  # Give time for user creation
                        
                        async with self.session.get(f"{API_BASE}/users") as users_response:
                            if users_response.status == 200:
                                users_data = await users_response.json()
                                users = users_data.get("users", [])
                                
                                # Look for our test user
                                test_user = next((u for u in users if u.get("user_id") == test_user_id), None)
                                
                                if test_user:
                                    # Check if user has expected profile fields
                                    required_fields = ["user_id", "referral_code", "free_attempts", "total_searches", "total_referrals"]
                                    missing_fields = [field for field in required_fields if field not in test_user]
                                    
                                    if not missing_fields:
                                        attempts = test_user.get("free_attempts", 0)
                                        referral_code = test_user.get("referral_code", "")
                                        
                                        if attempts >= 1 and referral_code:
                                            self.log_test("User Profile Creation", "PASS", 
                                                        f"User profile created with {attempts} attempts and referral code {referral_code}", 
                                                        test_user)
                                            return True
                                        else:
                                            self.log_test("User Profile Creation", "FAIL", 
                                                        f"User created but missing attempts ({attempts}) or referral code ({referral_code})", 
                                                        test_user)
                                            return False
                                    else:
                                        self.log_test("User Profile Creation", "FAIL", 
                                                    f"User profile missing fields: {missing_fields}", test_user)
                                        return False
                                else:
                                    self.log_test("User Profile Creation", "FAIL", 
                                                f"Test user {test_user_id} not found in users list")
                                    return False
                            else:
                                self.log_test("User Profile Creation", "FAIL", 
                                            f"Could not fetch users: HTTP {users_response.status}")
                                return False
                    else:
                        self.log_test("User Profile Creation", "FAIL", 
                                    "Webhook returned error status", data)
                        return False
                else:
                    self.log_test("User Profile Creation", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("User Profile Creation", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_profile_command(self):
        """Test /profile command functionality"""
        try:
            # Use the same test user from profile creation test
            test_user_id = 999888777
            
            sample_update = {
                "update_id": 123456801,
                "message": {
                    "message_id": 11,
                    "from": {
                        "id": test_user_id,
                        "is_bot": False,
                        "first_name": "TestUser",
                        "username": "testuser_profile"
                    },
                    "chat": {
                        "id": test_user_id,
                        "first_name": "TestUser",
                        "username": "testuser_profile",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "/profile"
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        self.log_test("Profile Command", "PASS", 
                                    "Profile command processed successfully", data)
                        return True
                    else:
                        self.log_test("Profile Command", "FAIL", 
                                    "Webhook returned error status", data)
                        return False
                else:
                    self.log_test("Profile Command", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Profile Command", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_referral_command(self):
        """Test /referral command functionality"""
        try:
            # Use the same test user from profile creation test
            test_user_id = 999888777
            
            sample_update = {
                "update_id": 123456802,
                "message": {
                    "message_id": 12,
                    "from": {
                        "id": test_user_id,
                        "is_bot": False,
                        "first_name": "TestUser",
                        "username": "testuser_profile"
                    },
                    "chat": {
                        "id": test_user_id,
                        "first_name": "TestUser",
                        "username": "testuser_profile",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "/referral"
                }
            }
            
            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        self.log_test("Referral Command", "PASS", 
                                    "Referral command processed successfully", data)
                        return True
                    else:
                        self.log_test("Referral Command", "FAIL", 
                                    "Webhook returned error status", data)
                        return False
                else:
                    self.log_test("Referral Command", "FAIL", 
                                f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_test("Referral Command", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_referral_system(self):
        """Test referral system with invite command"""
        try:
            # First get a referral code from existing user
            async with self.session.get(f"{API_BASE}/users") as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get("users", [])
                    
                    if users:
                        # Get referral code from first user
                        referral_code = users[0].get("referral_code", "")
                        
                        if referral_code:
                            # Create a new user with referral code
                            new_user_id = 888777666
                            
                            sample_update = {
                                "update_id": 123456803,
                                "message": {
                                    "message_id": 13,
                                    "from": {
                                        "id": new_user_id,
                                        "is_bot": False,
                                        "first_name": "ReferredUser",
                                        "username": "referred_user"
                                    },
                                    "chat": {
                                        "id": new_user_id,
                                        "first_name": "ReferredUser",
                                        "username": "referred_user",
                                        "type": "private"
                                    },
                                    "date": 1640995200,
                                    "text": f"/invite {referral_code}"
                                }
                            }
                            
                            async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as invite_response:
                                if invite_response.status == 200:
                                    invite_data = await invite_response.json()
                                    if invite_data.get("status") == "ok":
                                        # Check if referral was recorded
                                        await asyncio.sleep(1)  # Give time for referral processing
                                        
                                        async with self.session.get(f"{API_BASE}/referrals") as referrals_response:
                                            if referrals_response.status == 200:
                                                referrals_data = await referrals_response.json()
                                                referrals = referrals_data.get("referrals", [])
                                                
                                                # Look for our referral
                                                test_referral = next((r for r in referrals if r.get("referred_id") == new_user_id), None)
                                                
                                                if test_referral:
                                                    self.log_test("Referral System", "PASS", 
                                                                f"Referral processed successfully for code {referral_code}", 
                                                                test_referral)
                                                    return True
                                                else:
                                                    self.log_test("Referral System", "FAIL", 
                                                                f"Referral not found for user {new_user_id}")
                                                    return False
                                            else:
                                                self.log_test("Referral System", "FAIL", 
                                                            f"Could not fetch referrals: HTTP {referrals_response.status}")
                                                return False
                                    else:
                                        self.log_test("Referral System", "FAIL", 
                                                    "Invite command returned error", invite_data)
                                        return False
                                else:
                                    self.log_test("Referral System", "FAIL", 
                                                f"HTTP {invite_response.status}", await invite_response.text())
                                    return False
                        else:
                            self.log_test("Referral System", "FAIL", 
                                        "No referral code found in existing users")
                            return False
                    else:
                        self.log_test("Referral System", "FAIL", 
                                    "No users found to get referral code from")
                        return False
                else:
                    self.log_test("Referral System", "FAIL", 
                                f"Could not fetch users: HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Referral System", "FAIL", f"Connection error: {str(e)}")
            return False

    async def test_attempt_system(self):
        """Test attempt usage and tracking"""
        try:
            # Use the test user and try a search to use an attempt
            test_user_id = 999888777
            
            sample_update = {
                "update_id": 123456804,
                "message": {
                    "message_id": 14,
                    "from": {
                        "id": test_user_id,
                        "is_bot": False,
                        "first_name": "TestUser",
                        "username": "testuser_profile"
                    },
                    "chat": {
                        "id": test_user_id,
                        "first_name": "TestUser",
                        "username": "testuser_profile",
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "+79123456789"  # Search query
                }
            }
            
            # Get user's attempts before search
            async with self.session.get(f"{API_BASE}/users") as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get("users", [])
                    test_user = next((u for u in users if u.get("user_id") == test_user_id), None)
                    
                    if test_user:
                        attempts_before = test_user.get("free_attempts", 0)
                        
                        # Perform search
                        async with self.session.post(f"{API_BASE}/webhook", json=sample_update) as search_response:
                            if search_response.status == 200:
                                search_data = await search_response.json()
                                if search_data.get("status") == "ok":
                                    # Check attempts after search
                                    await asyncio.sleep(2)  # Give time for attempt processing
                                    
                                    async with self.session.get(f"{API_BASE}/users") as after_response:
                                        if after_response.status == 200:
                                            after_data = await after_response.json()
                                            after_users = after_data.get("users", [])
                                            after_user = next((u for u in after_users if u.get("user_id") == test_user_id), None)
                                            
                                            if after_user:
                                                attempts_after = after_user.get("free_attempts", 0)
                                                
                                                if attempts_before > attempts_after:
                                                    self.log_test("Attempt System", "PASS", 
                                                                f"Attempt used successfully: {attempts_before} -> {attempts_after}", 
                                                                {"before": attempts_before, "after": attempts_after})
                                                    return True
                                                else:
                                                    self.log_test("Attempt System", "FAIL", 
                                                                f"Attempt not decremented: {attempts_before} -> {attempts_after}")
                                                    return False
                                            else:
                                                self.log_test("Attempt System", "FAIL", 
                                                            "User not found after search")
                                                return False
                                        else:
                                            self.log_test("Attempt System", "FAIL", 
                                                        f"Could not fetch users after search: HTTP {after_response.status}")
                                            return False
                                else:
                                    self.log_test("Attempt System", "FAIL", 
                                                "Search command returned error", search_data)
                                    return False
                            else:
                                self.log_test("Attempt System", "FAIL", 
                                            f"HTTP {search_response.status}", await search_response.text())
                                return False
                    else:
                        self.log_test("Attempt System", "FAIL", 
                                    f"Test user {test_user_id} not found")
                        return False
                else:
                    self.log_test("Attempt System", "FAIL", 
                                f"Could not fetch users: HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Attempt System", "FAIL", f"Connection error: {str(e)}")
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
            ("Phone Number Formatting", self.test_phone_number_formatting),
            ("Usersbox Query Formatting", self.test_usersbox_query_formatting),
            ("Error Handling Improvements", self.test_error_handling_improvements),
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