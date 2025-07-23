"""
Utility Functions for Collection Flow

This module contains helper functions used across the collection flow.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.models.collection_flow import (AdaptiveQuestionnaire, AutomationTier,
                                        CollectionPhase)

logger = logging.getLogger(__name__)


def requires_user_approval(phase: str, client_requirements: Dict[str, Any]) -> bool:
    """Check if phase requires user approval"""
    approval_phases = client_requirements.get("approval_required_phases", [])
    return phase in approval_phases


def get_available_adapters() -> Dict[str, Any]:
    """Get available platform adapters"""
    # This would interface with the adapter registry
    from app.services.collection_flow.adapters import adapter_registry

    return {
        adapter_type: adapter_registry.get_adapter(adapter_type)
        for adapter_type in adapter_registry.list_adapters()
    }


def get_previous_phase(current_phase: CollectionPhase) -> Optional[CollectionPhase]:
    """Get the previous phase in sequence"""
    phase_order = [
        CollectionPhase.INITIALIZATION,
        CollectionPhase.PLATFORM_DETECTION,
        CollectionPhase.AUTOMATED_COLLECTION,
        CollectionPhase.GAP_ANALYSIS,
        CollectionPhase.QUESTIONNAIRE_GENERATION,
        CollectionPhase.MANUAL_COLLECTION,
        CollectionPhase.DATA_VALIDATION,
        CollectionPhase.FINALIZATION,
    ]

    try:
        current_index = phase_order.index(current_phase)
        if current_index > 0:
            return phase_order[current_index - 1]
    except ValueError:
        pass

    return None


def extract_questions_from_sections(
    sections: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract all questions from questionnaire sections"""
    questions = []
    for section in sections:
        questions.extend(section.get("questions", []))
    return questions


def extract_gap_categories(sections: List[Dict[str, Any]]) -> List[str]:
    """Extract gap categories from questionnaire sections"""
    categories = set()
    for section in sections:
        for question in section.get("questions", []):
            gap_resolution = question.get("gap_resolution", {})
            if gap_resolution.get("addresses_gap"):
                categories.add(gap_resolution["addresses_gap"])
    return list(categories)


async def save_questionnaires_to_db(
    questionnaires: List[Dict[str, Any]],
    flow_context,
    flow_id: str,
    automation_tier: AutomationTier,
    detected_platforms: List[str],
) -> List[Dict[str, Any]]:
    """Save generated questionnaires to database"""
    try:
        if not flow_context.db_session:
            logger.warning("No database session available for saving questionnaires")
            return questionnaires

        saved_questionnaires = []

        for questionnaire_data in questionnaires:
            # Extract questionnaire metadata from the generated data
            metadata = questionnaire_data.get("questionnaire", {}).get("metadata", {})
            sections = questionnaire_data.get("questionnaire", {}).get("sections", [])

            # Create questionnaire instance
            questionnaire = AdaptiveQuestionnaire(
                client_account_id=uuid.UUID(flow_context.client_account_id),
                engagement_id=uuid.UUID(flow_context.engagement_id),
                collection_flow_id=uuid.UUID(flow_id),
                title=metadata.get("title", "Adaptive Data Collection Questionnaire"),
                description=metadata.get(
                    "description", "AI-generated questionnaire for gap resolution"
                ),
                template_name=metadata.get("id", f"questionnaire-{flow_id}"),
                template_type="adaptive_collection",
                version=metadata.get("version", "1.0"),
                applicable_tiers=[automation_tier.value],
                question_set=questionnaire_data.get("questionnaire", {}),
                questions=extract_questions_from_sections(sections),
                question_count=metadata.get("total_questions", 0),
                estimated_completion_time=metadata.get(
                    "estimated_duration_minutes", 20
                ),
                target_gaps=questionnaire_data.get("questionnaire", {}).get(
                    "target_gaps", []
                ),
                gap_categories=extract_gap_categories(sections),
                platform_types=detected_platforms,
                data_domains=["collection", "migration_readiness"],
                scoring_rules=questionnaire_data.get("questionnaire", {}).get(
                    "completion_criteria", {}
                ),
                validation_rules=questionnaire_data.get("questionnaire", {}).get(
                    "adaptive_logic", {}
                ),
                completion_status="pending",
                is_template=False,  # This is an instance, not a template
            )

            # Save to database
            flow_context.db_session.add(questionnaire)

            # Add ID to questionnaire data for reference
            questionnaire_data["db_id"] = str(questionnaire.id)
            saved_questionnaires.append(questionnaire_data)

        # Commit all questionnaires
        await flow_context.db_session.commit()

        logger.info(
            f"✅ Saved {len(saved_questionnaires)} questionnaires to database for flow {flow_id}"
        )

        return saved_questionnaires

    except Exception as e:
        logger.error(f"Failed to save questionnaires to database: {e}")
        if flow_context.db_session:
            await flow_context.db_session.rollback()
        # Return original questionnaires even if save fails
        return questionnaires
