"""
Utility functions for collection questionnaires.
Helper functions for data processing, field mapping, and analysis.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
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
    agent_output = agent_result.get("agent_output", {})
    if not isinstance(agent_output, dict):
        return None

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


def _get_selected_application_info(
    flow: CollectionFlow, existing_assets: List[Asset]
) -> tuple[Optional[str], Optional[str]]:
    """Extract selected application info from flow config."""
    if not (
        flow.collection_config
        and flow.collection_config.get("selected_application_ids")
    ):
        return None, None

    selected_app_ids = flow.collection_config["selected_application_ids"]
    if not selected_app_ids:
        return None, None

    selected_id = selected_app_ids[0]
    for asset in existing_assets:
        if str(asset.id) == selected_id:
            return asset.name or asset.application_name, selected_id
    return None, selected_id


def _convert_template_field_to_question(
    field: dict, selected_application_name: Optional[str] = None
) -> dict:
    """Convert a template field to a questionnaire question format."""
    question = {
        "field_id": field["field_id"],
        "question_text": field["question_text"],
        "field_type": field["field_type"],
        "required": field["required"],
        "category": field["category"],
        "options": field.get("options", []),
        "help_text": field.get("help_text", ""),
        "multiple": field.get("multiple", False),
        "metadata": field.get("metadata", {}),
    }

    if selected_application_name:
        question["metadata"]["asset_name"] = selected_application_name
        if field["field_id"] in ("application_name", "asset_name"):
            question["default_value"] = selected_application_name

    if field.get("default_value"):
        question["default_value"] = field["default_value"]

    return question


def _suggest_field_mapping(field_name: str) -> str:
    """Suggest potential mapping for unmapped field."""
    field_lower = field_name.lower()
    mappings = {
        "app": "application_name",
        "application": "application_name",
        "server": "hostname",
        "host": "hostname",
        "ip": "ip_address",
        "owner": "business_owner",
        "tech_owner": "technical_owner",
        "tech_lead": "technical_owner",
        "os": "operating_system",
        "env": "environment",
        "environment": "environment",
        "location": "location",
        "dc": "datacenter",
        "data_center": "datacenter",
        "cpu": "cpu_cores",
        "memory": "memory_gb",
        "ram": "memory_gb",
        "storage": "storage_gb",
        "disk": "storage_gb",
        "criticality": "criticality",
        "priority": "migration_priority",
        "complexity": "migration_complexity",
        "strategy": "six_r_strategy",
        "6r": "six_r_strategy",
    }
    for key, value in mappings.items():
        if key in field_lower:
            return value
    return "custom_attribute"


def _get_asset_raw_data_safely(asset, asset_id_str: str) -> tuple:
    """Safely extract raw_data and field_mappings from asset."""
    try:
        raw_data = getattr(asset, "raw_data", {}) or {}
        if not isinstance(raw_data, dict):
            logger.debug(
                f"Asset {asset_id_str} raw_data is {type(raw_data)}, using empty dict"
            )
            raw_data = {}

        field_mappings = getattr(asset, "field_mappings_used", {}) or {}
        if not isinstance(field_mappings, dict):
            logger.debug(
                f"Asset {asset_id_str} field_mappings is {type(field_mappings)}, using empty dict"
            )
            field_mappings = {}
    except Exception as e:
        logger.warning(f"Error processing asset {asset_id_str} data: {e}")
        raw_data = {}
        field_mappings = {}

    return raw_data, field_mappings


def _find_unmapped_attributes(raw_data: dict, field_mappings: dict) -> List[dict]:
    """Find unmapped attributes in raw data."""
    unmapped = []
    if raw_data:
        mapped_fields = set(field_mappings.values()) if field_mappings else set()
        for key, value in raw_data.items():
            if key not in mapped_fields and value:
                unmapped.append(
                    {
                        "field": key,
                        "value": str(value)[:100],  # Truncate long values
                        "potential_mapping": _suggest_field_mapping(key),
                    }
                )
    return unmapped


def _check_missing_critical_fields(asset) -> List[str]:
    """Check for missing critical fields using 22-attribute assessment system."""
    try:
        from app.services.crewai_flows.tools.critical_attributes_tool.base import (
            CriticalAttributesDefinition,
        )

        attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
        missing_attributes = []

        for attr_name, attr_config in attribute_mapping.items():
            if not attr_config.get("required", False):
                continue

            has_value = False
            for field_path in attr_config.get("asset_fields", []):
                if "." in field_path:
                    value = asset
                    for part in field_path.split("."):
                        value = getattr(value, part, None) or {}
                        if not isinstance(value, dict):
                            break
                    if value and value != {}:
                        has_value = True
                        break
                else:
                    field_value = getattr(asset, field_path, None)
                    if field_value and not (
                        isinstance(field_value, (list, dict)) and len(field_value) == 0
                    ):
                        has_value = True
                        break

            if not has_value:
                missing_attributes.append(attr_name)

        return missing_attributes

    except ImportError as e:
        logger.warning(
            f"Could not import CriticalAttributesDefinition, using fallback: {e}"
        )
        critical_fields = [
            "business_owner",
            "technical_owner",
            "dependencies",
            "operating_system",
        ]
        return [field for field in critical_fields if not getattr(asset, field, None)]


def _assess_data_quality(asset) -> dict:
    """Assess data quality of asset."""
    completeness_score = getattr(asset, "completeness_score", 0.0) or 0.0
    confidence_score = getattr(asset, "confidence_score", 0.0) or 0.0
    if completeness_score < 0.8 or confidence_score < 0.7:
        return {
            "completeness": completeness_score,
            "confidence": confidence_score,
            "needs_validation": True,
        }
    return {}


def _determine_eol_status(
    operating_system: str, os_version: str, technology_stack: List[str]
) -> str:
    """
    Determine EOL technology status based on OS and technology stack.

    Returns:
        EOL status string: "EOL_EXPIRED", "EOL_SOON", "DEPRECATED", or "CURRENT"
    """
    # Known EOL operating systems and versions
    eol_os_patterns = {
        "AIX 7.1": "EOL_EXPIRED",
        "AIX 7.2": "EOL_EXPIRED",  # IBM ended extended support
        "Windows Server 2008": "EOL_EXPIRED",
        "Windows Server 2012": "EOL_EXPIRED",
        "RHEL 6": "EOL_EXPIRED",
        "RHEL 7": "EOL_SOON",
        "Solaris 10": "EOL_EXPIRED",
    }

    # Known EOL technology stack components
    eol_tech_patterns = {
        "websphere_85": "EOL_EXPIRED",  # WebSphere 8.5.x extended support ended
        "websphere_9": "EOL_SOON",
        "jboss_6": "EOL_EXPIRED",
        "tomcat_7": "EOL_EXPIRED",
    }

    # Check OS
    if operating_system and os_version:
        os_key = f"{operating_system} {os_version}".strip()
        for pattern, status in eol_os_patterns.items():
            if pattern in os_key:
                logger.info(f"Detected EOL OS: {os_key} → {status}")
                return status

    # Check technology stack
    if technology_stack and isinstance(technology_stack, list):
        for tech in technology_stack:
            if tech in eol_tech_patterns:
                logger.info(
                    f"Detected EOL technology: {tech} → {eol_tech_patterns[tech]}"
                )
                return eol_tech_patterns[tech]

    # Default to CURRENT if no EOL indicators found
    return "CURRENT"


def _analyze_selected_assets(existing_assets: List[Asset]) -> Tuple[List[dict], dict]:
    """Analyze selected assets and extract comprehensive analysis."""
    selected_assets = []
    asset_analysis = {
        "total_assets": 0,
        "assets_with_gaps": [],
        "unmapped_attributes": {},
        "failed_mappings": {},
        "missing_critical_fields": {},
        "data_quality_issues": {},
    }

    for asset in existing_assets:
        asset_id_str = str(asset.id)

        # Extract OS and tech stack for EOL determination
        operating_system = getattr(asset, "operating_system", None) or ""
        os_version = getattr(asset, "os_version", None) or ""
        technology_stack = getattr(asset, "technology_stack", [])

        # Determine EOL status for intelligent option ordering
        eol_technology = _determine_eol_status(
            operating_system, os_version, technology_stack
        )

        selected_assets.append(
            {
                "id": asset_id_str,  # CRITICAL: Use "id" not "asset_id" - section_builders.py expects "id" key
                "asset_name": asset.name or getattr(asset, "application_name", None),
                "asset_type": getattr(asset, "asset_type", "application"),
                "criticality": getattr(asset, "criticality", "unknown"),
                "environment": getattr(asset, "environment", "unknown"),
                "technology_stack": technology_stack,
                # CRITICAL: Add OS data for OS-aware questionnaire generation
                "operating_system": operating_system,
                "os_version": os_version,
                # CRITICAL: Add EOL status for security vulnerabilities intelligent ordering
                "eol_technology": eol_technology,
            }
        )

        raw_data, field_mappings = _get_asset_raw_data_safely(asset, asset_id_str)

        unmapped = _find_unmapped_attributes(raw_data, field_mappings)
        if unmapped:
            asset_analysis["unmapped_attributes"][asset_id_str] = unmapped

        mapping_status = getattr(asset, "mapping_status", None)
        if mapping_status and mapping_status != "complete":
            asset_analysis["failed_mappings"][asset_id_str] = {
                "status": mapping_status,
                "reason": "Incomplete field mapping during import",
            }

        missing_fields = _check_missing_critical_fields(asset)
        if missing_fields:
            asset_analysis["missing_critical_fields"][asset_id_str] = missing_fields
            asset_analysis["assets_with_gaps"].append(asset_id_str)

        quality_issues = _assess_data_quality(asset)
        if quality_issues:
            asset_analysis["data_quality_issues"][asset_id_str] = quality_issues

    asset_analysis["total_assets"] = len(selected_assets)
    return selected_assets, asset_analysis


def _extract_questionnaire_data(
    agent_result: dict, flow_id: str
) -> List[AdaptiveQuestionnaireResponse]:
    """Extract and convert questionnaire data from agent results."""
    logger.info(f"Agent result keys: {list(agent_result.keys())}")

    # Try to find questionnaire data using helper functions
    questionnaires_data, sections_data = _find_questionnaires_in_result(agent_result)

    # Determine which data to process
    data_to_process = (
        questionnaires_data
        or sections_data
        or _extract_from_agent_output(agent_result)
        or _generate_from_gap_analysis(agent_result)
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
