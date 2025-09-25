"""
Questionnaire Service Handlers
Main questionnaire generation service classes.
"""

import logging
from typing import Any, Dict, List, Optional

from .processors import QuestionnaireProcessor

logger = logging.getLogger(__name__)


class QuestionnaireService:
    """Main questionnaire generation service"""

    def __init__(self, processor: QuestionnaireProcessor, crew_instance=None):
        self.processor = processor
        self.crew_instance = crew_instance

    async def generate_questionnaires(
        self,
        data_gaps: List[Dict[str, Any]],
        business_context: Optional[Dict[str, Any]] = None,
        automation_tier: str = "tier_2",
        collection_flow_id: Optional[str] = None,
        stakeholder_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate questionnaires based on identified data gaps.

        Args:
            data_gaps: List of identified data gaps
            business_context: Business context information
            automation_tier: Automation tier (tier_1, tier_2, tier_3, tier_4)
            collection_flow_id: ID of the collection flow
            stakeholder_context: Stakeholder context information

        Returns:
            List of generated questionnaire sections
        """
        try:
            if not self.crew_instance:
                logger.warning("No crew instance available, using fallback generation")
                return self._generate_fallback_questionnaires(
                    data_gaps, business_context
                )

            # Prepare inputs for crew execution
            crew_inputs = self._prepare_crew_inputs(
                data_gaps,
                business_context,
                automation_tier,
                collection_flow_id,
                stakeholder_context,
            )

            # Execute crew to generate questionnaires
            logger.info("Executing crew for questionnaire generation")
            raw_results = await self.crew_instance.kickoff_async(inputs=crew_inputs)

            # Process results
            processed_results = self.processor.process_results(raw_results)

            # Extract questionnaires from processed results
            questionnaires = processed_results.get("sections", [])

            logger.info(f"Generated {len(questionnaires)} questionnaire sections")
            return questionnaires

        except Exception as e:
            logger.error(f"Error generating questionnaires: {e}")
            return self._generate_fallback_questionnaires(data_gaps, business_context)

    def _prepare_crew_inputs(
        self,
        data_gaps: List[Dict[str, Any]],
        business_context: Optional[Dict[str, Any]],
        automation_tier: str,
        collection_flow_id: Optional[str],
        stakeholder_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare inputs for crew execution."""
        return {
            "data_gaps": data_gaps,
            "business_context": business_context or {},
            "automation_tier": automation_tier,
            "collection_flow_id": collection_flow_id,
            "stakeholder_context": stakeholder_context or {},
            "task_description": f"Generate adaptive questionnaires for {len(data_gaps)} data gaps",
        }

    def _generate_fallback_questionnaires(
        self,
        data_gaps: List[Dict[str, Any]],
        business_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate fallback questionnaires when crew execution fails."""
        logger.info("Using fallback questionnaire generation")

        # Simple fallback questionnaire generation
        fallback_sections = []

        if data_gaps:
            # Create a basic questionnaire section
            questions = []
            for i, gap in enumerate(data_gaps[:10]):  # Limit to first 10 gaps
                questions.append(
                    {
                        "field_id": f"gap_{i}_{gap.get('gap_type', 'unknown')}",
                        "question_text": f"Please provide information about {gap.get('description', 'missing data')}",
                        "field_type": "textarea",
                        "required": gap.get("priority", "low") in ["high", "critical"],
                        "category": gap.get("gap_type", "general"),
                        "help_text": f"This information is needed to address: {gap.get('description', 'data gap')}",
                        "priority": gap.get("priority", "medium"),
                        "metadata": gap,
                    }
                )

            fallback_sections.append(
                {
                    "section_id": "fallback_section_1",
                    "section_title": "Data Gap Resolution Questionnaire",
                    "section_description": (
                        "Please provide the following information to help resolve identified data gaps"
                    ),
                    "questions": questions,
                    "validation_rules": {},
                    "metadata": {
                        "generated_by": "fallback_generator",
                        "total_gaps_addressed": len(questions),
                    },
                }
            )

        return fallback_sections
