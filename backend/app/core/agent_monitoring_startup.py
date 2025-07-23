"""
Agent Monitoring Startup Module
Initializes agent monitoring services on application startup
Part of the Agent Observability Enhancement Phase 2
"""

import logging

from app.services.agent_monitor import agent_monitor
from app.services.agent_performance_aggregation_service import (
    agent_performance_aggregation_service,
)

logger = logging.getLogger(__name__)


def initialize_agent_monitoring():
    """Initialize all agent monitoring services"""
    try:
        # Start agent monitor
        agent_monitor.start_monitoring()
        logger.info("✅ Agent monitor started successfully")

        # Start performance aggregation service
        agent_performance_aggregation_service.start()
        logger.info("✅ Agent performance aggregation service started successfully")

        # Log monitoring status
        logger.info("🔍 Agent monitoring services initialized:")
        logger.info("   - Real-time task monitoring: ACTIVE")
        logger.info("   - Database persistence: ACTIVE")
        logger.info("   - Daily aggregation: SCHEDULED")
        logger.info("   - Pattern discovery: ENABLED")

    except Exception as e:
        logger.error(f"❌ Failed to initialize agent monitoring: {e}")
        # Don't raise - allow app to start without monitoring


def shutdown_agent_monitoring():
    """Shutdown agent monitoring services gracefully"""
    try:
        # Stop agent monitor
        agent_monitor.stop_monitoring()
        logger.info("✅ Agent monitor stopped")

        # Stop aggregation service
        agent_performance_aggregation_service.stop()
        logger.info("✅ Agent performance aggregation service stopped")

    except Exception as e:
        logger.error(f"❌ Error during agent monitoring shutdown: {e}")
