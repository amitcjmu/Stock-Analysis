"""
Core flow manager for discovery flow operations.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .flow_manager_utils import (
    calculate_readiness_scores,
    convert_uuids_to_str,
    create_assets_from_inventory,
    create_extensions_record,
    update_master_flow_completion,
)

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
        master_flow_id: str = None,  # 🔧 CC FIX: Optional existing master flow to link to
    ) -> DiscoveryFlow:
        """
        Create a new discovery flow and ensure corresponding crewai_flow_state_extensions record.

        Architecture:
        1. Create master flow record in crewai_flow_state_extensions with flow_id = X (atomic transaction)
        2. Create discovery flow in discovery_flows table with flow_id = X and master_flow_id = X
        3. Both operations wrapped in single transaction for atomicity
        """
        # 🔧 CC FIX: Check if we're already in a transaction to avoid nested transaction error
        if self.db.in_transaction():
            # We're already in a transaction, execute directly without starting a new one
            return await self._create_discovery_flow_internal(
                flow_id=flow_id,
                raw_data=raw_data,
                metadata=metadata,
                data_import_id=data_import_id,
                user_id=user_id,
                master_flow_id=master_flow_id,
            )
        else:
            # Start a new transaction if we're not already in one
            async with self.db.begin():
                return await self._create_discovery_flow_internal(
                    flow_id=flow_id,
                    raw_data=raw_data,
                    metadata=metadata,
                    data_import_id=data_import_id,
                    user_id=user_id,
                    master_flow_id=master_flow_id,
                )

    async def _create_discovery_flow_internal(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None,
        master_flow_id: str = None,
    ) -> DiscoveryFlow:
        """Internal method that performs the actual discovery flow creation."""
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

            # 🔧 CC FIX: Convert UUIDs to strings in metadata to prevent JSON serialization errors
            safe_metadata = convert_uuids_to_str(metadata or {})

            # Step 1: Handle master flow (create new or verify existing)
            actual_master_flow_id = master_flow_id or flow_id

            if master_flow_id:
                # 🔧 CC FIX: If master_flow_id is provided, verify it exists
                logger.info(f"🔧 Using existing master flow: {master_flow_id}")
                master_flow_check = await self.master_flow_repo.get_master_flow_by_id(
                    master_flow_id
                )
                if not master_flow_check:
                    logger.warning(
                        f"⚠️ Provided master_flow_id {master_flow_id} not found, creating new one"
                    )
                    await create_extensions_record(
                        flow_id,
                        data_import_id,
                        user_id,
                        raw_data,
                        safe_metadata,
                        self.master_flow_repo,
                        self.context,
                        auto_commit=False,
                    )
                    # 🔧 CC FIX: Flush to ensure master flow persists in transaction
                    await self.db.flush()
                    actual_master_flow_id = flow_id
                else:
                    logger.info(
                        f"✅ Master flow {master_flow_id} verified and will be used"
                    )
            else:
                # Create new crewai_flow_state_extensions record
                await create_extensions_record(
                    flow_id,
                    data_import_id,
                    user_id,
                    raw_data,
                    safe_metadata,
                    self.master_flow_repo,
                    self.context,
                    auto_commit=False,
                )
                # 🔧 CC FIX: Flush to ensure master flow persists in transaction
                await self.db.flush()

            # Step 2: Create discovery flow in discovery_flows table
            logger.info(f"🔧 Creating discovery flow: {flow_id}")

            discovery_flow = await self.flow_repo.create_discovery_flow(
                flow_id=flow_id,
                master_flow_id=actual_master_flow_id,  # 🔧 CC FIX: Always pass master_flow_id
                data_import_id=data_import_id,
                user_id=user_id
                or (str(self.context.user_id) if self.context.user_id else "system"),
                raw_data=raw_data,
                metadata=safe_metadata,
                auto_commit=False,  # 🔧 CC FIX: Don't commit within transaction
            )

            logger.info(f"✅ Discovery flow created successfully: {flow_id}")
            logger.info(f"   Discovery flow: discovery_flows.flow_id = {flow_id}")
            logger.info(
                f"   Master flow: crewai_flow_state_extensions.flow_id = {actual_master_flow_id}"
            )

            return discovery_flow

        except Exception as e:
            logger.error(f"❌ Failed to create discovery flow: {e}")
            # Transaction will be automatically rolled back if we started one
            raise

    async def create_or_get_discovery_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None,
        master_flow_id: str = None,  # 🔧 CC FIX: Pass through master_flow_id
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
            master_flow_id=master_flow_id,
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

            # Extract completed flag from phase_data if present
            completed = phase_data.get("completed", False)

            # Update phase completion
            flow = await self.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                data=phase_data,
                completed=completed,
                agent_insights=agent_insights,
            )

            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            # Create assets if this is the inventory phase
            if phase == "inventory" and phase_data.get("assets"):
                await create_assets_from_inventory(
                    flow, phase_data["assets"], self.flow_repo
                )

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

        This service method orchestrates:
        1. Readiness score calculation (business logic)
        2. Flow completion in repository (data persistence)
        3. Master flow state update (cross-repository coordination)
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {flow_id}")

            # Step 1: Get current flow to calculate readiness
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")

            # Step 2: Calculate readiness scores (business logic in service layer)
            readiness_scores = calculate_readiness_scores(flow)
            logger.info(
                f"Calculated readiness scores for {flow_id}: overall={readiness_scores.get('overall', 0)}"
            )

            # Step 3: Complete flow in repository with calculated scores
            completed_flow = await self.flow_repo.complete_discovery_flow(
                flow_id, readiness_scores=readiness_scores
            )

            if not completed_flow:
                raise ValueError(f"Failed to complete discovery flow: {flow_id}")

            # Step 4: Update master flow state (cross-repository coordination in service)
            await update_master_flow_completion(flow_id, self.master_flow_repo)

            logger.info(
                f"✅ Discovery flow completed: {flow_id}, assets: {len(completed_flow.assets)}"
            )
            return completed_flow

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
