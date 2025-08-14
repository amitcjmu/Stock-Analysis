#!/usr/bin/env python3
"""
Test script to verify CrewAI execution issue
"""
import asyncio
import sys
import os
sys.path.insert(0, '/app')

# Set up environment
os.environ['DEEPINFRA_BASE_URL'] = 'https://api.deepinfra.com/v1/openai'

from crewai import Agent, Crew, Task, Process
from app.services.llm_config import get_crewai_llm

async def test_crew_execution():
    """Test both sync and async crew execution"""

    print("=" * 60)
    print("CREWAI EXECUTION TEST")
    print("=" * 60)

    # Get LLM
    llm = get_crewai_llm()
    print(f"✅ LLM configured: {llm}")

    # Create a simple test agent
    test_agent = Agent(
        role="Test Agent",
        goal="Test crew execution",
        backstory="You are a test agent to verify crew execution works",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        max_execution_time=10
    )

    # Create a simple task
    test_task = Task(
        description="Say 'CrewAI is working!' and return success",
        agent=test_agent,
        expected_output="A confirmation message"
    )

    # Create crew
    crew = Crew(
        agents=[test_agent],
        tasks=[test_task],
        process=Process.sequential,
        verbose=True
    )

    print("\n" + "=" * 60)
    print("TEST 1: Synchronous kickoff()")
    print("=" * 60)

    try:
        result = crew.kickoff()
        print(f"✅ Sync execution successful!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Sync execution failed: {e}")

    print("\n" + "=" * 60)
    print("TEST 2: Asynchronous kickoff_async()")
    print("=" * 60)

    try:
        result = await crew.kickoff_async()
        print(f"✅ Async execution successful!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Async execution failed: {e}")

    print("\n" + "=" * 60)
    print("TEST 3: asyncio.to_thread wrapper")
    print("=" * 60)

    # Create new crew for fresh test
    crew2 = Crew(
        agents=[test_agent],
        tasks=[test_task],
        process=Process.sequential,
        verbose=False  # Less verbose for wrapper test
    )

    try:
        result = await asyncio.to_thread(crew2.kickoff)
        print(f"✅ Thread wrapper execution successful!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Thread wrapper execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_crew_execution())
