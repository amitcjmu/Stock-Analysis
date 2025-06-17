#!/usr/bin/env python3
"""
Debug script to check what context is being used by the API
"""

import asyncio
import os
import sys
import requests

# Add the project root to the Python path
sys.path.append('/app')

def test_api_context():
    """Test what context the API is using."""
    
    print("=== TESTING API CONTEXT ===")
    
    # Test 1: No headers (like frontend might be doing)
    print("\n1. Testing with no headers...")
    response = requests.get("http://localhost:8000/api/v1/data-import/critical-attributes-status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total attributes: {data['statistics']['total_attributes']}")
        print(f"   Recommendation: {data['recommendations']['next_priority']}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # Test 2: With correct headers
    print("\n2. Testing with correct headers...")
    headers = {
        "X-Client-Account-ID": "bafd5b46-aaaf-4c95-8142-573699d93171",
        "X-Engagement-ID": "6e9c8133-4169-4b79-b052-106dc93d0208"
    }
    response = requests.get("http://localhost:8000/api/v1/data-import/critical-attributes-status", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total attributes: {data['statistics']['total_attributes']}")
        if data['attributes']:
            print(f"   First attribute: {data['attributes'][0]['name']} ({data['attributes'][0]['status']})")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # Test 3: With demo context headers
    print("\n3. Testing with demo context...")
    demo_headers = {
        "X-Client-Account-ID": "bafd5b46-aaaf-4c95-8142-573699d93171",  # From DEMO_CLIENT_CONFIG
        "X-Engagement-ID": "6e9c8133-4169-4b79-b052-106dc93d0208"
    }
    response = requests.get("http://localhost:8000/api/v1/data-import/critical-attributes-status", headers=demo_headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total attributes: {data['statistics']['total_attributes']}")
        if data['attributes']:
            print(f"   First attribute: {data['attributes'][0]['name']} ({data['attributes'][0]['status']})")
    else:
        print(f"   Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_api_context() 