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
TASK: Cloud migration readiness gap analysis for 6R strategy assessment.

CRITICAL INSTRUCTIONS - READ FIRST:
1. DO NOT USE ANY TOOLS - All data you need is in the asset summary below
2. Analyze assets DIRECTLY from the provided data - tools won't help here
3. The asset data includes:
   - current_fields: Data that already exists (from model fields and custom_attributes JSONB)
   - type: Asset type (application, database, server, network_device, storage, middleware)
4. Your job: IDENTIFY gaps that impact cloud migration/modernization decisions
5. DO NOT generate questionnaires (happens separately when user clicks "Continue to Questionnaire")

WHY NO TOOLS:
- You have complete Asset metadata with current_fields
- Data validation tools are for CSV imports, not gap analysis
- Tools would return "0 records" because no raw import data exists at this stage
- Direct analysis is 6x faster and more accurate

YOUR MISSION - CLOUD MIGRATION READINESS:
You are a cloud migration architect. Your goal is to identify missing data that impacts:
- **6R Strategy Decisions**: Rehost, Replatform, Refactor, Rearchitect, Retire, Retain
- **Cloud-Native Modernization**: Containerization, microservices, serverless viability
- **Migration Planning**: Dependencies, sequencing, risk assessment, cost estimation
- **Cloud Optimization**: Right-sizing, reserved instances, auto-scaling requirements

For EACH asset:

1. **ANALYZE FOR MIGRATION READINESS**:
   - **Not just checking attributes** - Think about what's needed for migration decisions
   - Consider the 22 critical attributes as GUIDANCE, not exhaustive requirements
   - Think beyond the list: What else is critical for cloud migration?
     * For applications: Cloud compatibility (12-factor app principles?)
     * For databases: Cloud DB service candidates (RDS, Aurora, managed services?)
     * For servers: Containerization readiness? VM vs serverless potential?
     * For dependencies: Cross-region data transfer costs? Latency requirements?
     * For compliance: Data residency? Regulatory constraints?
     * For licensing: BYOL eligibility? License portability to cloud?

2. **6R STRATEGY DECISION GAPS**:
   - **Rehost (Lift-and-Shift)**: Need OS, specs, network config
   - **Replatform (Lift-Tinker-Shift)**: Need technology stack, current platform details
   - **Refactor (Re-architect for cloud)**: Need architecture patterns, coupling analysis
   - **Rearchitect (Rebuild cloud-native)**: Need business logic complexity, API boundaries
   - **Retire**: Need business criticality, usage patterns, replacement options
   - **Retain (Keep on-prem)**: Need compliance constraints, data sensitivity

   Identify missing data that prevents choosing the right 6R strategy!

3. **CLOUD-NATIVE MODERNIZATION GAPS**:
   - Containerization: Image size, stateless/stateful, persistent storage needs?
   - Microservices: Service boundaries, API contracts, inter-service communication?
   - Serverless: Event-driven patterns, cold start tolerance, execution duration?
   - Managed Services: PaaS candidates (databases, queues, caches)?
   - Auto-scaling: Load patterns, predictable vs burst traffic?

4. **ASSIGN CRITICALITY BY IMPACT**:
   - **critical (priority 1)**: Blocks 6R decision or migration planning
   - **high (priority 2)**: Impacts cost estimates or migration complexity
   - **medium (priority 3)**: Useful for optimization but not blocking
   - **low (priority 4)**: Nice to have for long-term operational excellence

5. **CONFIDENCE SCORES BASED ON EVIDENCE**:
   - 0.9-1.0: Strong evidence in current_fields that this gap blocks migration decisions
   - 0.7-0.8: Moderate evidence, likely needed for accurate 6R strategy
   - 0.5-0.6: Weak evidence, may be inferred from other data
   - 0.0-0.4: Low priority or may not be relevant for this asset's migration path

ASSETS TO ANALYZE ({len(assets)} total - ALL MUST BE ANALYZED):
NOTE: This prompt shows only the first 10 assets as examples for token efficiency.
You MUST analyze ALL {len(assets)} assets that were provided to you, not just these 10 samples.

Asset samples (first 10 of {len(assets)}):
{json.dumps(asset_summary, indent=2)}

22 CRITICAL ATTRIBUTES FRAMEWORK (GUIDANCE, not exhaustive):
{json.dumps(all_critical_attrs, indent=2)}

THINK BEYOND THE LIST:
- What cloud services could this asset use? (Need details to evaluate)
- What migration risks exist? (Need dependencies, SLAs, DR requirements)
- What cost drivers are missing? (Need data volume, IOPS, network egress patterns)
- What modernization opportunities? (Need current architecture vs cloud-native patterns)

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
- IMPORTANT: "assets_analyzed" in summary MUST be {len(assets)} (the TOTAL count), not the sample count shown above
- Use your MIGRATION EXPERTISE to identify gaps that impact 6R strategy decisions
- The 22 attributes are GUIDANCE - think beyond them for cloud migration needs
- Don't create gaps just because an attribute is missing - ask "Does this block migration decisions?"
- Prioritize gaps by migration impact, not just data completeness
- Consider cloud-native modernization opportunities (containers, serverless, managed services)
- Every gap MUST have confidence_score field (0.0-1.0) based on migration decision impact
- Every gap MUST have ai_suggestions array (2-3 actionable items for finding the data)
- Every gap MUST have description explaining WHY it matters for 6R strategy or cloud migration
- DO NOT include "questionnaire" key in response (questionnaires generated separately)
- Return ONLY valid JSON, no markdown, no explanations

YOU ARE A MIGRATION ARCHITECT, NOT A DATA AUDITOR.
Focus on migration readiness, not just data completeness.
"""
