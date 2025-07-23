"""
Discovery Flow Base Repository

Main repository class that delegates to specialized query and command modules.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.context_aware_repository import ContextAwareRepository

# Import command handlers
from .commands import AssetCommands, FlowCommands

# Import query handlers
from .queries import AnalyticsQueries, AssetQueries, FlowQueries

logger = logging.getLogger(__name__)


class DiscoveryFlowRepository(ContextAwareRepository):
    """
    Repository for discovery flow operations.
    Uses CrewAI Flow ID as single source of truth.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str = None,
        user_id: Optional[str] = None,
    ):
        """Initialize with context-aware defaults"""
        # Handle None values and invalid UUIDs with proper fallbacks
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Safely convert client_account_id
        try:
            if isinstance(client_account_id, uuid.UUID):
                parsed_client_id = client_account_id
            elif client_account_id and client_account_id != "None":
                parsed_client_id = uuid.UUID(str(client_account_id))
            else:
                parsed_client_id = demo_client_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid client_account_id '{client_account_id}', using demo fallback"
            )
            parsed_client_id = demo_client_id

        # Safely convert engagement_id
        try:
            if isinstance(engagement_id, uuid.UUID):
                parsed_engagement_id = engagement_id
            elif engagement_id and engagement_id != "None":
                parsed_engagement_id = uuid.UUID(str(engagement_id))
            else:
                parsed_engagement_id = demo_engagement_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid engagement_id '{engagement_id}', using demo fallback"
            )
            parsed_engagement_id = demo_engagement_id

        super().__init__(
            db=db,
            model_class=DiscoveryFlow,
            client_account_id=str(parsed_client_id),
            engagement_id=str(parsed_engagement_id),
        )

        # Initialize query and command handlers
        self.flow_queries = FlowQueries(db, parsed_client_id, parsed_engagement_id)
        self.asset_queries = AssetQueries(db, parsed_client_id, parsed_engagement_id)
        self.analytics_queries = AnalyticsQueries(
            db, parsed_client_id, parsed_engagement_id
        )

        self.flow_commands = FlowCommands(db, parsed_client_id, parsed_engagement_id)
        self.asset_commands = AssetCommands(db, parsed_client_id, parsed_engagement_id)

        logger.info(
            f"DiscoveryFlowRepository initialized - Client: {parsed_client_id}, Engagement: {parsed_engagement_id}"
        )

    # ========================================
    # FLOW QUERY OPERATIONS (delegated)
    # ========================================

    async def get_by_flow_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow by ID with context filtering"""
        return await self.flow_queries.get_by_flow_id(flow_id)

    async def get_by_flow_id_global(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow by ID without context filtering"""
        return await self.flow_queries.get_by_flow_id_global(flow_id)

    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active flows"""
        return await self.flow_queries.get_active_flows()

    async def get_incomplete_flows(self) -> List[DiscoveryFlow]:
        """Get incomplete flows"""
        return await self.flow_queries.get_incomplete_flows()

    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get recently completed flows"""
        return await self.flow_queries.get_completed_flows(limit)

    async def get_by_master_flow_id(
        self, master_flow_id: str
    ) -> Optional[DiscoveryFlow]:
        """Get flow by master flow ID"""
        return await self.flow_queries.get_by_master_flow_id(master_flow_id)

    # ========================================
    # FLOW COMMAND OPERATIONS (delegated)
    # ========================================

    async def create_discovery_flow(
        self,
        flow_id: str,
        master_flow_id: Optional[str] = None,
        flow_type: str = "primary",
        description: Optional[str] = None,
        initial_state_data: Optional[Dict[str, Any]] = None,
        data_import_id: Optional[str] = None,
        user_id: Optional[str] = None,
        raw_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DiscoveryFlow:
        """Create a new discovery flow"""
        return await self.flow_commands.create_discovery_flow(
            flow_id=flow_id,
            master_flow_id=master_flow_id,
            flow_type=flow_type,
            description=description,
            initial_state_data=initial_state_data,
            data_import_id=data_import_id,
            user_id=user_id,
            raw_data=raw_data,
            metadata=metadata,
        )

    async def update_phase_completion(
        self,
        flow_id: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        crew_status: Optional[Dict[str, Any]] = None,
        completed: bool = True,
        agent_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DiscoveryFlow]:
        """Update phase completion status"""
        return await self.flow_commands.update_phase_completion(
            flow_id, phase, data, crew_status, completed, agent_insights
        )

    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """Mark a discovery flow as completed"""
        return await self.flow_commands.complete_discovery_flow(flow_id)

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow and its assets"""
        return await self.flow_commands.delete_flow(flow_id)

    async def update_master_flow_reference(
        self, flow_id: str, master_flow_id: str
    ) -> bool:
        """Update master flow reference"""
        return await self.flow_commands.update_master_flow_reference(
            flow_id, master_flow_id
        )

    async def transition_to_assessment_phase(
        self, flow_id: str, assessment_flow_id: str
    ) -> bool:
        """Transition flow to assessment phase"""
        return await self.flow_commands.transition_to_assessment_phase(
            flow_id, assessment_flow_id
        )

    # ========================================
    # ASSET QUERY OPERATIONS (delegated)
    # ========================================

    async def get_assets_by_flow_id(self, discovery_flow_id: uuid.UUID) -> List[Asset]:
        """Get all assets for a discovery flow"""
        return await self.asset_queries.get_assets_by_flow_id(discovery_flow_id)

    async def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type"""
        return await self.asset_queries.get_assets_by_type(asset_type)

    # ========================================
    # ASSET COMMAND OPERATIONS (delegated)
    # ========================================

    async def create_assets_from_discovery(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """Create assets from discovery data"""
        return await self.asset_commands.create_assets_from_discovery(
            discovery_flow_id, asset_data_list, discovered_in_phase
        )

    async def update_asset_validation(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_notes: Optional[str] = None,
    ) -> Optional[Asset]:
        """Update asset validation status"""
        return await self.asset_commands.update_asset_validation(
            asset_id, validation_status, validation_notes
        )

    # ========================================
    # ANALYTICS OPERATIONS (delegated)
    # ========================================

    async def get_master_flow_coordination_summary(self) -> Dict[str, Any]:
        """Get master flow coordination analytics"""
        return await self.analytics_queries.get_master_flow_coordination_summary()

    async def get_flow_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get flow analytics for the specified period"""
        return await self.analytics_queries.get_flow_analytics(days)
