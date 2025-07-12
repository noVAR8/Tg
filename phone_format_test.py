#!/usr/bin/env python3
"""
Direct test of phone number formatting functions
Tests the normalize_phone_number and format_search_query functions directly
"""

import sys
import os
sys.path.append('/app/backend')

# Import the functions from server.py
from server import normalize_phone_number, format_search_query

def test_normalize_phone_number():
    """Test the normalize_phone_number function directly"""
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
        },
        {
            "input": "8 929 847 04 21",
            "expected": "+79298470421",
            "description": "Format with spaces starting with 8"
        }
    ]
    
    print("🧪 Testing normalize_phone_number function:")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for case in test_cases:
        try:
            result = normalize_phone_number(case["input"])
            if result == case["expected"]:
                print(f"✅ {case['description']}")
                print(f"   Input: '{case['input']}' → Output: '{result}'")
                passed += 1
            else:
                print(f"❌ {case['description']}")
                print(f"   Input: '{case['input']}'")
                print(f"   Expected: '{case['expected']}'")
                print(f"   Got: '{result}'")
        except Exception as e:
            print(f"❌ {case['description']}")
            print(f"   Error: {str(e)}")
    
    print(f"\n📊 normalize_phone_number: {passed}/{total} tests passed")
    return passed == total

def test_format_search_query():
    """Test the format_search_query function directly"""
    test_cases = [
        {
            "input": "+7 929 847-04-21",
            "expected": "+79298470421",
            "description": "Phone number with spaces and dashes"
        },
        {
            "input": "8-929-847-04-21", 
            "expected": "+79298470421",
            "description": "Russian phone format"
        },
        {
            "input": "example@mail.ru",
            "expected": "example@mail.ru",
            "description": "Email address (should remain unchanged)"
        },
        {
            "input": "Иван Петров",
            "expected": "Иван Петров",
            "description": "Name (should remain unchanged)"
        },
        {
            "input": "  multiple   spaces  ",
            "expected": "multiple spaces",
            "description": "Text with extra spaces"
        }
    ]
    
    print("\n🧪 Testing format_search_query function:")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for case in test_cases:
        try:
            result = format_search_query(case["input"])
            if result == case["expected"]:
                print(f"✅ {case['description']}")
                print(f"   Input: '{case['input']}' → Output: '{result}'")
                passed += 1
            else:
                print(f"❌ {case['description']}")
                print(f"   Input: '{case['input']}'")
                print(f"   Expected: '{case['expected']}'")
                print(f"   Got: '{result}'")
        except Exception as e:
            print(f"❌ {case['description']}")
            print(f"   Error: {str(e)}")
    
    print(f"\n📊 format_search_query: {passed}/{total} tests passed")
    return passed == total

def main():
    """Run all phone formatting tests"""
    print("🚀 Testing Phone Number Formatting Functions")
    print("=" * 60)
    
    normalize_passed = test_normalize_phone_number()
    format_passed = test_format_search_query()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    
    if normalize_passed and format_passed:
        print("🎉 All phone formatting tests passed!")
        print("✅ Phone number normalization is working correctly")
        print("✅ Query formatting is working correctly")
        return True
    else:
        print("❌ Some phone formatting tests failed")
        if not normalize_passed:
            print("❌ normalize_phone_number function has issues")
        if not format_passed:
            print("❌ format_search_query function has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)