"""
RAG EOL Enrichment Tool

Level 2 of DB-first, RAG-augment strategy:
When catalog lookup returns cache_miss, use RAG to look up EOL data from:
1. Embedded EOL knowledge base (endoflife.date data)
2. Vendor-specific documentation

Then cache results back to catalog for future lookups.
"""

import logging
from typing import Any, Dict, List, Optional

from .crewai_wrapper import (
    CREWAI_TOOLS_AVAILABLE,
    RAGEOLEnrichmentTool,
)
from .impl import RAGEOLEnrichmentToolImpl
from .knowledge_base import EOL_KNOWLEDGE_BASE
from .utils import calculate_eol_status

logger = logging.getLogger(__name__)

__all__ = [
    "RAGEOLEnrichmentToolImpl",
    "RAGEOLEnrichmentTool",
    "EOL_KNOWLEDGE_BASE",
    "calculate_eol_status",
    "create_rag_eol_enrichment_tools",
    "CREWAI_TOOLS_AVAILABLE",
]


def create_rag_eol_enrichment_tools(
    context_info: Dict[str, Any], registry: Optional[Any] = None
) -> List:
    """
    Create RAG EOL enrichment tools for compliance validation agent.

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id
        registry: Optional ServiceRegistry for dependency injection

    Returns:
        List of RAG EOL enrichment tools
    """
    logger.info("🔧 Creating RAG EOL enrichment tools for compliance validation")

    if registry is None:
        registry = context_info.get("service_registry") if context_info else None
        if registry is None:
            logger.warning(
                "⚠️ No ServiceRegistry available - returning empty tools list"
            )
            return []

    tools = []

    if CREWAI_TOOLS_AVAILABLE:
        tools.append(RAGEOLEnrichmentTool(registry))
    else:
        impl = RAGEOLEnrichmentToolImpl(registry)
        tools.append(impl)

    logger.info(f"✅ Created {len(tools)} RAG EOL enrichment tools")
    return tools
