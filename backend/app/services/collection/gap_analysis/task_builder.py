"""Task description builder for gap analysis."""

import json
import logging
from typing import Any, Dict, List

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


def build_enhancement_task_description(
    gaps: List[Dict[str, Any]], assets: List[Asset]
) -> str:
    """Build task description for ENHANCING existing programmatic gaps with AI.

    Args:
        gaps: List of programmatic gaps to enhance (from ProgrammaticGapScanner)
        assets: List of Asset objects for context

    Returns:
        Task description string for CrewAI agent to enhance gaps
    """
    # Build asset context (minimal - just ID, name, type)
    asset_context = {}
    for asset in assets:
        asset_context[str(asset.id)] = {
            "name": asset.name,
            "type": asset.asset_type,
        }

    # Group gaps by asset for better context
    gaps_by_asset = {}
    for gap in gaps:
        asset_id = gap.get("asset_id")
        if asset_id not in gaps_by_asset:
            gaps_by_asset[asset_id] = []
        gaps_by_asset[asset_id].append(
            {
                "field_name": gap.get("field_name"),
                "gap_type": gap.get("gap_type"),
                "gap_category": gap.get("gap_category"),
                "priority": gap.get("priority"),
                "current_value": gap.get("current_value"),
            }
        )

    return f"""
TASK: Enhance existing data gaps with AI confidence scores and suggestions.

IMPORTANT: You are NOT detecting new gaps. You are ENHANCING the gaps already found by programmatic scan.

PROGRAMMATIC GAPS TO ENHANCE ({len(gaps)} total):
{json.dumps(gaps_by_asset, indent=2)}

ASSET CONTEXT:
{json.dumps(asset_context, indent=2)}

YOUR TASK:
1. For EACH gap provided above, analyze it and add:
   - confidence_score: Float 0.0-1.0 (how confident you are this is a real gap needing attention)
   - ai_suggestions: List of 2-3 specific suggestions for resolving the gap
   - suggested_resolution: Single best resolution strategy

2. Confidence Score Guidelines:
   - 0.9-1.0: Definitely needs attention (e.g., missing critical field like technology_stack)
   - 0.7-0.8: Probably needs attention (e.g., missing architecture details)
   - 0.5-0.6: Maybe needs attention (e.g., missing optional metadata)
   - 0.0-0.4: Low priority or may not be critical

3. AI Suggestions should be ACTIONABLE:
   - "Check package.json for Node.js technology stack"
   - "Review deployment manifests for architecture pattern"
   - "Request from application owner during onboarding"

4. CRITICAL: Return EXACT SAME field_name and asset_id for each gap
   - Do NOT invent new gaps
   - Do NOT change field names
   - Do NOT change asset IDs
   - ONLY add confidence_score, ai_suggestions, suggested_resolution

RETURN JSON FORMAT (enhance ALL {len(gaps)} gaps):
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "EXACT_SAME_UUID_FROM_INPUT",
                "field_name": "EXACT_SAME_FIELD_NAME_FROM_INPUT",
                "gap_type": "missing_field",
                "gap_category": "application",
                "priority": 1,
                "confidence_score": 0.95,
                "ai_suggestions": [
                    "Check application manifest for tech stack",
                    "Review deployment artifacts for framework detection",
                    "Request from development team lead"
                ],
                "suggested_resolution": "Check deployment artifacts for framework detection"
            }}
        ],
        "high": [...],
        "medium": [...],
        "low": [...]
    }},
    "summary": {{
        "total_gaps": {len(gaps)},
        "assets_analyzed": {len(assets)},
        "execution_time_ms": 0
    }}
}}

REMEMBER: Enhance all {len(gaps)} gaps. Do not skip any. Use EXACT asset_id and field_name from input.
"""
