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


def build_comprehensive_gap_analysis_task(
    assets: List[Asset], related_assets_map: dict = None
) -> str:
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

    UPDATED for Issue #1193 (December 2025):
    - Now accepts related_assets_map to include data from underlying servers
    - Applications inherit OS/virtualization/tech_stack data from mapped servers
    - This prevents redundant gap questions for data that exists in related assets

    This is different from:
    - build_task_description(): Builds gaps AND questionnaires
    - build_enhancement_task_description(): Only enhances existing heuristic gaps

    Args:
        assets: List of Asset objects for agent to comprehensively analyze
        related_assets_map: Dict mapping asset_id -> list of related Asset objects
                           (e.g., servers that an application depends on)

    Returns:
        Task description string for CrewAI agent with full autonomy to detect gaps
    """
    if related_assets_map is None:
        related_assets_map = {}
    # Build asset summary with current data (let agent determine gaps)
    asset_summary = []
    for asset in assets[:10]:  # Show first 10
        # Get existing fields from all sources (model + JSONB)
        existing_fields = DataIntelligence.get_existing_fields(asset)

        # Issue #1193 Fix: Also include fields from related assets (e.g., servers)
        # This allows applications to inherit OS/virtualization/tech_stack from servers
        related_assets = related_assets_map.get(str(asset.id), [])
        related_asset_fields = {}
        related_asset_info = []

        # Define fields to inherit before the loop
        # (infrastructure fields that apps typically inherit from servers)
        inherit_fields = [
            "operating_system_version",
            "virtualization_platform",
            "cpu_memory_storage_specs",
            "network_configuration",
        ]

        for related in related_assets:
            related_fields = DataIntelligence.get_existing_fields(related)
            related_asset_info.append(
                {
                    "name": related.name,
                    "type": related.asset_type,
                    "fields": related_fields,
                }
            )
            # Aggregate values from each related asset (app can have multiple servers)
            for field_name, field_value in related_fields.items():
                if field_name in inherit_fields and field_name not in existing_fields:
                    inherited_key = f"inherited_{field_name}"
                    if inherited_key not in related_asset_fields:
                        related_asset_fields[inherited_key] = {
                            "value": [],
                            "source": [],
                        }

                    # Add unique values to the list
                    if field_value not in related_asset_fields[inherited_key]["value"]:
                        related_asset_fields[inherited_key]["value"].append(field_value)
                        related_asset_fields[inherited_key]["source"].append(
                            f"related_asset:{related.name}"
                        )

        # Get attributes applicable to this asset type (as guidance, not prescription)
        applicable_attrs = AssetTypeRequirements.get_applicable_attributes(
            asset.asset_type
        )

        asset_data = {
            "id": str(asset.id),
            "name": asset.name,
            "type": asset.asset_type,
            "current_fields": existing_fields,  # Data that exists on this asset
            "inherited_from_related_assets": related_asset_fields,  # Data from servers
            "related_assets_count": len(
                related_assets
            ),  # How many servers it depends on
            "applicable_attributes_count": len(
                applicable_attrs
            ),  # Guidance on typical scope
        }

        # Include detailed related asset info if there are related assets
        if related_asset_info:
            asset_data["related_assets"] = related_asset_info

        asset_summary.append(asset_data)

        logger.debug(
            f"Asset {asset.name} ({asset.asset_type}): "
            f"{len(existing_fields)} existing fields, "
            f"{len(related_asset_fields)} inherited fields from {len(related_assets)} related assets, "
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
7. **CHECK INHERITED DATA FROM RELATED ASSETS** - Applications inherit infrastructure data
   from underlying servers. If "inherited_from_related_assets" has data like
   operating_system_version, virtualization_platform, etc., DO NOT create gaps for those!

WHY NO TOOLS:
- You have complete Asset metadata with current_fields
- Data validation tools are for CSV imports, not gap analysis
- Tools would return "0 records" because no raw import data exists at this stage
- Direct analysis is 6x faster and more accurate

**IMPORTANT - RELATED ASSET DATA INHERITANCE (Issue #1193)**:
- Applications often depend on servers (via asset_dependencies)
- Each asset includes "inherited_from_related_assets" showing data from dependent assets
- For APPLICATIONS: If a related SERVER has operating_system, virtualization_platform,
  cpu_memory_storage_specs, or network_configuration, DO NOT create gaps for these fields!
- The inherited data IS the data for the application's infrastructure context
- Example: If "Analytics Engine" (app) depends on "BackupServer-02" (server) with
  operating_system="CentOS 8", DO NOT create an operating_system_version gap for the app

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
