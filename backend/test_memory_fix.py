#!/usr/bin/env python3
"""
Test script to identify and fix CrewAI memory system issues.
This script tests memory functionality in isolation to diagnose the APIStatusError.
"""

import asyncio
import sys
import traceback
from datetime import datetime

# Add the app directory to the Python path
sys.path.append('/app')

async def test_memory_components():
    """Test individual memory components to isolate the issue"""
    
    print(f"🧪 Testing CrewAI Memory Components - {datetime.now()}")
    print("=" * 60)
    
    # Test 1: Basic imports
    print("\n1️⃣ Testing Basic Imports...")
    try:
        from crewai import Agent, Crew, Task
        from crewai.memory import LongTermMemory
        print("✅ Core CrewAI imports successful")
        
        # Try to import available storage from newer CrewAI
        try:
            from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
            print("✅ LTMSQLiteStorage available")
            storage_available = True
        except ImportError:
            print("⚠️ No compatible storage found")
            # Let's see what's actually available
            import crewai.memory.storage
            available = dir(crewai.memory.storage)
            print(f"Available in storage module: {available}")
            storage_available = False
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Basic LLM setup
    print("\n2️⃣ Testing LLM Configuration...")
    try:
        from app.services.llm_config import get_crewai_llm
        llm = get_crewai_llm()
        print(f"✅ LLM configured: {type(llm).__name__}")
    except Exception as e:
        print(f"❌ LLM setup failed: {e}")
        print("ℹ️  Trying without LLM...")
        llm = None  # We'll test with default LLM
    
    # Test 3: Try LTMSQLiteStorage if available
    if storage_available:
        print("\n3️⃣ Testing LTMSQLiteStorage...")
        try:
            sqlite_storage = LTMSQLiteStorage()
            print("✅ LTMSQLiteStorage initialized")
        except Exception as e:
            print(f"❌ LTMSQLiteStorage failed: {e}")
            traceback.print_exc()
            storage_available = False
    
    # Test 4: Test default memory initialization (no explicit storage)
    print("\n4️⃣ Testing Default LongTermMemory...")
    try:
        if storage_available:
            LongTermMemory(storage=sqlite_storage)
            print("✅ LongTermMemory with SQLite storage successful")
        else:
            # Try with default configuration
            LongTermMemory()
            print("✅ LongTermMemory with default configuration successful")
    except Exception as e:
        print(f"❌ LongTermMemory initialization failed: {e}")
        traceback.print_exc()
        print("ℹ️  Trying without explicit memory configuration...")
    
    # Test 5: Simple agent with memory (the critical test)
    print("\n5️⃣ Testing Agent with Memory...")
    try:
        agent_kwargs = {
            "role": "Test Agent",
            "goal": "Test memory functionality", 
            "backstory": "Testing agent for memory system",
            "memory": True,
            "verbose": False
        }
        if llm:
            agent_kwargs["llm"] = llm
            
        test_agent = Agent(**agent_kwargs)
        print("✅ Agent with memory=True created successfully")
    except Exception as e:
        print(f"❌ Agent with memory failed: {e}")
        traceback.print_exc()
        print("ℹ️  Trying agent without memory...")
        try:
            fallback_kwargs = {
                "role": "Test Agent",
                "goal": "Test memory functionality",
                "backstory": "Testing agent for memory system", 
                "memory": False,
                "verbose": False
            }
            if llm:
                fallback_kwargs["llm"] = llm
                
            test_agent = Agent(**fallback_kwargs)
            print("✅ Agent with memory=False works")
        except Exception as e2:
            print(f"❌ Even agent without memory failed: {e2}")
            return False
    
    # Test 6: Simple crew with memory (the ultimate test)
    print("\n6️⃣ Testing Crew with Memory...")
    try:
        test_task = Task(
            description="Test task to verify memory functionality works correctly.",
            agent=test_agent,
            expected_output="Simple confirmation that memory is working"
        )
        
        test_crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            memory=True,
            verbose=False
        )
        print("✅ Crew with memory=True created successfully")
        
        # Test 7: Actually run the crew (this is where APIStatusError typically occurs)
        print("\n7️⃣ Testing Crew Execution...")
        result = test_crew.kickoff()
        print(f"✅ Crew execution successful: {str(result)[:100]}...")
        
    except Exception as e:
        print(f"❌ Crew with memory failed: {e}")
        traceback.print_exc()
        
        # Analyze the specific error
        error_str = str(e)
        if "APIStatusError" in error_str:
            print("\n🔍 ANALYSIS: APIStatusError detected!")
            print("This is the exact error that caused memory to be disabled.")
            if "missing 2 required keyword-only arguments" in error_str:
                print("Issue: OpenAI client version mismatch with CrewAI expectations")
                print("Solution: Need to check OpenAI client version compatibility")
        
        # Try without memory as fallback test
        print("\n🔄 Testing Crew without memory as fallback...")
        try:
            fallback_crew = Crew(
                agents=[test_agent],
                tasks=[test_task],
                memory=False,
                verbose=False
            )
            fallback_result = fallback_crew.kickoff()
            print(f"✅ Crew without memory works: {str(fallback_result)[:100]}...")
            print("🔍 DIAGNOSIS: Memory system is the issue, not basic CrewAI functionality")
        except Exception as e2:
            print(f"❌ Even crew without memory failed: {e2}")
            traceback.print_exc()
        
        return False
    
    print("\n🎉 All memory tests passed! Memory system appears to be working correctly.")
    return True

async def test_dependency_versions():
    """Check current dependency versions and compatibility"""
    
    print("\n📋 Dependency Version Analysis")
    print("=" * 40)
    
    import pkg_resources
    
    dependencies = ['crewai', 'openai', 'litellm', 'chromadb', 'langchain-openai']
    
    for dep in dependencies:
        try:
            version = pkg_resources.get_distribution(dep).version
            print(f"{dep:20} {version}")
        except pkg_resources.DistributionNotFound:
            print(f"{dep:20} NOT INSTALLED")
    
    # Check for known problematic combinations
    print("\n🔍 Checking for known issues...")
    
    try:
        openai_version = pkg_resources.get_distribution('openai').version
        crewai_version = pkg_resources.get_distribution('crewai').version
        
        print(f"OpenAI version: {openai_version}")
        print(f"CrewAI version: {crewai_version}")
        
        # Known issue: OpenAI 1.x with older CrewAI versions
        if openai_version.startswith('1.') and crewai_version < '0.30.0':
            print("⚠️  Potential issue: OpenAI 1.x with older CrewAI")
            
    except Exception as e:
        print(f"Could not analyze versions: {e}")

async def suggest_fixes():
    """Suggest specific fixes based on test results"""
    
    print("\n🔧 Suggested Actions:")
    print("=" * 30)
    
    print("1. If memory tests PASSED:")
    print("   - Memory system is working correctly with current versions")
    print("   - Can safely re-enable memory by removing global disable patch")
    print("   - Remove memory=False from individual crews")
    
    print("\n2. If memory tests FAILED with APIStatusError:")
    print("   - Update dependencies to compatible versions")
    print("   - Check OpenAI client compatibility with CrewAI")
    print("   - Consider using JSON storage instead of ChromaDB initially")
    
    print("\n3. Next steps:")
    print("   - Remove global memory disable in crews/__init__.py")
    print("   - Test with one crew first")
    print("   - Gradually re-enable across all crews")

if __name__ == "__main__":
    async def main():
        try:
            await test_dependency_versions()
            success = await test_memory_components()
            await suggest_fixes()
            
            if success:
                print("\n✅ CONCLUSION: Memory system is working! Ready to re-enable.")
                exit(0)
            else:
                print("\n❌ CONCLUSION: Memory system has issues. Need dependency fixes.")
                exit(1)
                
        except Exception as e:
            print(f"\n💥 Unexpected error in testing: {e}")
            traceback.print_exc()
            exit(1)
    
    asyncio.run(main())