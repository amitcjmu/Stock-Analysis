#!/usr/bin/env python3
"""
Test direct DeepInfra API call with OpenAI format and reasoning_effort=none.
"""

import requests
import time
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.core.config import settings

def test_direct_api_call():
    """Test direct API call to DeepInfra with OpenAI format."""
    print("🔬 Testing Direct DeepInfra API Call")
    print("=" * 50)
    
    # API endpoint and headers
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.DEEPINFRA_API_KEY}"
    }
    
    # Request payload with reasoning_effort=none
    payload = {
        "model": settings.DEEPINFRA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "What is 5+5? Answer with just the number."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "reasoning_effort": "none",  # CRITICAL: Disable reasoning
        "stream": False
    }
    
    print(f"🌐 API URL: {url}")
    print(f"🤖 Model: {settings.DEEPINFRA_MODEL}")
    print("🧠 Reasoning effort: none")
    print("📝 Prompt: What is 5+5? Answer with just the number.")
    
    try:
        print("\n🚀 Making API call...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        duration = time.time() - start_time
        print(f"⏱️  Response time: {duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"✅ Response: {content.strip()}")
                
                # Check usage stats
                if "usage" in result:
                    usage = result["usage"]
                    print(f"📊 Usage: {usage.get('prompt_tokens', 0)} prompt + {usage.get('completion_tokens', 0)} completion = {usage.get('total_tokens', 0)} total tokens")
                
                if duration < 5:
                    print("🎉 SUCCESS: Fast response without thinking mode!")
                    return True
                else:
                    print(f"⚠️  Response took {duration:.2f}s - might still have thinking mode")
                    return False
            else:
                print(f"❌ Unexpected response format: {result}")
                return False
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ API call failed after {duration:.2f}s: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_api_call()
    if success:
        print("\n🎉 Direct API test passed! DeepInfra API is working without thinking mode.")
    else:
        print("\n❌ Direct API test failed. Check the configuration and API format.") 