"""
Field mapping re-analysis service
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import HTTPException
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, ImportFieldMapping

logger = logging.getLogger(__name__)


async def trigger_discovery_flow_analysis(
    context: RequestContext, data_import: DataImport, db: AsyncSession
):
    """
    Trigger the discovery flow to perform agentic analysis of critical attributes.

    This initiates the field mapping crew and other agents to analyze the data
    and determine critical attributes dynamically.
    """
    try:
        # Use the proper CrewAI Flow service for discovery analysis
        from app.services.crewai_flow_service import CrewAIFlowService

        CrewAIFlowService()

        # Prepare data for discovery flow
        flow_id = data_import.id  # Use data import ID directly as flow ID

        # Get sample data from the import
        mappings_query = (
            select(ImportFieldMapping)
            .where(ImportFieldMapping.data_import_id == data_import.id)
            .limit(10)
        )  # Sample for analysis

        mappings_result = await db.execute(mappings_query)
        sample_mappings = mappings_result.scalars().all()

        if sample_mappings:
            # Prepare data structure for discovery flow
            sample_data = []
            for mapping in sample_mappings:
                sample_data.append(
                    {
                        mapping.source_field: f"sample_value_{mapping.source_field}",
                        "confidence": mapping.confidence_score or 0.7,
                    }
                )

            # Trigger proper CrewAI Flow for agentic analysis
            type(
                "FlowContext",
                (),
                {
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id,
                    "user_id": context.user_id or "system",
                    "flow_id": flow_id,
                    "data_import_id": str(data_import.id),
                    "source": "critical_attributes_analysis",
                },
            )()

            # Trigger field mapping re-analysis
            await trigger_field_mapping_reanalysis(context, data_import, db)

            logger.info(f"🚀 Discovery flow re-analysis triggered for: {flow_id}")
    except ImportError:
        logger.warning("Discovery flow service not available")
    except Exception as e:
        logger.error(f"Failed to trigger discovery flow: {e}")


async def trigger_field_mapping_reanalysis(
    context: RequestContext, data_import: DataImport, db: AsyncSession
):
    """
    Trigger re-analysis of field mappings using the discovery flow's field mapping phase.
    This will regenerate field mappings using CrewAI agents with the latest logic.
    """
    try:
        logger.info(
            f"🔄 Starting field mapping re-analysis for data_import: {data_import.id}"
        )

        # Get the discovery flow associated with this data import
        discovery_flow = await _find_discovery_flow_for_reanalysis(data_import, db)
        if not discovery_flow:
            logger.error(
                f"❌ No discovery flow found for data_import_id: {data_import.id} (tried all lookup methods)"
            )
            return

        # Get raw data and execute re-analysis
        raw_data = await _get_raw_data_for_reanalysis(data_import, db)
        if not raw_data:
            return

        # Execute the re-analysis with CrewAI agents
        await _execute_field_mapping_reanalysis(
            context, data_import, discovery_flow, raw_data, db
        )

    except Exception as e:
        logger.error(
            f"❌ Failed to trigger field mapping re-analysis: {e}", exc_info=True
        )


async def _find_discovery_flow_for_reanalysis(
    data_import: DataImport, db: AsyncSession
):
    """Find discovery flow for re-analysis using multiple lookup methods"""
    from app.models.discovery_flow import DiscoveryFlow

    # First try direct data_import_id lookup
    flow_query = select(DiscoveryFlow).where(
        DiscoveryFlow.data_import_id == data_import.id
    )
    flow_result = await db.execute(flow_query)
    discovery_flow = flow_result.scalar_one_or_none()

    if discovery_flow:
        return discovery_flow

    # If not found by data_import_id, try lookup through master flow relationship
    if data_import.master_flow_id:
        logger.info(
            f"🔍 Discovery flow not found by data_import_id for re-analysis, trying master flow lookup for: "
            f"{data_import.master_flow_id}"
        )

        # Look for discovery flow with matching master_flow_id
        master_flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == data_import.master_flow_id
        )
        master_flow_result = await db.execute(master_flow_query)
        discovery_flow = master_flow_result.scalar_one_or_none()

        if discovery_flow:
            logger.info(
                f"✅ Found discovery flow for re-analysis through master flow relationship: {discovery_flow.flow_id}"
            )
            return discovery_flow

        # Configuration-based lookup
        discovery_flow = await _find_discovery_flow_by_config_for_reanalysis(
            data_import, db
        )
        if discovery_flow:
            return discovery_flow

    return None


async def _find_discovery_flow_by_config_for_reanalysis(
    data_import: DataImport, db: AsyncSession
):
    """Find discovery flow through configuration for re-analysis"""
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

    logger.info(
        "🔍 No discovery flow found by master_flow_id for re-analysis, trying configuration-based lookup"
    )

    # Use parameterized query to prevent SQL injection
    config_query = (
        select(CrewAIFlowStateExtensions)
        .where(sql_text("flow_configuration::text LIKE :search_pattern"))
        .params(search_pattern=f"%{data_import.id}%")
    )
    config_result = await db.execute(config_query)
    master_flows_with_import = config_result.scalars().all()

    for master_flow in master_flows_with_import:
        # Check if there's a discovery flow linked to this master flow
        linked_flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == master_flow.flow_id
        )
        linked_flow_result = await db.execute(linked_flow_query)
        discovery_flow = linked_flow_result.scalar_one_or_none()

        if discovery_flow:
            logger.info(
                f"✅ Found discovery flow for re-analysis through configuration-based lookup: "
                f"{discovery_flow.flow_id}"
            )
            return discovery_flow

    return None


async def _get_raw_data_for_reanalysis(data_import: DataImport, db: AsyncSession):
    """Get raw data for re-analysis"""
    from app.models.data_import import RawImportRecord

    raw_records_query = (
        select(RawImportRecord)
        .where(RawImportRecord.data_import_id == data_import.id)
        .limit(100)
    )  # Get sample for analysis

    raw_records_result = await db.execute(raw_records_query)
    raw_records = raw_records_result.scalars().all()

    if not raw_records:
        logger.error(f"❌ No raw records found for data_import_id: {data_import.id}")
        return None

    # Extract raw data from records
    raw_data = [record.raw_data for record in raw_records if record.raw_data]

    if not raw_data:
        logger.error("❌ No raw data available in records")
        return None

    logger.info(f"📊 Found {len(raw_data)} raw records for re-analysis")
    return raw_data


async def _execute_field_mapping_reanalysis(
    context: RequestContext,
    data_import: DataImport,
    discovery_flow,
    raw_data,
    db: AsyncSession,
):
    """Execute the actual field mapping re-analysis with CrewAI"""
    from app.services.crewai_flow_service import CrewAIFlowService
    from app.services.crewai_flows.handlers.phase_executors.field_mapping_executor import (
        FieldMappingExecutor,
    )
    from app.services.crewai_flows.handlers.unified_flow_crew_manager import (
        UnifiedFlowCrewManager,
    )

    # Create a minimal state object for the executor
    class FlowState:
        def __init__(self):
            self.raw_data = raw_data
            self.data_import_id = str(data_import.id)
            self.flow_id = discovery_flow.flow_id
            self.client_account_id = context.client_account_id
            self.engagement_id = context.engagement_id
            self.current_phase = "attribute_mapping"

    flow_state = FlowState()

    # Create crew manager with proper CrewAI service
    crewai_service = CrewAIFlowService()
    crew_manager = UnifiedFlowCrewManager(crewai_service, flow_state)

    # Create and execute field mapping executor with error handling
    try:
        executor = FieldMappingExecutor(flow_state, crew_manager)
    except Exception as e:
        logger.error(f"❌ Failed to create FieldMappingExecutor: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize field mapping executor: {str(e)}",
        )

    # Clean up JSON artifacts before re-analysis
    await _cleanup_json_artifacts(context, data_import, db)

    # Execute field mapping analysis
    logger.info("🤖 Executing field mapping re-analysis with CrewAI agents...")
    try:
        result = await executor.execute_suggestions_only({})
    except Exception as e:
        logger.error(f"❌ Field mapping re-analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Field mapping re-analysis failed: {str(e)}"
        )

    if result and result.get("mappings"):
        logger.info(
            f"✅ Field mapping re-analysis completed. Generated {len(result['mappings'])} mappings"
        )

        # Update existing field mappings in the database
        await update_field_mappings_from_reanalysis(
            data_import.id,
            result["mappings"],
            result.get("confidence_scores", {}),
            db,
        )
    else:
        logger.warning("⚠️ Field mapping re-analysis returned no mappings")


async def _cleanup_json_artifacts(
    context: RequestContext, data_import: DataImport, db: AsyncSession
):
    """Clean up JSON artifacts before field mapping re-analysis"""
    logger.info("🧹 Cleaning up JSON artifacts before field mapping re-analysis...")
    try:
        from app.services.data_import.storage_manager.mapping_operations import (
            FieldMappingOperationsMixin,
        )

        # Create cleanup service
        class CleanupService(FieldMappingOperationsMixin):
            def __init__(self, db_session, client_account_id):
                self.db = db_session
                self.client_account_id = client_account_id

        cleanup_service = CleanupService(db, context.client_account_id)
        removed_count = await cleanup_service.cleanup_json_artifact_mappings(
            data_import
        )

        if removed_count > 0:
            logger.info(
                f"🧹 Removed {removed_count} JSON artifact field mappings before re-analysis"
            )

    except Exception as cleanup_error:
        logger.warning(
            f"⚠️ JSON artifact cleanup failed but continuing: {cleanup_error}"
        )


async def update_field_mappings_from_reanalysis(
    data_import_id: str,
    new_mappings: Dict[str, str],
    confidence_scores: Dict[str, float],
    db: AsyncSession,
):
    """
    Update existing field mappings with new mappings from re-analysis.
    """
    try:
        # Get existing field mappings
        existing_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == data_import_id
        )
        existing_result = await db.execute(existing_query)
        existing_mappings = existing_result.scalars().all()

        updated_count = 0

        for mapping in existing_mappings:
            source_field = mapping.source_field

            # Check if we have a new mapping for this field
            if source_field in new_mappings:
                new_target = new_mappings[source_field]
                new_confidence = confidence_scores.get(source_field, 0.7)

                # Update the mapping
                mapping.target_field = new_target
                mapping.confidence_score = new_confidence
                mapping.match_type = "agent_reanalysis"
                mapping.transformation_rules = {
                    "method": "agent_reanalysis",
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": new_confidence,
                }
                mapping.updated_at = datetime.utcnow()

                updated_count += 1

        # Commit the updates
        await db.commit()

        logger.info(f"✅ Updated {updated_count} field mappings from re-analysis")

    except Exception as e:
        logger.error(f"❌ Failed to update field mappings from re-analysis: {e}")
        await db.rollback()
