"""
Core flow manager for discovery flow operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FlowManager:
    """Core manager for discovery flow operations and lifecycle management."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

        # Initialize repositories with multi-tenant context
        self.master_flow_repo = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        # Asset operations handled through flow_repo.asset_queries and flow_repo.asset_commands

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

        Architecture:
        1. Create discovery flow in discovery_flows table with flow_id = X
        2. Create crewai_flow_state_extensions record with same flow_id = X
        3. Both tables linked by having the same flow_id value
        """
        try:
            logger.info(f"🚀 Creating discovery flow and extensions record: {flow_id}")

            # Validate input
            if not flow_id:
                raise ValueError("CrewAI Flow ID is required")

            if not raw_data:
                raise ValueError("Raw data is required for discovery flow")

            # Check if flow already exists (global check to handle duplicates)
            existing_flow = await self.flow_repo.get_by_flow_id_global(flow_id)
            if existing_flow:
                logger.info(
                    f"✅ Discovery flow already exists globally, returning existing: {flow_id}"
                )
                return existing_flow

            # Step 1: Create discovery flow in discovery_flows table
            logger.info(f"🔧 Creating discovery flow: {flow_id}")

            discovery_flow = await self.flow_repo.create_discovery_flow(
                flow_id=flow_id,
                data_import_id=data_import_id,
                user_id=user_id
                or (str(self.context.user_id) if self.context.user_id else "system"),
                raw_data=raw_data,
                metadata=metadata or {},
            )

            # Step 2: Create corresponding crewai_flow_state_extensions record
            await self._create_extensions_record(
                flow_id, data_import_id, user_id, raw_data, metadata
            )

            logger.info(f"✅ Discovery flow created successfully: {flow_id}")
            logger.info(f"   Discovery flow: discovery_flows.flow_id = {flow_id}")
            logger.info(
                f"   Extensions: crewai_flow_state_extensions.flow_id = {flow_id}"
            )

            return discovery_flow

        except Exception as e:
            logger.error(f"❌ Failed to create discovery flow: {e}")
            raise

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
        This is the preferred method for flow creation from CrewAI flows.
        """
        return await self.create_discovery_flow(
            flow_id=flow_id,
            raw_data=raw_data,
            metadata=metadata,
            data_import_id=data_import_id,
            user_id=user_id,
        )

    async def get_flow_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID (single source of truth)"""
        try:
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if flow:
                logger.info(
                    f"✅ Discovery flow found: {flow_id}, next phase: {flow.get_next_phase()}"
                )
            else:
                logger.warning(f"⚠️ Discovery flow not found: {flow_id}")

            return flow

        except Exception as e:
            logger.error(f"❌ Failed to get discovery flow {flow_id}: {e}")
            raise

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
        try:
            logger.info(f"🔄 Updating phase completion: {flow_id}, phase: {phase}")

            # Validate phase
            valid_phases = [
                "data_import",
                "attribute_mapping",
                "data_cleansing",
                "inventory",
                "dependencies",
                "tech_debt",
            ]
            if phase not in valid_phases:
                raise ValueError(
                    f"Invalid phase: {phase}. Valid phases: {valid_phases}"
                )

            # Update phase completion
            flow = await self.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                data=phase_data,
                crew_status=crew_status,
                agent_insights=agent_insights,
            )

            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            # Create assets if this is the inventory phase
            if phase == "inventory" and phase_data.get("assets"):
                await self._create_assets_from_inventory(flow, phase_data["assets"])

            logger.info(
                f"✅ Phase completion updated: {flow_id}, phase: {phase}, progress: {flow.progress_percentage}%"
            )
            return flow

        except Exception as e:
            logger.error(f"❌ Failed to update phase completion for {flow_id}: {e}")
            raise

    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """
        Complete discovery flow and prepare assessment handoff package.
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {flow_id}")

            flow = await self.flow_repo.complete_discovery_flow(flow_id)

            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            logger.info(
                f"✅ Discovery flow completed: {flow_id}, assets: {len(flow.assets)}"
            )
            return flow

        except Exception as e:
            logger.error(f"❌ Failed to complete discovery flow {flow_id}: {e}")
            raise

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow and all associated assets"""
        try:
            logger.info(f"🗑️ Deleting discovery flow: {flow_id}")

            deleted = await self.flow_repo.delete_flow(flow_id)

            if deleted:
                logger.info(f"✅ Discovery flow deleted: {flow_id}")
            else:
                logger.warning(f"⚠️ Discovery flow not found for deletion: {flow_id}")

            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete discovery flow {flow_id}: {e}")
            raise

    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active discovery flows for the current client/engagement"""
        try:
            flows = await self.flow_repo.get_active_flows()
            logger.info(f"✅ Found {len(flows)} active discovery flows")
            return flows

        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            raise

    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get completed discovery flows for the current client/engagement"""
        try:
            flows = await self.flow_repo.get_completed_flows(limit)
            logger.info(f"✅ Found {len(flows)} completed discovery flows")
            return flows

        except Exception as e:
            logger.error(f"❌ Failed to get completed flows: {e}")
            raise

    async def _create_extensions_record(
        self,
        flow_id: str,
        data_import_id: str,
        user_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> None:
        """Create corresponding crewai_flow_state_extensions record."""
        logger.info(f"🔧 Creating crewai_flow_state_extensions record: {flow_id}")

        try:
            extensions_record = await self.master_flow_repo.create_master_flow(
                flow_id=flow_id,  # Same flow_id as discovery flow
                flow_type="discovery",
                user_id=user_id
                or (str(self.context.user_id) if self.context.user_id else "system"),
                flow_name=f"Discovery Flow {flow_id[:8]}",
                flow_configuration={
                    "data_import_id": data_import_id,
                    "raw_data_count": len(raw_data),
                    "metadata": metadata or {},
                },
                initial_state={
                    "created_from": "discovery_flow_service",
                    "raw_data_sample": raw_data[:2] if raw_data else [],
                    "creation_timestamp": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"✅ Extensions record created: {extensions_record.flow_id}")
        except Exception as ext_error:
            logger.warning(
                f"⚠️ Failed to create extensions record (non-critical): {ext_error}"
            )
            # Don't fail the whole operation if extensions creation fails

    async def _create_assets_from_inventory(
        self, flow: DiscoveryFlow, asset_data_list: List[Dict[str, Any]]
    ) -> List[Asset]:
        """Create discovery assets from inventory phase results"""
        try:
            logger.info(
                f"📦 Creating {len(asset_data_list)} assets from inventory for flow: {flow.flow_id}"
            )

            assets = await self.flow_repo.asset_commands.create_assets_from_discovery(
                discovery_flow_id=flow.id,
                asset_data_list=asset_data_list,
                discovered_in_phase="inventory",
            )

            logger.info(f"✅ Created {len(assets)} assets from inventory")
            return assets

        except Exception as e:
            logger.error(f"❌ Failed to create assets from inventory: {e}")
            raise
