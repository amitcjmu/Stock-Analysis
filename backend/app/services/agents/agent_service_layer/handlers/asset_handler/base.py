"""
Base AssetHandler class that orchestrates asset operations.
"""

import logging
from typing import Any, Dict

from app.core.context import RequestContext
from .queries import AssetQueries
from .analysis import AssetAnalysis
from .validation import AssetValidation

logger = logging.getLogger(__name__)


class AssetHandler:
    """Handles asset management operations for the agent service layer."""

    def __init__(self, context: RequestContext):
        self.context = context
        self._queries = AssetQueries(context)
        self._analysis = AssetAnalysis(context)
        self._validation = AssetValidation(context)

    # Asset Query Operations
    async def get_discovered_assets(self, flow_id: str, asset_type: str = None):
        """Get discovered assets for a flow"""
        return await self._queries.get_discovered_assets(flow_id, asset_type)

    async def get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get relationships for a specific asset"""
        return await self._queries.get_asset_relationships(asset_id)

    # Asset Analysis Operations
    async def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get asset dependencies for a flow"""
        return await self._analysis.get_asset_dependencies(flow_id)

    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis for a flow"""
        return await self._analysis.get_tech_debt_analysis(flow_id)

    # Asset Validation Operations
    async def validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        return await self._validation.validate_asset_data(asset_id)
