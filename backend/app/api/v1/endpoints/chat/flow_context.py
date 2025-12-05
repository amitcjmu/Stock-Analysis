"""
Flow context retrieval endpoints for AI chat assistant.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class FlowContextResponse(BaseModel):
    """Response model for flow context."""

    flow_id: Optional[str] = None
    flow_type: Optional[str] = None
    current_phase: Optional[str] = None
    completion_percentage: Optional[int] = None
    status: Optional[str] = None
    pending_actions: List[str] = []
    metadata: Dict[str, Any] = {}


@router.get("/flow-context/{flow_type}/{flow_id}")
async def get_flow_context_for_chat(
    flow_type: str,
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> FlowContextResponse:
    """
    Get flow context for the AI chat assistant.

    This endpoint provides dynamic flow state information that the chat
    assistant uses to provide context-aware responses.

    Args:
        flow_type: Type of flow (discovery, collection, assessment, etc.)
        flow_id: UUID of the flow
        db: Database session
        context: Request context with tenant information

    Returns:
        FlowContextResponse with current flow state

    Issue: #1218 - [Feature] Contextual AI Chat Assistant
    Milestone: Contextual AI Chat Assistant
    """
    try:
        logger.info(f"Getting flow context for chat: {flow_type}/{flow_id}")

        # Validate flow_id is a valid UUID
        try:
            flow_uuid = UUID(flow_id)
        except ValueError:
            return FlowContextResponse(
                flow_id=flow_id,
                flow_type=flow_type,
                status="invalid_id",
                pending_actions=["Provide a valid flow ID"],
            )

        # Get flow context based on flow type
        flow_context = await _get_flow_context_by_type(
            flow_type=flow_type,
            flow_id=flow_uuid,
            db=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )

        return FlowContextResponse(**flow_context)

    except Exception as e:
        logger.error(f"Error getting flow context: {e}")
        return FlowContextResponse(
            flow_id=flow_id,
            flow_type=flow_type,
            status="error",
            pending_actions=[f"Error fetching flow state: {str(e)}"],
        )


async def _get_flow_context_by_type(
    flow_type: str,
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """
    Get flow context based on flow type.

    Queries the appropriate flow table and returns unified flow state.
    """
    base_response = {
        "flow_id": str(flow_id),
        "flow_type": flow_type,
        "current_phase": None,
        "completion_percentage": None,
        "status": None,
        "pending_actions": [],
        "metadata": {},
    }

    try:
        if flow_type == "discovery":
            return await _get_discovery_flow_context(
                flow_id, db, client_account_id, engagement_id
            )
        elif flow_type == "collection":
            return await _get_collection_flow_context(
                flow_id, db, client_account_id, engagement_id
            )
        elif flow_type == "assessment":
            return await _get_assessment_flow_context(
                flow_id, db, client_account_id, engagement_id
            )
        elif flow_type == "decommission":
            return await _get_decommission_flow_context(
                flow_id, db, client_account_id, engagement_id
            )
        else:
            # Return base response for unsupported flow types
            base_response["status"] = "unsupported_flow_type"
            base_response["pending_actions"] = [
                f"Flow type '{flow_type}' not supported for context retrieval"
            ]
            return base_response

    except Exception as e:
        logger.warning(f"Failed to get {flow_type} flow context: {e}")
        base_response["status"] = "error"
        base_response["pending_actions"] = [str(e)]
        return base_response


async def _get_discovery_flow_context(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """Get discovery flow context."""
    from app.models.discovery_flow import DiscoveryFlow

    query = select(DiscoveryFlow).where(
        DiscoveryFlow.flow_id == str(flow_id),
        DiscoveryFlow.client_account_id == client_account_id,
        DiscoveryFlow.engagement_id == engagement_id,
    )
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        return {
            "flow_id": str(flow_id),
            "flow_type": "discovery",
            "status": "not_found",
            "current_phase": None,
            "completion_percentage": None,
            "pending_actions": ["Flow not found"],
            "metadata": {},
        }

    # Calculate progress from phase completion flags
    phases = {
        "data_import": flow.data_import_completed,
        "data_validation": flow.data_validation_completed,
        "field_mapping": flow.field_mapping_completed,
        "data_cleansing": flow.data_cleansing_completed,
        "asset_inventory": flow.asset_inventory_completed,
    }
    completed_count = sum(1 for v in phases.values() if v)
    progress = int((completed_count / len(phases)) * 100)

    # Determine pending actions based on current phase
    pending_actions = _get_discovery_pending_actions(flow.current_phase, phases)

    return {
        "flow_id": str(flow_id),
        "flow_type": "discovery",
        "status": flow.status,
        "current_phase": flow.current_phase,
        "completion_percentage": progress,
        "pending_actions": pending_actions,
        "metadata": {
            "phases_completed": phases,
            "data_import_id": flow.data_import_id,
        },
    }


def _get_discovery_pending_actions(
    current_phase: Optional[str], phases: Dict[str, bool]
) -> List[str]:
    """Get pending actions for discovery flow."""
    actions = []

    if current_phase == "data_import" and not phases.get("data_import"):
        actions.append("Upload CMDB data file")
    elif current_phase == "field_mapping" and not phases.get("field_mapping"):
        actions.append("Review and approve field mappings")
    elif current_phase == "data_cleansing" and not phases.get("data_cleansing"):
        actions.append("Resolve data quality issues")
    elif current_phase == "data_validation" and not phases.get("data_validation"):
        actions.append("Complete data validation")
    elif current_phase == "asset_inventory" and not phases.get("asset_inventory"):
        actions.append("Review asset inventory")

    return actions


async def _get_collection_flow_context(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """Get collection flow context."""
    from app.models.collection_flow import CollectionFlow

    query = select(CollectionFlow).where(
        CollectionFlow.id == flow_id,
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        return {
            "flow_id": str(flow_id),
            "flow_type": "collection",
            "status": "not_found",
            "current_phase": None,
            "completion_percentage": None,
            "pending_actions": ["Flow not found"],
            "metadata": {},
        }

    # Determine pending actions
    pending_actions = _get_collection_pending_actions(flow.current_phase, flow.status)

    return {
        "flow_id": str(flow_id),
        "flow_type": "collection",
        "status": flow.status,
        "current_phase": flow.current_phase,
        "completion_percentage": flow.completion_percentage or 0,
        "pending_actions": pending_actions,
        "metadata": {
            "gaps_identified": flow.gaps_identified,
            "automation_tier": flow.automation_tier,
        },
    }


def _get_collection_pending_actions(
    current_phase: Optional[str], status: Optional[str]
) -> List[str]:
    """Get pending actions for collection flow."""
    actions = []

    if current_phase == "gap_analysis":
        actions.append("Review identified data gaps")
    elif current_phase == "questionnaire_generation":
        actions.append("Wait for questionnaire generation")
    elif current_phase == "data_collection":
        actions.append("Complete questionnaire responses")
    elif current_phase == "validation":
        actions.append("Validate collected data")

    if status == "paused":
        actions.append("Resume the collection flow")

    return actions


async def _get_assessment_flow_context(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """Get assessment flow context."""
    from app.models.assessment_flow import AssessmentFlow

    # Assessment flow uses both id and master_flow_id
    query = select(AssessmentFlow).where(
        or_(
            AssessmentFlow.id == flow_id,
            AssessmentFlow.master_flow_id == flow_id,
        ),
        AssessmentFlow.client_account_id == client_account_id,
        AssessmentFlow.engagement_id == engagement_id,
    )
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        return {
            "flow_id": str(flow_id),
            "flow_type": "assessment",
            "status": "not_found",
            "current_phase": None,
            "completion_percentage": None,
            "pending_actions": ["Flow not found"],
            "metadata": {},
        }

    # Determine pending actions
    pending_actions = _get_assessment_pending_actions(flow.current_phase, flow.status)

    return {
        "flow_id": str(flow_id),
        "flow_type": "assessment",
        "status": flow.status,
        "current_phase": flow.current_phase,
        "completion_percentage": flow.progress or 0,
        "pending_actions": pending_actions,
        "metadata": {
            "selected_applications": len(flow.selected_application_ids or []),
            "phase_progress": flow.phase_progress,
        },
    }


def _get_assessment_pending_actions(
    current_phase: Optional[str], status: Optional[str]
) -> List[str]:
    """Get pending actions for assessment flow."""
    actions = []

    if current_phase == "architecture_standards":
        actions.append("Review architecture standards analysis")
    elif current_phase == "tech_debt_analysis":
        actions.append("Review technical debt findings")
    elif current_phase == "dependency_analysis":
        actions.append("Review dependency analysis")
    elif current_phase == "6r_decision":
        actions.append("Review 6R recommendations")
    elif current_phase == "acceptance":
        actions.append("Accept or modify 6R recommendations")

    if status == "paused":
        actions.append("Resume the assessment flow")

    return actions


async def _get_decommission_flow_context(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """Get decommission flow context."""
    from app.models.decommission_flow import DecommissionFlow

    query = select(DecommissionFlow).where(
        DecommissionFlow.id == flow_id,
        DecommissionFlow.client_account_id == client_account_id,
        DecommissionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        return {
            "flow_id": str(flow_id),
            "flow_type": "decommission",
            "status": "not_found",
            "current_phase": None,
            "completion_percentage": None,
            "pending_actions": ["Flow not found"],
            "metadata": {},
        }

    return {
        "flow_id": str(flow_id),
        "flow_type": "decommission",
        "status": flow.status,
        "current_phase": flow.current_phase,
        "completion_percentage": flow.completion_percentage or 0,
        "pending_actions": _get_decommission_pending_actions(
            flow.current_phase, flow.status
        ),
        "metadata": {},
    }


def _get_decommission_pending_actions(
    current_phase: Optional[str], status: Optional[str]
) -> List[str]:
    """Get pending actions for decommission flow."""
    actions = []

    if current_phase == "planning":
        actions.append("Complete decommission planning")
    elif current_phase == "data_migration":
        actions.append("Monitor data migration progress")
    elif current_phase == "system_shutdown":
        actions.append("Verify system shutdown")
    elif current_phase == "validation":
        actions.append("Validate decommission completion")

    if status == "paused":
        actions.append("Resume the decommission flow")

    return actions
