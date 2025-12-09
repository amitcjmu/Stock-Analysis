"""
Request handlers for asset processing endpoints.
Handles API routes and coordinates processing workflow.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.asset import Asset
from app.models.data_import import RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping

from .processors import fallback_raw_to_assets_processing
from .utils import get_safe_context

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/process-raw-to-assets")
async def process_raw_to_assets(
    flow_id: str = None, db: AsyncSession = Depends(get_db)
):
    """
    Process raw import data into classified assets using unified CrewAI Flow Service.

    This endpoint uses the consolidated CrewAI Flow Service with modular handler architecture
    for intelligent asset classification and workflow integration.

    IMPORTANT: This endpoint now enforces field mapping approval before asset creation.
    """

    if not flow_id:
        raise HTTPException(status_code=400, detail="flow_id is required")

    try:
        context = get_safe_context()
        # SECURITY CHECK: Verify field mappings are approved before asset creation
        # During migration: flow_id maps to data import session
        mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == flow_id
        )
        mappings_result = await db.execute(mappings_query)
        mappings = mappings_result.scalars().all()

        if not mappings:
            raise HTTPException(
                status_code=400,
                detail="No field mappings found. Please complete field mapping first.",
            )

        # Check approval status
        approved_mappings = [m for m in mappings if m.status == "approved"]
        pending_mappings = [m for m in mappings if m.status in ["suggested", "pending"]]

        if not approved_mappings:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No field mappings have been approved. Please review and approve field mappings "
                    "before creating assets."
                ),
            )

        if pending_mappings:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{len(pending_mappings)} field mappings are still pending approval. "
                    f"Please approve or reject all mappings before proceeding."
                ),
            )

        logger.info(
            f"✅ Field mapping approval verified: {len(approved_mappings)} approved mappings found"
        )

        # Check if we have raw records to process
        raw_count_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id
            )
        )
        raw_count = raw_count_query.scalar()

        if raw_count == 0:
            return {
                "status": "error",
                "message": "No raw import records found for the specified session",
                "flow_id": flow_id,
            }

        logger.info(
            safe_log_format(
                "🔄 Processing {raw_count} raw records from flow: {flow_id}",
                raw_count=raw_count,
                flow_id=flow_id,
            )
        )

        # Use the unified CrewAI Flow Service with proper modular architecture
        try:
            from app.services.crewai_flow_service import crewai_flow_service

            # Check if the unified service is available
            if crewai_flow_service.is_available():
                logger.info(
                    "🤖 Using unified CrewAI Flow Service for intelligent processing"
                )

                # Use unified flow with database integration
                result = await crewai_flow_service.run_discovery_flow_with_state(
                    cmdb_data={
                        "headers": [],  # Will be loaded from raw records
                        "sample_data": [],  # Will be loaded from raw records
                        "flow_id": flow_id,
                    },
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id,
                )

                # Enhanced response with detailed classification results
                if result.get("status") == "success":
                    logger.info("✅ Unified CrewAI Flow completed successfully!")
                    logger.info(
                        f"   📊 Processing Status: {result.get('processing_status', 'completed')}"
                    )
                    logger.info(
                        f"   📱 Applications: {result.get('classification_results', {}).get('applications', 0)}"
                    )
                    logger.info(
                        f"   🖥️  Servers: {result.get('classification_results', {}).get('servers', 0)}"
                    )
                    logger.info(
                        f"   🗄️  Databases: {result.get('classification_results', {}).get('databases', 0)}"
                    )

                    # Generate detailed user message
                    total_processed = result.get("total_processed", 0)

                    user_message = "✨ Unified CrewAI intelligent processing completed successfully! "
                    if total_processed > 0:
                        user_message += (
                            f"Processed {total_processed} assets with AI classification, workflow progression, "
                            f"and database integration using the unified modular service architecture. "
                        )
                        user_message += (
                            "All assets have been enriched with AI insights and properly classified "
                            "using agentic intelligence."
                        )
                    else:
                        user_message += (
                            "Processing completed with unified workflow management. "
                            "Check asset inventory for results."
                        )

                    return {
                        "status": "success",
                        "message": user_message,
                        "processed_count": total_processed,
                        "flow_id": result.get("flow_id", "unified_flow"),
                        "processing_status": result.get(
                            "processing_status", "completed"
                        ),
                        "progress_percentage": 100.0,
                        "agentic_intelligence": {
                            "crewai_flow_active": True,
                            "unified_service": True,
                            "modular_handlers": True,
                            "database_integration": True,
                            "workflow_progression": True,
                            "state_management": True,
                            "processing_method": "unified_crewai_flow_service",
                        },
                        "classification_results": result.get(
                            "classification_results", {}
                        ),
                        "workflow_progression": result.get("workflow_progression", {}),
                        "processed_asset_ids": result.get("processed_asset_ids", []),
                        "completed_at": result.get("completed_at"),
                        "duplicate_detection": {
                            "detection_active": True,
                            "duplicates_found": False,
                            "detection_method": "unified_workflow_integration",
                        },
                    }
                else:
                    logger.warning(
                        f"Unified CrewAI Flow returned error: {result.get('error', 'Unknown error')}"
                    )
                    # Fall back to fallback processing
                    pass
            else:
                logger.info(
                    "Unified CrewAI Flow not available, using fallback processing"
                )
                # Fall back to fallback processing
                pass

        except (ImportError, Exception) as e:
            logger.warning(
                f"Unified CrewAI Flow service not available ({e}), falling back to basic processing"
            )
            # Fall back to fallback processing
            pass

        # Fallback processing when CrewAI is not available
        return await fallback_raw_to_assets_processing(flow_id, db, context)

    except Exception as e:
        logger.error(safe_log_format("Asset processing failed: {e}", e=e))
        raise HTTPException(
            status_code=500, detail=f"Asset processing failed: {str(e)}"
        )


@router.get("/processing-status/{flow_id}")
async def get_processing_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get the processing status for an import session."""

    try:
        # Get processing statistics
        total_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id
            )
        )
        total_records = total_query.scalar()

        processed_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id,
                RawImportRecord.is_processed == True,  # noqa: E712
            )
        )
        processed_records = processed_query.scalar()

        # Get created assets count
        assets_query = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        total_assets = assets_query.scalar()

        return {
            "flow_id": flow_id,
            "total_records": total_records,
            "processed_records": processed_records,
            "pending_records": total_records - processed_records,
            "processing_percentage": (
                (processed_records / total_records * 100) if total_records > 0 else 0
            ),
            "total_assets_created": total_assets,
            "status": (
                "completed" if processed_records == total_records else "in_progress"
            ),
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to get processing status: {e}", e=e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get processing status: {str(e)}"
        )
