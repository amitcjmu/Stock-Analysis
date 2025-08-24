"""
Field Mapping Auto-Trigger Service

This service monitors flows and automatically triggers field mapping generation
when a flow enters the field_mapping phase with no existing mappings.
"""

import asyncio
import logging
import uuid
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import DiscoveryFlow, ImportFieldMapping, DataImport
from app.services.field_mapping_executor.base import FieldMappingExecutor
from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class FieldMappingAutoTrigger:
    """Service to automatically trigger field mapping generation"""

    def __init__(self):
        self.check_interval = 30  # Check every 30 seconds
        self.running = False

    async def start(self):
        """Start the auto-trigger service"""
        if self.running:
            logger.warning("Field mapping auto-trigger already running")
            return

        self.running = True
        logger.info("✅ Field mapping auto-trigger service started")

        # Run in background
        asyncio.create_task(self._monitor_flows())

    async def stop(self):
        """Stop the auto-trigger service"""
        self.running = False
        logger.info("Field mapping auto-trigger service stopped")

    async def _monitor_flows(self):
        """Monitor flows and trigger field mapping when needed"""
        while self.running:
            try:
                await self._check_flows()
            except Exception as e:
                logger.error(f"Error in field mapping auto-trigger: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_flows(self):
        """Check flows that need field mapping generation"""
        async with AsyncSessionLocal() as db:
            # Find flows in field_mapping phase with waiting_for_approval status
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.current_phase == "field_mapping",
                    DiscoveryFlow.status.in_(
                        ["waiting_for_approval", "active", "processing"]
                    ),
                )
            )

            result = await db.execute(stmt)
            flows = result.scalars().all()

            for flow in flows:
                await self._process_flow(flow, db)

    async def _process_flow(self, flow: DiscoveryFlow, db: AsyncSession):  # noqa: C901
        """Process a single flow for field mapping generation"""
        try:
            # Check if field mappings already exist
            mappings_stmt = (
                select(ImportFieldMapping)
                .where(ImportFieldMapping.master_flow_id == flow.flow_id)
                .limit(1)
            )

            result = await db.execute(mappings_stmt)
            existing_mappings = result.scalar_one_or_none()

            if existing_mappings:
                # Mappings already exist, skip
                return

            logger.info(f"🚀 Auto-triggering field mapping for flow {flow.flow_id}")

            # Create state object from flow data
            raw_data = []
            metadata = {}

            if flow.crewai_state_data:
                # Handle different raw_data formats
                raw_data_field = flow.crewai_state_data.get("raw_data", {})
                if isinstance(raw_data_field, dict) and "data" in raw_data_field:
                    raw_data = raw_data_field["data"]
                elif isinstance(raw_data_field, list):
                    raw_data = raw_data_field

                metadata = flow.crewai_state_data.get("metadata", {})

            state = UnifiedDiscoveryFlowState(
                flow_id=str(flow.flow_id),
                client_account_id=str(flow.client_account_id),
                engagement_id=str(flow.engagement_id),
                current_phase="field_mapping",
                raw_data=raw_data,
                metadata=metadata,
                field_mappings={},  # Use dict instead of list
            )

            # Check if we have detected columns
            if not state.metadata.get("detected_columns"):
                # Try to extract from raw data
                if state.raw_data and len(state.raw_data) > 0:
                    first_record = state.raw_data[0]
                    if isinstance(first_record, dict):
                        state.metadata["detected_columns"] = list(first_record.keys())
                        logger.info(
                            f"Detected {len(state.metadata['detected_columns'])} columns from raw data"
                        )

            if not state.metadata.get("detected_columns"):
                logger.warning(
                    f"No detected columns for flow {flow.flow_id}, skipping auto-trigger"
                )
                return

            # Initialize field mapping executor
            executor = FieldMappingExecutor(
                client_account_id=str(flow.client_account_id),
                engagement_id=str(flow.engagement_id),
            )

            # Execute field mapping
            try:
                result = await executor.execute_phase(state, db)

                if result.get("success") or result.get("mappings"):
                    logger.info(
                        f"✅ Field mapping auto-generated for flow {flow.flow_id}"
                    )

                    # Extract mappings from result
                    mappings = {}
                    confidence_scores = {}

                    # Handle different mapping formats
                    if isinstance(result.get("mappings"), list):
                        # List of mapping objects
                        for mapping in result.get("mappings", []):
                            if isinstance(mapping, dict):
                                source = mapping.get("source_field")
                                target = mapping.get("target_field")
                                confidence = mapping.get("confidence", 0.7)
                                if source and target:
                                    mappings[source] = target
                                    confidence_scores[source] = confidence
                    elif isinstance(result.get("mappings"), dict):
                        # Direct dictionary mapping
                        mappings = result.get("mappings", {})
                        confidence_scores = result.get("confidence_scores", {})

                    if mappings:
                        await self._save_mappings_to_db(
                            flow, mappings, confidence_scores, db
                        )

                    # Update flow status if needed
                    if flow.status == "processing":
                        flow.status = "waiting_for_approval"
                        await db.commit()
                else:
                    logger.warning(
                        f"Field mapping generation failed for flow {flow.flow_id}: {result.get('error')}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to execute field mapping for flow {flow.flow_id}: {e}"
                )

        except Exception as e:
            logger.error(f"Error processing flow {flow.flow_id}: {e}")

    async def _save_mappings_to_db(
        self,
        flow: DiscoveryFlow,
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
        db: AsyncSession,
    ):
        """Save field mappings to the database"""
        try:
            # First, try to find the data_import for this flow
            data_import_stmt = (
                select(DataImport)
                .where(DataImport.master_flow_id == flow.flow_id)
                .limit(1)
            )
            result = await db.execute(data_import_stmt)
            data_import = result.scalar_one_or_none()

            # If no data_import with master_flow_id, try by client_account_id
            if not data_import:
                data_import_stmt = (
                    select(DataImport)
                    .where(DataImport.client_account_id == flow.client_account_id)
                    .order_by(DataImport.created_at.desc())
                    .limit(1)
                )
                result = await db.execute(data_import_stmt)
                data_import = result.scalar_one_or_none()

            if not data_import:
                logger.warning(
                    f"No data_import found for flow {flow.flow_id}, creating one"
                )
                # Create a data_import if needed
                data_import = DataImport(
                    id=uuid.uuid4(),
                    client_account_id=flow.client_account_id,
                    master_flow_id=flow.flow_id,
                    import_type="csv",
                    file_name="auto_generated",
                    status="completed",
                )
                db.add(data_import)
                await db.flush()

            # Now save the field mappings
            for source_field, target_field in mappings.items():
                confidence = confidence_scores.get(source_field, 0.7)

                # Check if mapping already exists
                existing_stmt = (
                    select(ImportFieldMapping)
                    .where(
                        ImportFieldMapping.master_flow_id == flow.flow_id,
                        ImportFieldMapping.source_field == source_field,
                    )
                    .limit(1)
                )
                result = await db.execute(existing_stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    mapping = ImportFieldMapping(
                        id=uuid.uuid4(),
                        data_import_id=data_import.id,
                        client_account_id=flow.client_account_id,
                        master_flow_id=flow.flow_id,
                        source_field=source_field,
                        target_field=target_field,
                        confidence_score=confidence,
                        status="auto_mapped",
                        match_type="direct",
                        suggested_by="ai_mapper",
                    )
                    db.add(mapping)

            await db.commit()
            logger.info(
                f"✅ Saved {len(mappings)} field mappings for flow {flow.flow_id}"
            )

        except Exception as e:
            logger.error(f"Failed to save mappings for flow {flow.flow_id}: {e}")
            await db.rollback()


# Global instance
field_mapping_auto_trigger = FieldMappingAutoTrigger()


async def start_field_mapping_monitor():
    """Start the field mapping auto-trigger monitor"""
    await field_mapping_auto_trigger.start()


async def stop_field_mapping_monitor():
    """Stop the field mapping auto-trigger monitor"""
    await field_mapping_auto_trigger.stop()
