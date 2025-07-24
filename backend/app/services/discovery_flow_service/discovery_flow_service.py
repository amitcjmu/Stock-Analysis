"""
Main discovery flow service that orchestrates the modular components.
Provides backward compatibility with the original DiscoveryFlowService interface.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy.ext.asyncio import AsyncSession

from .core.flow_manager import FlowManager
from .managers.asset_manager import AssetManager
from .managers.summary_manager import SummaryManager

logger = logging.getLogger(__name__)


class DiscoveryFlowService:
    """
    Main service layer for discovery flows using new database architecture.
    Integrates with CrewAI flows and maintains enterprise features.

    This class orchestrates the modular components to provide the same interface
    as the original monolithic DiscoveryFlowService.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

        # Initialize modular components
        self.flow_manager = FlowManager(db, context)
        self.asset_manager = AssetManager(db, context)
        self.summary_manager = SummaryManager(db, context)

    async def create_discovery_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None,
    ) -> DiscoveryFlow:
        """
        Create a new discovery flow and ensure corresponding crewai_flow_state_extensions record.
        """
        return await self.flow_manager.create_discovery_flow(
            flow_id=flow_id,
            raw_data=raw_data,
            metadata=metadata,
            data_import_id=data_import_id,
            user_id=user_id,
        )

    async def create_or_get_discovery_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None,
    ) -> DiscoveryFlow:
        """
        Create a new discovery flow or return existing one if it already exists.
        """
        return await self.flow_manager.create_or_get_discovery_flow(
            flow_id=flow_id,
            raw_data=raw_data,
            metadata=metadata,
            data_import_id=data_import_id,
            user_id=user_id,
        )

    async def get_flow_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID (single source of truth)"""
        return await self.flow_manager.get_flow_by_id(flow_id)

    async def update_phase_completion(
        self,
        flow_id: str,
        phase: str,
        phase_data: Dict[str, Any],
        crew_status: Dict[str, Any] = None,
        agent_insights: List[Dict[str, Any]] = None,
    ) -> DiscoveryFlow:
        """
        Update phase completion and store results.
        Integrates with CrewAI crew coordination.
        """
        return await self.flow_manager.update_phase_completion(
            flow_id=flow_id,
            phase=phase,
            phase_data=phase_data,
            crew_status=crew_status,
            agent_insights=agent_insights,
        )

    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """
        Complete discovery flow and prepare assessment handoff package.
        """
        return await self.flow_manager.complete_discovery_flow(flow_id)

    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active discovery flows for the current client/engagement"""
        return await self.flow_manager.get_active_flows()

    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get completed discovery flows for the current client/engagement"""
        return await self.flow_manager.get_completed_flows(limit)

    async def get_flow_assets(self, flow_id: str) -> List[Asset]:
        """Get all assets for a discovery flow"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            return await self.asset_manager.get_flow_assets(flow_id, flow.id)

        except Exception as e:
            logger.error(f"❌ Failed to get assets for flow {flow_id}: {e}")
            raise

    async def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type for the current client/engagement"""
        return await self.asset_manager.get_assets_by_type(asset_type)

    async def validate_asset(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_results: Dict[str, Any] = None,
    ) -> Asset:
        """Update asset validation status and results"""
        return await self.asset_manager.validate_asset(
            asset_id=asset_id,
            validation_status=validation_status,
            validation_results=validation_results,
        )

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow and all associated assets"""
        return await self.flow_manager.delete_flow(flow_id)

    async def get_flow_summary(self, flow_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of the discovery flow"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            return await self.summary_manager.get_flow_summary(flow)

        except Exception as e:
            logger.error(f"❌ Failed to generate flow summary for {flow_id}: {e}")
            raise

    # Enhanced methods using modular components

    async def get_flow_health_report(self, flow_id: str) -> Dict[str, Any]:
        """Generate a health report for a discovery flow"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            return await self.summary_manager.get_flow_health_report(flow)

        except Exception as e:
            logger.error(f"❌ Failed to generate health report for {flow_id}: {e}")
            raise

    async def get_multi_flow_summary(
        self, flow_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get summary statistics across multiple discovery flows"""
        try:
            if flow_ids:
                flows = []
                for flow_id in flow_ids:
                    flow = await self.get_flow_by_id(flow_id)
                    if flow:
                        flows.append(flow)
            else:
                # Get all active flows
                flows = await self.get_active_flows()

            return await self.summary_manager.get_multi_flow_summary(flows)

        except Exception as e:
            logger.error(f"❌ Failed to generate multi-flow summary: {e}")
            raise

    async def bulk_validate_assets(
        self,
        asset_ids: List[uuid.UUID],
        validation_status: str,
        validation_results: Dict[str, Any] = None,
    ) -> List[Asset]:
        """Bulk validate multiple assets"""
        return await self.asset_manager.bulk_validate_assets(
            asset_ids=asset_ids,
            validation_status=validation_status,
            validation_results=validation_results,
        )

    async def get_assets_requiring_review(
        self, flow_id: Optional[str] = None, min_confidence_threshold: float = 0.7
    ) -> List[Asset]:
        """Get assets that require manual review based on confidence threshold"""
        if flow_id:
            # Get assets for specific flow
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            all_assets = await self.asset_manager.get_flow_assets(flow_id, flow.id)
            return [
                asset
                for asset in all_assets
                if (asset.confidence_score or 0) < min_confidence_threshold
            ]
        else:
            # Get all assets requiring review
            return await self.asset_manager.get_assets_requiring_review(
                min_confidence_threshold
            )

    async def filter_flow_assets(
        self, flow_id: str, criteria: Dict[str, Any]
    ) -> List[Asset]:
        """Filter assets in a flow by specific criteria"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            return await self.asset_manager.filter_assets_by_criteria(flow.id, criteria)

        except Exception as e:
            logger.error(f"❌ Failed to filter assets for flow {flow_id}: {e}")
            raise

    async def update_asset_quality_scores(
        self, asset_id: uuid.UUID, quality_score: float, confidence_score: float
    ) -> Asset:
        """Update asset quality and confidence scores"""
        return await self.asset_manager.update_asset_quality_scores(
            asset_id=asset_id,
            quality_score=quality_score,
            confidence_score=confidence_score,
        )

    # Legacy compatibility methods (private implementation details of original class)

    async def _create_assets_from_inventory(
        self, flow: DiscoveryFlow, asset_data_list: List[Dict[str, Any]]
    ) -> List[Asset]:
        """Create discovery assets from inventory phase results (legacy compatibility)"""
        return await self.asset_manager.create_assets_from_discovery(
            discovery_flow_id=flow.id,
            asset_data_list=asset_data_list,
            discovered_in_phase="inventory",
        )
