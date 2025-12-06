"""
CrewAI Tool Wrappers for Asset Product Linker

Provides CrewAI BaseTool wrappers and dummy implementations when CrewAI is unavailable.
"""

import asyncio
import concurrent.futures
import logging
from typing import Optional

import nest_asyncio

from .impl import AssetProductLinkerToolImpl

logger = logging.getLogger(__name__)

try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


if CREWAI_TOOLS_AVAILABLE:  # noqa: C901

    class AssetProductLinkerTool(BaseTool):
        """CrewAI Tool wrapper for asset product linking"""

        name: str = "asset_product_linker"
        description: str = (
            "Link an asset to a catalog product version after EOL lookup.\n\n"
            "Call this after successfully looking up EOL data to create a persistent link.\n\n"
            "Input:\n"
            "- asset_id: UUID of the asset to link\n"
            "- catalog_version_id: UUID from eol_catalog_lookup result\n"
            "- technology: Technology name (for tracking)\n"
            "- version: Version string (for tracking)\n"
            "- confidence_score: Match confidence (0.0 to 1.0, default: 0.9)\n"
            "- matched_by: 'agent', 'manual', or 'import'\n\n"
            "Output: JSON with link_id and status (created/updated)"
        )

        def __init__(self, registry):
            super().__init__()
            self._impl = AssetProductLinkerToolImpl(registry)

        async def _arun(
            self,
            asset_id: str,
            catalog_version_id: Optional[str] = None,
            tenant_version_id: Optional[str] = None,
            technology: Optional[str] = None,
            version: Optional[str] = None,
            confidence_score: float = 0.9,
            matched_by: str = "agent",
        ) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(
                asset_id,
                catalog_version_id,
                tenant_version_id,
                technology,
                version,
                confidence_score,
                matched_by,
            )

        def _run(
            self,
            asset_id: str,
            catalog_version_id: Optional[str] = None,
            tenant_version_id: Optional[str] = None,
            technology: Optional[str] = None,
            version: Optional[str] = None,
            confidence_score: float = 0.9,
            matched_by: str = "agent",
        ) -> str:
            return self._impl.execute_sync(
                asset_id,
                catalog_version_id,
                tenant_version_id,
                technology,
                version,
                confidence_score,
                matched_by,
            )

    class AssetProductQueryTool(BaseTool):
        """CrewAI Tool wrapper for querying asset products"""

        name: str = "asset_product_query"
        description: str = (
            "Get all products linked to an asset with their EOL status.\n\n"
            "Use this to check what products an asset is already linked to.\n\n"
            "Input:\n"
            "- asset_id: UUID of the asset\n\n"
            "Output: JSON with list of linked products and EOL information"
        )

        def __init__(self, registry):
            super().__init__()
            self._impl = AssetProductLinkerToolImpl(registry)

        async def _arun(self, asset_id: str) -> str:
            return await self._impl.get_asset_products_async(asset_id)

        def _run(self, asset_id: str) -> str:
            nest_asyncio.apply()

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._impl.get_asset_products_async(asset_id),
                        )
                        return future.result()
                else:
                    return asyncio.run(self._impl.get_asset_products_async(asset_id))
            except RuntimeError:
                return asyncio.run(self._impl.get_asset_products_async(asset_id))

else:

    class AssetProductLinkerTool:
        """Dummy tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = AssetProductLinkerToolImpl(registry)

        async def _arun(
            self,
            asset_id: str,
            catalog_version_id: Optional[str] = None,
            tenant_version_id: Optional[str] = None,
            technology: Optional[str] = None,
            version: Optional[str] = None,
            confidence_score: float = 0.9,
            matched_by: str = "agent",
        ) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(
                asset_id,
                catalog_version_id,
                tenant_version_id,
                technology,
                version,
                confidence_score,
                matched_by,
            )

        def _run(
            self,
            asset_id: str,
            catalog_version_id: Optional[str] = None,
            tenant_version_id: Optional[str] = None,
            technology: Optional[str] = None,
            version: Optional[str] = None,
            confidence_score: float = 0.9,
            matched_by: str = "agent",
        ) -> str:
            return self._impl.execute_sync(
                asset_id,
                catalog_version_id,
                tenant_version_id,
                technology,
                version,
                confidence_score,
                matched_by,
            )

    class AssetProductQueryTool:
        """Dummy tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = AssetProductLinkerToolImpl(registry)

        async def _arun(self, asset_id: str) -> str:
            return await self._impl.get_asset_products_async(asset_id)

        def _run(self, asset_id: str) -> str:
            nest_asyncio.apply()

            try:
                return asyncio.run(self._impl.get_asset_products_async(asset_id))
            except RuntimeError:
                return asyncio.run(self._impl.get_asset_products_async(asset_id))
