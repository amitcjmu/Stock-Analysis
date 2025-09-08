"""
Questionnaire Generator Package - Modularized

This package provides AI-powered adaptive questionnaire generation for data gap resolution.
All imports are maintained for backward compatibility.
"""

# Import enums
from .enums import QuestionPriority, QuestionType

# Import agents manager
from .agents import QuestionnaireAgentManager

# Import tasks manager
from .tasks import QuestionnaireTaskManager

# Import utility functions
from .utils import (
    assess_business_alignment,
    assess_data_quality,
    assess_deployment_readiness,
    assess_question_quality,
    assess_user_experience,
    create_deployment_package,
    generate_optimization_suggestions,
    identify_integration_requirements,
    parse_text_results,
)

# Import service classes
from .service import QuestionnaireProcessor, QuestionnaireService

# Main class for backward compatibility
try:
    from crewai import Process
    from app.services.crews.base_crew import BaseDiscoveryCrew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Process = object
    BaseDiscoveryCrew = object

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AdaptiveQuestionnaireGenerator(BaseDiscoveryCrew):
    """
    AI-powered adaptive questionnaire generator using CrewAI framework.

    Main class maintained for backward compatibility.
    """

    def __init__(self):
        """Initialize questionnaire generation crew"""
        if CREWAI_AVAILABLE:
            super().__init__(
                name="questionnaire_generation_crew",
                description="AI-powered adaptive questionnaire generation for data gap resolution",
                process=Process.sequential,
                verbose=True,
                memory=True,
                cache=True,
            )
        else:
            # Fallback initialization when CrewAI is not available
            self.name = "questionnaire_generation_crew"
            self.description = (
                "AI-powered adaptive questionnaire generation for data gap resolution"
            )
            self.verbose = True

        # Initialize modular components
        self.agent_manager = QuestionnaireAgentManager(getattr(self, "llm", None))
        self.agents = self.agent_manager.create_agents()
        self.task_manager = QuestionnaireTaskManager(self.agents)
        self.processor = QuestionnaireProcessor(self.agents, [], self.name)
        self.service = QuestionnaireService(self.processor)

    def create_agents(self) -> List[Any]:
        """Create specialized AI agents for questionnaire generation"""
        return self.agent_manager.create_agents()

    def create_tasks(self, inputs: Dict[str, Any]) -> List[Any]:
        """Create questionnaire generation tasks"""
        tasks = self.task_manager.create_tasks(inputs)
        self.processor.tasks = tasks
        return tasks

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process questionnaire generation results"""
        return self.processor.process_results(raw_results)

    async def generate_questionnaires(
        self,
        data_gaps: List[Dict[str, Any]],
        business_context: Optional[Dict[str, Any]] = None,
        automation_tier: str = "tier_2",
        collection_flow_id: Optional[str] = None,
        stakeholder_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate questionnaires based on identified data gaps"""
        return await self.service.generate_questionnaires(
            data_gaps,
            business_context,
            automation_tier,
            collection_flow_id,
            stakeholder_context,
        )


# High-level function for backward compatibility
async def generate_adaptive_questionnaire(
    gap_analysis: Dict[str, Any],
    collection_flow_id: UUID,
    business_context: Optional[Dict[str, Any]] = None,
    stakeholder_context: Optional[Dict[str, Any]] = None,
    automation_tier: str = "tier_2",
) -> Dict[str, Any]:
    """
    High-level function to generate adaptive questionnaire using AI agents.
    """
    try:
        # Initialize questionnaire generator
        questionnaire_generator = AdaptiveQuestionnaireGenerator()

        # Prepare generation inputs
        generation_inputs = {
            "gap_analysis": gap_analysis,
            "collection_flow_id": str(collection_flow_id),
            "business_context": business_context or {},
            "stakeholder_context": stakeholder_context or {},
            "automation_tier": automation_tier,
        }

        # For now, return mock results since we're not using full CrewAI
        logger.info(
            f"Starting questionnaire generation for collection flow: {collection_flow_id}"
        )

        # Create tasks to initialize the processor properly
        questionnaire_generator.create_tasks(generation_inputs)

        # Process mock results
        mock_results = {
            "questionnaire_metadata": {
                "id": f"questionnaire-{collection_flow_id}",
                "title": "Migration Data Collection Questionnaire",
                "estimated_duration_minutes": 20,
            },
            "questionnaire_sections": [],
            "adaptive_logic": {},
            "completion_criteria": {},
        }

        result = questionnaire_generator.process_results(mock_results)

        logger.info(
            f"Questionnaire generation completed for collection flow: {collection_flow_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to generate adaptive questionnaire: {e}")
        return {
            "crew_name": "questionnaire_generation_crew",
            "status": "error",
            "error": str(e),
            "questionnaire": {"metadata": {"error": True}},
            "metadata": {"generation_timestamp": "2025-01-01T00:00:00Z"},
        }


# Export all public interfaces for backward compatibility
__all__ = [
    "AdaptiveQuestionnaireGenerator",
    "QuestionType",
    "QuestionPriority",
    "QuestionnaireAgentManager",
    "QuestionnaireTaskManager",
    "QuestionnaireProcessor",
    "QuestionnaireService",
    "generate_adaptive_questionnaire",
    # Utility functions
    "assess_business_alignment",
    "assess_data_quality",
    "assess_deployment_readiness",
    "assess_question_quality",
    "assess_user_experience",
    "create_deployment_package",
    "generate_optimization_suggestions",
    "identify_integration_requirements",
    "parse_text_results",
]
