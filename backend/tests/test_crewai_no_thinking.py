#!/usr/bin/env python3
"""
Test CrewAI with completely fresh agents and LLM instance that has thinking mode disabled.
"""

import asyncio
import gc
import os
import sys
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.core.config import settings
from app.services.deepinfra_llm import create_crewai_compatible_llm


async def test_completely_fresh_crewai():
    """Test CrewAI with completely fresh agents and LLM instance."""
    print("🧪 Testing CrewAI with Completely Fresh Agents (No Thinking Mode)")
    print("=" * 70)
    
    # Force garbage collection to clear any cached instances
    gc.collect()
    
    # Create a fresh LLM instance with thinking mode explicitly disabled
    fresh_llm = create_crewai_compatible_llm(
        api_token=settings.DEEPINFRA_API_KEY,
        model_id=settings.DEEPINFRA_MODEL,
        temperature=0.1,
        max_tokens=100,  # Small for quick testing
        reasoning_effort="none"  # Explicitly disable reasoning
    )
    
    print(f"✅ Fresh LLM created: {fresh_llm.model_id}")
    print(f"   Max tokens: {fresh_llm.max_tokens}")
    print(f"   Temperature: {fresh_llm.temperature}")
    print(f"   Reasoning effort: {fresh_llm.reasoning_effort}")
    print(f"   Base URL: {fresh_llm.base_url}")
    
    # Test direct LLM call first
    print("\n🔍 Step 1: Direct LLM Test")
    start_time = time.time()
    try:
        result = fresh_llm._call("What is 3+3? Just the number.")
        duration = time.time() - start_time
        print(f"✅ Direct LLM: {result.strip()} in {duration:.2f}s")
        
        if duration > 10:
            print("⚠️  Direct LLM call took too long - might still have thinking mode")
            return False
            
    except Exception as e:
        print(f"❌ Direct LLM failed: {e}")
        return False
    
    # Now test with completely fresh CrewAI agents
    print("\n🔍 Step 2: Fresh CrewAI Agents Test")
    try:
        # Import CrewAI components fresh
        from crewai import Agent, Crew, Process, Task
        
        print("✅ CrewAI components imported")
        
        # Create a completely fresh agent with the fresh LLM
        fresh_agent = Agent(
            role="Quick Math Assistant",
            goal="Answer simple math questions as quickly as possible",
            backstory="You are a helpful assistant that answers math questions with just the number. You work quickly and efficiently.",
            llm=fresh_llm,
            verbose=False,  # Disable verbose to reduce overhead
            allow_delegation=False,
            memory=False  # Disable memory for faster execution
        )
        
        print("✅ Fresh agent created")
        
        # Create a simple task
        simple_task = Task(
            description="What is 7+8? Answer with just the number.",
            agent=fresh_agent,
            expected_output="A single number"
        )
        
        print("✅ Simple task created")
        
        # Create a fresh crew
        fresh_crew = Crew(
            agents=[fresh_agent],
            tasks=[simple_task],
            process=Process.sequential,
            verbose=False,  # Disable verbose to reduce overhead
            memory=False  # Disable memory for faster execution
        )
        
        print("✅ Fresh crew created")
        print("🚀 Executing fresh crew...")
        
        start_time = time.time()
        result = fresh_crew.kickoff()
        duration = time.time() - start_time
        
        print(f"✅ Fresh Crew Result: {str(result).strip()} in {duration:.2f}s")
        
        if duration < 10:
            print("🎉 SUCCESS: Fresh CrewAI executed quickly without thinking mode!")
            return True
        else:
            print(f"⚠️  Fresh CrewAI took {duration:.2f}s - might still have thinking mode issues")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Fresh CrewAI failed after {duration:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fresh_cmdb_analysis():
    """Test CMDB analysis with completely fresh setup."""
    print("\n🔍 Step 3: Fresh CMDB Analysis Test")
    
    try:
        # Force garbage collection again
        gc.collect()
        
        # Create another fresh LLM for CMDB analysis
        cmdb_llm = create_crewai_compatible_llm(
            api_token=settings.DEEPINFRA_API_KEY,
            model_id=settings.DEEPINFRA_MODEL,
            temperature=0.1,
            max_tokens=200,  # Slightly larger for CMDB analysis
            reasoning_effort="none"
        )
        
        # Import fresh
        from crewai import Agent, Crew, Process, Task
        
        # Create a fresh CMDB analyst agent
        cmdb_agent = Agent(
            role="CMDB Data Analyst",
            goal="Quickly analyze CMDB data and identify asset types",
            backstory="You are a CMDB analyst who works efficiently to identify asset types from data patterns.",
            llm=cmdb_llm,
            verbose=False,
            allow_delegation=False,
            memory=False
        )
        
        # Create CMDB analysis task
        cmdb_task = Task(
            description="""
            Analyze this CMDB data and determine the primary asset type:
            
            Sample data:
            - Name: WebApp1, Type: Application, Environment: Prod
            - Name: Server1, Type: Server, Environment: Prod
            
            Answer with just: "mixed" (since there are both applications and servers)
            """,
            agent=cmdb_agent,
            expected_output="A single word indicating the asset type"
        )
        
        # Create fresh crew for CMDB analysis
        cmdb_crew = Crew(
            agents=[cmdb_agent],
            tasks=[cmdb_task],
            process=Process.sequential,
            verbose=False,
            memory=False
        )
        
        print("✅ Fresh CMDB analysis setup created")
        print("🚀 Executing CMDB analysis...")
        
        start_time = time.time()
        result = cmdb_crew.kickoff()
        duration = time.time() - start_time
        
        print(f"✅ CMDB Analysis Result: {str(result).strip()} in {duration:.2f}s")
        
        if duration < 15:
            print("🎉 SUCCESS: Fresh CMDB analysis executed quickly!")
            return True
        else:
            print(f"⚠️  CMDB analysis took {duration:.2f}s - might still have issues")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Fresh CMDB analysis failed after {duration:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🔬 CrewAI Fresh Agent Test Suite")
        print("=" * 50)
        
        # Test 1: Fresh CrewAI agents
        test1_success = await test_completely_fresh_crewai()
        
        if test1_success:
            # Test 2: Fresh CMDB analysis
            test2_success = await test_fresh_cmdb_analysis()
            
            if test1_success and test2_success:
                print("\n🎉 ALL TESTS PASSED! CrewAI is working without thinking mode.")
                print("✅ Fresh agents can be created and execute quickly")
                print("✅ CMDB analysis works with fresh setup")
            else:
                print("\n⚠️  Some tests passed but CMDB analysis still has issues")
        else:
            print("\n❌ Basic CrewAI test failed. Check the LLM configuration.")
    
    asyncio.run(main()) 