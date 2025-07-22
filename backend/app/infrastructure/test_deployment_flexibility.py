"""
Test script to demonstrate deployment flexibility features.
"""

import asyncio
import os
from typing import Any, Dict

from app.infrastructure import DeploymentMode, get_deployment_config, get_service_factory
from app.infrastructure.telemetry import MetricType


async def test_deployment_mode(mode: str) -> Dict[str, Any]:
    """Test services in a specific deployment mode."""
    print(f"\n{'='*60}")
    print(f"Testing {mode.upper()} deployment mode")
    print(f"{'='*60}")
    
    # Set deployment mode
    os.environ["DEPLOYMENT_MODE"] = mode
    
    # Get configuration
    config = get_deployment_config()
    print(f"\nDeployment Mode: {config.mode.value}")
    print(f"Features: {config.features}")
    
    # Get service factory
    factory = get_service_factory()
    
    # Test credential manager
    print("\n--- Testing Credential Manager ---")
    cred_manager = await factory.get_credential_manager()
    
    # Store credential
    await cred_manager.set_credential("test_key", "test_value", "test_namespace")
    print("✅ Stored credential")
    
    # Retrieve credential
    value = await cred_manager.get_credential("test_key", "test_namespace")
    print(f"✅ Retrieved credential: {value}")
    
    # Test telemetry service
    print("\n--- Testing Telemetry Service ---")
    telemetry = await factory.get_telemetry_service()
    
    # Record metric
    await telemetry.record_metric(
        "test_metric",
        42.0,
        MetricType.GAUGE,
        tags={"mode": mode}
    )
    print("✅ Recorded metric")
    
    # Record event
    await telemetry.record_event(
        "test_event",
        properties={"mode": mode, "test": True}
    )
    print("✅ Recorded event")
    
    # Test authentication
    print("\n--- Testing Authentication Backend ---")
    auth_backend = await factory.get_auth_backend()
    
    # Create user
    try:
        user = await auth_backend.create_user(
            username=f"test_{mode}",
            email=f"test_{mode}@example.com",
            password="test_password"
        )
        print(f"✅ Created user: {user.get('username')}")
    except Exception as e:
        print(f"⚠️  User creation skipped: {e}")
    
    # Health checks
    print("\n--- Health Checks ---")
    health_status = await factory.health_check()
    for service, healthy in health_status.items():
        status = "✅" if healthy else "❌"
        print(f"{status} {service}: {'healthy' if healthy else 'unhealthy'}")
    
    return {
        "mode": mode,
        "config": config.mode.value,
        "features": config.features,
        "health": health_status
    }


async def test_service_fallbacks():
    """Test service fallback mechanisms."""
    print(f"\n{'='*60}")
    print("Testing Service Fallbacks")
    print(f"{'='*60}")
    
    # Set SaaS mode but without cloud service configs
    os.environ["DEPLOYMENT_MODE"] = "saas"
    os.environ["KMS_ENDPOINT"] = ""  # Empty to trigger fallback
    os.environ["TELEMETRY_ENDPOINT"] = ""
    
    factory = get_service_factory()
    
    # Test credential fallback
    print("\n--- Testing Credential Manager Fallback ---")
    cred_manager = await factory.get_credential_manager()
    await cred_manager.set_credential("fallback_test", "fallback_value")
    value = await cred_manager.get_credential("fallback_test")
    print(f"✅ Fallback worked: {value}")
    
    # Test telemetry fallback
    print("\n--- Testing Telemetry Service Fallback ---")
    telemetry = await factory.get_telemetry_service()
    await telemetry.record_metric("fallback_metric", 100.0)
    print("✅ Telemetry fallback to NoOp worked")


async def main():
    """Run all deployment flexibility tests."""
    print("🚀 Deployment Flexibility Test Suite")
    
    # Test each deployment mode
    modes = ["development", "on_premises", "saas", "hybrid"]
    results = []
    
    for mode in modes:
        try:
            result = await test_deployment_mode(mode)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error testing {mode} mode: {e}")
    
    # Test fallbacks
    await test_service_fallbacks()
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n{result['mode'].upper()}:")
        print(f"  - Mode: {result['config']}")
        print(f"  - Features enabled: {sum(1 for v in result['features'].values() if v)}")
        print(f"  - Services healthy: {sum(1 for v in result['health'].values() if v)}/{len(result['health'])}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())