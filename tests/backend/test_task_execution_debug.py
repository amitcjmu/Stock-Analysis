import asyncio
import time
import signal
import sys
from app.services.crewai_service import crewai_service

class TimeoutHandler:
    def __init__(self, timeout_seconds=30):
        self.timeout_seconds = timeout_seconds
        self.timed_out = False
    
    def timeout_handler(self, signum, frame):
        self.timed_out = True
        print(f"\n⏰ TIMEOUT after {self.timeout_seconds} seconds!")
        print("Task execution is hanging - this confirms the issue")
        sys.exit(1)
    
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout_seconds)
        return self
    
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

async def test_task_execution_steps():
    """Test each step of task execution to find where it hangs."""
    print("🧪 Testing CrewAI Task Execution Steps")
    print("=" * 50)
    
    # Step 1: Verify service is ready
    print("Step 1: Verifying CrewAI service...")
    if not crewai_service.llm:
        print("❌ LLM not available")
        return False
    if not crewai_service.agent_manager:
        print("❌ Agent manager not available")
        return False
    print(f"✅ Service ready with {len(crewai_service.agents)} agents")
    
    # Step 2: Test simple data preparation
    print("\nStep 2: Preparing test data...")
    test_data = {
        'filename': 'simple_test.csv',
        'headers': ['Name', 'Type'],
        'sample_data': [['Server01', 'Server']]
    }
    print("✅ Test data prepared")
    
    # Step 3: Test the analyze_cmdb_data method entry
    print("\nStep 3: Calling analyze_cmdb_data...")
    try:
        with TimeoutHandler(30):  # 30 second timeout
            result = await crewai_service.analyze_cmdb_data(test_data)
            print(f"✅ Analysis completed: {result.get('analysis_type', 'unknown')}")
            return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

async def test_direct_crew_execution():
    """Test direct crew execution to isolate the hanging."""
    print("\n🔧 Testing Direct Crew Execution")
    print("=" * 40)
    
    try:
        from crewai import Task
        
        # Get the CMDB analyst agent
        agent = crewai_service.agents.get('cmdb_analyst')
        if not agent:
            print("❌ CMDB analyst agent not found")
            return False
        
        print(f"✅ Agent found: {agent.role}")
        
        # Create a simple task
        print("\nCreating simple task...")
        task = Task(
            description="Analyze this simple data: Name=Server01, Type=Server. What asset type is this?",
            agent=agent
        )
        print("✅ Task created")
        
        # Try to execute the task directly
        print("\nExecuting task with timeout...")
        with TimeoutHandler(30):
            result = await crewai_service._execute_task_async(task)
            print(f"✅ Task completed: {result[:100]}...")
            return True
            
    except Exception as e:
        print(f"❌ Direct execution failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("CrewAI Task Execution Debug Test")
        print("=" * 60)
        
        # Test 1: Full analyze_cmdb_data method
        print("TEST 1: Full CMDB Analysis Method")
        success1 = await test_task_execution_steps()
        
        if not success1:
            print("\nTEST 2: Direct Crew Execution")
            success2 = await test_direct_crew_execution()
            
            if not success2:
                print("\n💥 CONFIRMED: Task execution is hanging")
                print("This is the root cause of the timeout issues")
        else:
            print("\n🎉 Task execution working properly!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except SystemExit:
        print("\n⚠️  Test timed out - hanging confirmed") 