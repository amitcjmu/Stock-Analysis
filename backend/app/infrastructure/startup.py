"""
Enhanced startup module with deployment flexibility support.
"""

import logging

from app.infrastructure import get_deployment_config, get_service_factory
from app.infrastructure.deployment.detector import service_detector

logger = logging.getLogger(__name__)


async def initialize_infrastructure() -> None:
    """
    Initialize infrastructure services based on deployment configuration.
    """
    logger.info("🔧 Initializing infrastructure services...")

    # Get deployment configuration
    deployment_config = get_deployment_config()
    logger.info(f"📋 Deployment mode: {deployment_config.mode.value}")

    # Initialize service detector
    await service_detector.initialize_default_checks()

    # Get service factory
    factory = get_service_factory()

    # Initialize core services
    logger.info("🔐 Initializing credential manager...")
    await factory.get_credential_manager()

    logger.info("📊 Initializing telemetry service...")
    await factory.get_telemetry_service()

    logger.info("🔑 Initializing authentication backend...")
    await factory.get_auth_backend()

    # Log feature flags
    logger.info("📌 Feature flags:")
    for feature, enabled in deployment_config.features.items():
        status = "✅" if enabled else "❌"
        logger.info(f"  {status} {feature}: {enabled}")

    # Check service health
    logger.info("🏥 Checking service health...")
    health_status = await factory.health_check()
    for service, healthy in health_status.items():
        status = "✅" if healthy else "❌"
        logger.info(f"  {status} {service}: {'healthy' if healthy else 'unhealthy'}")

    logger.info("✅ Infrastructure initialization completed")


async def shutdown_infrastructure() -> None:
    """
    Shutdown infrastructure services gracefully.
    """
    logger.info("🛑 Shutting down infrastructure services...")

    factory = get_service_factory()

    # Flush telemetry data
    try:
        telemetry_service = await factory.get_telemetry_service()
        await telemetry_service.flush()
        logger.info("✅ Telemetry data flushed")
    except Exception as e:
        logger.error(f"❌ Failed to flush telemetry: {e}")

    logger.info("✅ Infrastructure shutdown completed")


def get_infrastructure_info() -> dict:
    """
    Get information about the current infrastructure configuration.

    Returns:
        Dictionary with infrastructure information
    """
    deployment_config = get_deployment_config()

    return {
        "deployment_mode": deployment_config.mode.value,
        "features": deployment_config.features,
        "services": {
            name: {
                "enabled": config.enabled,
                "implementation": config.implementation,
                "has_fallback": config.fallback is not None,
            }
            for name, config in deployment_config.services.items()
        },
    }
