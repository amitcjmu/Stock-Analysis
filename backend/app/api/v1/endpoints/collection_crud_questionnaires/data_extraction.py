"""
Data extraction utilities for collection questionnaires.
Functions for extracting and processing agent-generated questionnaire data.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

logger = logging.getLogger(__name__)


def _try_extract_from_wrapper(agent_result: dict, key: str) -> Optional[dict]:
    """Try to extract data from common wrapper keys."""
    wrapper_data = agent_result.get(key, {})
    if isinstance(wrapper_data, dict):
        return wrapper_data
    return None


def _find_questionnaires_in_result(agent_result: dict) -> Tuple[list, list]:
    """Find questionnaire or section data in agent result. Returns (questionnaires_data, sections_data)"""

    def get_data(source, q_key="questionnaires", s_key="sections"):
        return source.get(q_key, []), source.get(s_key, [])

    q_data, s_data = get_data(agent_result)
    if q_data or s_data:
        return q_data, s_data

    for wrapper_key in ["result", "data"]:
        wrapper = _try_extract_from_wrapper(agent_result, wrapper_key)
        if wrapper:
            q_data, s_data = get_data(wrapper)
            if q_data or s_data:
                return q_data, s_data

    if forms := agent_result.get("forms", []):
        return forms, []

    if items := agent_result.get("items", []):
        return [], [{"questions": items, "section_title": "Data Collection"}]

    return [], []


def _extract_from_agent_output(agent_result: dict) -> Optional[list]:
    """Extract sections from agent_output field."""
    import json
    import re

    agent_output = agent_result.get("agent_output", {})

    # CRITICAL FIX: agent_output can be a JSON STRING, parse it first
    if isinstance(agent_output, str):
        try:
            # FIX 0.7 (QA Bug #3): Agent returns Python booleans (True/False) instead of JSON (true/false)
            # Replace Python booleans with JSON booleans before parsing
            agent_output_fixed = re.sub(r"\bTrue\b", "true", agent_output)
            agent_output_fixed = re.sub(r"\bFalse\b", "false", agent_output_fixed)
            agent_output = json.loads(agent_output_fixed)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse agent_output as JSON: {str(e)[:100]} - {agent_output[:200]}"
            )
            return None

    if not isinstance(agent_output, dict):
        return None

    # FIX 0.7 (QA Bug #3): Check for both "questionnaire" (singular) and "questionnaires" (plural)
    # Agent may return either format
    questionnaires = agent_output.get("questionnaires") or agent_output.get(
        "questionnaire", []
    )
    if questionnaires:
        return questionnaires

    sections = agent_output.get("sections", [])
    if sections:
        return sections

    # Check result.sections in agent_output
    result_data = _try_extract_from_wrapper(agent_output, "result")
    if result_data:
        sections = result_data.get("sections", [])
        if sections:
            return sections

    return None


def _generate_from_gap_analysis(agent_result: dict) -> Optional[list]:
    """Generate questionnaire sections from gap_analysis data."""
    processed = agent_result.get("processed_data", {})
    if not isinstance(processed, dict):
        return None

    gap_analysis = processed.get("gap_analysis")
    if not gap_analysis or not isinstance(gap_analysis, dict):
        return None

    logger.info("Generating questionnaire from gap_analysis data")
    questions = []
    for asset_id, fields in gap_analysis.get("missing_critical_fields", {}).items():
        for field in fields:
            questions.append(
                {
                    "field_id": field,
                    "question_text": f"Please provide {field.replace('_', ' ').title()}",
                    "field_type": "text",
                    "required": True,
                    "category": "critical_field",
                    "metadata": {"asset_id": asset_id},
                }
            )

    return (
        [
            {
                "section_id": "gap_resolution",
                "section_title": "Data Gap Resolution",
                "section_description": "Please provide missing critical information",
                "questions": questions,
            }
        ]
        if questions
        else None
    )


def _extract_questionnaire_data(
    agent_result: dict, flow_id: str
) -> List[AdaptiveQuestionnaireResponse]:
    """Extract and convert questionnaire data from agent results."""
    logger.info(f"Agent result keys: {list(agent_result.keys())}")

    # Try to find questionnaire data using helper functions
    questionnaires_data, sections_data = _find_questionnaires_in_result(agent_result)

    # Determine which data to process
    # CRITICAL: Fallback disabled to diagnose LLM flow issues
    # If this fails, we need to fix the agent's LLM output, not mask with fallback
    data_to_process = (
        questionnaires_data
        or sections_data
        or _extract_from_agent_output(agent_result)
        # FALLBACK DISABLED: or _generate_from_gap_analysis(agent_result)
    )

    if not data_to_process:
        logger.warning(
            f"No questionnaire data found. Keys: {list(agent_result.keys())}"
        )
        raise Exception("Agent returned success but no questionnaire data")

    # Convert agent results to AdaptiveQuestionnaireResponse format
    result = []
    for idx, section in enumerate(data_to_process):
        if not isinstance(section, dict) or not section.get("questions"):
            continue

        questionnaire = AdaptiveQuestionnaireResponse(
            id=section.get("section_id", f"agent-{idx}-{flow_id}"),
            collection_flow_id=str(flow_id),
            title=section.get("section_title", "AI-Generated Data Gap Questionnaire"),
            description=section.get(
                "section_description",
                "Generated by AI agent to resolve identified data gaps",
            ),
            target_gaps=[
                "missing_critical_fields",
                "unmapped_attributes",
                "data_quality_issues",
            ],
            questions=section["questions"],
            validation_rules=section.get("validation_rules", {}),
            completion_status="pending",
            responses_collected={},
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        result.append(questionnaire)

    if not result:
        raise Exception("No valid questionnaires generated from agent result")

    logger.info(
        f"Successfully generated {len(result)} questionnaires using persistent agent"
    )
    return result
