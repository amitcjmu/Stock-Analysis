"""
CrewAI Tool Wrappers for RAG EOL Enrichment

Provides CrewAI BaseTool wrapper and dummy implementation when CrewAI is unavailable.
"""

import logging

from .impl import RAGEOLEnrichmentToolImpl

logger = logging.getLogger(__name__)

try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


if CREWAI_TOOLS_AVAILABLE:

    class RAGEOLEnrichmentTool(BaseTool):
        """CrewAI Tool wrapper for RAG EOL enrichment"""

        name: str = "rag_eol_enrichment"
        description: str = (
            "Look up End-of-Life (EOL) information from RAG knowledge base.\n\n"
            "Use this when eol_catalog_lookup returns cache_hit=false.\n\n"
            "Input:\n"
            "- normalized_key: Key from catalog lookup (e.g., 'rhel:9')\n"
            "- technology: Original technology name\n"
            "- version: Original version string\n"
            "- cache_result: Whether to cache result to catalog (default: true)\n\n"
            "Output: JSON with:\n"
            "- rag_hit: true if found in RAG knowledge base\n"
            "- eol_date: End-of-life date\n"
            "- eol_status: 'active', 'eol_soon', or 'eol_expired'\n"
            "- cached_to_catalog: true if result was cached for future lookups"
        )

        def __init__(self, registry):
            super().__init__()
            self._impl = RAGEOLEnrichmentToolImpl(registry)

        async def _arun(
            self,
            normalized_key: str,
            technology: str,
            version: str,
            cache_result: bool = True,
        ) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(
                normalized_key, technology, version, cache_result
            )

        def _run(
            self,
            normalized_key: str,
            technology: str,
            version: str,
            cache_result: bool = True,
        ) -> str:
            return self._impl.execute_sync(
                normalized_key, technology, version, cache_result
            )

else:

    class RAGEOLEnrichmentTool:
        """Dummy tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = RAGEOLEnrichmentToolImpl(registry)

        async def _arun(
            self,
            normalized_key: str,
            technology: str,
            version: str,
            cache_result: bool = True,
        ) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(
                normalized_key, technology, version, cache_result
            )

        def _run(
            self,
            normalized_key: str,
            technology: str,
            version: str,
            cache_result: bool = True,
        ) -> str:
            return self._impl.execute_sync(
                normalized_key, technology, version, cache_result
            )
