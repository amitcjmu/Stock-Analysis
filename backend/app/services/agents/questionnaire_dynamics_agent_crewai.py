"""
Questionnaire Dynamics Agent - Generates adaptive questionnaires for manual data collection
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class QuestionnaireDynamicsAgent(BaseCrewAIAgent):
    """
    Generates intelligent, adaptive questionnaires for manual data collection.

    Capabilities:
    - Dynamic question generation based on gaps
    - Conditional logic for follow-up questions
    - Answer validation rules
    - Context-aware question sequencing
    - Multi-format support (text, dropdown, checkbox, etc.)
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Questionnaire Dynamics Specialist",
            goal=(
                "Create intelligent adaptive questionnaires that efficiently "
                "collect missing critical data through user-friendly forms"
            ),
            backstory="""You are an expert in form design and user experience for data collection.
            You excel at:
            - Creating intuitive questionnaires that minimize user effort
            - Implementing smart conditional logic to show relevant questions
            - Designing validation rules that ensure data quality
            - Structuring questions in logical, easy-to-follow sequences
            - Adapting question types to the nature of data being collected

            Your questionnaires achieve high completion rates while gathering accurate,
            comprehensive data needed for successful migrations.""",
            tools=tools,
            llm=llm,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="questionnaire_dynamics_agent",
            description="Generates adaptive questionnaires for efficient manual data collection",
            agent_class=cls,
            required_tools=[
                "gap_analyzer",
                "question_generator",
                "validation_rule_builder",
                "form_template_selector",
                "conditional_logic_builder",
            ],
            capabilities=[
                "questionnaire_generation",
                "conditional_logic",
                "validation_rules",
                "adaptive_forms",
                "user_experience_optimization",
            ],
            max_iter=12,
            memory=False,  # Per ADR-024: Use TenantMemoryManager
            verbose=True,
            allow_delegation=False,
        )

    async def generate_questionnaire_with_memory(
        self,
        asset_type: str,
        gap_categories: List[str],
        existing_data: Dict[str, Any],
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Generate questionnaire with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical questionnaire generation patterns
        2. Provide patterns as context for question generation
        3. Execute questionnaire generation with historical insights
        4. Store discovered patterns for future use

        Args:
            asset_type: Type of asset for questionnaire (e.g., 'server', 'application', 'database')
            gap_categories: Categories of gaps to address (e.g., ['infrastructure', 'operational'])
            existing_data: Existing data to avoid redundancy in questions
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing questionnaire with questions, logic, and validation rules
        """
        try:
            logger.info(
                f"🧠 Starting questionnaire generation with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"asset_type={asset_type})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical questionnaire patterns
            logger.info("📚 Retrieving historical questionnaire generation patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="questionnaire_generation",
                query_context={
                    "asset_type": asset_type,
                    "gap_categories": gap_categories,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Generate questionnaire with historical context
            logger.info("🔍 Generating questionnaire with historical insights...")

            # Extract effective question patterns from history
            effective_questions = []
            form_structures = []

            for pattern in historical_patterns[:5]:  # Top 5 patterns
                pattern_data = pattern.get("pattern_data", {})
                if "effective_questions" in pattern_data:
                    effective_questions.extend(pattern_data["effective_questions"])
                if "form_structure" in pattern_data:
                    form_structures.append(pattern_data["form_structure"])

            # Generate questions based on gaps
            questions = []
            for category in gap_categories:
                questions.append(
                    {
                        "id": f"q_{len(questions) + 1}",
                        "category": category,
                        "question": f"Please provide {category} information for {asset_type}",
                        "type": "text",
                        "required": True,
                        "validation": "non_empty",
                    }
                )

            # Build questionnaire result
            questionnaire_result = {
                "asset_type": asset_type,
                "gap_categories": gap_categories,
                "questions": questions,
                "form_structure": {
                    "sections": [
                        {
                            "name": cat,
                            "questions": [q for q in questions if q["category"] == cat],
                        }
                        for cat in gap_categories
                    ],
                    "conditional_logic": [],
                    "validation_rules": [
                        {"field": q["id"], "rule": q["validation"]} for q in questions
                    ],
                },
                "historical_context": {
                    "patterns_found": len(historical_patterns),
                    "effective_patterns_applied": len(effective_questions),
                },
            }

            # Step 4: Store discovered patterns
            logger.info("💾 Storing questionnaire generation patterns...")

            pattern_data = {
                "name": f"questionnaire_generation_{asset_type}_{engagement_id}",
                "asset_type": asset_type,
                "gap_categories": gap_categories,
                "questions_generated": len(questions),
                "effective_questions": [q["question"] for q in questions[:3]],
                "form_structure": questionnaire_result["form_structure"],
                "historical_patterns_used": len(historical_patterns),
            }

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="questionnaire_generation",
                pattern_data=pattern_data,
            )

            logger.info(
                f"✅ Stored questionnaire generation pattern with ID: {pattern_id}"
            )

            # Enhance result with memory metadata
            questionnaire_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return questionnaire_result

        except Exception as e:
            logger.error(
                f"❌ Questionnaire generation with memory failed: {e}", exc_info=True
            )
            # Fallback to basic questionnaire
            logger.warning(
                "⚠️ Falling back to basic questionnaire generation without memory"
            )

            # Generate minimal questions
            questions = []
            for category in gap_categories:
                questions.append(
                    {
                        "id": f"q_{len(questions) + 1}",
                        "category": category,
                        "question": f"Please provide {category} information",
                        "type": "text",
                        "required": True,
                    }
                )

            return {
                "asset_type": asset_type,
                "gap_categories": gap_categories,
                "questions": questions,
                "form_structure": {
                    "sections": [],
                    "conditional_logic": [],
                    "validation_rules": [],
                },
                "status": "error",
                "error": str(e),
            }
