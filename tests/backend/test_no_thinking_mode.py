#!/usr/bin/env python3
"""
Test to verify that thinking mode is disabled and LLM responds quickly.
"""

import asyncio
import time
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.deepinfra_llm import create_deepinfra_llm
from app.core.config import settings

async def test_no_thinking_mode():
    """Test that LLM responds quickly without thinking mode."""
    print("🧪 Testing DeepInfra LLM without thinking mode")
    print("=" * 50)
    
    # Create LLM with reduced tokens for faster response
    llm = create_deepinfra_llm(
        api_token=settings.DEEPINFRA_API_KEY,
        model_id=settings.DEEPINFRA_MODEL,
        temperature=0.1,  # Lower temperature for faster, more deterministic responses
        max_new_tokens=50  # Much smaller for quick testing
    )
    
    print(f"✅ LLM created: {llm.model_id}")
    print(f"   Max tokens: {llm.max_new_tokens}")
    print(f"   Temperature: {llm.temperature}")
    
    # Test simple math question
    test_prompts = [
        "What is 2+2? Answer with just the number.",
        "Name one color. Just the color name.",
        "What day comes after Monday? Just the day name."
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🔍 Test {i}: {prompt}")
        
        start_time = time.time()
        try:
            result = llm._call(prompt)
            duration = time.time() - start_time
            
            print(f"✅ Response in {duration:.2f}s: {result.strip()}")
            
            if duration > 10:
                print(f"⚠️  Response took {duration:.2f}s - might still be using thinking mode")
            else:
                print("🚀 Fast response - thinking mode likely disabled")
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Failed after {duration:.2f}s: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_no_thinking_mode()) 