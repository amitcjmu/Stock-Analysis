"""Comprehensive gap analysis task builder.

Per PR #1043: Auto-trigger phase that performs comprehensive gap detection
with AI enhancement (confidence scores, suggestions) but NO questionnaires.
"""

import json
import logging
from typing import List

from app.models.asset import Asset

logger = logging.getLogger(__name__)


def build_comprehensive_gap_analysis_task(assets: List[Asset]) -> str:
    """Build task for comprehensive AI gap detection and enhancement (gaps ONLY, no questionnaires).

    Per PR #1043: Auto-trigger phase that:
    1. Examines ALL asset data to find missing critical attributes
    2. AI enhances gaps with confidence scores and suggestions
    3. Does NOT generate questionnaires (happens separately when user proceeds)

    This is different from:
    - build_task_description(): Builds gaps AND questionnaires
    - build_enhancement_task_description(): Only enhances existing heuristic gaps

    Args:
        assets: List of Asset objects to comprehensively analyze

    Returns:
        Task description string for CrewAI agent
    """
    # Import critical attributes
    from app.services.crewai_flows.tools.critical_attributes_tool.base import (
        CriticalAttributesDefinition,
    )

    all_attributes = CriticalAttributesDefinition.get_all_attributes()
    attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

    # Build asset summary with current_fields
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
TASK: Comprehensive AI gap detection and enhancement for cloud migration assessment.

CRITICAL INSTRUCTIONS:
1. Perform COMPREHENSIVE analysis - look at ALL asset data to find missing critical attributes
2. Use current_fields to intelligently infer gaps based on asset context
3. Assign confidence scores (0.0-1.0) based on evidence strength
4. Provide actionable AI suggestions for each gap
5. DO NOT generate questionnaires (happens separately when user clicks "Continue to Questionnaire")

ASSETS TO ANALYZE ({len(assets)} total):
{json.dumps(asset_summary, indent=2)}

CRITICAL ATTRIBUTES FRAMEWORK (22 attributes for assessment readiness):
{json.dumps(list(attribute_mapping.keys()), indent=2)}

YOUR COMPREHENSIVE ANALYSIS TASK:
1. For EACH asset, examine current_fields to understand what data exists
2. Compare against ALL 22 critical attributes to identify what's missing
3. Use existing data to intelligently infer confidence about missing fields:
   - If asset has "name": "Oracle Database" but missing "technology_stack" → HIGH confidence gap (0.95)
   - If asset has deployment info but missing "os" → HIGH confidence gap (0.90)
   - If no context clues exist for missing field → MEDIUM confidence gap (0.60)
4. Classify gaps by priority based on 6R migration needs:
   - critical (priority 1): Required for 6R decisions (os, cpu_memory_storage, technology_stack)
   - high (priority 2): Important for planning (architecture, integration_dependencies)
   - medium (priority 3): Useful for optimization (performance_baseline, user_load_patterns)
   - low (priority 4): Nice to have (documentation_quality)
5. Provide 2-3 ACTIONABLE ai_suggestions per gap based on asset context:
   - Use current_fields data to suggest where to look
   - Example: "Check custom_attributes.environment for OS details"
   - Example: "Review asset name 'Oracle DB' to infer technology_stack"

CONFIDENCE SCORE GUIDELINES (0.0-1.0):
- 0.9-1.0: Strong evidence in asset data that this field is missing and critical
- 0.7-0.8: Moderate evidence, likely needs attention for assessment
- 0.5-0.6: Weak evidence, may need attention depending on 6R strategy
- 0.0-0.4: Low priority or may be inferred from other fields

RETURN JSON FORMAT (gaps ONLY, no questionnaires):
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "uuid",
                "field_name": "technology_stack",
                "gap_type": "missing_field",
                "gap_category": "application",
                "description": "Technology stack not specified - critical for 6R decision",
                "impact_on_sixr": "high",
                "priority": 1,
                "confidence_score": 0.95,
                "ai_suggestions": [
                    "Check asset name 'Oracle Database' - likely Oracle RDBMS stack",
                    "Review deployment manifests or config files for framework",
                    "Request from application owner or DBA team"
                ],
                "suggested_resolution": "Check asset name and deployment artifacts to infer Oracle stack details"
            }}
        ],
        "high": [
            {{
                "asset_id": "uuid",
                "field_name": "integration_dependencies",
                "gap_type": "missing_field",
                "gap_category": "application",
                "description": "Integration dependencies unknown - important for migration sequencing",
                "impact_on_sixr": "medium",
                "priority": 2,
                "confidence_score": 0.85,
                "ai_suggestions": [
                    "Analyze network traffic logs for API calls",
                    "Review application configuration for service endpoints",
                    "Interview development team about external integrations"
                ],
                "suggested_resolution": "Analyze application config and network patterns"
            }}
        ],
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

CRITICAL REMINDERS:
- DO COMPREHENSIVE analysis (not just predetermined gaps) - look at ALL 22 critical attributes
- Use asset current_fields data to intelligently assign confidence scores
- Every gap MUST have confidence_score field (0.0-1.0)
- Every gap MUST have ai_suggestions array (2-3 actionable items based on asset context)
- Every gap MUST have description explaining WHY it matters for 6R assessment
- DO NOT include "questionnaire" key in response (questionnaires generated separately)
- Return ONLY valid JSON, no markdown, no explanations
"""
