"""Comprehensive gap analysis task builder.

Per PR #1043: Auto-trigger phase that performs comprehensive gap detection
with AI enhancement (confidence scores, suggestions) but NO questionnaires.

UPDATED per COLLECTION_FLOW_TWO_CRITICAL_ISSUES.md:
- Intelligent filtering based on asset type (NOT 6R strategy - assessment hasn't run yet)
- Checks existing JSONB data before creating gaps
- Only presents relevant attributes to agent (reduces agent work and improves performance)
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
    """Build task for comprehensive AI gap detection and enhancement (gaps ONLY, no questionnaires).

    Per PR #1043: Auto-trigger phase that:
    1. Examines ALL asset data to find missing critical attributes
    2. AI enhances gaps with confidence scores and suggestions
    3. Does NOT generate questionnaires (happens separately when user proceeds)

    UPDATED per COLLECTION_FLOW_TWO_CRITICAL_ISSUES.md:
    - Pre-filters attributes based on asset type (applications don't need network_device attrs)
    - Checks existing JSONB data (custom_attributes, technical_details) before creating gaps
    - Only presents missing + applicable attributes to agent (improves performance)

    This is different from:
    - build_task_description(): Builds gaps AND questionnaires
    - build_enhancement_task_description(): Only enhances existing heuristic gaps

    Args:
        assets: List of Asset objects to comprehensively analyze

    Returns:
        Task description string for CrewAI agent
    """
    # Build intelligent asset summary with pre-filtered gaps
    asset_summary = []
    for asset in assets[:10]:  # Show first 10
        # Get existing fields from all sources (model + JSONB)
        existing_fields = DataIntelligence.get_existing_fields(asset)

        # Get attributes applicable to this asset type
        applicable_attrs = AssetTypeRequirements.get_applicable_attributes(
            asset.asset_type
        )

        # Get missing attributes (applicable but not present)
        missing_attrs = DataIntelligence.get_missing_attributes(asset, applicable_attrs)

        asset_data = {
            "id": str(asset.id),
            "name": asset.name,
            "type": asset.asset_type,
            "current_fields": existing_fields,  # Data that exists
            "missing_attributes": missing_attrs,  # Gaps to create
            "applicable_count": len(applicable_attrs),  # Total relevant attributes
            "missing_count": len(missing_attrs),  # Total gaps
        }

        asset_summary.append(asset_data)

        logger.debug(
            f"Asset {asset.name} ({asset.asset_type}): "
            f"{len(existing_fields)} existing, {len(missing_attrs)} missing "
            f"out of {len(applicable_attrs)} applicable attributes"
        )

    return f"""
TASK: AI gap detection and enhancement for cloud migration assessment.

CRITICAL INSTRUCTIONS - READ FIRST:
1. DO NOT USE ANY TOOLS - All data you need is in the asset summary below
2. Analyze assets DIRECTLY from the provided data - tools won't help here
3. The asset data includes:
   - current_fields: Data that already exists (from model fields and custom_attributes JSONB)
   - missing_attributes: Pre-filtered list of gaps (applicable to asset type, not in current_fields)
4. Your job: Enhance each missing attribute with confidence scores and AI suggestions
5. DO NOT generate questionnaires (happens separately when user clicks "Continue to Questionnaire")

WHY NO TOOLS:
- You have complete Asset metadata with current_fields and missing_attributes
- Data validation tools are for CSV imports, not gap analysis
- Tools would return "0 records" because no raw import data exists at this stage
- Direct analysis is 6x faster and more accurate

INTELLIGENT PRE-FILTERING APPLIED:
- Asset type filtering: Only attributes applicable to each asset type (e.g., databases don't need "user_load_patterns")
- Data checking: Existing JSONB data (custom_attributes, technical_details) already checked
- You receive ONLY the missing attributes that need gap records created

ASSETS TO ANALYZE ({len(assets)} total, showing first 10):
{json.dumps(asset_summary, indent=2)}

YOUR ANALYSIS TASK:
1. For EACH asset's missing_attributes list, create enhanced gap records
2. Use current_fields to intelligently assign confidence scores:
   - If asset has "name": "Oracle Database" but missing "technology_stack" → HIGH confidence (0.95)
   - If asset has deployment info but missing "os" → HIGH confidence (0.90)
   - If no context clues exist for missing field → MEDIUM confidence (0.60)
3. Classify gaps by priority based on 6R migration needs:
   - critical (priority 1): Required for 6R decisions (os, cpu_memory_storage, technology_stack)
   - high (priority 2): Important for planning (architecture, integration_dependencies)
   - medium (priority 3): Useful for optimization (performance_baseline, user_load_patterns)
   - low (priority 4): Nice to have (documentation_quality)
4. Provide 2-3 ACTIONABLE ai_suggestions per gap based on asset context:
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
