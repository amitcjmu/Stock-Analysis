"""
Discovery Flow Phase Transition Service

Handles automatic phase transitions after completion of phase requirements.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.discovery_flow import DiscoveryFlow
from app.models.data_import.mapping import ImportFieldMapping
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands,
)

logger = logging.getLogger(__name__)


class DiscoveryPhaseTransitionService:
    """Service to handle automatic phase transitions in discovery flow"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # Note: phase_mgmt will be created per flow with proper context

    async def check_and_transition_from_attribute_mapping(
        self, flow_id: str
    ) -> Optional[str]:
        """
        Check if attribute mapping is complete and transition to data cleansing.

        Returns:
            Next phase name if transition occurred, None otherwise
        """
        try:
            # First get the flow to extract client_account_id and engagement_id
            flow_result = await self.db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
            )
            flow = flow_result.scalar_one_or_none()

            if not flow:
                logger.error(f"Flow {flow_id} not found")
                return None

            # Check if all required field mappings are approved
            approved_mappings = await self.db.execute(
                select(ImportFieldMapping)
                .where(ImportFieldMapping.master_flow_id == flow_id)
                .where(ImportFieldMapping.is_approved.is_(True))
            )
            approved_count = len(approved_mappings.scalars().all())

            if approved_count == 0:
                logger.info(
                    f"No approved mappings for flow {flow_id}, cannot transition"
                )
                return None

            # Check total mappings that need approval
            total_mappings = await self.db.execute(
                select(ImportFieldMapping).where(
                    ImportFieldMapping.master_flow_id == flow_id
                )
            )
            total_count = len(total_mappings.scalars().all())

            # Calculate approval percentage
            approval_percentage = (
                (approved_count / total_count * 100) if total_count > 0 else 0
            )

            # Require at least 80% approval to proceed
            if approval_percentage < 80:
                logger.info(
                    f"Only {approval_percentage:.1f}% mappings approved for flow {flow_id}, "
                    f"need at least 80% to transition"
                )
                return None

            # Create phase management with proper context from the flow
            phase_mgmt = FlowPhaseManagementCommands(
                self.db, flow.client_account_id, flow.engagement_id
            )

            # Update phase completion status
            await phase_mgmt.update_phase_completion(
                flow_id=flow_id,
                phase="field_mapping",
                completed=True,
                data={
                    "approved_mappings": approved_count,
                    "total_mappings": total_count,
                    "approval_percentage": approval_percentage,
                },
            )

            # Transition to data cleansing phase
            await self.db.execute(
                update(DiscoveryFlow)
                .where(DiscoveryFlow.id == flow_id)
                .values(
                    current_phase="data_cleansing",
                    field_mapping_completed=True,
                )
            )
            await self.db.commit()

            logger.info(
                f"✅ Successfully transitioned flow {flow_id} from attribute_mapping "
                f"to data_cleansing ({approved_count}/{total_count} mappings approved)"
            )

            return "data_cleansing"

        except Exception as e:
            logger.error(f"Error in phase transition for flow {flow_id}: {e}")
            await self.db.rollback()
            return None

    async def check_and_transition_from_data_cleansing(
        self, flow_id: str
    ) -> Optional[str]:
        """
        Check if data cleansing is complete and transition to inventory.

        Returns:
            Next phase name if transition occurred, None otherwise
        """
        try:
            # Get the discovery flow
            result = await self.db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
            )
            flow = result.scalar_one_or_none()

            if not flow:
                logger.error(f"Discovery flow {flow_id} not found")
                return None

            # Check if data cleansing has been marked complete
            # This would typically be set by the data cleansing completion endpoint
            if flow.data_cleansing_completed:
                # Transition to inventory phase
                await self.db.execute(
                    update(DiscoveryFlow)
                    .where(DiscoveryFlow.id == flow_id)
                    .values(current_phase="inventory")
                )
                await self.db.commit()

                logger.info(
                    f"✅ Successfully transitioned flow {flow_id} from data_cleansing to inventory"
                )

                return "inventory"

            return None

        except Exception as e:
            logger.error(f"Error in phase transition for flow {flow_id}: {e}")
            await self.db.rollback()
            return None
