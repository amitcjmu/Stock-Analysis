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
TASK: Comprehensive AI-powered gap detection for cloud migration assessment.

CRITICAL INSTRUCTIONS - READ FIRST:
1. DO NOT USE ANY TOOLS - All data you need is in the asset summary below
2. Analyze assets DIRECTLY from the provided data - tools won't help here
3. The asset data includes:
   - current_fields: Data that already exists (from model fields and custom_attributes JSONB)
   - type: Asset type (application, database, server, network_device, storage, middleware)
4. Your job: IDENTIFY and CREATE gap records for missing critical attributes
5. DO NOT generate questionnaires (happens separately when user clicks "Continue to Questionnaire")

WHY NO TOOLS:
- You have complete Asset metadata with current_fields
- Data validation tools are for CSV imports, not gap analysis
- Tools would return "0 records" because no raw import data exists at this stage
- Direct analysis is 6x faster and more accurate

YOUR COMPREHENSIVE ANALYSIS TASK:
You are an expert migration analyst. For EACH asset:

1. **IDENTIFY MISSING CRITICAL ATTRIBUTES**:
   - Compare current_fields against the 22 critical attributes below
   - Consider which attributes are relevant for this asset type:
     * Applications: Need all architecture, integration, user patterns
     * Databases: Need infrastructure, data volume, security - NOT user UX patterns
     * Servers: Need infrastructure, hosted services - NOT app architecture
     * Network devices: Need network config, connectivity - NOT app dependencies
     * Storage: Need capacity, I/O, redundancy - NOT business logic
     * Middleware: Need runtime specs, clustering - asset-type specific
   - Use your intelligence to determine if a gap is truly relevant

2. **ASSESS CRITICALITY AND CONFIDENCE**:
   - Assign confidence scores based on evidence in current_fields:
     * If asset name = "Oracle Database" but missing "technology_stack" → HIGH (0.95)
     * If deployment info exists but missing "os" → HIGH (0.90)
     * If no context clues for missing field → MEDIUM (0.60)
   - Classify priority based on 6R migration needs:
     * critical (priority 1): Required for 6R decisions (os, cpu, technology_stack)
     * high (priority 2): Important for planning (architecture, dependencies)
     * medium (priority 3): Useful for optimization (performance, patterns)
     * low (priority 4): Nice to have (documentation)

3. **PROVIDE ACTIONABLE AI SUGGESTIONS**:
   - Use current_fields to suggest where to find missing data
   - Example: "Check custom_attributes.environment for OS details"
   - Example: "Review asset name 'Oracle DB' to infer technology_stack"

ASSETS TO ANALYZE ({len(assets)} total, showing first 10):
{json.dumps(asset_summary, indent=2)}

22 CRITICAL ATTRIBUTES FOR MIGRATION READINESS:
{json.dumps(all_critical_attrs, indent=2)}

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
- Use your INTELLIGENCE to identify which of the 22 attributes are missing AND relevant for each asset type
- Don't create gaps for irrelevant attributes (e.g., "user_load_patterns" for databases)
- Use asset current_fields data to intelligently assign confidence scores
- Every gap MUST have confidence_score field (0.0-1.0)
- Every gap MUST have ai_suggestions array (2-3 actionable items based on asset context)
- Every gap MUST have description explaining WHY it matters for 6R assessment
- DO NOT include "questionnaire" key in response (questionnaires generated separately)
- Return ONLY valid JSON, no markdown, no explanations
"""
