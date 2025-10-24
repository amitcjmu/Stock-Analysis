"""
Dynamic Question Engine

Filters questions by asset type with CrewAI agent pruning and TenantMemoryManager integration.
Per Issue #775 and design doc Section 6.2.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    CollectionQuestionRules,
    CollectionAnswerHistory,
)
from app.repositories.context_aware_repository import ContextAwareRepository
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class FilteredQuestions:
    """Result from question filtering operation."""

    def __init__(
        self,
        questions: List[Dict[str, Any]],
        agent_status: str,
        fallback_used: bool,
    ):
        self.questions = questions
        self.agent_status = agent_status
        self.fallback_used = fallback_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "questions": self.questions,
            "agent_status": self.agent_status,
            "fallback_used": self.fallback_used,
        }


class DynamicQuestionEngine:
    """
    Service for dynamic question filtering by asset type.

    Provides:
    - Asset-type-specific question filtering
    - Inheritance rule application
    - Optional CrewAI agent pruning
    - Dependency change handling with re-emergence
    """

    # Critical fields that always trigger re-emergence on change
    CRITICAL_FIELDS = [
        "os_version",
        "ip_address",
        "decommission_status",
        "hosting_platform",
        "database_type",
    ]

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
    ):
        """
        Initialize dynamic question engine.

        Args:
            db: Async database session
            context: Request context with client_account_id, engagement_id
        """
        self.db = db
        self.context = context

        # Context-aware repositories
        self.question_rules_repo = ContextAwareRepository(
            db, CollectionQuestionRules, context
        )
        self.questionnaire_repo = ContextAwareRepository(
            db, AdaptiveQuestionnaire, context
        )
        self.answer_history_repo = ContextAwareRepository(
            db, CollectionAnswerHistory, context
        )

    async def get_filtered_questions(
        self,
        child_flow_id: UUID,
        asset_id: UUID,
        asset_type: str,
        include_answered: bool = False,
        refresh_agent_analysis: bool = False,
    ) -> FilteredQuestions:
        """
        Return questions applicable to this asset type.

        Args:
            child_flow_id: Collection child flow UUID
            asset_id: Asset UUID
            asset_type: Asset type (Application, Server, Database, etc.)
            include_answered: If False, filter out already-answered questions
            refresh_agent_analysis: If True, use agent pruning

        Returns:
            Filtered questions with agent status
        """
        # Step 1: Get base questions from DB rules
        base_questions = await self._get_db_questions(asset_type)

        # Step 2: Apply inheritance rules
        questions = await self._apply_inheritance(base_questions, asset_type)

        # Step 3: Agent-based pruning (if requested)
        agent_status = "not_requested"
        fallback_used = False

        if refresh_agent_analysis:
            try:
                # IMPORTANT: Uses multi_model_service for LLM tracking (per CLAUDE.md)
                agent_result = await asyncio.wait_for(
                    self._prune_questions_with_agent(asset_id, asset_type, questions),
                    timeout=30,
                )
                questions = agent_result
                agent_status = "completed"
                fallback_used = False

                logger.info(
                    f"✅ Agent pruning completed for asset {asset_id} ({asset_type})"
                )

            except asyncio.TimeoutError:
                # Graceful degradation
                logger.warning(f"⚠️  Agent pruning timeout for asset {asset_id}")
                agent_status = "fallback"
                fallback_used = True

            except Exception as e:
                logger.error(f"❌ Agent pruning failed for asset {asset_id}: {e}")
                agent_status = "fallback"
                fallback_used = True

        # Step 4: Filter out answered questions (if requested)
        if not include_answered:
            questionnaire = await self._get_questionnaire(child_flow_id, asset_id)
            if questionnaire and questionnaire.closed_questions:
                questions = [
                    q
                    for q in questions
                    if q["question_id"] not in questionnaire.closed_questions
                ]

        return FilteredQuestions(
            questions=questions,
            agent_status=agent_status,
            fallback_used=fallback_used,
        )

    async def handle_dependency_change(
        self,
        changed_asset_id: UUID,
        changed_field: str,
        old_value: Any,
        new_value: Any,
    ) -> List[str]:
        """
        Detect which questions should reopen due to dependency change.

        Args:
            changed_asset_id: Asset UUID that changed
            changed_field: Field name that changed
            old_value: Previous value
            new_value: New value

        Returns:
            List of question IDs to reopen
        """
        # Check if this is a critical field
        if changed_field in self.CRITICAL_FIELDS:
            # Fallback: Always reopen dependent questions
            logger.info(
                f"🔄 Critical field '{changed_field}' changed on asset {changed_asset_id} "
                f"from '{old_value}' to '{new_value}' - reopening dependent questions"
            )
            return await self._reopen_dependent_questions_fallback(
                changed_asset_id, changed_field
            )

        # Otherwise, use agent analysis
        try:
            agent = await TenantScopedAgentPool.get_agent(
                self.context, "dependency_analyzer", service_registry=None
            )

            task_description = f"""
            Analyze dependency impact for field change:

            Asset ID: {changed_asset_id}
            Changed Field: {changed_field}
            Old Value: {old_value}
            New Value: {new_value}

            Determine which questions should be reopened due to this change.
            Return a list of question IDs that are affected by this dependency change.
            """

            # Execute agent analysis
            if hasattr(agent, "execute_async"):
                result = await agent.execute_async(inputs={"task": task_description})
            else:
                result = agent.execute(task=task_description)

            affected_question_ids = self._parse_agent_result(result)

            # Reopen questions
            await self._batch_reopen_questions(
                changed_asset_id,
                affected_question_ids,
                reason=f"Dependency change: {changed_field} changed from {old_value} to {new_value}",
            )

            logger.info(
                f"✅ Agent analysis identified {len(affected_question_ids)} questions to reopen"
            )
            return affected_question_ids

        except Exception as e:
            logger.error(f"❌ Agent dependency analysis failed: {e}")
            # Fallback to critical field logic
            return await self._reopen_dependent_questions_fallback(
                changed_asset_id, changed_field
            )

    async def _get_db_questions(self, asset_type: str) -> List[Dict[str, Any]]:
        """Get base questions from database rules."""
        rules = await self.question_rules_repo.get_by_filters(
            asset_type=asset_type, is_applicable=True
        )

        return [
            {
                "question_id": rule.question_id,
                "question_text": rule.question_text,
                "question_type": rule.question_type,
                "answer_options": rule.answer_options,
                "section": rule.section,
                "weight": rule.weight,
                "is_required": rule.is_required,
                "display_order": rule.display_order,
            }
            for rule in sorted(rules, key=lambda r: r.display_order or 0)
        ]

    async def _apply_inheritance(
        self, base_questions: List[Dict[str, Any]], asset_type: str
    ) -> List[Dict[str, Any]]:
        """
        Apply inheritance rules (placeholder for now).

        In future, this would check parent asset types and inherit questions.
        For now, just returns base questions.
        """
        # TODO: Implement inheritance logic when parent/child asset types are defined
        return base_questions

    async def _prune_questions_with_agent(
        self, asset_id: UUID, asset_type: str, questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use multi_model_service for automatic LLM cost tracking.

        Per CLAUDE.md: ALL LLM calls MUST use multi_model_service.generate_response()
        for automatic tracking to llm_usage_logs table.
        """
        question_list = "\n".join(
            [f"- {q['question_id']}: {q['question_text']}" for q in questions]
        )

        prompt = f"""
        Analyze which questions are truly relevant for {asset_type} asset {asset_id}.

        Current question list:
        {question_list}

        Return only the question IDs that are absolutely necessary for this asset type.
        Filter out redundant or inapplicable questions.

        Return format: Comma-separated question IDs
        """

        response = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="question_pruning",
            complexity=TaskComplexity.AGENTIC,  # Complex analysis requires Llama 4
        )

        # Parse response to get question IDs
        relevant_ids = self._parse_question_ids(response)

        # Filter questions by relevant IDs
        return [q for q in questions if q["question_id"] in relevant_ids]

    def _parse_question_ids(self, response: str) -> List[str]:
        """Parse comma-separated question IDs from LLM response."""
        # Simple parsing - can be enhanced
        return [qid.strip() for qid in response.split(",") if qid.strip()]

    def _parse_agent_result(self, result: Any) -> List[str]:
        """Parse agent result to extract affected question IDs."""
        # Handle different result formats
        if isinstance(result, list):
            return result
        elif isinstance(result, str):
            return self._parse_question_ids(result)
        elif hasattr(result, "output"):
            return self._parse_question_ids(result.output)
        else:
            logger.warning(f"Unknown agent result format: {type(result)}")
            return []

    async def _get_questionnaire(
        self, child_flow_id: UUID, asset_id: UUID
    ) -> Optional[AdaptiveQuestionnaire]:
        """Get questionnaire for asset."""
        questionnaires = await self.questionnaire_repo.get_by_filters(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
        )
        return questionnaires[0] if questionnaires else None

    async def _reopen_dependent_questions_fallback(
        self, changed_asset_id: UUID, changed_field: str
    ) -> List[str]:
        """
        Fallback logic for reopening questions when agent analysis fails.

        Uses hardcoded rules based on critical fields.
        """
        # Define field-to-question dependencies
        dependencies = {
            "os_version": ["tech_stack", "supported_versions", "patch_status"],
            "ip_address": ["network_zone", "firewall_rules", "dns_records"],
            "decommission_status": [
                "migration_priority",
                "dependency_count",
                "cutover_date",
            ],
            "hosting_platform": [
                "cloud_region",
                "instance_type",
                "auto_scaling",
            ],
            "database_type": ["db_version", "connection_string", "replication_mode"],
        }

        affected_questions = dependencies.get(changed_field, [])

        # Reopen these questions
        if affected_questions:
            await self._batch_reopen_questions(
                changed_asset_id,
                affected_questions,
                reason=f"Critical field change: {changed_field}",
            )

        return affected_questions

    async def _batch_reopen_questions(
        self,
        asset_id: UUID,
        question_ids: List[str],
        reason: str,
    ) -> None:
        """Reopen multiple questions and record in history."""
        questionnaires = await self.questionnaire_repo.get_by_filters(asset_id=asset_id)

        if not questionnaires:
            logger.warning(f"No questionnaire found for asset {asset_id}")
            return

        questionnaire = questionnaires[0]

        for question_id in question_ids:
            # Remove from closed_questions
            if (
                questionnaire.closed_questions
                and question_id in questionnaire.closed_questions
            ):
                questionnaire.closed_questions.remove(question_id)

            # Add to reopened_questions
            if questionnaire.reopened_questions is None:
                questionnaire.reopened_questions = []
            if question_id not in questionnaire.reopened_questions:
                questionnaire.reopened_questions.append(question_id)

            # Record in history
            await self.answer_history_repo.create_no_commit(
                questionnaire_id=questionnaire.id,
                asset_id=asset_id,
                question_id=question_id,
                reopened_reason=reason,
                reopened_by="agent_dependency_change",
                answer_value=None,  # Re-emergence, not a new answer
                answer_source="system",
            )

        logger.info(
            f"✅ Reopened {len(question_ids)} questions for asset {asset_id}: {reason}"
        )
