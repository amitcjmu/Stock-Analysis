"""
Discovery Flow Phase Transition Service

Handles automatic phase transitions after completion of phase requirements.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.discovery_flow import DiscoveryFlow
from app.models.data_import.mapping import ImportFieldMapping
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands,
)
from app.services.discovery.phase_persistence_helpers import advance_phase
from app.utils.flow_constants.thresholds import FIELD_MAPPING_APPROVAL_THRESHOLD

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
            logger.debug(
                "Evaluating attribute_mapping transition readiness",
                extra={"flow_id": flow_id},
            )

            # First get the flow to extract tenant context
            try:
                flow_result = await self.db.execute(
                    select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                )
                flow = flow_result.scalar_one_or_none()
            except SQLAlchemyError:
                logger.exception(
                    "Database error retrieving discovery flow during field mapping transition",
                    extra={"flow_id": flow_id},
                )
                await self.db.rollback()
                return None

            if not flow:
                logger.error(
                    "Flow not found when evaluating attribute_mapping transition",
                    extra={"flow_id": flow_id},
                )
                return None

            try:
                master_status = None
                if flow.master_flow_id:
                    master_status_result = await self.db.execute(
                        select(CrewAIFlowStateExtensions.flow_status).where(
                            CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
                        )
                    )
                    master_status = master_status_result.scalar_one_or_none()

                if master_status and master_status.lower() != "running":
                    logger.warning(
                        "Master flow not in running state, skipping transition",
                        extra={"flow_id": flow_id, "master_status": master_status},
                    )
                    return None
            except SQLAlchemyError:
                logger.exception(
                    "Database error retrieving master flow status during field mapping transition",
                    extra={"flow_id": flow_id},
                )
                await self.db.rollback()
                return None

            # Check if all required field mappings are approved
            try:
                counts_query = (
                    select(
                        func.count().label("total"),
                        func.sum(cast(ImportFieldMapping.is_approved, Integer)).label(
                            "approved"
                        ),
                    )
                    .select_from(ImportFieldMapping)
                    .where(ImportFieldMapping.master_flow_id == flow_id)
                )
                counts_result = await self.db.execute(counts_query)
                counts_row = counts_result.one()
                total_count = counts_row.total
                approved_count = counts_row.approved or 0
            except SQLAlchemyError:
                logger.exception(
                    "Database error counting field mappings for transition",
                    extra={"flow_id": flow_id},
                )
                await self.db.rollback()
                return None

            if approved_count == 0:
                logger.info(
                    "No approved mappings, skipping attribute_mapping transition",
                    extra={"flow_id": flow_id},
                )
                return None

            # Calculate approval percentage
            approval_percentage = (
                (approved_count / total_count * 100) if total_count > 0 else 0
            )

            # Check if approval percentage meets the configurable threshold
            if approval_percentage < FIELD_MAPPING_APPROVAL_THRESHOLD:
                logger.info(
                    "Approval threshold not met for attribute_mapping transition",
                    extra={
                        "flow_id": flow_id,
                        "approved_mappings": approved_count,
                        "total_mappings": total_count,
                        "approval_percentage": round(approval_percentage, 2),
                        "required_percentage": FIELD_MAPPING_APPROVAL_THRESHOLD,
                    },
                )
                return None

            logger.info(
                "Approval threshold satisfied for attribute_mapping transition",
                extra={
                    "flow_id": flow_id,
                    "approved_mappings": approved_count,
                    "total_mappings": total_count,
                    "approval_percentage": round(approval_percentage, 2),
                    "required_percentage": FIELD_MAPPING_APPROVAL_THRESHOLD,
                },
            )

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

            # Transition to data cleansing phase using atomic helper
            transition_result = await advance_phase(
                db=self.db,
                flow=flow,
                target_phase="data_cleansing",
                extra_updates={"field_mapping_completed": True},
            )

            if not transition_result.success:
                logger.warning(
                    "Field mapping transition failed during phase advancement",
                    extra={
                        "flow_id": flow_id,
                        "warnings": transition_result.warnings,
                    },
                )
                return None

            logger.info(
                "✅ Attribute_mapping transitioned to data_cleansing",
                extra={
                    "flow_id": flow_id,
                    "approved_mappings": approved_count,
                    "total_mappings": total_count,
                    "approval_percentage": round(approval_percentage, 2),
                },
            )

            return "data_cleansing"

        except Exception:
            logger.exception(
                "Unexpected error during attribute_mapping transition",
                extra={"flow_id": flow_id},
            )
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
            logger.debug(
                "Evaluating data_cleansing transition readiness",
                extra={"flow_id": flow_id},
            )

            # Get the discovery flow
            try:
                result = await self.db.execute(
                    select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                )
                flow = result.scalar_one_or_none()
            except SQLAlchemyError:
                logger.exception(
                    "Database error retrieving discovery flow during data cleansing transition",
                    extra={"flow_id": flow_id},
                )
                await self.db.rollback()
                return None

            if not flow:
                logger.error(
                    "Discovery flow not found during data cleansing transition",
                    extra={"flow_id": flow_id},
                )
                return None

            try:
                master_status = None
                if flow.master_flow_id:
                    master_status_result = await self.db.execute(
                        select(CrewAIFlowStateExtensions.flow_status).where(
                            CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
                        )
                    )
                    master_status = master_status_result.scalar_one_or_none()

                if master_status and master_status.lower() != "running":
                    logger.warning(
                        "Master flow not in running state, skipping data cleansing transition",
                        extra={"flow_id": flow_id, "master_status": master_status},
                    )
                    return None
            except SQLAlchemyError:
                logger.exception(
                    "Database error retrieving master flow status during data cleansing transition",
                    extra={"flow_id": flow_id},
                )
                await self.db.rollback()
                return None

            # Check if data cleansing has been marked complete
            if flow.data_cleansing_completed:
                # Transition to asset inventory phase using atomic helper
                transition_result = await advance_phase(
                    db=self.db, flow=flow, target_phase="asset_inventory"
                )

                if not transition_result.success:
                    logger.warning(
                        "Data cleansing transition failed during phase advancement",
                        extra={
                            "flow_id": flow_id,
                            "warnings": transition_result.warnings,
                        },
                    )
                    return None

                logger.info(
                    "✅ Data_cleansing transitioned to asset_inventory",
                    extra={"flow_id": flow_id},
                )

                return "asset_inventory"

            logger.debug(
                "Data cleansing not yet complete, skipping transition",
                extra={"flow_id": flow_id},
            )
            return None

        except Exception:
            logger.exception(
                "Unexpected error during data cleansing transition",
                extra={"flow_id": flow_id},
            )
            await self.db.rollback()
            return None
