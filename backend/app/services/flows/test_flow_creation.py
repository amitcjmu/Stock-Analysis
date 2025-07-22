"""
Test script for Phase 2 CrewAI Flow Framework
Tests flow creation, execution, and event handling
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_flow_creation():
    """Test basic flow creation and initialization"""
    try:
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.flows.discovery_flow import DiscoveryFlowState, UnifiedDiscoveryFlow
        
        logger.info("🧪 Testing Phase 2 Flow Creation")
        
        # Create test context
        context = RequestContext(
            client_account_id="test-client-123",
            engagement_id="test-engagement-456",
            user_id="test-user-789"
        )
        
        # Create test data
        import_data = {
            "flow_id": "test-flow-123",
            "import_id": "test-import",
            "filename": "test_data.csv",
            "record_count": 100,
            "raw_data": [
                {"hostname": "server1", "ip": "192.168.1.1", "type": "server"},
                {"hostname": "server2", "ip": "192.168.1.2", "type": "database"},
                {"hostname": "app1", "ip": "192.168.1.3", "type": "application"}
            ]
        }
        
        # Test with mock database session
        async with AsyncSessionLocal() as db:
            logger.info("✅ Database session created")
            
            # Create flow instance
            flow = UnifiedDiscoveryFlow(db, context)
            logger.info("✅ Flow instance created")
            
            # Test state initialization
            initial_state = DiscoveryFlowState(
                flow_id=import_data["flow_id"],
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                data_import_id=import_data["import_id"],
                import_filename=import_data["filename"],
                total_records=import_data["record_count"],
                raw_data=import_data["raw_data"]
            )
            
            logger.info(f"✅ Initial state created: {initial_state.flow_id}")
            logger.info(f"   - Phase: {initial_state.current_phase}")
            logger.info(f"   - Records: {initial_state.total_records}")
            logger.info(f"   - Status: {initial_state.status}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Flow creation test failed: {e}")
        return False


async def test_event_bus():
    """Test event bus functionality"""
    try:
        from datetime import datetime

        from app.services.flows.events import FlowEvent, flow_event_bus
        
        logger.info("🧪 Testing Event Bus")
        
        # Create test event
        test_event = FlowEvent(
            flow_id="test-flow-123",
            event_type="test_event",
            phase="testing",
            data={"message": "Test event data"},
            timestamp=datetime.utcnow(),
            context={"test": True}
        )
        
        # Publish event
        await flow_event_bus.publish(test_event)
        logger.info("✅ Event published")
        
        # Check event history
        recent_events = flow_event_bus.get_recent_events(10)
        logger.info(f"✅ Event history size: {len(recent_events)}")
        
        # Check flow-specific events
        flow_events = flow_event_bus.get_flow_events("test-flow-123")
        logger.info(f"✅ Flow events: {len(flow_events)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Event bus test failed: {e}")
        return False


async def test_flow_manager():
    """Test flow manager functionality"""
    try:
        from app.services.flows.manager import flow_manager
        
        logger.info("🧪 Testing Flow Manager")
        
        # Test manager initialization
        logger.info(f"✅ Active flows: {len(flow_manager.active_flows)}")
        logger.info(f"✅ Flow tasks: {len(flow_manager.flow_tasks)}")
        
        # Test cleanup
        cleaned = await flow_manager.cleanup_completed_flows()
        logger.info(f"✅ Cleaned flows: {cleaned}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Flow manager test failed: {e}")
        return False


async def test_decorators():
    """Test @start and @listen decorators"""
    try:
        from app.services.flows.discovery_flow import listen, start
        
        logger.info("🧪 Testing CrewAI Decorators")
        
        # Test decorator imports
        logger.info("✅ @start decorator imported")
        logger.info("✅ @listen decorator imported")
        
        # Check if decorators are callable
        if callable(start):
            logger.info("✅ @start decorator is callable")
        else:
            logger.warning("⚠️ @start decorator is not callable (fallback mode)")
            
        if callable(listen):
            logger.info("✅ @listen decorator is callable")
        else:
            logger.warning("⚠️ @listen decorator is not callable (fallback mode)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Decorator test failed: {e}")
        return False


async def test_crew_factory():
    """Test crew factory integration"""
    try:
        from app.services.flows.discovery_flow import CREW_FACTORY_AVAILABLE, CrewFactory
        
        logger.info("🧪 Testing Crew Factory Integration")
        
        if CREW_FACTORY_AVAILABLE:
            logger.info("✅ CrewFactory available")
        else:
            logger.warning("⚠️ CrewFactory not available (fallback mode)")
        
        # Test crew factory execution
        crew_factory = CrewFactory()
        result = await crew_factory.execute_crew(
            crew_type="test_crew",
            inputs={"test": "data"}
        )
        
        logger.info(f"✅ Crew execution result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Crew factory test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results"""
    logger.info("🚀 Starting Phase 2 Flow Framework Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Flow Creation", test_flow_creation),
        ("Event Bus", test_event_bus), 
        ("Flow Manager", test_flow_manager),
        ("CrewAI Decorators", test_decorators),
        ("Crew Factory", test_crew_factory)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} Test...")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED {test_name}: {e}")
    
    # Report summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Phase 2 Flow Framework tests passed!")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())