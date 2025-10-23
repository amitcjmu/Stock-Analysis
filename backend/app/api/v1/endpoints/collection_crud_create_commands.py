"""
Collection Flow Create Command Operations
Create operations for collection flows including creation from discovery
and new collection flow creation.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import modular functions
from app.api.v1.endpoints import (
    collection_serializers,
    collection_utils,
    collection_validators,
)
from app.api.v1.endpoints.collection_crud_create_helpers import (
    build_existing_flow_error_detail,
    create_data_gaps_for_missing_attributes,
    handle_transaction_rollback,
    initialize_background_execution_if_needed,
)
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

        # Create collection flow (session handles transaction automatically)
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
            flow_metadata={
                "use_agent_generation": True
            },  # Enable CrewAI agent generation
            current_phase=CollectionPhase.GAP_ANALYSIS.value,  # Start with gap analysis
            discovery_flow_id=uuid.UUID(discovery_flow_id),  # Link to Discovery flow
        )

        db.add(collection_flow)
        await db.flush()  # Make ID available for foreign key relationships
        await db.refresh(collection_flow)

        # Initialize with Master Flow Orchestrator within the same transaction
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
            # Skip platform detection since we have Discovery data
            "start_phase": "gap_analysis",
        }

        # Create the flow through MFO with atomic=True to prevent internal commits
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        orchestrator = MasterFlowOrchestrator(db, context)

        master_flow_id, master_flow_data = await orchestrator.create_flow(
            flow_type="collection",
            flow_name=flow_name,
            initial_state=flow_input,
            atomic=False,
        )

        # Update collection flow with master flow ID
        # Convert string to UUID for master_flow_id field
        if not master_flow_id:
            raise ValueError(
                "MFO creation failed - transaction will be automatically rolled back"
            )

        collection_flow.master_flow_id = uuid.UUID(master_flow_id)
        # Transaction context manager will handle the final commit

        # Check if initial phase requires user input before executing
        PHASES_REQUIRING_USER_INPUT = [CollectionPhase.ASSET_SELECTION.value]

        await initialize_background_execution_if_needed(
            db=db,
            context=context,
            collection_flow=collection_flow,
            master_flow_id=uuid.UUID(master_flow_id),
            flow_input=flow_input,
            phases_requiring_user_input=PHASES_REQUIRING_USER_INPUT,
        )

        logger.info(
            "Created collection flow %s from discovery flow %s with %d applications",
            collection_flow.flow_id,
            discovery_flow_id,
            len(selected_application_ids),
        )

        # Serialize flow
        serialized_flow = collection_serializers.serialize_collection_flow(
            collection_flow
        )
        return serialized_flow

    except HTTPException:
        # Ensure rollback on HTTP exceptions that might leave partial state
        await handle_transaction_rollback(db, "HTTP exception")
        raise
    except Exception as e:
        # Rollback transaction on any unexpected errors
        await handle_transaction_rollback(db, "unexpected error")

        logger.error(
            safe_log_format(
                "Error creating collection from discovery: "
                "discovery_flow_id={discovery_flow_id}, error={error}",
                discovery_flow_id=discovery_flow_id,
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail="Collection creation failed")


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
        # Per ADR-012: Use lifecycle states instead of phase values
        existing_result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.in_(
                    [
                        CollectionFlowStatus.INITIALIZED.value,
                        CollectionFlowStatus.RUNNING.value,
                        CollectionFlowStatus.PAUSED.value,
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

            error_detail = build_existing_flow_error_detail(
                existing_flow, flow_analysis
            )

            raise HTTPException(status_code=409, detail=error_detail)

        # Create collection flow (session handles transaction automatically)
        # Create flow record
        flow_id = uuid.uuid4()

        # Per ADR-028: phase_state eliminated - phase tracking will be added to master flow
        # Phase tracking will be managed via master flow's phase_transitions after creation

        # Bug Fix: Parse assessment_flow_id to UUID if provided
        assessment_uuid = None
        if flow_data.assessment_flow_id:
            from uuid import UUID

            assessment_uuid = (
                UUID(flow_data.assessment_flow_id)
                if isinstance(flow_data.assessment_flow_id, str)
                else flow_data.assessment_flow_id
            )

        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=collection_utils.format_flow_display_name(),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,
            created_by=current_user.id,
            # Per ADR-012: asset_selection phase requires PAUSED status (user input needed)
            status=CollectionFlowStatus.PAUSED.value,
            automation_tier=flow_data.automation_tier,
            collection_config=flow_data.collection_config or {},
            flow_metadata={
                "use_agent_generation": True
            },  # Enable CrewAI agent generation
            current_phase=CollectionPhase.ASSET_SELECTION.value,
            # Bug Fix: Link collection flow to assessment flow
            assessment_flow_id=assessment_uuid,
            # phase_state removed per ADR-028 - use master flow's phase_transitions
        )

        db.add(collection_flow)
        await db.flush()  # Make ID available for foreign key relationships
        await db.refresh(collection_flow)

        # Bug #668 Fix: Create data gaps for specific missing attributes if provided
        if flow_data.missing_attributes:
            await create_data_gaps_for_missing_attributes(
                db=db,
                collection_flow_id=collection_flow.id,
                missing_attributes=flow_data.missing_attributes,
            )

        # Initialize with Master Flow Orchestrator within the same transaction
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
            "start_phase": "asset_selection",
        }

        # Create the flow through MFO with atomic=True to prevent internal commits
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        orchestrator = MasterFlowOrchestrator(db, context)

        master_flow_id, master_flow_data = await orchestrator.create_flow(
            flow_type="collection",
            flow_name=collection_flow.flow_name,
            initial_state=flow_input,
            atomic=True,  # Fixed: We're in a transaction, don't commit internally
        )

        # Update collection flow with master flow ID
        # Convert string to UUID for master_flow_id field
        if not master_flow_id:
            raise RuntimeError(
                "MFO creation failed - transaction will be automatically rolled back"
            )

        collection_flow.master_flow_id = uuid.UUID(master_flow_id)
        # Transaction context manager will handle the final commit

        # Check if initial phase requires user input before executing
        PHASES_REQUIRING_USER_INPUT = [CollectionPhase.ASSET_SELECTION.value]

        await initialize_background_execution_if_needed(
            db=db,
            context=context,
            collection_flow=collection_flow,
            master_flow_id=uuid.UUID(master_flow_id),
            flow_input=flow_input,
            phases_requiring_user_input=PHASES_REQUIRING_USER_INPUT,
        )

        logger.info(
            safe_log_format(
                "Created collection flow: flow_id={flow_id}, "
                "engagement_id={engagement_id}",
                flow_id=str(collection_flow.flow_id),
                engagement_id=context.engagement_id,
            )
        )

        # Serialize flow
        serialized_flow = collection_serializers.serialize_collection_flow(
            collection_flow
        )
        return serialized_flow

    except HTTPException:
        # Ensure rollback on HTTP exceptions that might leave partial state
        await handle_transaction_rollback(db, "HTTP exception")
        raise
    except Exception as e:
        # Rollback transaction on any unexpected errors
        await handle_transaction_rollback(db, "unexpected error")

        logger.error(
            safe_log_format(
                "Error creating collection flow: error={error}",
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail="Collection flow creation failed")
