"""
Example usage of Phase 2 CrewAI Flow Framework

This demonstrates how to use the new flow framework with proper @start/@listen decorators
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_flow_creation():
    """Example: Creating and starting a discovery flow"""
    try:
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.flows import flow_manager

        logger.info("📝 Example: Creating a discovery flow")

        # Create context
        context = RequestContext(
            client_account_id="example-client-123",
            engagement_id="example-engagement-456",
            user_id="example-user-789",
        )

        # Prepare import data
        import_data = {
            "flow_id": "example-flow-123",
            "import_id": "example-import",
            "filename": "example_servers.csv",
            "record_count": 50,
            "raw_data": [
                {
                    "hostname": "web-server-01",
                    "ip_address": "10.0.1.10",
                    "operating_system": "Ubuntu 20.04",
                    "asset_type": "server",
                    "environment": "production",
                    "business_owner": "IT Team",
                },
                {
                    "hostname": "db-server-01",
                    "ip_address": "10.0.1.20",
                    "operating_system": "RHEL 8",
                    "asset_type": "database",
                    "environment": "production",
                    "business_owner": "Data Team",
                },
                {
                    "hostname": "app-server-01",
                    "ip_address": "10.0.1.30",
                    "operating_system": "Windows Server 2019",
                    "asset_type": "application",
                    "environment": "staging",
                    "business_owner": "Development Team",
                },
            ],
            "session_id": "example-session-456",
        }

        # Create flow using manager
        async with AsyncSessionLocal() as db:
            flow_id = await flow_manager.create_discovery_flow(db, context, import_data)
            logger.info(f"✅ Created flow: {flow_id}")

            # Check flow status
            await asyncio.sleep(1)  # Give flow time to start
            status = await flow_manager.get_flow_status(flow_id)
            if status:
                logger.info(
                    f"📊 Flow status: {status['current_phase']} ({status['progress_percentage']}%)"
                )

            return flow_id

    except Exception as e:
        logger.error(f"❌ Flow creation example failed: {e}")
        return None


async def example_event_monitoring():
    """Example: Monitoring flow events"""
    try:
        from app.services.flows.events import (flow_event_bus,
                                               publish_flow_event)

        logger.info("📝 Example: Event monitoring")

        # Subscribe to events
        def event_handler(event):
            logger.info(
                f"🔔 Event received: {event.event_type} for flow {event.flow_id}"
            )
            logger.info(f"   Phase: {event.phase}")
            logger.info(f"   Data: {event.data}")

        flow_event_bus.subscribe("*", event_handler)

        # Publish test event
        await publish_flow_event(
            flow_id="example-flow-123",
            event_type="example_event",
            phase="example_phase",
            data={"message": "This is an example event"},
            context={"example": True},
        )

        # Check event history
        events = flow_event_bus.get_recent_events(10)
        logger.info(f"📋 Total events in history: {len(events)}")

        return True

    except Exception as e:
        logger.error(f"❌ Event monitoring example failed: {e}")
        return False


async def example_direct_flow_usage():
    """Example: Using flow directly (without manager)"""
    try:
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.flows import UnifiedDiscoveryFlow

        logger.info("📝 Example: Direct flow usage")

        # Create context
        context = RequestContext(
            client_account_id="direct-client-123",
            engagement_id="direct-engagement-456",
            user_id="direct-user-789",
        )

        # Create flow directly
        async with AsyncSessionLocal() as db:
            flow = UnifiedDiscoveryFlow(db, context)

            # Prepare data
            import_data = {
                "flow_id": "direct-flow-123",
                "import_id": "direct-import",
                "filename": "direct_test.csv",
                "record_count": 10,
                "raw_data": [
                    {"hostname": "test-server", "type": "server"},
                    {"hostname": "test-db", "type": "database"},
                ],
                "session_id": "direct-session-456",
            }

            # Initialize flow
            state = await flow.initialize_discovery(import_data)
            logger.info(f"✅ Flow initialized: {state.flow_id}")
            logger.info(f"   Phase: {state.current_phase}")
            logger.info(f"   Records: {state.total_records}")

            # Manually execute next phase (normally handled by @listen decorators)
            # This is just for demonstration - in real usage, CrewAI handles the flow
            logger.info("🔄 Would normally proceed through phases automatically...")

            return True

    except Exception as e:
        logger.error(f"❌ Direct flow usage example failed: {e}")
        return False


async def example_api_usage():
    """Example: How to use the new API endpoints"""
    logger.info("📝 Example: API endpoint usage")

    api_examples = {
        "Create CrewAI Flow": "POST /api/v3/discovery-flow/flows/crewai",
        "Get Flow Status": "GET /api/v3/discovery-flow/flows/{flow_id}/crewai-status",
        "Pause Flow": "POST /api/v3/discovery-flow/flows/{flow_id}/pause",
        "Resume Flow": "POST /api/v3/discovery-flow/flows/{flow_id}/resume",
        "Get Flow Events": "GET /api/v3/discovery-flow/flows/events/{flow_id}",
        "Manager Status": "GET /api/v3/discovery-flow/flows/manager/status",
    }

    logger.info("🌐 New Phase 2 API Endpoints:")
    for name, endpoint in api_examples.items():
        logger.info(f"   {name}: {endpoint}")

    # Example request payloads
    logger.info("\n📋 Example request payloads:")

    create_flow_payload = {
        "name": "Example Migration Discovery",
        "description": "Discover assets for Q4 migration project",
        "execution_mode": "hybrid",
    }
    logger.info(f"Create Flow Payload: {create_flow_payload}")

    return True


async def example_phase_transitions():
    """Example: Understanding phase transitions"""
    logger.info("📝 Example: Phase transitions with @start/@listen")

    phases = [
        ("@start", "initialize_discovery", "Entry point - triggered externally"),
        ("@listen", "validate_and_analyze_data", "Triggered after initialization"),
        ("@listen", "perform_field_mapping", "Triggered after validation"),
        ("@listen", "cleanse_data", "Triggered after field mapping"),
        ("@listen", "build_asset_inventory", "Triggered after cleansing"),
        ("@listen", "analyze_dependencies", "Triggered after inventory"),
        ("@listen", "assess_technical_debt", "Triggered after dependencies"),
    ]

    logger.info("🔄 Phase Transition Flow:")
    for i, (decorator, method, description) in enumerate(phases, 1):
        logger.info(f"   {i}. {decorator} {method}()")
        logger.info(f"      {description}")

    logger.info("\n💡 Key Benefits:")
    logger.info("   ✅ Event-driven execution")
    logger.info("   ✅ Automatic phase progression")
    logger.info("   ✅ State persistence at each step")
    logger.info("   ✅ Error handling and recovery")
    logger.info("   ✅ Real-time monitoring via events")

    return True


async def run_examples():
    """Run all examples"""
    logger.info("🚀 Phase 2 CrewAI Flow Framework Examples")
    logger.info("=" * 60)

    examples = [
        ("Phase Transitions", example_phase_transitions),
        ("API Usage", example_api_usage),
        ("Event Monitoring", example_event_monitoring),
        ("Direct Flow Usage", example_direct_flow_usage),
        ("Flow Creation", example_flow_creation),
    ]

    for name, example_func in examples:
        logger.info(f"\n🔍 {name} Example")
        logger.info("-" * 40)
        try:
            await example_func()
            logger.info(f"✅ {name} example completed")
        except Exception as e:
            logger.error(f"❌ {name} example failed: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("🎉 All Phase 2 Flow Framework examples completed!")
    logger.info("\n📚 Next Steps:")
    logger.info("   1. Integrate with Agent System (Track A)")
    logger.info("   2. Connect to Crew Management (Track A2)")
    logger.info("   3. Use Context Framework (Track C1)")
    logger.info("   4. Integrate Tools (Track D1)")


if __name__ == "__main__":
    asyncio.run(run_examples())
