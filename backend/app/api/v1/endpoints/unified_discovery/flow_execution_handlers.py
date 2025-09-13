"""
Flow Execution Handlers for Unified Discovery

Handles flow execution and phase management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery.flow_execution_service import execute_flow_phase

logger = logging.getLogger(__name__)

router = APIRouter()


def _determine_next_phase(discovery_flow: DiscoveryFlow) -> str:
    """
    Determine the next phase to execute based on the current flow state.
    Check completion flags first to determine next phase.
    """
    # Check completion flags first to determine next phase
    if not discovery_flow.data_import_completed:
        return "field_mapping"
    if (
        discovery_flow.data_import_completed
        and not discovery_flow.field_mapping_completed
    ):
        return "field_mapping"
    if (
        discovery_flow.field_mapping_completed
        and not discovery_flow.data_cleansing_completed
    ):
        return "data_cleansing"
    if (
        discovery_flow.data_cleansing_completed
        and not discovery_flow.asset_inventory_completed
    ):
        return "asset_inventory"
    if discovery_flow.asset_inventory_completed:
        # Continue with remaining phases
        if not discovery_flow.dependency_analysis_completed:
            return "dependency_mapping"
        if discovery_flow.dependency_analysis_completed:
            return "recommendations"
    return "completed"


@router.post("/flows/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute the next phase of a discovery flow."""
    try:
        # Query the flow with proper tenant scoping
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()
        if not discovery_flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")

        # Guard against deleted flows
        if discovery_flow.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot process deleted flow")

        # Determine the next phase to execute
        next_phase = _determine_next_phase(discovery_flow)

        if not next_phase:
            return {
                "success": True,
                "message": "Flow execution completed - no more phases to execute",
                "status": "completed",
            }

        # Execute the phase with correct signature
        result = await execute_flow_phase(flow_id, discovery_flow, context, db)

        logger.info(
            safe_log_format(
                "Flow phase executed: flow_id={flow_id}, phase={phase}, success={success}",
                flow_id=mask_id(str(flow_id)),
                phase=next_phase,
                success=result.get("success", False),
            )
        )

        # Check for specific error codes that should trigger HTTP exceptions
        if result.get("error_code") == "CLEANSING_REQUIRED":
            # Return 422 for missing cleansed data
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "CLEANSING_REQUIRED",
                    "message": result.get(
                        "message",
                        "No cleansed data available. Run data cleansing first.",
                    ),
                    "counts": result.get("counts", {}),
                    "requires_cleansing": True,
                    "flow_id": flow_id,
                    "phase": next_phase,
                },
            )

        # Check if result indicates an HTTP status code should be returned
        if not result.get("success") and result.get("http_status"):
            http_status = result.get("http_status")
            if http_status == 422:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": result.get("error_code", "VALIDATION_ERROR"),
                        "message": result.get("message", "Request validation failed"),
                        "flow_id": flow_id,
                        "phase": next_phase,
                        **{
                            k: v
                            for k, v in result.items()
                            if k
                            not in [
                                "success",
                                "http_status",
                                "flow_id",
                                "message",
                                "error_code",
                            ]
                        },
                    },
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Flow execution failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
