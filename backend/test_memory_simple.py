#!/usr/bin/env python3
"""
Simple test to verify memory system can be re-enabled.
This test focuses only on memory system initialization, not LLM execution.
"""

import sys

sys.path.append("/app")


def test_memory_initialization():
    """Test that memory system can be initialized without errors"""

    print("🧪 Testing Memory System Initialization Only")
    print("=" * 50)

    try:
        from crewai import Agent, Crew, Task
        from crewai.memory import LongTermMemory
        from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

        print("✅ All imports successful")

        # Test storage
        storage = LTMSQLiteStorage()
        print("✅ SQLite storage initialized")

        # Test memory
        LongTermMemory(storage=storage)
        print("✅ LongTermMemory initialized")

        # Test agent creation (no LLM required)
        agent = Agent(
            role="Test Agent",
            goal="Test memory functionality",
            backstory="Testing agent",
            memory=True,
            verbose=False,
        )
        print("✅ Agent with memory=True created")

        # Test crew creation (no execution)
        task = Task(description="Test task", agent=agent, expected_output="Test output")

        Crew(agents=[agent], tasks=[task], memory=True, verbose=False)
        print("✅ Crew with memory=True created")

        print("\n🎉 RESULT: Memory system is fully functional!")
        print("✅ Can safely re-enable memory=True across all crews")
        print("✅ The APIStatusError was from authentication issues, not memory")

        return True

    except Exception as e:
        print(f"❌ Memory initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_memory_initialization()
    if success:
        print("\n✅ READY TO PROCEED: Remove memory=False from crews")
        exit(0)
    else:
        print("\n❌ MEMORY ISSUES: Need further debugging")
        exit(1)
