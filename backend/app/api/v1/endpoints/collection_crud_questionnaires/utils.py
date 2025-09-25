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


def _get_selected_application_info(
    flow: CollectionFlow, existing_assets: List[Asset]
) -> tuple[Optional[str], Optional[str]]:
    """Extract selected application info from flow config."""
    selected_application_name: Optional[str] = None
    selected_application_id: Optional[str] = None

    if flow.collection_config and flow.collection_config.get(
        "selected_application_ids"
    ):
        selected_app_ids = flow.collection_config["selected_application_ids"]
        if selected_app_ids:
            # Get the first selected application
            selected_application_id = selected_app_ids[0]

            # Find the asset name from the assets list
            for asset in existing_assets:
                if str(asset.id) == selected_application_id:
                    selected_application_name = asset.name or asset.application_name
                    break

    return selected_application_name, selected_application_id


def _convert_template_field_to_question(
    field: dict, selected_application_name: Optional[str] = None
) -> dict:
    """Convert a template field to a questionnaire question format.

    Args:
        field: Field from questionnaire template
        selected_application_name: Name of pre-selected application

    Returns:
        Question dictionary
    """
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

    # Add asset_id to maintain asset-question relationship
    if selected_application_name and "metadata" in question:
        # Find asset ID from the name
        question["metadata"]["asset_name"] = selected_application_name

    # Pre-fill values if available
    if field["field_id"] == "application_name" and selected_application_name:
        question["default_value"] = selected_application_name
    elif field["field_id"] == "asset_name" and selected_application_name:
        question["default_value"] = selected_application_name

    # Handle default values for asset selector
    if field.get("default_value"):
        question["default_value"] = field["default_value"]

    return question


def _suggest_field_mapping(field_name: str) -> str:
    """Suggest potential mapping for unmapped field."""
    field_lower = field_name.lower()

    # Common field mappings
    mapping_suggestions = {
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

    for key, value in mapping_suggestions.items():
        if key in field_lower:
            return value

    return "custom_attribute"


def _analyze_selected_assets(existing_assets: List[Asset]) -> Tuple[List[dict], dict]:
    """
    Analyze selected assets and extract comprehensive analysis.

    Modified to work with asset list directly instead of flow configuration.

    Args:
        existing_assets: List of assets to analyze

    Returns:
        Tuple of (selected_assets_info, asset_analysis_data)
    """
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

        # Basic asset information
        asset_info = {
            "asset_id": asset_id_str,
            "asset_name": asset.name or getattr(asset, "application_name", None),
            "asset_type": getattr(asset, "asset_type", "application"),
            "criticality": getattr(asset, "criticality", "unknown"),
            "environment": getattr(asset, "environment", "unknown"),
            "technology_stack": getattr(asset, "technology_stack", "unknown"),
        }
        selected_assets.append(asset_info)

        # Analyze unmapped attributes from raw data
        raw_data = getattr(asset, "raw_data", {}) or {}
        field_mappings = getattr(asset, "field_mappings_used", {}) or {}

        # Find unmapped attributes (in raw data but not in mapped fields)
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

        if unmapped:
            asset_analysis["unmapped_attributes"][asset_id_str] = unmapped

        # Identify failed mappings and data quality issues
        mapping_status = getattr(asset, "mapping_status", None)
        if mapping_status and mapping_status != "complete":
            asset_analysis["failed_mappings"][asset_id_str] = {
                "status": mapping_status,
                "reason": "Incomplete field mapping during import",
            }

        # Check for missing critical fields
        critical_fields = [
            "business_owner",
            "technical_owner",
            "six_r_strategy",
            "migration_complexity",
            "dependencies",
            "operating_system",
        ]
        missing_fields = []
        for field in critical_fields:
            if not getattr(asset, field, None):
                missing_fields.append(field)

        if missing_fields:
            asset_analysis["missing_critical_fields"][asset_id_str] = missing_fields
            asset_analysis["assets_with_gaps"].append(asset_id_str)

        # Assess data quality
        completeness_score = getattr(asset, "completeness_score", 0.0) or 0.0
        confidence_score = getattr(asset, "confidence_score", 0.0) or 0.0
        if completeness_score < 0.8 or confidence_score < 0.7:
            asset_analysis["data_quality_issues"][asset_id_str] = {
                "completeness": completeness_score,
                "confidence": confidence_score,
                "needs_validation": True,
            }

    asset_analysis["total_assets"] = len(selected_assets)
    return selected_assets, asset_analysis


def _extract_questionnaire_data(
    agent_result: dict, flow_id: str
) -> List[AdaptiveQuestionnaireResponse]:
    """Extract and convert questionnaire data from agent results."""
    questionnaires_data = agent_result.get("questionnaires", [])
    sections_data = agent_result.get("sections", [])

    # Handle different result formats
    if questionnaires_data:
        data_to_process = questionnaires_data
    elif sections_data:
        data_to_process = sections_data
    else:
        # Try to extract from agent output or raw response
        agent_output = agent_result.get("agent_output", {})
        if isinstance(agent_output, dict):
            data_to_process = agent_output.get("sections", [])
        else:
            logger.warning("No questionnaire data found in agent result")
            raise Exception("Agent returned success but no questionnaire data")

    # Convert agent results to AdaptiveQuestionnaireResponse format
    result = []
    for idx, section in enumerate(data_to_process):
        if not isinstance(section, dict):
            continue

        questions = section.get("questions", [])
        if not questions:
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
            questions=questions,
            validation_rules=section.get("validation_rules", {}),
            completion_status="pending",
            responses_collected={},
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        result.append(questionnaire)

    if result:
        logger.info(
            f"Successfully generated {len(result)} questionnaires using persistent agent"
        )
        return result
    else:
        raise Exception("No valid questionnaires generated from agent result")
