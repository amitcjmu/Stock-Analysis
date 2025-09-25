"""
Core Questionnaire Generator Service
Main service class combining processors and handlers.
"""

import logging
from typing import Any, Dict

from .processors import QuestionnaireProcessor
from .handlers import QuestionnaireService

logger = logging.getLogger(__name__)


class QuestionnaireGeneratorService:
    """
    High-level questionnaire generator service.
    Combines processors and handlers for complete questionnaire generation workflow.
    """

    def __init__(self):
        self.logger = logger

    async def generate_questionnaires(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate questionnaires from high-level inputs.

        Args:
            inputs: Dictionary containing generation inputs

        Returns:
            Dictionary containing generation results
        """
        try:
            data_gaps = inputs.get("data_gaps", [])
            business_context = inputs.get("business_context", {})
            automation_tier = inputs.get("automation_tier", "tier_2")
            collection_flow_id = inputs.get("collection_flow_id")

            # Create processor and service instances
            # Note: In the actual implementation, agents and tasks would be created here
            processor = QuestionnaireProcessor([], [], "questionnaire_generation")
            service = QuestionnaireService(processor)

            # Generate questionnaires
            questionnaires = await service.generate_questionnaires(
                data_gaps=data_gaps,
                business_context=business_context,
                automation_tier=automation_tier,
                collection_flow_id=collection_flow_id,
            )

            return {
                "status": "success",
                "questionnaires": questionnaires,
                "total_generated": len(questionnaires),
                "metadata": {
                    "automation_tier": automation_tier,
                    "collection_flow_id": collection_flow_id,
                },
            }

        except Exception as e:
            logger.error(f"Error in questionnaire generation service: {e}")
            return {
                "status": "error",
                "error": str(e),
                "questionnaires": [],
                "total_generated": 0,
            }
