"""
Collection Questionnaire and Response Handlers
ADCS: Questionnaire generation and response processing handlers

Provides handler functions for questionnaire generation and response processing operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from .base import CollectionHandlerBase, get_question_template

logger = logging.getLogger(__name__)


class QuestionnaireHandlers(CollectionHandlerBase):
    """Handlers for questionnaire generation and response processing"""

    async def questionnaire_generation(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate questionnaires for manual collection"""
        try:
            logger.info("📝 Generating questionnaires for manual collection")

            # Get collection flow and gaps
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Query gaps that need manual collection
            gaps_query = """
                SELECT id, gap_type, field_name, description, priority, suggested_resolution
                FROM collection_data_gaps
                WHERE collection_flow_id = :collection_flow_id
                AND resolution_status = 'pending'
                ORDER BY priority DESC
            """

            result = await db.execute(
                gaps_query, {"collection_flow_id": collection_flow["id"]}
            )
            gaps = result.fetchall()

            # Generate questions based on gaps
            questions_generated = 0
            for gap in gaps:
                # Create questionnaire based on gap type
                question_template = get_question_template(gap.gap_type)

                question_data = {
                    "id": uuid.uuid4(),
                    "collection_flow_id": collection_flow["id"],
                    "gap_id": gap.id,
                    "questionnaire_type": "gap_resolution",
                    "question_category": gap.gap_type,
                    "question_id": f"gap_{gap.id}",
                    "question_text": question_template.format(
                        field_name=gap.field_name, description=gap.description
                    ),
                    "response_type": "structured",
                    "metadata": {
                        "priority": gap.priority,
                        "suggested_resolution": gap.suggested_resolution,
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }

                insert_query = """
                    INSERT INTO collection_questionnaire_responses
                    (id, collection_flow_id, gap_id, questionnaire_type, question_category,
                     question_id, question_text, response_type, metadata, created_at, updated_at)
                    VALUES
                    (:id, :collection_flow_id, :gap_id, :questionnaire_type, :question_category,
                     :question_id, :question_text, :response_type, :metadata::jsonb, :created_at, :updated_at)
                """

                await db.execute(insert_query, question_data)
                questions_generated += 1

            await db.commit()

            return {
                "success": True,
                "questions_generated": questions_generated,
                "gaps_addressed": len(gaps),
            }

        except Exception as e:
            logger.error(f"❌ Questionnaire generation failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def response_processing(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process questionnaire responses"""
        try:
            crew_results = phase_results.get("crew_results", {})
            responses = crew_results.get("responses", {})

            logger.info(f"✅ Processing {len(responses)} questionnaire responses")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Update questionnaire responses
            for gap_id, response in responses.items():
                update_query = """
                    UPDATE collection_questionnaire_responses
                    SET response_value = :response_value::jsonb,
                        confidence_score = :confidence_score,
                        validation_status = :validation_status,
                        responded_by = :responded_by,
                        responded_at = :responded_at,
                        updated_at = :updated_at
                    WHERE collection_flow_id = :collection_flow_id
                    AND gap_id = :gap_id
                """

                await db.execute(
                    update_query,
                    {
                        "response_value": response.get("value", {}),
                        "confidence_score": response.get("confidence", 0.0),
                        "validation_status": (
                            "validated"
                            if response.get("is_valid", False)
                            else "pending"
                        ),
                        "responded_by": context["user_id"],
                        "responded_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "collection_flow_id": collection_flow["id"],
                        "gap_id": gap_id,
                    },
                )

                # Update gap resolution status
                if response.get("is_valid", False):
                    gap_update_query = """
                        UPDATE collection_data_gaps
                        SET resolution_status = 'resolved',
                            resolved_at = :resolved_at,
                            resolved_by = 'manual_collection'
                        WHERE id = :gap_id
                    """

                    await db.execute(
                        gap_update_query,
                        {"resolved_at": datetime.utcnow(), "gap_id": gap_id},
                    )

            await db.commit()

            # Apply resolved gaps to assets (always on)
            try:
                from .asset_handlers import asset_handlers

                await asset_handlers.apply_resolved_gaps_to_assets(
                    db, collection_flow["id"], context
                )
            except Exception as e:
                logger.error(f"❌ Write-back of resolved gaps failed: {e}")

            return {
                "success": True,
                "responses_processed": len(responses),
                "gaps_resolved": len(
                    [r for r in responses.values() if r.get("is_valid", False)]
                ),
            }

        except Exception as e:
            logger.error(f"❌ Response processing failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
questionnaire_handlers = QuestionnaireHandlers()


# Export functions for backward compatibility
async def questionnaire_generation(*args, **kwargs):
    return await questionnaire_handlers.questionnaire_generation(*args, **kwargs)


async def response_processing(*args, **kwargs):
    return await questionnaire_handlers.response_processing(*args, **kwargs)
