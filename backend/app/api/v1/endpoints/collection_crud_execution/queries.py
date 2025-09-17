"""
Collection Flow Execution - Query Operations
Read operations for collection flows including ensuring flow existence.
"""

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.models import User
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)
from app.schemas.collection_flow import CollectionFlowCreate, CollectionFlowResponse

# Import modular functions
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers

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
        # Import locally to avoid circular import
        from app.api.v1.endpoints.collection_crud_create_commands import (
            create_collection_flow,
        )

        flow_data = CollectionFlowCreate(automation_tier=AutomationTier.TIER_2.value)
        return await create_collection_flow(flow_data, db, current_user, context)

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")
