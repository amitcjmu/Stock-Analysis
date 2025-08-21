"""
Collection Flow Create Command Operations
Create operations for collection flows including creation from discovery
and new collection flow creation.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import (
    COLLECTION_CREATE_ROLES,
    require_role,
)
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)
from app.schemas.collection_flow import (
    CollectionFlowCreate,
    CollectionFlowResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_utils
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def create_collection_from_discovery(
    discovery_flow_id: str,
    selected_application_ids: List[str],
    collection_strategy: Optional[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Create Collection flow from Discovery results with selected applications.

    This function enables seamless transition from Discovery to Collection,
    allowing users to select applications from the Discovery inventory for
    detailed data collection and gap analysis.

    Args:
        discovery_flow_id: The Discovery flow ID to transition from
        selected_application_ids: List of application IDs to collect data for
        collection_strategy: Optional configuration for collection approach
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse with the created Collection flow details
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "create collection flows")

    try:
        # Validate required context
        if not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Missing engagement_id in request context"
            )

        # Validate Discovery flow exists and is complete
        # Convert engagement_id to UUID since validators expect UUID type
        engagement_uuid = uuid.UUID(context.engagement_id)
        discovery_flow = await collection_validators.validate_discovery_flow_exists(
            db, discovery_flow_id, engagement_uuid
        )

        # Validate selected applications exist and belong to the engagement
        applications = await collection_validators.validate_applications_exist(
            db, selected_application_ids, engagement_uuid
        )

        # Use actual application IDs if none were provided
        if not selected_application_ids:
            selected_application_ids = (
                collection_serializers.extract_application_ids_from_assets(applications)
            )

        # Build collection configuration
        collection_config = (
            collection_serializers.build_collection_config_from_discovery(
                discovery_flow,
                applications,
                selected_application_ids,
                collection_strategy,
            )
        )

        # Create collection flow record
        flow_id = uuid.uuid4()
        flow_name = collection_utils.format_flow_display_name(
            len(selected_application_ids)
        )

        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=flow_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,
            created_by=current_user.id,
            status=CollectionFlowStatus.INITIALIZED.value,
            automation_tier=collection_config["automation_tier"],
            collection_config=collection_config,
            current_phase=CollectionPhase.GAP_ANALYSIS.value,  # Start with gap analysis
            discovery_flow_id=uuid.UUID(discovery_flow_id),  # Link to Discovery flow
        )

        db.add(collection_flow)
        await db.commit()
        await db.refresh(collection_flow)

        # Initialize with Master Flow Orchestrator
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
            # Skip platform detection since we have Discovery data
            "start_phase": "gap_analysis",
        }

        # Create the flow - it will be automatically started by the execution engine
        master_flow_id, master_flow_data = await collection_utils.create_mfo_flow(
            db, context, "collection", flow_input
        )

        # Update collection flow with master flow ID
        # Convert string to UUID for master_flow_id field
        if master_flow_id:
            collection_flow.master_flow_id = uuid.UUID(master_flow_id)
            await db.commit()
            await db.refresh(collection_flow)
        else:
            logger.warning(
                "Master flow creation returned None - collection flow will not "
                "have master_flow_id set"
            )

        logger.info(
            "Created collection flow %s from discovery flow %s with %d applications",
            collection_flow.id,
            discovery_flow_id,
            len(selected_application_ids),
        )

        # Serialize flow and add warning if master_flow_id is missing
        serialized_flow = collection_serializers.serialize_collection_flow(
            collection_flow
        )
        if not master_flow_id:
            serialized_flow["warning"] = (
                "Master flow creation failed - collection flow created without "
                "master orchestration. Please retry or contact support."
            )

        return serialized_flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error creating collection from discovery: "
                "discovery_flow_id={discovery_flow_id}, error={e}",
                discovery_flow_id=discovery_flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def create_collection_flow(
    flow_data: CollectionFlowCreate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Create and start a new collection flow.

    Args:
        flow_data: Collection flow creation data
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Created collection flow details

    Raises:
        HTTPException: If creation fails
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "create collection flows")

    try:
        # Import lifecycle manager locally to avoid circular imports
        from app.api.v1.endpoints.collection_flow_lifecycle import (
            CollectionFlowLifecycleManager,
        )

        lifecycle_manager = CollectionFlowLifecycleManager(db, context)

        # Check for existing active flows (no automatic mutations)
        existing_result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.in_(
                    [
                        CollectionFlowStatus.INITIALIZED.value,
                        CollectionFlowStatus.PLATFORM_DETECTION.value,
                        CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                        CollectionFlowStatus.GAP_ANALYSIS.value,
                        CollectionFlowStatus.MANUAL_COLLECTION.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.updated_at.desc().nulls_last())
            .limit(1)
        )
        existing_flow = existing_result.scalar_one_or_none()

        if existing_flow and not getattr(flow_data, "allow_multiple", False):
            # Analyze the existing flow to provide better error information
            flow_analysis = await lifecycle_manager.analyze_existing_flows(
                str(current_user.id)
            )

            # Create enhanced error response with user options
            error_detail = {
                "error": "Active collection flow already exists",
                "message": (
                    "Cannot create new flow while another is active. "
                    "Please manage existing flows first."
                ),
                "existing_flow_id": str(existing_flow.flow_id),
                "existing_flow_name": existing_flow.flow_name,
                "existing_flow_status": existing_flow.status,
                "last_activity": (
                    existing_flow.updated_at.isoformat()
                    if existing_flow.updated_at
                    else existing_flow.created_at.isoformat()
                ),
                "age_hours": round(
                    (
                        datetime.utcnow()
                        - (existing_flow.updated_at or existing_flow.created_at)
                    ).total_seconds()
                    / 3600,
                    2,
                ),
                "analysis": flow_analysis,
                "suggested_endpoints": {
                    "analyze_flows": "/api/v1/collection/flows/analysis",
                    "manage_flows": "/api/v1/collection/flows/manage",
                    "resume_flow": (
                        f"/api/v1/collection/flows/{existing_flow.flow_id}/continue"
                    ),
                },
                "resolution_steps": [
                    (
                        "1. Call /api/v1/collection/flows/analysis to view all "
                        "existing flows and their states"
                    ),
                    (
                        "2. Use /api/v1/collection/flows/manage to cancel, "
                        "complete, or clean up flows as needed"
                    ),
                    (
                        "3. Retry flow creation or resume the existing flow "
                        "using the continue endpoint"
                    ),
                ],
                "user_action_required": True,
            }

            raise HTTPException(
                status_code=409,
                detail=error_detail,
            )

        # Create flow record
        flow_id = uuid.uuid4()
        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=collection_utils.format_flow_display_name(),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,
            created_by=current_user.id,
            status=CollectionFlowStatus.INITIALIZED.value,
            automation_tier=flow_data.automation_tier,
            collection_config=flow_data.collection_config or {},
            current_phase=CollectionPhase.PLATFORM_DETECTION.value,
        )

        db.add(collection_flow)
        await db.commit()
        await db.refresh(collection_flow)

        # Initialize with Master Flow Orchestrator
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
        }

        master_flow_id, master_flow_data = await collection_utils.create_mfo_flow(
            db, context, "collection", flow_input
        )

        # Update collection flow with master flow ID
        # Convert string to UUID for master_flow_id field
        if master_flow_id:
            collection_flow.master_flow_id = uuid.UUID(master_flow_id)
            await db.commit()
            await db.refresh(collection_flow)
        else:
            logger.warning(
                "Master flow creation returned None - collection flow will not "
                "have master_flow_id set"
            )

        logger.info(
            safe_log_format(
                "Created collection flow: flow_id={flow_id}, "
                "engagement_id={engagement_id}",
                flow_id=str(collection_flow.flow_id),
                engagement_id=context.engagement_id,
            )
        )

        # Serialize flow and add warning if master_flow_id is missing
        serialized_flow = collection_serializers.serialize_collection_flow(
            collection_flow
        )
        if not master_flow_id:
            serialized_flow["warning"] = (
                "Master flow creation failed - collection flow created without "
                "master orchestration. Please retry or contact support."
            )

        return serialized_flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error creating collection flow: flow_data={flow_data}, error={e}",
                flow_data=flow_data.model_dump(),
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
