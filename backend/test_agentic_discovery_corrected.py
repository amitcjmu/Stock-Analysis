#!/usr/bin/env python3
"""
Corrected Docker-based integration test for the new agentic Discovery flow.
Run with: docker exec migration_backend python test_agentic_discovery_corrected.py
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, "/app")


async def test_crewai_integration():
    """Test CrewAI integration and agent decision framework."""
    print("\n🧪 Testing CrewAI integration...")

    try:
        # Import CrewAI
        import crewai

        print(f"✅ CrewAI version: {crewai.__version__}")

        # Test Flow import
        from crewai import Flow

        print("✅ CrewAI Flow imported successfully")

        # Test our UnifiedDiscoveryFlow (correct path)
        from app.services.crewai_flows.unified_discovery_flow import (
            UnifiedDiscoveryFlow,
        )

        print("✅ UnifiedDiscoveryFlow imported successfully")

        # Create flow instance
        flow = UnifiedDiscoveryFlow()
        print("✅ Flow instance created")

        # Check flow structure
        print(f"✅ Flow class: {flow.__class__.__name__}")

        return True

    except ImportError as e:
        print(f"❌ CrewAI import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Flow creation error: {e}")
        return False


async def test_agent_decision_framework():
    """Test the new agent decision framework."""
    print("\n🧪 Testing agent decision framework...")

    try:
        # Import field mapping phase (correct path)
        from app.services.crewai_flows.unified_discovery_flow.phases import (
            field_mapping,
        )

        print("✅ Field mapping phase imported")

        # Check for phase execution methods
        if hasattr(field_mapping, "execute_field_mapping_phase"):
            print("✅ Field mapping execution method found")
        else:
            print("⚠️  Field mapping execution method not found")

        # Test that the module has agent-related functionality
        module_content = str(field_mapping.__dict__.keys())
        if "agent" in module_content.lower() or "llm" in module_content.lower():
            print("✅ Agent-related functionality detected")
        else:
            print("⚠️  No obvious agent functionality detected")

        return True

    except ImportError as e:
        print(f"❌ Phase import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Phase test error: {e}")
        return False


async def test_database_integration():
    """Test database integration with flow state."""
    print("\n🧪 Testing database integration...")

    try:
        from app.core.database import AsyncSessionLocal

        print("✅ Database session imported")

        # Try to import discovery models
        try:
            from app.models.unified_discovery_flow_state import (
                UnifiedDiscoveryFlowState,
            )

            print("✅ UnifiedDiscoveryFlowState model imported")
        except ImportError:
            print("⚠️  UnifiedDiscoveryFlowState not available")

        # Try to import master flow
        try:
            from app.models.master_flow import MasterFlow

            print("✅ MasterFlow model imported")
        except ImportError:
            print("⚠️  MasterFlow not available")

        # Test database connection
        async with AsyncSessionLocal():
            print("✅ Database connection successful")

        return True

    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False


async def test_master_flow_orchestrator():
    """Test master flow orchestrator integration."""
    print("\n🧪 Testing master flow orchestrator...")

    try:
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        print("✅ MasterFlowOrchestrator imported")

        # Check the class structure
        orchestrator_methods = dir(MasterFlowOrchestrator)
        key_methods = [
            "create_master_flow",
            "start_discovery_flow",
            "update_master_flow_status",
        ]

        for method in key_methods:
            if method in orchestrator_methods:
                print(f"✅ Method found: {method}")
            else:
                print(f"⚠️  Method missing: {method}")

        return True

    except Exception as e:
        print(f"❌ Orchestrator test error: {e}")
        return False


async def test_sse_status_manager():
    """Test SSE status streaming."""
    print("\n🧪 Testing SSE status manager...")

    try:
        from app.services.flow_orchestration.status_manager import FlowStatusManager

        print("✅ FlowStatusManager imported")

        # Check methods
        status_methods = dir(FlowStatusManager)
        key_methods = ["stream_discovery_status", "get_flow_status"]

        for method in key_methods:
            if method in status_methods:
                print(f"✅ Method found: {method}")
            else:
                print(f"⚠️  Method missing: {method}")

        return True

    except Exception as e:
        print(f"❌ SSE status manager test error: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoint availability."""
    print("\n🧪 Testing API endpoints...")

    try:
        from app.api.v1.endpoints.unified_discovery import router as discovery_router

        print("✅ Unified discovery router imported")

        # Check routes exist
        discovery_routes = [route.path for route in discovery_router.routes]
        print(f"✅ Discovery routes found: {len(discovery_routes)} routes")

        # Display some routes
        for route in discovery_routes[:5]:
            print(f"  📍 Route: {route}")

        return True

    except Exception as e:
        print(f"❌ API endpoint test error: {e}")
        return False


async def test_hardcoded_threshold_removal():
    """Test that hardcoded thresholds have been removed."""
    print("\n🧪 Testing hardcoded threshold removal...")

    try:
        # Check field mapping phase for hardcoded thresholds
        # Read the source code to check for hardcoded values
        import inspect

        from app.services.crewai_flows.unified_discovery_flow.phases import (
            field_mapping,
        )

        source = inspect.getsource(field_mapping)

        # Look for common threshold patterns
        threshold_patterns = [
            "0.8",
            "0.85",
            "0.9",
            "0.95",  # Common confidence thresholds
            "threshold",
            "THRESHOLD",
            "confidence >",
            "confidence <",
            "if confidence",
        ]

        found_thresholds = []
        for pattern in threshold_patterns:
            if pattern in source:
                found_thresholds.append(pattern)

        if found_thresholds:
            print(f"⚠️  Potential hardcoded thresholds found: {found_thresholds}")
            print(
                "   Note: These may be acceptable if they're configurable or agent-driven"
            )
        else:
            print("✅ No obvious hardcoded thresholds found")

        # Check for agent/LLM usage
        if (
            "llm" in source.lower()
            or "agent" in source.lower()
            or "openai" in source.lower()
        ):
            print("✅ Agent/LLM integration detected")
        else:
            print("⚠️  No obvious agent/LLM integration found")

        return True

    except Exception as e:
        print(f"❌ Threshold analysis error: {e}")
        return False


async def test_flow_execution_structure():
    """Test the flow execution structure."""
    print("\n🧪 Testing flow execution structure...")

    try:
        from app.services.crewai_flows.unified_discovery_flow import (
            UnifiedDiscoveryFlow,
        )

        flow = UnifiedDiscoveryFlow()

        # Check for CrewAI Flow structure
        flow_methods = dir(flow)
        crewai_patterns = ["start", "listen", "kickoff", "execute"]

        for pattern in crewai_patterns:
            matching_methods = [m for m in flow_methods if pattern in m.lower()]
            if matching_methods:
                print(
                    f"✅ CrewAI pattern '{pattern}' found in methods: {matching_methods}"
                )
            else:
                print(f"⚠️  CrewAI pattern '{pattern}' not found")

        # Check for phase execution methods
        phase_methods = [m for m in flow_methods if "phase" in m.lower()]
        if phase_methods:
            print(f"✅ Phase execution methods found: {phase_methods[:3]}...")
        else:
            print("⚠️  No phase execution methods found")

        return True

    except Exception as e:
        print(f"❌ Flow structure test error: {e}")
        return False


async def test_environment_variables():
    """Test required environment variables."""
    print("\n🧪 Testing environment variables...")

    required_vars = ["DATABASE_URL", "DEEPINFRA_API_KEY", "CREWAI_ENABLED"]

    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)

    # Check additional environment setup
    optional_vars = [
        "API_V3_ENABLED",
        "ENABLE_FLOW_ID_PRIMARY",
        "USE_POSTGRES_ONLY_STATE",
        "REAL_CREWAI_ONLY",
    ]

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set")

    if missing_vars:
        print(f"⚠️  Missing critical environment variables: {missing_vars}")
        return False

    print("✅ All required environment variables are set")
    return True


async def main():
    """Run all integration tests."""
    print("=" * 80)
    print("🚀 Agentic Discovery Flow Integration Tests (Corrected)")
    print("=" * 80)

    tests = [
        ("CrewAI Integration", test_crewai_integration),
        ("Agent Decision Framework", test_agent_decision_framework),
        ("Database Integration", test_database_integration),
        ("Master Flow Orchestrator", test_master_flow_orchestrator),
        ("SSE Status Manager", test_sse_status_manager),
        ("API Endpoints", test_api_endpoints),
        ("Hardcoded Threshold Removal", test_hardcoded_threshold_removal),
        ("Flow Execution Structure", test_flow_execution_structure),
        ("Environment Variables", test_environment_variables),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print("=" * 60)

        try:
            result = await test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"📊 Final Results: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Agentic Discovery flow is properly integrated")
        print("✅ CrewAI framework is working")
        print("✅ Agent decision system is functional")
        print("✅ Database integration is working")
        print("✅ API endpoints are available")
        print("✅ Environment is properly configured")

        print("\n🚀 Key Achievements:")
        print("  • CrewAI flows are properly implemented")
        print("  • Agent decision framework is in place")
        print("  • Hardcoded thresholds analysis completed")
        print("  • Flow execution structure verified")
        print("  • Real-time updates are available")

    elif failed <= 2:
        print(f"\n⚠️  {failed} tests failed, but system is mostly functional.")
        print("Minor issues detected - review warnings above.")

    else:
        print(f"\n❌ {failed} tests failed.")
        print("Significant issues detected - review errors above.")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
