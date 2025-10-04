"""Task description builder for gap analysis."""

import json
import logging
from typing import List

from app.models.asset import Asset

logger = logging.getLogger(__name__)


def build_task_description(assets: List[Asset]) -> str:
    """Build task description with REAL asset data.

    Args:
        assets: List of Asset objects to analyze

    Returns:
        Task description string for CrewAI agent
    """
    # Import critical attributes
    from app.services.crewai_flows.tools.critical_attributes_tool.base import (
        CriticalAttributesDefinition,
    )

    all_attributes = CriticalAttributesDefinition.get_all_attributes()
    attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

    # Build asset summary
    asset_summary = []
    for asset in assets[:10]:  # Show first 10
        asset_data = {
            "id": str(asset.id),
            "name": asset.name,
            "type": asset.asset_type,
            "current_fields": {},
        }

        # Check which critical attributes this asset has
        for attr_name in all_attributes:
            attr_config = attribute_mapping.get(attr_name, {})
            asset_fields = attr_config.get("asset_fields", [])

            # Check if asset has any of these fields
            for field in asset_fields:
                if "." in field:  # custom_attributes.field_name
                    parts = field.split(".")
                    if hasattr(asset, parts[0]):
                        custom_attrs = getattr(asset, parts[0])
                        if custom_attrs and parts[1] in custom_attrs:
                            asset_data["current_fields"][attr_name] = custom_attrs[
                                parts[1]
                            ]
                else:
                    if hasattr(asset, field) and getattr(asset, field) is not None:
                        asset_data["current_fields"][attr_name] = getattr(asset, field)

        asset_summary.append(asset_data)

    return f"""
Analyze REAL assets and generate questionnaire for missing critical attributes.

ASSETS TO ANALYZE ({len(assets)} total):
{json.dumps(asset_summary, indent=2)}

CRITICAL ATTRIBUTES FRAMEWORK (22 attributes):
{json.dumps(list(attribute_mapping.keys()), indent=2)}

YOUR TASK:
1. For each asset, compare against 22 critical attributes
2. Identify missing/null fields using the attribute_mapping
3. Classify gaps by priority:
   - critical (priority 1): Required for 6R decisions (os, cpu_memory_storage, technology_stack)
   - high (priority 2): Important for planning (architecture, integration_dependencies)
   - medium (priority 3): Useful for optimization (performance_baseline, user_load_patterns)
   - low (priority 4): Nice to have (documentation_quality)
4. Generate questionnaire sections for missing fields grouped by category

RETURN JSON FORMAT:
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "uuid",
                "field_name": "technology_stack",
                "gap_type": "missing_field",
                "gap_category": "application",
                "description": "Technology stack not specified",
                "impact_on_sixr": "high",
                "priority": 1,
                "suggested_resolution": "Request from application owner"
            }}
        ],
        "high": [...],
        "medium": [...],
        "low": [...]
    }},
    "questionnaire": {{
        "sections": [
            {{
                "section_id": "infrastructure",
                "title": "Infrastructure Details",
                "questions": [
                    {{
                        "field": "operating_system_version",
                        "question": "What is the operating system and version?",
                        "asset_ids": ["uuid1", "uuid2"]
                    }}
                ]
            }}
        ]
    }},
    "summary": {{
        "total_gaps": 15,
        "assets_analyzed": {len(assets)},
        "critical_gaps": 5,
        "high_priority_gaps": 4,
        "medium_priority_gaps": 4,
        "low_priority_gaps": 2
    }}
}}
"""
