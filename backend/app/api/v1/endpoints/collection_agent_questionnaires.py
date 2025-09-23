"""
Agent-First Questionnaire Generation for Collection Flows
Implements agent-driven questionnaire generation with graceful fallback
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.feature_flags import is_feature_enabled
from app.models import User, Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    QuestionnaireGenerationRequest,
    QuestionnaireGenerationResponse,
)
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
AGENT_GENERATION_TIMEOUT = 10  # seconds
QUESTIONNAIRE_POLL_INTERVAL = 5  # seconds


@router.post("/flows/{flow_id}/questionnaires/generate")
async def generate_questionnaire(
    flow_id: str,
    request: Optional[QuestionnaireGenerationRequest] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(lambda: User()),  # Simplified for now
) -> QuestionnaireGenerationResponse:
    """
    Trigger agent-driven questionnaire generation.
    Returns immediately with pending status if agent is working.
    """
    try:
        # Verify flow exists and user has access
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Check if agent-first generation is enabled
        use_agent = is_feature_enabled("collection.gaps.v2_agent_questionnaires", True)
        use_fallback = is_feature_enabled("collection.gaps.bootstrap_fallback", True)

        if not use_agent:
            # Return immediately that bootstrap should be used
            logger.info(
                f"Agent questionnaires disabled, using bootstrap for flow {flow_id}"
            )
            return QuestionnaireGenerationResponse(
                status="ready",
                questionnaire_id="bootstrap",
                message="Using bootstrap questionnaire (agent generation disabled)",
            )

        # Check if questionnaire generation is already in progress
        if flow.metadata and flow.metadata.get("questionnaire_generating"):
            generation_start = flow.metadata.get("generation_started_at")
            if generation_start:
                started = datetime.fromisoformat(generation_start)
                elapsed = (datetime.utcnow() - started).total_seconds()

                if elapsed < AGENT_GENERATION_TIMEOUT:
                    # Still generating
                    return QuestionnaireGenerationResponse(
                        status="pending",
                        error_code="QUESTIONNAIRE_GENERATING",
                        retry_after=QUESTIONNAIRE_POLL_INTERVAL,
                        message=f"Questionnaire generation in progress ({int(elapsed)}s elapsed)",
                    )
                else:
                    # Timeout - use fallback if enabled
                    if use_fallback:
                        logger.warning(
                            f"Agent generation timed out for flow {flow_id}, using fallback"
                        )
                        return QuestionnaireGenerationResponse(
                            status="fallback",
                            questionnaire_id="bootstrap",
                            message="Agent generation timed out, using bootstrap questionnaire",
                        )
                    else:
                        return QuestionnaireGenerationResponse(
                            status="error",
                            error_code="GENERATION_TIMEOUT",
                            message="Questionnaire generation timed out",
                        )

        # Start agent generation
        logger.info(
            f"Starting agent-driven questionnaire generation for flow {flow_id}"
        )

        # Mark flow as generating
        if not flow.metadata:
            flow.metadata = {}
        flow.metadata["questionnaire_generating"] = True
        flow.metadata["generation_started_at"] = datetime.utcnow().isoformat()
        await db.commit()

        # Trigger async agent generation
        asyncio.create_task(
            _generate_with_agent(
                flow_id=flow.id,
                flow_uuid=flow.flow_id,
                context=context,
                selected_asset_ids=request.selected_asset_ids if request else None,
            )
        )

        # Return pending status immediately
        return QuestionnaireGenerationResponse(
            status="pending",
            error_code="QUESTIONNAIRE_GENERATING",
            retry_after=QUESTIONNAIRE_POLL_INTERVAL,
            message="Agent is generating questionnaire",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating questionnaire generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate questionnaire generation",
        )


async def _generate_with_agent(
    flow_id: int,
    flow_uuid: UUID,
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> None:
    """
    Background task to generate questionnaire using persistent agent.
    """
    try:
        async with AsyncSession(get_db()) as db:
            # Get agent pool
            agent_pool = TenantScopedAgentPool(
                tenant_id=str(context.client_account_id),
                engagement_id=str(context.engagement_id),
            )

            # Gather context for agent
            agent_context = await _build_agent_context(
                db=db,
                flow_id=flow_id,
                context=context,
                selected_asset_ids=selected_asset_ids,
            )

            # Get collection agent
            collection_agent = await agent_pool.get_agent(
                "adaptive_collection_specialist",
                context=agent_context,
            )

            if not collection_agent:
                logger.error(f"Could not get collection agent for flow {flow_uuid}")
                await _mark_generation_failed(db, flow_id)
                return

            # Generate questionnaire
            logger.info(f"Agent generating questionnaire for flow {flow_uuid}")

            result = await collection_agent.generate_questionnaire(
                flow_id=str(flow_uuid),
                gaps=agent_context.get("gaps", []),
                assets=agent_context.get("assets", []),
                scope=agent_context.get("scope", "engagement"),
            )

            if result and result.get("questionnaire"):
                # Save questionnaire to database
                questionnaire_data = result["questionnaire"]

                questionnaire = AdaptiveQuestionnaire(
                    collection_flow_id=flow_id,
                    title=questionnaire_data.get("title", "Adaptive Questionnaire"),
                    description=questionnaire_data.get("description", ""),
                    questions=questionnaire_data.get("questions", []),
                    target_gaps=questionnaire_data.get("target_gaps", []),
                    validation_rules=questionnaire_data.get("validation_rules", {}),
                    completion_status="pending",
                    metadata={
                        "agent_generated": True,
                        "requires_asset_selection": result.get(
                            "requires_asset_selection", False
                        ),
                        "generation_time": datetime.utcnow().isoformat(),
                    },
                )

                db.add(questionnaire)

                # Update flow metadata
                flow_result = await db.execute(
                    select(CollectionFlow).where(CollectionFlow.id == flow_id)
                )
                flow = flow_result.scalar_one()

                if not flow.metadata:
                    flow.metadata = {}
                flow.metadata["questionnaire_generating"] = False
                flow.metadata["questionnaire_ready"] = True
                flow.metadata["agent_questionnaire_id"] = str(questionnaire.id)

                await db.commit()

                logger.info(f"Agent questionnaire generated for flow {flow_uuid}")

            else:
                logger.warning(f"Agent returned no questionnaire for flow {flow_uuid}")
                await _mark_generation_failed(db, flow_id)

    except Exception as e:
        logger.error(f"Agent questionnaire generation failed: {e}")
        try:
            async with AsyncSession(get_db()) as db:
                await _mark_generation_failed(db, flow_id)
        except Exception:
            pass


async def _build_agent_context(
    db: AsyncSession,
    flow_id: int,
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Build context for agent to generate questionnaire.
    """
    # Get flow details
    flow_result = await db.execute(
        select(CollectionFlow).where(CollectionFlow.id == flow_id)
    )
    flow = flow_result.scalar_one()

    # Get assets
    assets_query = select(Asset).where(
        Asset.engagement_id == context.engagement_id,
        Asset.client_account_id == context.client_account_id,
    )

    if selected_asset_ids:
        assets_query = assets_query.where(
            Asset.id.in_([UUID(aid) for aid in selected_asset_ids])
        )

    assets_result = await db.execute(assets_query)
    assets = assets_result.scalars().all()

    # Build context
    return {
        "flow_id": str(flow.flow_id),
        "scope": (
            flow.collection_config.get("scope", "engagement")
            if flow.collection_config
            else "engagement"
        ),
        "selected_asset_ids": selected_asset_ids or [],
        "assets": [
            {
                "id": str(asset.id),
                "name": asset.name or asset.application_name,
                "type": asset.asset_type,
                "completeness": _calculate_completeness(asset),
                "gaps": _identify_gaps(asset),
            }
            for asset in assets
        ],
        "gaps": [],  # TODO: Get actual gaps from gap analysis
        "tenant_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
    }


async def _mark_generation_failed(db: AsyncSession, flow_id: int) -> None:
    """
    Mark questionnaire generation as failed.
    """
    flow_result = await db.execute(
        select(CollectionFlow).where(CollectionFlow.id == flow_id)
    )
    flow = flow_result.scalar_one_or_none()

    if flow:
        if not flow.metadata:
            flow.metadata = {}
        flow.metadata["questionnaire_generating"] = False
        flow.metadata["generation_failed"] = True
        await db.commit()


def _calculate_completeness(asset: Asset) -> float:
    """
    Calculate asset completeness score.
    """
    required_fields = [
        "name",
        "asset_type",
        "description",
        "business_criticality",
        "technical_stack",
        "deployment_environment",
    ]
    optional_fields = [
        "data_classification",
        "compliance_requirements",
        "disaster_recovery",
        "maintenance_windows",
    ]

    required_complete = sum(
        1 for field in required_fields if getattr(asset, field, None) is not None
    ) / len(required_fields)

    optional_complete = (
        sum(1 for field in optional_fields if getattr(asset, field, None) is not None)
        / len(optional_fields)
        if optional_fields
        else 0
    )

    return (required_complete * 0.7) + (optional_complete * 0.3)


def _identify_gaps(asset: Asset) -> list[str]:
    """
    Identify data gaps in asset.
    """
    gaps = []
    critical_fields = {
        "business_criticality": "Business criticality not specified",
        "technical_stack": "Technical stack information missing",
        "deployment_environment": "Deployment environment not documented",
        "data_classification": "Data classification required",
    }

    for field, message in critical_fields.items():
        if not getattr(asset, field, None):
            gaps.append(message)

    return gaps
