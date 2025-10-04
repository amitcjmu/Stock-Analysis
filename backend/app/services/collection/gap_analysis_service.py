"""
Lean Gap Analysis Service - Single Persistent Agent

Uses TenantScopedAgentPool (ADR-015) for gap detection and questionnaire generation.
Replaces bloated 3-agent crew (gap_specialist, sixr_impact_assessor, gap_prioritizer)
with direct asset comparison and single-task questionnaire generation.
"""

import json
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap

logger = logging.getLogger(__name__)


class GapAnalysisService:
    """
    Lean gap analysis using single persistent agent.

    Loads REAL assets from database, compares against 22 critical attributes,
    identifies gaps, and generates questionnaires - all in one atomic operation.
    """

    def __init__(
        self,
        client_account_id: str,
        engagement_id: str,
        collection_flow_id: str,
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.collection_flow_id = collection_flow_id

    async def analyze_and_generate_questionnaire(
        self,
        selected_asset_ids: List[str],
        db: AsyncSession,
        automation_tier: str = "tier_2",
    ) -> Dict[str, Any]:
        """
        Single atomic operation: Load assets, detect gaps, generate questionnaire.

        Args:
            selected_asset_ids: UUIDs of assets selected for gap analysis
            db: Database session
            automation_tier: Automation tier for agent configuration

        Returns:
            {
                "gaps": {
                    "critical": [...],
                    "high": [...],
                    "medium": [...],
                    "low": [...]
                },
                "questionnaire": {
                    "sections": [...]
                },
                "summary": {
                    "total_gaps": int,
                    "assets_analyzed": int
                }
            }
        """
        try:
            # 1. Load REAL assets from database
            assets = await self._load_assets(selected_asset_ids, db)
            if not assets:
                logger.warning("No assets found for gap analysis")
                return self._empty_result()

            logger.info(f"📦 Loaded {len(assets)} real assets for gap analysis")

            # 2. Get single persistent agent
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_type="gap_analysis_specialist",
            )

            # 3. Create single task: analyze + generate questionnaire
            from crewai import Task

            task = Task(
                description=self._build_task_description(assets),
                agent=agent,
                expected_output="JSON with gaps and questionnaire structure",
            )

            # 4. Execute task
            logger.info("🤖 Executing single-agent gap analysis task")
            task_output = await task.execute_async()

            # 5. Parse result
            result_dict = self._parse_task_output(task_output)

            # 6. Persist gaps to database
            gaps_count = await self._persist_gaps(result_dict, assets, db)
            result_dict["summary"]["gaps_persisted"] = gaps_count

            logger.info(
                f"✅ Gap analysis complete: {gaps_count} gaps persisted, {len(assets)} assets analyzed"
            )

            return result_dict

        except Exception as e:
            logger.error(f"Gap analysis failed: {e}", exc_info=True)
            return self._error_result(str(e))

    async def _load_assets(
        self, selected_asset_ids: List[str], db: AsyncSession
    ) -> List[Asset]:
        """Load REAL assets from database."""
        asset_uuids = [
            UUID(aid) if isinstance(aid, str) else aid for aid in selected_asset_ids
        ]

        stmt = select(Asset).where(
            and_(
                Asset.id.in_(asset_uuids),
                Asset.client_account_id == str(self.client_account_id),
                Asset.engagement_id == str(self.engagement_id),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def _build_task_description(self, assets: List[Asset]) -> str:
        """Build task description with REAL asset data."""
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
                            asset_data["current_fields"][attr_name] = getattr(
                                asset, field
                            )

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

    def _parse_task_output(self, task_output: Any) -> Dict[str, Any]:
        """Parse task output with proper error handling."""
        raw_output = (
            task_output.raw if hasattr(task_output, "raw") else str(task_output)
        )

        try:
            # Try to parse as JSON
            result = json.loads(raw_output)

            # Ensure required structure exists
            if "gaps" not in result:
                result["gaps"] = {}
            if "questionnaire" not in result:
                result["questionnaire"] = {"sections": []}
            if "summary" not in result:
                result["summary"] = {
                    "total_gaps": 0,
                    "assets_analyzed": 0,
                }

            return result

        except json.JSONDecodeError:
            logger.warning("Task output not valid JSON, attempting to extract data")

            # Try to find JSON in the text
            import re

            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # Return minimal structure with raw output
            return {
                "gaps": {},
                "questionnaire": {"sections": []},
                "summary": {"total_gaps": 0, "assets_analyzed": 0},
                "raw_output": raw_output,
            }

    async def _persist_gaps(
        self, result_dict: Dict[str, Any], assets: List[Asset], db: AsyncSession
    ) -> int:
        """Persist gaps to collection_data_gaps table."""
        gaps_by_priority = result_dict.get("gaps", {})
        gaps_persisted = 0

        for priority_level, gaps in gaps_by_priority.items():
            if not isinstance(gaps, list):
                continue

            priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
            priority_value = priority_map.get(priority_level, 3)

            for gap in gaps:
                try:
                    gap_record = CollectionDataGap(
                        collection_flow_id=UUID(self.collection_flow_id),
                        gap_type=gap.get("gap_type", "missing_field"),
                        gap_category=gap.get("gap_category", "unknown"),
                        field_name=gap.get("field_name", "unknown"),
                        description=gap.get("description", ""),
                        impact_on_sixr=gap.get("impact_on_sixr", "medium"),
                        priority=priority_value,
                        suggested_resolution=gap.get(
                            "suggested_resolution",
                            "Manual collection required",
                        ),
                        resolution_status="pending",
                        gap_metadata={
                            "asset_id": gap.get("asset_id"),
                            "priority_level": priority_level,
                        },
                    )

                    db.add(gap_record)
                    gaps_persisted += 1

                except Exception as e:
                    logger.error(f"Failed to persist gap: {e}")
                    continue

        await db.commit()
        logger.info(f"💾 Persisted {gaps_persisted} gaps to database")

        return gaps_persisted

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no assets found."""
        return {
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0, "gaps_persisted": 0},
        }

    def _error_result(self, error: str) -> Dict[str, Any]:
        """Return error result."""
        return {
            "status": "error",
            "error": error,
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0, "gaps_persisted": 0},
        }
