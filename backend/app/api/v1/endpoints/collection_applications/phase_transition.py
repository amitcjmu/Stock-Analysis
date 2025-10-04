"""Phase transition logic for collection flows."""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.collection_flow.schemas import CollectionPhase
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.master_flow_sync_service import MasterFlowSyncService

logger = logging.getLogger(__name__)


async def transition_to_gap_analysis(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    normalized_ids: List[str],
    flow_id: str,
    context: RequestContext,
    processed_count: int,
    normalized_records_count: int,
) -> Dict[str, Any]:
    """Transition collection flow to gap analysis phase.

    Args:
        db: Database session
        collection_flow: Collection flow object
        normalized_ids: List of selected application IDs
        flow_id: Collection flow ID string
        context: Request context with tenant scoping
        processed_count: Number of applications processed
        normalized_records_count: Number of normalized records created

    Returns:
        Response dict with transition results
    """
    if not collection_flow.master_flow_id:
        logger.warning(
            f"Collection flow {flow_id} has no master_flow_id - skipping execution"
        )
        return {
            "success": True,
            "message": (
                f"Successfully updated collection flow with {processed_count} applications, "
                f"created {normalized_records_count} normalized records"
            ),
            "flow_id": flow_id,
            "selected_application_count": processed_count,
            "normalized_records_created": normalized_records_count,
            "mfo_execution_triggered": False,
            "warning": "no_master_flow_id",
        }

    try:
        orchestrator = MasterFlowOrchestrator(db, context)

        # Only transition if currently in ASSET_SELECTION phase
        if collection_flow.current_phase == CollectionPhase.ASSET_SELECTION.value:
            execution_result = await _execute_gap_analysis_phase(
                orchestrator=orchestrator,
                collection_flow=collection_flow,
                normalized_ids=normalized_ids,
                flow_id=flow_id,
                context=context,
            )

            # Update collection flow phase
            collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
            collection_flow.status = CollectionPhase.GAP_ANALYSIS.value
            await db.commit()

            logger.info(
                f"Transitioned collection flow {flow_id} from ASSET_SELECTION to GAP_ANALYSIS"
            )
        else:
            # If not in asset_selection, just trigger execution of current phase
            execution_result = await orchestrator.execute_phase(
                flow_id=str(collection_flow.master_flow_id),
                phase_name=collection_flow.current_phase,
            )

        # Sync master flow changes back to collection flow
        await _sync_master_flow_changes(
            db=db,
            collection_flow=collection_flow,
            flow_id=flow_id,
            context=context,
        )

        logger.info(
            f"Triggered phase execution for master flow {collection_flow.master_flow_id}"
        )

        return {
            "success": True,
            "message": (
                f"Successfully updated collection flow with {processed_count} "
                f"applications, created {normalized_records_count} normalized records, "
                "and transitioned to gap analysis phase"
            ),
            "flow_id": flow_id,
            "selected_application_count": processed_count,
            "normalized_records_created": normalized_records_count,
            "mfo_execution_triggered": True,
            "execution_result": execution_result,
        }

    except Exception as mfo_error:
        logger.error(f"MFO execution failed: {str(mfo_error)}")
        # Still return success for the application selection part
        return {
            "success": True,
            "message": (
                f"Successfully updated collection flow with {processed_count} "
                f"applications, created {normalized_records_count} normalized records "
                "(phase transition failed)"
            ),
            "flow_id": flow_id,
            "selected_application_count": processed_count,
            "normalized_records_created": normalized_records_count,
            "mfo_execution_triggered": False,
            "mfo_error": str(mfo_error),
        }


async def _execute_gap_analysis_phase(
    orchestrator: MasterFlowOrchestrator,
    collection_flow: CollectionFlow,
    normalized_ids: List[str],
    flow_id: str,
    context: RequestContext,
) -> Dict[str, Any]:
    """Execute gap analysis phase with proper input.

    CRITICAL: Pass selected application IDs to gap analysis phase.
    Gap analysis needs asset IDs to create collection_data_gap records.
    """
    phase_input = {
        "selected_application_ids": normalized_ids,
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "flow_id": flow_id,
    }

    execution_result = await orchestrator.execute_phase(
        flow_id=str(collection_flow.master_flow_id),
        phase_name="gap_analysis",
        phase_input=phase_input,
    )

    return execution_result


async def _sync_master_flow_changes(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    flow_id: str,
    context: RequestContext,
) -> None:
    """Sync master flow changes back to collection flow."""
    try:
        sync_service = MasterFlowSyncService(db, context)
        await sync_service.sync_master_to_collection_flow(
            master_flow_id=str(collection_flow.master_flow_id),
            collection_flow_id=flow_id,
        )
    except Exception as sync_error:
        logger.warning(
            f"Failed to sync master flow after phase execution: {sync_error}"
        )
