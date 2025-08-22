"""
Collection Flow Execution Operations
Flow lifecycle operations including ensuring flow existence, execution,
and continuation/resumption of collection flows.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)
from app.schemas.collection_flow import CollectionFlowCreate, CollectionFlowResponse

# Import modular functions
from app.api.v1.endpoints import collection_utils
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers
from app.api.v1.endpoints.collection_crud_commands import create_collection_flow

logger = logging.getLogger(__name__)


async def ensure_collection_flow(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery to Collection without users
    needing to manually start a flow. It reuses any non-completed flow; if none
    exist, it creates a new one and returns it immediately.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse for existing or newly created flow
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "ensure collection flows")

    # Validate tenant context early
    collection_validators.validate_tenant_context(context)

    try:
        # Try to find an active collection flow for this engagement
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        existing = result.scalar_one_or_none()

        if existing:
            return collection_serializers.build_collection_flow_response(existing)

        # Otherwise, create a new one (delegates to existing create logic)
        flow_data = CollectionFlowCreate(automation_tier=AutomationTier.TIER_2.value)
        return await create_collection_flow(flow_data, db, current_user, context)

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")


async def execute_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Execute a collection flow phase through Master Flow Orchestrator.

    This function triggers actual CrewAI execution of the collection flow,
    enabling phase progression and questionnaire generation.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Execution result dictionary
    """
    try:
        # Get the collection flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be executed
        await collection_validators.validate_flow_can_be_executed(collection_flow)

        # Execute the current phase using the master flow ID if available
        current_phase = collection_flow.current_phase or "initialization"

        # Use master_flow_id if it exists, otherwise try with collection flow_id
        execute_flow_id = (
            str(collection_flow.master_flow_id)
            if collection_flow.master_flow_id
            else flow_id
        )

        logger.info(
            safe_log_format(
                "Executing phase {phase} for collection flow {flow_id} using MFO flow {mfo_id}",
                phase=current_phase,
                flow_id=flow_id,
                mfo_id=execute_flow_id,
            )
        )

        # Execute through MasterFlowOrchestrator directly
        orchestrator = MasterFlowOrchestrator(db, context)
        execution_result = await orchestrator.execute_phase(
            flow_id=execute_flow_id, phase_name=current_phase, phase_input={}
        )

        logger.info(
            f"Executed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_execution_response(
            flow_id, execution_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error executing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def continue_flow(
    flow_id: str,
    resume_context: Optional[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Continue/resume a paused or incomplete collection flow.

    Args:
        flow_id: Collection flow ID
        resume_context: Optional context for resuming
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Continue flow response dictionary
    """
    try:
        # Verify flow exists and belongs to engagement
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be resumed
        await collection_validators.validate_flow_can_be_resumed(collection_flow)

        # Resume flow through MFO
        result = await collection_utils.resume_mfo_flow(
            db, context, flow_id, resume_context or {}
        )

        logger.info(
            f"Resumed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_continue_flow_response(flow_id, result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error continuing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
