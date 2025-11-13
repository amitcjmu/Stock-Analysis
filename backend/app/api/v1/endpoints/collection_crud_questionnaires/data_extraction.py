"""
Data extraction utilities for collection questionnaires.
Functions for extracting and processing agent-generated questionnaire data.
"""

import ast
import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

logger = logging.getLogger(__name__)


def _parse_agent_output_string(raw: str) -> Optional[dict]:
    if not raw:
        return None

    candidate = raw.strip()
    if candidate.startswith("```json"):
        candidate = candidate[7:]
        if candidate.endswith("```"):
            candidate = candidate[:-3]
        candidate = candidate.strip()
    elif candidate.startswith("```"):
        candidate = candidate[3:]
        if candidate.endswith("```"):
            candidate = candidate[:-3]
        candidate = candidate.strip()

    literal_candidate = candidate
    candidate = re.sub(r"\bTrue\b", "true", candidate)
    candidate = re.sub(r"\bFalse\b", "false", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as json_err:
        logger.warning(f"⚠️ JSON parse failed: {str(json_err)[:200]}")
        try:
            result = ast.literal_eval(literal_candidate)
            logger.info("✅ ast.literal_eval succeeded as fallback")
            return result
        except (ValueError, SyntaxError) as ast_err:
            logger.error(
                "❌ Both JSON and ast.literal_eval failed. "
                f"JSON error: {str(json_err)[:100]}, "
                f"AST error: {str(ast_err)[:100]}"
            )
            return None


def _resolve_agent_output(agent_output) -> Optional[dict]:
    if isinstance(agent_output, dict):
        raw_text = agent_output.get("raw_text")
        if isinstance(raw_text, str):
            logger.info(f"🔍 Parsing raw_text of length: {len(raw_text)}")
            parsed = _parse_agent_output_string(raw_text)
            if isinstance(parsed, dict):
                logger.info(
                    f"✅ Successfully parsed raw_text, result keys: {list(parsed.keys())}"
                )
                return parsed
            else:
                logger.warning(
                    f"⚠️ Failed to parse raw_text, returned type: {type(parsed)}"
                )
        return agent_output

    if isinstance(agent_output, str):
        parsed = _parse_agent_output_string(agent_output)
        if isinstance(parsed, dict):
            return parsed
        return None

    return None


def _extract_sections_from_agent_output(agent_output: dict) -> Optional[list]:
    questionnaires = agent_output.get("questionnaires") or agent_output.get(
        "questionnaire", []
    )
    if questionnaires:
        return questionnaires

    sections = agent_output.get("sections", [])
    if sections:
        return sections

    result_data = _try_extract_from_wrapper(agent_output, "result")
    if result_data:
        sections = result_data.get("sections", [])
        if sections:
            return sections

    return None


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
    raw_agent_output = agent_result.get("agent_output", {})
    keys_info = (
        list(raw_agent_output.keys()) if isinstance(raw_agent_output, dict) else "N/A"
    )
    logger.info(
        f"🔍 Raw agent_output type: {type(raw_agent_output)}, keys: {keys_info}"
    )

    agent_output = _resolve_agent_output(raw_agent_output)
    has_sections = (
        agent_output.get("sections") if isinstance(agent_output, dict) else "N/A"
    )
    logger.info(
        f"🔍 Resolved agent_output type: {type(agent_output)}, "
        f"has sections: {has_sections}"
    )

    if not agent_output:
        logger.warning("⚠️ agent_output resolved to None")
        return None

    # BUG FIX #996: The agent_output now contains the parsed JSON from raw_text
    # Check if it directly has sections (which is the case after parsing raw_text)
    if isinstance(agent_output, dict) and agent_output.get("sections"):
        logger.info(
            f"✅ Found sections directly in parsed agent_output: {len(agent_output['sections'])} sections"
        )
        return agent_output["sections"]

    logger.info(
        "🔍 No sections found directly, " "trying _extract_sections_from_agent_output"
    )
    agent_result["agent_output"] = agent_output
    return _extract_sections_from_agent_output(agent_output)


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
    # BUG FIX #996: Use explicit empty-check to ensure _extract_from_agent_output is called
    # when questionnaires_data and sections_data are empty lists (not just falsy)
    data_to_process = (
        questionnaires_data
        if questionnaires_data
        else (
            sections_data if sections_data else _extract_from_agent_output(agent_result)
        )
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
