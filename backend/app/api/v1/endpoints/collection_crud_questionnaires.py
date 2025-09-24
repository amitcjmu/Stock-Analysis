"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific read operations for collection flows.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from app.core.context import RequestContext
from app.models import User
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers
from app.api.v1.endpoints.questionnaire_templates import (
    get_bootstrap_questionnaire_template,
)

logger = logging.getLogger(__name__)

# Track background tasks to prevent memory leaks
_background_tasks: set = set()


async def _get_flow_by_id(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Get and validate collection flow by ID."""
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.client_account_id == context.client_account_id,
        )
    )
    flow = flow_result.scalar_one_or_none()
    if not flow:
        logger.warning(f"Collection flow not found: {flow_id}")
        raise HTTPException(status_code=404, detail="Collection flow not found")
    return flow


async def _get_existing_questionnaires_tenant_scoped(
    flow: CollectionFlow, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """Get existing questionnaires from database with tenant scoping."""
    questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(
            AdaptiveQuestionnaire.collection_flow_id == flow.id,
            AdaptiveQuestionnaire.client_account_id == context.client_account_id,
            AdaptiveQuestionnaire.engagement_id == context.engagement_id,
        )
        .order_by(AdaptiveQuestionnaire.created_at.desc())
    )
    questionnaires = questionnaires_result.scalars().all()

    if questionnaires:
        logger.info(f"Found {len(questionnaires)} questionnaires in database")
        return [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]
    return []


async def _get_existing_assets(
    db: AsyncSession, context: RequestContext
) -> List[Asset]:
    """Get existing assets for engagement."""
    assets_result = await db.execute(
        select(Asset)
        .where(Asset.engagement_id == context.engagement_id)
        .where(Asset.client_account_id == context.client_account_id)
        .order_by(Asset.created_at.desc())
    )
    return list(assets_result.scalars().all())


def _get_selected_application_info(
    flow: CollectionFlow, existing_assets: List[Asset]
) -> tuple[Optional[str], Optional[str]]:
    """Extract selected application info from flow config."""
    selected_application_name: Optional[str] = None
    selected_application_id: Optional[str] = None

    if flow.collection_config and flow.collection_config.get(
        "selected_application_ids"
    ):
        selected_app_ids = flow.collection_config.get("selected_application_ids", [])
        if selected_app_ids:
            selected_application_id = selected_app_ids[0]

            for asset in existing_assets:
                if str(asset.id) == str(selected_application_id):
                    selected_application_name = str(
                        asset.name or asset.application_name or ""
                    )
                    logger.info(
                        f"Pre-populating questionnaire with application: "
                        f"{selected_application_name} (ID: {selected_application_id})"
                    )
                    break
            else:
                logger.warning(
                    f"Selected application {selected_application_id} "
                    f"not found in asset inventory"
                )

    return selected_application_name, selected_application_id


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Get adaptive questionnaires for a collection flow with tenant-scoped queries.

    Implements agent-first generation with background processing and fallback
    strategies.
    """
    try:
        # Get and validate flow
        flow = await _get_flow_by_id(flow_id, db, context)

        # Try existing questionnaires first with tenant scoping
        existing_questionnaires = await _get_existing_questionnaires_tenant_scoped(
            flow, db, context
        )
        if existing_questionnaires:
            return existing_questionnaires

        # Check if flow is completed
        if flow.status == "completed":
            logger.info(f"Flow {flow_id} is completed. Returning empty list.")
            return []

        # Get existing assets needed for both agent and bootstrap generation
        existing_assets = await _get_existing_assets(db, context)

        # Check agent generation feature flag
        from app.core.feature_flags import is_feature_enabled

        use_agent = is_feature_enabled("collection.gaps.v2_agent_questionnaires", True)
        bootstrap_fallback = is_feature_enabled(
            "collection.gaps.bootstrap_fallback", True
        )

        if use_agent:
            logger.info(f"Agent generation enabled for flow {flow_id}")

            # Start agent generation in background and return pending record
            pending_questionnaires = await _start_agent_generation(
                flow_id, flow, existing_assets, context, db
            )

            if pending_questionnaires:
                logger.info(f"Started background agent generation for flow {flow_id}")
                return pending_questionnaires

        # Fallback to bootstrap if agent generation not enabled or failed to start
        if bootstrap_fallback:
            logger.info(f"Generating bootstrap questionnaire for flow {flow_id}")
            selected_app_name, selected_app_id = _get_selected_application_info(
                flow, existing_assets
            )

            collection_scope = "engagement"
            if flow.collection_config:
                collection_scope = flow.collection_config.get("scope", "engagement")

            bootstrap_template = get_bootstrap_questionnaire_template(
                flow_id=flow_id,
                selected_application_id=selected_app_id,
                selected_application_name=selected_app_name,
                existing_assets=existing_assets,
                scope=collection_scope,
            )

            bootstrap_questionnaire = AdaptiveQuestionnaireResponse(
                id=bootstrap_template["id"],
                collection_flow_id=bootstrap_template["flow_id"],
                title=f"{bootstrap_template['title']} (Bootstrap)",
                description=(
                    f"{bootstrap_template['description']} - "
                    "Generated using bootstrap template"
                ),
                target_gaps=[
                    "application_selection",
                    "basic_info",
                    "technical_details",
                    "infrastructure",
                    "compliance",
                ],
                questions=[
                    _convert_template_field_to_question(field, selected_app_name)
                    for field in bootstrap_template["form_fields"]
                ],
                validation_rules=bootstrap_template["validation_rules"],
                completion_status="fallback",
                responses_collected={},
                created_at=datetime.fromisoformat(
                    bootstrap_template["created_at"].replace("Z", "+00:00")
                ),
                completed_at=None,
            )

            logger.info("Returning bootstrap questionnaire with fallback status")
            return [bootstrap_questionnaire]

        # If no fallback available
        logger.warning(
            f"No questionnaire generation method available for flow {flow_id}"
        )
        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _convert_template_field_to_question(
    field: dict, selected_application_name: Optional[str] = None
) -> dict:
    """Convert a template field to a questionnaire question format.

    Args:
        field: Field from questionnaire template
        selected_application_name: Name of pre-selected application

    Returns:
        Question dictionary
    """
    question = {
        "field_id": field["field_id"],
        "question_text": field["question_text"],
        "field_type": field["field_type"],
        "required": field["required"],
        "category": field["category"],
        "options": field.get("options", []),
        "help_text": field.get("help_text", ""),
        "multiple": field.get("multiple", False),
        "metadata": field.get("metadata", {}),
    }

    # Pre-fill values if available
    if field["field_id"] == "application_name" and selected_application_name:
        question["default_value"] = selected_application_name
    elif field["field_id"] == "asset_name" and selected_application_name:
        question["default_value"] = selected_application_name

    # Handle default values for asset selector
    if field.get("default_value"):
        question["default_value"] = field["default_value"]

    return question


async def _start_agent_generation(
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
    db: AsyncSession,
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Start agent generation in background and return pending questionnaire record.

    Creates a pending questionnaire record in database and starts background task
    to generate actual questionnaires. Returns immediately with pending status.
    """
    try:
        # Create pending questionnaire record with tenant fields
        questionnaire_id = uuid4()
        pending_questionnaire = AdaptiveQuestionnaire(
            id=questionnaire_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            collection_flow_id=flow.id,
            title="AI-Generated Data Collection Questionnaire",
            description="Generating tailored questionnaire using AI agent analysis...",
            template_name="agent_generated",
            template_type="detailed",
            version="2.0",
            applicable_tiers=["tier_1", "tier_2", "tier_3", "tier_4"],
            question_set={},
            questions=[],
            validation_rules={},
            completion_status="pending",
            responses_collected={},
            is_active=True,
            is_template=False,
            created_at=datetime.utcnow(),
        )

        # Insert pending record with tenant isolation
        db.add(pending_questionnaire)
        await db.commit()
        await db.refresh(pending_questionnaire)

        logger.info(
            f"Created pending questionnaire {questionnaire_id} for flow {flow_id}"
        )

        # Start background generation task
        task = asyncio.create_task(
            _background_generate(
                questionnaire_id,
                flow_id,
                flow,
                existing_assets,
                context.client_account_id,
                context.engagement_id,
            )
        )

        # Track task to prevent memory leaks
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

        # Return pending response
        return [
            collection_serializers.build_questionnaire_response(pending_questionnaire)
        ]

    except Exception as e:
        logger.error(f"Failed to start agent generation for flow {flow_id}: {e}")
        return []


async def _update_questionnaire_status(
    db: AsyncSession,
    questionnaire_id: UUID,
    context_client_id: UUID,
    context_engagement_id: UUID,
    status: str,
    values: Optional[Dict[str, Any]] = None,
) -> None:
    """Update the status and other values of a questionnaire."""
    update_values = {"completion_status": status, "updated_at": datetime.utcnow()}
    if values:
        update_values.update(values)

    try:
        result = await db.execute(
            update(AdaptiveQuestionnaire)
            .where(
                AdaptiveQuestionnaire.id == questionnaire_id,
                AdaptiveQuestionnaire.client_account_id == context_client_id,
                AdaptiveQuestionnaire.engagement_id == context_engagement_id,
            )
            .values(**update_values)
        )
        if result.rowcount > 0:
            await db.commit()
            logger.info(
                f"Updated questionnaire {questionnaire_id} to status '{status}'"
            )
        else:
            await db.rollback()
            logger.warning(
                f"Failed to update questionnaire {questionnaire_id} to "
                f"status '{status}': tenant guard failed or record not found"
            )
    except Exception as e:
        await db.rollback()
        logger.error(
            f"DB error updating questionnaire {questionnaire_id} to "
            f"status '{status}': {e}"
        )
        raise  # Re-raise to ensure the background task failure is visible


async def _background_generate(
    questionnaire_id: UUID,
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    client_account_id: UUID,
    engagement_id: UUID,
) -> None:
    """
    Background task to generate questionnaire using agent.

    Uses fresh AsyncSession to avoid session conflicts with main request.
    Updates completion_status based on generation outcome.
    """
    from app.core.database import AsyncSessionLocal

    status_to_set = "failed"  # Default status if anything goes wrong
    update_values: Optional[Dict[str, Any]] = None

    async with AsyncSessionLocal() as fresh_db:
        try:
            logger.info(
                f"Starting background agent generation for "
                f"questionnaire {questionnaire_id}"
            )

            # Create RequestContext for backwards compatibility with
            # _generate_agent_questionnaires
            from app.core.context import RequestContext

            context = RequestContext(
                client_account_id=str(client_account_id),
                engagement_id=str(engagement_id),
                user_id="system",  # Background task user
            )

            # Generate questionnaires with timeout
            agent_questionnaires = await asyncio.wait_for(
                _generate_agent_questionnaires(flow_id, flow, existing_assets, context),
                timeout=30.0,
            )

            if agent_questionnaires and len(agent_questionnaires) > 0:
                # Extract questions from first generated questionnaire
                first_questionnaire = agent_questionnaires[0]
                questions = first_questionnaire.questions
                validation_rules = first_questionnaire.validation_rules

                # Set success status and values
                status_to_set = "ready"
                update_values = {
                    "questions": questions,
                    "validation_rules": validation_rules,
                }
                logger.info(f"Successfully generated questionnaire {questionnaire_id}")

            else:
                # No questionnaires generated - use fallback
                from app.core.feature_flags import is_feature_enabled

                bootstrap_fallback = is_feature_enabled(
                    "collection.gaps.bootstrap_fallback", True
                )

                if bootstrap_fallback:
                    status_to_set = "fallback"
                    logger.info(
                        f"Updated questionnaire {questionnaire_id} to fallback status"
                    )
                else:
                    status_to_set = "failed"
                    logger.warning(f"Marked questionnaire {questionnaire_id} as failed")

        except asyncio.TimeoutError:
            logger.warning(
                f"Agent generation timed out for questionnaire {questionnaire_id}"
            )
            status_to_set = "failed"

        except Exception as e:
            logger.error(
                f"Background generation failed for "
                f"questionnaire {questionnaire_id}: {e}"
            )
            status_to_set = "failed"

        finally:
            # Always update status in finally block to ensure it happens
            try:
                await _update_questionnaire_status(
                    fresh_db,
                    questionnaire_id,
                    client_account_id,
                    engagement_id,
                    status_to_set,
                    update_values,
                )
            except Exception as final_error:
                logger.error(
                    f"Failed to update questionnaire status in "
                    f"finally block: {final_error}"
                )


async def _generate_agent_questionnaires(
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Generate questionnaires using AI agent with hybrid fallback."""
    try:
        from app.services.ai_analysis.questionnaire_generator import (
            QuestionnaireService,
            QuestionnaireProcessor,
        )
        from app.services.ai_analysis.questionnaire_generator.agents import (
            QuestionnaireAgentManager,
        )
        from app.services.ai_analysis.questionnaire_generator.tasks import (
            QuestionnaireTaskManager,
        )

        # Initialize questionnaire generation service
        agent_manager = QuestionnaireAgentManager()
        agents = agent_manager.create_agents()

        # Create task inputs for questionnaire generation
        task_inputs: dict[str, Any] = {
            "gap_analysis": flow.gap_analysis_results or {},
            "business_context": flow.collection_config or {},
            "collection_flow_id": flow_id,
            "stakeholder_context": {},
            "automation_tier": "tier_2",
        }

        task_manager = QuestionnaireTaskManager(agents)
        tasks = task_manager.create_tasks(task_inputs)

        processor = QuestionnaireProcessor(
            agents=agents, tasks=tasks, name="questionnaire_generation"
        )
        service = QuestionnaireService(processor)

        # Prepare data gaps context
        data_gaps = [
            {"gap_type": "application_selection", "priority": "critical"},
            {"gap_type": "basic_info", "priority": "high"},
            {"gap_type": "technical_details", "priority": "medium"},
            {"gap_type": "infrastructure", "priority": "medium"},
            {"gap_type": "compliance", "priority": "low"},
        ]

        # Generate questionnaires
        questionnaires_data = await service.generate_questionnaires(
            data_gaps=data_gaps,
            business_context={"flow_id": flow_id, "scope": "engagement"},
            automation_tier="tier_2",
            collection_flow_id=flow_id,
        )

        # Convert to response format
        result = []
        for idx, q_data in enumerate(questionnaires_data):
            questionnaire = AdaptiveQuestionnaireResponse(
                id=q_data.get("id", f"agent-generated-{idx}"),
                collection_flow_id=flow_id,
                title=f"{q_data.get('title', 'AI-Generated Questionnaire')} (Agent)",
                description=(
                    f"{q_data.get('description', 'Generated by AI agent')} - "
                    "Created using AI questionnaire agent"
                ),
                target_gaps=[
                    "application_selection",
                    "basic_info",
                    "technical_details",
                ],
                questions=q_data.get("questions", []),
                validation_rules=q_data.get("validation_rules", {}),
                completion_status="pending",
                responses_collected={},
                created_at=datetime.now(),
                completed_at=None,
            )
            result.append(questionnaire)

        logger.info(f"Generated {len(result)} questionnaires using AI agent")
        return result

    except ImportError as e:
        logger.warning(f"Questionnaire generation service not available: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to generate questionnaires with agent: {e}")
        return []
