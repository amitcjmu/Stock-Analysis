"""
Asset Product Linker Tool

Links assets to catalog products/versions after EOL lookup.
Creates entries in AssetProductLinks table with confidence scores.

This enables:
- Tracking which assets are linked to which product versions
- Building compliance reports across assets
- Identifying assets needing attention based on EOL status
"""

import logging
from typing import Any, Dict, List, Optional

from .crewai_wrapper import (
    AssetProductLinkerTool,
    AssetProductQueryTool,
    CREWAI_TOOLS_AVAILABLE,
)
from .impl import AssetProductLinkerToolImpl

logger = logging.getLogger(__name__)

__all__ = [
    "AssetProductLinkerToolImpl",
    "AssetProductLinkerTool",
    "AssetProductQueryTool",
    "create_asset_product_linker_tools",
    "CREWAI_TOOLS_AVAILABLE",
]


def create_asset_product_linker_tools(  # noqa: C901
    context_info: Dict[str, Any], registry: Optional[Any] = None
) -> List:
    """
    Create asset product linker tools for compliance validation agent.

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id
        registry: Optional ServiceRegistry for dependency injection

    Returns:
        List of asset product linker tools
    """
    logger.info("🔧 Creating asset product linker tools for compliance validation")

    if registry is None:
        registry = context_info.get("service_registry") if context_info else None
        if registry is None:
            logger.warning(
                "⚠️ No ServiceRegistry available - returning empty tools list"
            )
            return []

    tools = []

    if CREWAI_TOOLS_AVAILABLE:
        tools.append(AssetProductLinkerTool(registry))
        tools.append(AssetProductQueryTool(registry))
    else:
        impl = AssetProductLinkerToolImpl(registry)
        tools.append(impl)

    logger.info(f"✅ Created {len(tools)} asset product linker tools")
    return tools
