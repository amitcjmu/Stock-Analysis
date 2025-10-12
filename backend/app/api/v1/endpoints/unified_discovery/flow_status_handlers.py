"""
Flow Status and Management Handlers for Unified Discovery

Handles flow status checking and active flow listing.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.client_account import User
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.discovery.flow_status_service import (
    get_active_flows as get_active_flows_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_import_raw_data(db: AsyncSession, data_import_id: str):
    """Helper to get raw data for a data import."""
    try:
        from app.models.data_import.core import DataImport, RawImportRecord

        # DataImport uses 'id' as primary key, not 'import_id'
        import_query = select(DataImport).where(DataImport.id == data_import_id)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()

        if data_import:
            # Get raw records for this import
            raw_records_query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import.id)
                .order_by(RawImportRecord.row_number)
            )
            raw_result = await db.execute(raw_records_query)
            raw_records = raw_result.scalars().all()

            # Extract raw_data from records
            return [record.raw_data for record in raw_records] if raw_records else []
    except Exception as e:
        logger.warning(f"Failed to get raw data for import {data_import_id}: {e}")

    return []


@router.get("/flows/{flow_id}/status")
async def get_flow_status(
    flow_id: str,
    include_details: bool = Query(
        True, description="Include detailed flow information"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive flow status and metadata.

    This endpoint provides detailed information about a discovery flow,
    including current status, phases, progress, and metadata.
    """
    try:
        logger.info(safe_log_format("Getting flow status: {flow_id}", flow_id=flow_id))

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        try:
            flow = await flow_repo.get_by_flow_id(flow_id)
            if not flow:
                raise HTTPException(
                    status_code=404,
                    detail=f"Flow {flow_id} not found",
                )

            # Guard against deleted flows
            if flow.status == "archived":
                raise HTTPException(
                    status_code=400, detail="Cannot process deleted flow"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to retrieve flow {flow_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to access flow: {str(e)}",
            )

        # Build comprehensive flow status response
        flow_status = {
            "flow_id": flow.flow_id,
            "status": flow.status,
            "current_phase": flow.current_phase,
            "next_phase": getattr(
                flow, "next_phase", None
            ),  # Safe access - may not exist
            "progress_percentage": flow.progress_percentage or 0,
            "phase_state": flow.phase_state
            or {},  # CC: Include phase_state for conflict resolution tracking
            "created_at": flow.created_at.isoformat() if flow.created_at else None,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
        }

        if include_details:
            # Add detailed information
            flow_status.update(
                {
                    "data_import_id": flow.data_import_id,
                    "master_flow_id": flow.master_flow_id,
                    "field_mappings": flow.field_mappings,
                    "phases": getattr(flow, "phases", {}) or {},  # Safe access
                    "error_details": getattr(
                        flow, "error_details", None
                    ),  # Safe access
                    "metadata": {
                        "total_assets": getattr(flow, "total_assets", 0),
                        "processed_assets": getattr(flow, "processed_assets", 0),
                        "agent_status": getattr(flow, "agent_status", {}),
                    },
                    # Add import_metadata for frontend compatibility
                    "import_metadata": {
                        "import_id": flow.data_import_id,
                        "data_import_id": flow.data_import_id,
                    },
                }
            )

            # Add raw_data if available from data import
            if flow.data_import_id:
                raw_data = await _get_import_raw_data(db, flow.data_import_id)
                flow_status["raw_data"] = raw_data
                if raw_data:
                    flow_status["flow_name"] = f"Discovery Import {flow.data_import_id}"
                    logger.info(f"✅ Added {len(raw_data)} raw records to flow status")

            # Get extended state information if available
            try:
                extended_state_query = select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow_id
                )
                extended_result = await db.execute(extended_state_query)
                extended_state = extended_result.scalar_one_or_none()

                if extended_state:
                    flow_status["extended_state"] = {
                        "flow_configuration": extended_state.flow_configuration,
                        "execution_metadata": getattr(
                            extended_state, "execution_metadata", {}
                        ),
                        "current_state_data": getattr(
                            extended_state, "current_state_data", {}
                        ),
                        "agent_interactions": getattr(
                            extended_state, "agent_interactions", []
                        ),
                        "checkpoint_data": getattr(
                            extended_state, "checkpoint_data", {}
                        ),
                    }
            except Exception as e:
                logger.warning(f"Failed to get extended state for flow {flow_id}: {e}")
                flow_status["extended_state"] = None

        logger.info(f"✅ Flow status retrieved for flow {flow_id}")
        return flow_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get flow status: {e}", e=e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get flow status: {str(e)}"
        )


@router.get("/flows/active")
async def get_active_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get all active discovery flows for the current tenant."""
    try:
        flows = await get_active_flows_service(db, context)
        return {
            "success": True,
            "flows": flows,
            "count": len(flows),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(safe_log_format("Active flows retrieval failed: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
