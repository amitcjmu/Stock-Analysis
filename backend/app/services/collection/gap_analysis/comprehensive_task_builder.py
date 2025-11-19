"""Comprehensive gap analysis task builder.

Per PR #1043: Auto-trigger phase that performs comprehensive gap detection
with AI enhancement (confidence scores, suggestions) but NO questionnaires.

UPDATED per user feedback (PR #1059 review):
- Agent performs INDEPENDENT gap detection (not just enhancement of predetermined gaps)
- Provides current_fields + asset type + 22 critical attributes framework
- Agent uses INTELLIGENCE to determine which gaps are relevant for each asset type
- Checks existing JSONB data to provide current_fields, but lets agent decide what's missing
- Agent autonomously creates gaps with confidence scores and AI suggestions
"""

import json
import logging
from typing import List

from app.models.asset import Asset
from app.services.collection.gap_analysis.asset_type_requirements import (
    AssetTypeRequirements,
)
from app.services.collection.gap_analysis.data_intelligence import DataIntelligence

logger = logging.getLogger(__name__)


def build_comprehensive_gap_analysis_task(assets: List[Asset]) -> str:
    """Build task for comprehensive AI gap detection (gaps ONLY, no questionnaires).

    Per PR #1043: Auto-trigger phase that:
    1. Agent INDEPENDENTLY identifies missing critical attributes using AI intelligence
    2. Agent creates gaps with confidence scores and AI suggestions
    3. Does NOT generate questionnaires (happens separately when user proceeds)

    UPDATED per user feedback (PR #1059 review):
    - Agent performs INDEPENDENT gap detection (not enhancement of predetermined gaps)
    - Provides current_fields (from model + JSONB) + asset type + 22 attributes framework
    - Agent decides which attributes are missing AND relevant for each asset type
    - Agent autonomously filters irrelevant gaps (e.g., "user_patterns" for databases)

    This is different from:
    - build_task_description(): Builds gaps AND questionnaires
    - build_enhancement_task_description(): Only enhances existing heuristic gaps

    Args:
        assets: List of Asset objects for agent to comprehensively analyze

    Returns:
        Task description string for CrewAI agent with full autonomy to detect gaps
    """
    # Build asset summary with current data (let agent determine gaps)
    asset_summary = []
    for asset in assets[:10]:  # Show first 10
        # Get existing fields from all sources (model + JSONB)
        existing_fields = DataIntelligence.get_existing_fields(asset)

        # Get attributes applicable to this asset type (as guidance, not prescription)
        applicable_attrs = AssetTypeRequirements.get_applicable_attributes(
            asset.asset_type
        )

        asset_data = {
            "id": str(asset.id),
            "name": asset.name,
            "type": asset.asset_type,
            "current_fields": existing_fields,  # Data that exists
            "applicable_attributes_count": len(
                applicable_attrs
            ),  # Guidance on typical scope
        }

        asset_summary.append(asset_data)

        logger.debug(
            f"Asset {asset.name} ({asset.asset_type}): "
            f"{len(existing_fields)} existing fields, "
            f"{len(applicable_attrs)} typically applicable attributes"
        )

    # Import critical attributes framework for prompt
    from app.services.crewai_flows.tools.critical_attributes_tool.base import (
        CriticalAttributesDefinition,
    )

    all_critical_attrs = CriticalAttributesDefinition.get_all_attributes()

    return f"""
TASK: Identify missing data gaps for cloud migration assessment (6R strategy).

INSTRUCTIONS:
1. DO NOT USE TOOLS - analyze provided asset data directly
2. Focus on 22 critical attributes (MANDATORY for 85% assessment readiness)
3. Identify gaps blocking 6R decisions (Rehost/Replatform/Refactor/Rearchitect/Retire/Retain)
4. Assign priority: 1=blocks migration, 2=impacts cost/complexity, 3=optimization, 4=nice-to-have
5. Set confidence_score (0.0-1.0): 1.0=definitely missing, 0.5=maybe relevant
6. Return gaps ONLY (no questionnaires - those generate separately)

ASSETS ({len(assets)} total):
{json.dumps(asset_summary, indent=2)}

CRITICAL ATTRIBUTES (22 total - check ALL):
{json.dumps(all_critical_attrs, indent=2)}

OUTPUT FORMAT:
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "uuid",
                "field_name": "technology_stack",
                "gap_type": "missing_field",
                "gap_category": "application",
                "description": "Missing - blocks 6R decision",
                "impact_on_sixr": "high",
                "priority": 1,
                "confidence_score": 0.95,
                "ai_suggestions": [
                    "Check asset name for tech stack hints",
                    "Review deployment artifacts",
                    "Request from owner"
                ],
                "suggested_resolution": "Infer from asset name and config"
            }}
        ],
        "high": [...],
        "medium": [...],
        "low": [...]
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

RULES:
- ALL gaps need: confidence_score, ai_suggestions (2-3 items), description
- summary.assets_analyzed MUST be {len(assets)} (total, not sample)
- Only create gaps that block migration decisions (not just for data completeness)
- Return valid JSON only (no markdown, no explanations)
"""
