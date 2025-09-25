"""
Command operations for collection questionnaires.
Write operations and background task management for questionnaire generation.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)

# Track background tasks to prevent memory leaks
_background_tasks: set = set()


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
            created_at=datetime.now(timezone.utc),
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
                context,
            )
        )

        # Add task to background tasks set and remove when done
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

        # Return pending questionnaire immediately
        return [
            collection_serializers.build_questionnaire_response(pending_questionnaire)
        ]

    except Exception as e:
        logger.error(f"Error starting agent generation for flow {flow_id}: {e}")
        raise


async def _update_questionnaire_status(
    questionnaire_id: UUID,
    status: str,
    questions: List[dict] = None,
    error_message: str = None,
    db: AsyncSession = None,
) -> None:
    """Update questionnaire status and optionally add questions."""
    from app.database import AsyncSessionLocal

    # Use provided db session or create new one
    if db is None:
        async with AsyncSessionLocal() as session:
            await _do_update_questionnaire_status(
                session, questionnaire_id, status, questions, error_message
            )
    else:
        await _do_update_questionnaire_status(
            db, questionnaire_id, status, questions, error_message
        )


async def _do_update_questionnaire_status(
    db: AsyncSession,
    questionnaire_id: UUID,
    status: str,
    questions: List[dict] = None,
    error_message: str = None,
) -> None:
    """Internal helper to update questionnaire status."""
    try:
        update_data = {
            "completion_status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        if questions:
            update_data["questions"] = questions
            update_data["description"] = (
                f"AI-Generated questionnaire with {len(questions)} targeted questions"
            )

        if error_message:
            update_data["description"] = f"Generation failed: {error_message}"

        await db.execute(
            update(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.id == questionnaire_id)
            .values(**update_data)
        )
        await db.commit()

        logger.info(f"Updated questionnaire {questionnaire_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating questionnaire {questionnaire_id} status: {e}")
        raise


async def _background_generate(
    questionnaire_id: UUID,
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
) -> None:
    """
    Background task to generate questionnaires using AI agent.

    This runs in background and updates the pending questionnaire record
    when generation is complete or fails.
    """
    from app.database import AsyncSessionLocal

    try:
        logger.info(f"Starting background questionnaire generation for {flow_id}")

        # Use agent generation
        from .agents import _generate_agent_questionnaires

        questionnaires = await _generate_agent_questionnaires(
            flow_id, existing_assets, context
        )

        if questionnaires:
            # Extract questions from first questionnaire
            questions = questionnaires[0].questions if questionnaires else []

            # Update questionnaire with generated questions
            async with AsyncSessionLocal() as db:
                await _update_questionnaire_status(
                    questionnaire_id, "completed", questions, db=db
                )

            logger.info(
                f"Successfully generated {len(questions)} questions for flow {flow_id}"
            )
        else:
            # No questionnaires generated - mark as failed
            async with AsyncSessionLocal() as db:
                await _update_questionnaire_status(
                    questionnaire_id,
                    "failed",
                    error_message="No questionnaires could be generated",
                    db=db,
                )
            logger.warning(f"No questionnaires generated for flow {flow_id}")

    except Exception as e:
        logger.error(f"Background generation failed for flow {flow_id}: {e}")
        try:
            # Mark questionnaire as failed
            async with AsyncSessionLocal() as db:
                await _update_questionnaire_status(
                    questionnaire_id, "failed", error_message=str(e), db=db
                )
        except Exception as update_error:
            logger.error(f"Failed to update questionnaire status: {update_error}")
    finally:
        logger.info(f"Background generation completed for flow {flow_id}")
