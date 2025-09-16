"""
Utilities - Helper Functions and Factory Methods

Contains factory functions and utility methods for UnifiedDiscoveryFlow.
"""

import logging
import uuid
from typing import Optional

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


def create_unified_discovery_flow(
    crewai_service,
    context: RequestContext,
    flow_id: Optional[str] = None,
    master_flow_id: Optional[str] = None,
    **kwargs,
):
    """
    Factory function to create a UnifiedDiscoveryFlow instance
    """
    from .base import UnifiedDiscoveryFlow

    logger.info("🏭 Creating new UnifiedDiscoveryFlow instance")

    # Generate flow_id if not provided
    if not flow_id:
        flow_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new flow_id: {flow_id}")

    # Create flow instance
    flow = UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        flow_id=flow_id,
        master_flow_id=master_flow_id,
        **kwargs,
    )

    logger.info(f"✅ UnifiedDiscoveryFlow created successfully - ID: {flow_id}")
    return flow
