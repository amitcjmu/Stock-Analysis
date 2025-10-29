"""
Collection Flow Validators
Validation logic for collection flows including discovery flow validation,
application validation, flow state validation, and tenant context validation.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


async def validate_discovery_flow_exists(
    db: AsyncSession, discovery_flow_id: str, engagement_id: UUID
) -> DiscoveryFlow:
    """Validate that discovery flow exists and is completed.

    Args:
        db: Database session
        discovery_flow_id: Discovery flow ID to validate
        engagement_id: Engagement ID for scope validation

    Returns:
        Validated discovery flow

    Raises:
        HTTPException: If discovery flow not found or not completed
    """
    try:
        result = await db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == discovery_flow_id,
                DiscoveryFlow.engagement_id == engagement_id,
                DiscoveryFlow.status == "completed",
            )
        )
        discovery_flow = result.scalar_one_or_none()

        if not discovery_flow:
            raise HTTPException(
                status_code=404, detail="Discovery flow not found or not completed"
            )

        return discovery_flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating discovery flow {discovery_flow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate discovery flow")


async def validate_applications_exist(
    db: AsyncSession, application_ids: List[str], engagement_id: UUID
) -> List[Asset]:
    """Validate that applications exist and belong to the engagement.

    Args:
        db: Database session
        application_ids: List of application IDs to validate
        engagement_id: Engagement ID for scope validation

    Returns:
        List of validated applications

    Raises:
        HTTPException: If applications not found or don't belong to engagement
    """
    if not application_ids:
        # If no applications specified, get all from engagement
        try:
            result = await db.execute(
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                select(Asset).where(Asset.engagement_id == engagement_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"Error fetching applications for engagement {engagement_id}: {e}"
            )
            raise HTTPException(status_code=500, detail="Failed to fetch applications")

    try:
        # Convert string IDs to UUIDs
        uuid_ids = [UUID(aid) for aid in application_ids]

        result = await db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(Asset).where(
                Asset.id.in_(uuid_ids),
                Asset.engagement_id == engagement_id,
            )
        )
        applications = result.scalars().all()

        if len(applications) != len(application_ids):
            raise HTTPException(
                status_code=400,
                detail="Some selected applications not found or don't belong to this engagement",
            )

        return applications

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid application ID format: {e}"
        )
    except Exception as e:
        logger.error(f"Error validating applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate applications")


async def validate_collection_flow_exists(
    db: AsyncSession, flow_id: str, engagement_id: UUID
) -> CollectionFlow:
    """Validate that collection flow exists and belongs to engagement.

    Args:
        db: Database session
        flow_id: Collection flow ID to validate
        engagement_id: Engagement ID for scope validation

    Returns:
        Validated collection flow

    Raises:
        HTTPException: If collection flow not found
    """
    try:
        result = await db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        return collection_flow

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid flow ID format: {e}")
    except Exception as e:
        logger.error(f"Error validating collection flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to validate collection flow"
        )


async def validate_flow_can_be_executed(flow: CollectionFlow) -> None:
    """Validate that a collection flow can be executed.

    Args:
        flow: Collection flow to validate

    Raises:
        HTTPException: If flow cannot be executed
    """
    non_executable_statuses = [
        CollectionFlowStatus.COMPLETED.value,
        CollectionFlowStatus.CANCELLED.value,
        CollectionFlowStatus.FAILED.value,
    ]

    if flow.status in non_executable_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute flow with status: {flow.status}",
        )


async def validate_flow_can_be_resumed(flow: CollectionFlow) -> None:
    """Validate that a collection flow can be resumed.

    Args:
        flow: Collection flow to validate

    Raises:
        HTTPException: If flow cannot be resumed
    """
    non_resumable_statuses = [
        CollectionFlowStatus.COMPLETED.value,
        CollectionFlowStatus.CANCELLED.value,
    ]

    if flow.status in non_resumable_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume flow with status: {flow.status}",
        )


async def validate_flow_can_be_deleted(
    flow: CollectionFlow, force: bool = False
) -> None:
    """Validate that a collection flow can be deleted.

    Args:
        flow: Collection flow to validate
        force: Whether to force delete active flows

    Raises:
        HTTPException: If flow cannot be deleted
    """
    if force:
        return  # Force delete bypasses validation

    # Per ADR-012: Use lifecycle states instead of phase values
    active_statuses = [
        CollectionFlowStatus.RUNNING.value,
        CollectionFlowStatus.PAUSED.value,
    ]

    if flow.status in active_statuses:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active flow. Use force=true to override.",
        )


def validate_tenant_context(context: RequestContext) -> None:
    """Validate that tenant context has required identifiers.

    Args:
        context: Request context to validate

    Raises:
        HTTPException: If context is missing required identifiers
    """
    if not getattr(context, "client_account_id", None) or not getattr(
        context, "engagement_id", None
    ):
        raise HTTPException(
            status_code=400, detail="Missing tenant context identifiers"
        )


async def check_for_existing_active_flow(
    db: AsyncSession, engagement_id: UUID, exclude_flow_id: Optional[str] = None
) -> Optional[CollectionFlow]:
    """Check for existing active collection flows in engagement.

    Args:
        db: Database session
        engagement_id: Engagement ID to check
        exclude_flow_id: Optional flow ID to exclude from check

    Returns:
        Existing active flow or None
    """
    try:
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(CollectionFlow).where(
            CollectionFlow.engagement_id == engagement_id,
            CollectionFlow.status.notin_(
                [
                    CollectionFlowStatus.COMPLETED.value,
                    CollectionFlowStatus.FAILED.value,
                    CollectionFlowStatus.CANCELLED.value,
                ]
            ),
        )

        if exclude_flow_id:
            query = query.where(CollectionFlow.flow_id != UUID(exclude_flow_id))

        query = query.order_by(CollectionFlow.created_at.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    except Exception as e:
        logger.error(f"Error checking for active flows: {e}")
        return None


def validate_questionnaire_responses(responses: dict) -> None:
    """Validate questionnaire responses structure.

    Args:
        responses: Questionnaire responses to validate

    Raises:
        HTTPException: If responses are invalid
    """
    if not isinstance(responses, dict):
        raise HTTPException(status_code=400, detail="Responses must be a dictionary")

    # Add specific validation rules as needed
    # For now, just ensure it's a valid dict structure


def validate_flow_update_action(action: str) -> None:
    """Validate collection flow update action.

    Args:
        action: Update action to validate

    Raises:
        HTTPException: If action is invalid
    """
    valid_actions = ["continue", "pause", "cancel", "update_applications"]

    if action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
        )


async def validate_flow_belongs_to_engagement(
    db: AsyncSession,
    flow_id: str,
    engagement_id: UUID,
    flow_table_column: str = "flow_id",
) -> bool:
    """Validate that a flow belongs to the specified engagement.

    Args:
        db: Database session
        flow_id: Flow ID to check
        engagement_id: Expected engagement ID
        flow_table_column: Column name to check (flow_id or id)

    Returns:
        True if flow belongs to engagement, False otherwise
    """
    try:
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        if flow_table_column == "flow_id":
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            query = select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == engagement_id,
            )
        else:
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            query = select(CollectionFlow).where(
                CollectionFlow.id == UUID(flow_id),
                CollectionFlow.engagement_id == engagement_id,
            )

        result = await db.execute(query)
        flow = result.scalar_one_or_none()
        return flow is not None

    except Exception as e:
        logger.error(f"Error validating flow ownership: {e}")
        return False


def validate_automation_tier(tier: str) -> None:
    """Validate automation tier value.

    Args:
        tier: Automation tier to validate

    Raises:
        HTTPException: If tier is invalid
    """
    # Import here to avoid circular imports
    from app.models.collection_flow import AutomationTier

    valid_tiers = [t.value for t in AutomationTier]

    if tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid automation tier. Must be one of: {', '.join(valid_tiers)}",
        )


def validate_collection_config(config: dict) -> dict:
    """Validate and normalize collection configuration.

    Args:
        config: Collection configuration to validate

    Returns:
        Validated and normalized configuration

    Raises:
        HTTPException: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise HTTPException(
            status_code=400, detail="Collection config must be a dictionary"
        )

    # Normalize and validate specific config fields
    normalized_config = config.copy()

    # Ensure required fields have defaults
    if "start_phase" not in normalized_config:
        normalized_config["start_phase"] = "initialization"

    if "priority" not in normalized_config:
        normalized_config["priority"] = "balanced"

    return normalized_config


async def validate_batch_delete_permissions(
    flow_ids: List[str], engagement_id: UUID, db: AsyncSession
) -> Tuple[List[CollectionFlow], List[str]]:
    """Validate flows for batch deletion and return valid/invalid lists.

    Args:
        flow_ids: List of flow IDs to validate
        engagement_id: Engagement ID for scope validation
        db: Database session

    Returns:
        Tuple of (valid_flows, invalid_flow_ids)
    """
    valid_flows = []
    invalid_flow_ids = []

    for flow_id in flow_ids:
        try:
            # Note: This uses database id, not flow_id - matching original behavior
            result = await db.execute(
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                select(CollectionFlow).where(
                    CollectionFlow.id == UUID(flow_id),
                    CollectionFlow.engagement_id == engagement_id,
                )
            )
            flow = result.scalar_one_or_none()

            if flow:
                valid_flows.append(flow)
            else:
                invalid_flow_ids.append(flow_id)

        except Exception as e:
            logger.error(f"Error validating flow {flow_id} for batch delete: {e}")
            invalid_flow_ids.append(flow_id)

    return valid_flows, invalid_flow_ids
