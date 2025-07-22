#!/usr/bin/env python3
"""
Test CrewAI with LiteLLM configuration for DeepInfra.
"""

import asyncio
import time
import sys
import os
import gc

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.core.config import settings

def test_crewai_with_litellm():
    """Test CrewAI with LiteLLM configuration for DeepInfra."""
    print("🧪 Testing CrewAI with LiteLLM DeepInfra Configuration")
    print("=" * 60)
    
    try:
        # Import LiteLLM and CrewAI
        import litellm
        from crewai import Agent, Task, Crew, Process, LLM
        
        # Configure LiteLLM for DeepInfra
        print("🔧 Configuring LiteLLM for DeepInfra...")
        
        # Create LiteLLM configuration for DeepInfra
        llm = LLM(
            model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            api_key=settings.DEEPINFRA_API_KEY,
            temperature=0.1,
            max_tokens=100
        )
        
        print("✅ LiteLLM configured for DeepInfra")
        print(f"   Model: {llm.model}")
        print(f"   Temperature: {llm.temperature}")
        print(f"   Max tokens: {llm.max_tokens}")
        
        # Create a fresh agent
        agent = Agent(
            role="Math Assistant",
            goal="Answer math questions quickly",
            backstory="You are a helpful math assistant.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
            memory=False
        )
        
        print("✅ Agent created with LiteLLM")
        
        # Create a simple task
        task = Task(
            description="What is 9+9? Answer with just the number.",
            agent=agent,
            expected_output="A single number"
        )
        
        print("✅ Task created")
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
            memory=False
        )
        
        print("✅ Crew created")
        print("🚀 Executing crew with LiteLLM...")
        
        start_time = time.time()
        result = crew.kickoff()
        duration = time.time() - start_time
        
        print(f"✅ Result: {str(result).strip()} in {duration:.2f}s")
        
        if duration < 10:
            print("🎉 SUCCESS: CrewAI with LiteLLM executed quickly!")
            return True
        else:
            print(f"⚠️  Execution took {duration:.2f}s - might have issues")
            return False
            
    except Exception as e:
        print(f"❌ LiteLLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_litellm():
    """Test direct LiteLLM call to DeepInfra."""
    print("\n🔍 Testing Direct LiteLLM Call")
    print("=" * 40)
    
    try:
        import litellm
        
        # Configure LiteLLM for DeepInfra
        print("🔧 Making direct LiteLLM call...")
        
        start_time = time.time()
        
        response = litellm.completion(
            model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "user", "content": "What is 4+4? Just the number."}],
            api_key=settings.DEEPINFRA_API_KEY,
            temperature=0.1,
            max_tokens=50
        )
        
        duration = time.time() - start_time
        
        content = response.choices[0].message.content
        print(f"✅ Direct LiteLLM: {content.strip()} in {duration:.2f}s")
        
        if duration < 5:
            print("🎉 SUCCESS: Direct LiteLLM call was fast!")
            return True
        else:
            print(f"⚠️  Direct call took {duration:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Direct LiteLLM failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 CrewAI LiteLLM Test Suite")
    print("=" * 50)
    
    # Test 1: Direct LiteLLM
    test1_success = test_direct_litellm()
    
    if test1_success:
        # Test 2: CrewAI with LiteLLM
        test2_success = test_crewai_with_litellm()
        
        if test1_success and test2_success:
            print("\n🎉 ALL TESTS PASSED! CrewAI works with LiteLLM DeepInfra!")
        else:
            print("\n⚠️  Direct LiteLLM works but CrewAI integration has issues")
    else:
        print("\n❌ Direct LiteLLM test failed. Check the configuration.") 