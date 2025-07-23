#!/usr/bin/env python3
"""
Focused test to identify exactly where CrewAI tasks are hanging.
This test provides step-by-step monitoring to isolate the exact hanging point.
"""

import asyncio
import time
import signal
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Test imports first
try:
    import crewai
    print(f"✅ CrewAI imported successfully: {crewai.__version__}")
    CREWAI_AVAILABLE = True
except ImportError as e:
    print(f"❌ CrewAI import failed: {e}")
    CREWAI_AVAILABLE = False

from app.services.crewai_flow_service import crewai_service
from app.services.agent_monitor import agent_monitor

class HangingDebugger:
    def __init__(self):
        self.test_running = True
        self.start_time = None
        
    def setup_signal_handler(self):
        """Setup signal handler for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n🛑 Test interrupted by signal {signum}")
            self.print_debug_info()
            agent_monitor.print_summary()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def print_debug_info(self):
        """Print detailed debug information."""
        print("\n" + "="*60)
        print("🔍 HANGING DEBUG INFORMATION")
        print("="*60)
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"Total test time: {elapsed:.1f} seconds")
        
        # Get detailed status
        status = agent_monitor.get_status_report()
        
        print("\nMonitoring Status:")
        print(f"  Active: {status['monitoring_active']}")
        print(f"  Active tasks: {status['active_tasks']}")
        print(f"  Hanging tasks: {status['hanging_tasks']}")
        
        if status['hanging_task_details']:
            print("\n🚨 HANGING TASK ANALYSIS:")
            for task in status['hanging_task_details']:
                print(f"  Task ID: {task['task_id']}")
                print(f"  Agent: {task['agent']}")
                print(f"  Elapsed: {task['elapsed']}")
                print(f"  Since Activity: {task['since_activity']}")
                print(f"  Hanging Reason: {task['hanging_reason']}")
                print(f"  LLM Calls: {task['llm_calls']}")
                print(f"  Last LLM Call: {task['last_llm_call']}")
                print(f"  Thinking Phases: {task['thinking_phases']}")
                print(f"  Last Thinking: {task['last_thinking']}")
                print()

async def test_step_by_step():
    """Test CrewAI execution step by step with detailed monitoring."""
    debugger = HangingDebugger()
    debugger.setup_signal_handler()
    debugger.start_time = time.time()
    
    print("🔬 HANGING DEBUG TEST")
    print("="*50)
    print("This test will show exactly where the hanging occurs...")
    print("Press Ctrl+C at any time to see debug info")
    print("="*50)
    
    # Step 1: Verify monitoring
    print("\n📊 STEP 1: Verify Monitoring")
    if not agent_monitor.monitoring_active:
        print("❌ Agent monitoring not active!")
        return False
    print("✅ Agent monitoring is active")
    
    # Step 2: Check CrewAI service initialization
    print("\n🤖 STEP 2: Check CrewAI Service")
    print(f"  LLM initialized: {crewai_service.llm is not None}")
    print(f"  Agent manager: {crewai_service.agent_manager is not None}")
    print(f"  Available agents: {len(crewai_service.agents)}")
    print(f"  Available crews: {len(crewai_service.crews)}")
    
    if not crewai_service.agents:
        print("❌ No agents available!")
        return False
    
    # Step 3: Test simple agent access
    print("\n🧠 STEP 3: Test Agent Access")
    cmdb_agent = crewai_service.agents.get('cmdb_analyst')
    if not cmdb_agent:
        print("❌ CMDB analyst agent not found!")
        print(f"Available agents: {list(crewai_service.agents.keys())}")
        return False
    
    print(f"✅ CMDB analyst agent found: {cmdb_agent.role}")
    
    # Step 4: Create minimal task
    print("\n📋 STEP 4: Create Minimal Task")
    if not CREWAI_AVAILABLE:
        print("❌ CrewAI not available - cannot create task")
        return False
        
    try:
        from crewai import Task
        
        simple_task = Task(
            description="What is 2+2? Answer with just the number.",
            agent=cmdb_agent,
            expected_output="A single number"
        )
        print("✅ Task created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create task: {e}")
        return False
    
    # Step 5: Execute with monitoring
    print("\n🚀 STEP 5: Execute Task with Monitoring")
    print("Starting background status monitoring...")
    
    # Start background monitoring
    async def status_monitor():
        while debugger.test_running:
            await asyncio.sleep(5)
            status = agent_monitor.get_status_report()
            if status['active_tasks'] > 0:
                print(f"\n⏱️  STATUS: {status['active_tasks']} active tasks")
                for task in status['active_task_details']:
                    print(f"   {task['agent']}: {task['status']} ({task['elapsed']}) - {task['description'][:50]}...")
                    if task['is_hanging']:
                        print(f"   🚨 HANGING: {task['hanging_reason']}")
    
    monitor_task = asyncio.create_task(status_monitor())
    
    try:
        print("Executing task...")
        result = await crewai_service._execute_task_async(simple_task)
        print(f"✅ Task completed! Result: {result[:100]}...")
        debugger.test_running = False
        return True
        
    except asyncio.TimeoutError:
        print("⏰ Task timed out!")
        debugger.print_debug_info()
        return False
        
    except Exception as e:
        print(f"❌ Task failed: {e}")
        debugger.print_debug_info()
        return False
        
    finally:
        debugger.test_running = False
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

async def test_direct_llm():
    """Test direct LLM call to isolate the issue."""
    print("\n🔧 DIRECT LLM TEST")
    print("="*30)
    
    try:
        llm = crewai_service.llm
        if not llm:
            print("❌ No LLM available")
            return False
        
        print("✅ LLM instance available")
        print(f"LLM type: {type(llm)}")
        
        # Try a direct call
        print("Making direct LLM call...")
        start_time = time.time()
        
        # This will depend on the LLM interface
        try:
            if hasattr(llm, 'invoke'):
                result = llm.invoke("What is 2+2?")
            elif hasattr(llm, '__call__'):
                result = llm("What is 2+2?")
            else:
                print(f"❌ Unknown LLM interface: {dir(llm)}")
                return False
            
            duration = time.time() - start_time
            print(f"✅ Direct LLM call succeeded in {duration:.2f}s")
            print(f"Result: {str(result)[:100]}...")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Direct LLM call failed after {duration:.2f}s: {e}")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🔬 CrewAI Hanging Debug Test")
        print("=" * 50)
        
        # Test 1: Direct LLM
        print("TEST 1: Direct LLM Call")
        llm_success = await test_direct_llm()
        
        if llm_success:
            print("\n" + "="*50)
            print("TEST 2: Step-by-Step CrewAI Execution")
            await test_step_by_step()
        else:
            print("\n❌ Direct LLM failed - issue is with LLM, not CrewAI")
        
        # Final summary
        agent_monitor.print_summary()
        agent_monitor.stop_monitoring()
    
    asyncio.run(main()) 