import asyncio
import time
import signal
import sys
from app.services.crewai_service_modular import crewai_service
from app.services.agent_monitor import agent_monitor

class MonitoredTest:
    def __init__(self):
        self.test_running = True
        
    def setup_signal_handler(self):
        """Setup signal handler for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n🛑 Test interrupted by signal {signum}")
            self.test_running = False
            agent_monitor.print_summary()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def test_with_monitoring():
    """Test CMDB analysis with comprehensive monitoring."""
    test = MonitoredTest()
    test.setup_signal_handler()
    
    print("🔍 Starting Monitored CrewAI Test")
    print("=" * 60)
    print("This test will show exactly where the hanging occurs...")
    print("Press Ctrl+C to stop and see summary")
    print("=" * 60)
    
    # Verify monitoring is active
    if not agent_monitor.monitoring_active:
        print("❌ Agent monitoring not active!")
        return False
    
    print("✅ Agent monitoring is active")
    
    # Test data
    test_data = {
        'filename': 'monitored_test.csv',
        'headers': ['Name', 'CI_Type', 'Environment', 'CPU_Cores'],
        'sample_data': [
            ['WebServer01', 'Server', 'Production', '4'],
            ['Database01', 'Database', 'Production', '8']
        ]
    }
    
    print(f"\n📊 Test data prepared: {len(test_data['sample_data'])} assets")
    
    try:
        print("\n🚀 Starting CMDB analysis...")
        print("Watch the real-time monitoring output below:")
        print("-" * 60)
        
        # Start the analysis
        start_time = time.time()
        result = await crewai_service.analyze_cmdb_data(test_data)
        end_time = time.time()
        
        print("-" * 60)
        print(f"✅ Analysis completed in {end_time - start_time:.2f} seconds!")
        print(f"Result type: {result.get('analysis_type', 'unknown')}")
        
        return True
        
    except asyncio.TimeoutError:
        print("\n⏰ Analysis timed out!")
        return False
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return False
    finally:
        # Always print summary
        agent_monitor.print_summary()

async def test_simple_task():
    """Test a simple task to isolate the issue."""
    print("\n🧪 Testing Simple Task Execution")
    print("=" * 40)
    
    try:
        from crewai import Task
        
        # Get agent
        agent = crewai_service.agents.get('cmdb_analyst')
        if not agent:
            print("❌ Agent not available")
            return False
        
        print(f"✅ Using agent: {agent.role}")
        
        # Create simple task
        task = Task(
            description="What type of asset is this: Name=Server01, Type=Server?",
            agent=agent,
            expected_output="Asset type classification (e.g., Server, Database, Application)"
        )
        
        print("🔄 Executing simple task...")
        result = await crewai_service._execute_task_async(task)
        print(f"✅ Simple task completed: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple task failed: {e}")
        return False

async def monitor_status_loop():
    """Background task to print status updates."""
    while True:
        await asyncio.sleep(10)  # Every 10 seconds
        status = agent_monitor.get_status_report()
        
        if status['active_tasks'] > 0:
            print(f"\n📊 STATUS UPDATE: {status['active_tasks']} active tasks")
            for task in status['active_task_details']:
                if task['is_hanging']:
                    print(f"🚨 HANGING: {task['agent']} - {task['elapsed']} - {task['description']}")
                else:
                    print(f"⏳ RUNNING: {task['agent']} - {task['elapsed']} - {task['status']}")

if __name__ == "__main__":
    async def main():
        print("🔬 CrewAI Monitored Execution Test")
        print("=" * 50)
        
        # Start background monitoring
        monitor_task = asyncio.create_task(monitor_status_loop())
        
        try:
            # Test 1: Simple task
            print("TEST 1: Simple Task Execution")
            simple_success = await test_simple_task()
            
            if simple_success:
                print("\n" + "="*50)
                print("TEST 2: Full CMDB Analysis")
                await test_with_monitoring()
            else:
                print("\n❌ Simple task failed - skipping full analysis")
                
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
        finally:
            monitor_task.cancel()
            agent_monitor.print_summary()
            agent_monitor.stop_monitoring()
    
    asyncio.run(main()) 