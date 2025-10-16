"""
Dependency Enrichment Agent - Enriches assets with dependency relationship mapping.

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for learning (memory=False)
- LLM Tracking: Uses multi_model_service.generate_response()

**Target Table**: asset_dependencies
**Fields Populated**:
- depends_on_asset_id: FK to assets.id (dependency target)
- dependency_type: 'network', 'database', 'service', 'data'
- criticality: 'critical', 'high', 'medium', 'low'
- bidirectional: Boolean indicating two-way dependency
"""

import json
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.multi_model_service import TaskComplexity, multi_model_service
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class DependencyEnrichmentAgent:
    """
    Enriches assets with dependency relationship mapping.

    **Enrichment Target**: asset_dependencies table

    **Fields Populated**:
    - depends_on_asset_id: Target asset UUID
    - dependency_type: Type of dependency
    - criticality: Dependency criticality level
    - bidirectional: Two-way dependency flag

    **Agent Strategy**:
    1. Analyze asset type and technology stack
    2. Query all assets in environment for potential dependencies
    3. Use LLM to infer likely dependencies
    4. Create dependency relationships
    5. Store learned dependency patterns
    """

    def __init__(
        self,
        db: AsyncSession,
        agent_pool: TenantScopedAgentPool,
        memory_manager: TenantMemoryManager,
        client_account_id: UUID,
        engagement_id: UUID,
    ):
        self.db = db
        self.agent_pool = agent_pool
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def enrich_assets(self, assets: List[Asset]) -> int:
        """
        Enrich multiple assets with dependency information.

        Args:
            assets: List of Asset objects to enrich

        Returns:
            Count of successfully enriched assets
        """
        enriched_count = 0

        # Get all assets in environment for dependency matching
        all_assets = await self._get_all_assets_for_matching()

        for asset in assets:
            try:
                # Step 1: Retrieve similar dependency patterns (scope is implicit via engagement_id)
                patterns = await self.memory_manager.retrieve_similar_patterns(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_type="DEPENDENCY_ANALYSIS",
                    query_context={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                    },
                )

                # Step 2: Build analysis prompt
                prompt = self._build_dependency_prompt(asset, all_assets, patterns)

                # Step 3: Call LLM (automatic tracking)
                response = await multi_model_service.generate_response(
                    prompt=prompt,
                    task_type="dependency_analysis",
                    complexity=TaskComplexity.AGENTIC,
                )

                # Step 4: Parse response
                dependency_data = self._parse_dependency_response(
                    response["response"], all_assets
                )

                # Step 5: Store enrichment data
                if asset.custom_attributes is None:
                    asset.custom_attributes = {}

                asset.custom_attributes["dependency_enrichment"] = {
                    "dependencies": dependency_data.get("dependencies", []),
                    "dependency_count": len(dependency_data.get("dependencies", [])),
                    "critical_dependencies": dependency_data.get(
                        "critical_dependencies", 0
                    ),
                    "confidence": dependency_data.get("confidence", 0.5),
                    "enriched_at": "now",
                }

                await self.db.flush()

                # Step 6: Store learned pattern
                await self.memory_manager.store_learning(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="DEPENDENCY_ANALYSIS",
                    pattern_data={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                        "dependency_count": len(
                            dependency_data.get("dependencies", [])
                        ),
                        "dependency_types": [
                            d.get("dependency_type")
                            for d in dependency_data.get("dependencies", [])
                        ],
                        "confidence": dependency_data.get("confidence", 0.5),
                    },
                )

                enriched_count += 1
                dep_count = len(dependency_data.get("dependencies", []))
                logger.info(
                    f"Enriched asset {asset.id} with {dep_count} dependencies "
                    f"(critical: {dependency_data.get('critical_dependencies', 0)})"
                )

            except Exception as e:
                logger.error(f"Failed to enrich asset {asset.id}: {e}", exc_info=True)
                continue

        return enriched_count

    async def _get_all_assets_for_matching(self) -> List[Asset]:
        """Get all assets in engagement for dependency matching"""
        query = select(Asset).where(
            Asset.client_account_id == self.client_account_id,
            Asset.engagement_id == self.engagement_id,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _build_dependency_prompt(
        self, asset: Asset, all_assets: List[Asset], patterns: List[Dict]
    ) -> str:
        """Build LLM prompt for dependency analysis"""
        # Build list of potential dependency targets
        potential_dependencies = []
        for other_asset in all_assets[:50]:  # Limit to first 50 to avoid token overflow
            if other_asset.id != asset.id:  # Don't include self
                potential_dependencies.append(
                    {
                        "asset_name": other_asset.asset_name,
                        "asset_type": other_asset.asset_type,
                        "technology_stack": other_asset.technology_stack or [],
                    }
                )

        pattern_context = ""
        if patterns:
            pattern_context = "\n\nKnown dependency patterns:\n"
            for pattern in patterns[:3]:
                pattern_data = pattern.get("pattern_data", {})
                dep_count = pattern_data.get("dependency_count")
                dep_types = pattern_data.get("dependency_types")
                asset_type = pattern_data.get("asset_type")
                pattern_context += (
                    f"- {asset_type}: {dep_count} deps, types: {dep_types}\n"
                )

        return f"""
Analyze the following asset to identify its dependencies on other assets:

**Current Asset**:
- Name: {asset.asset_name or 'Unknown'}
- Type: {asset.asset_type}
- Technology Stack: {asset.technology_stack or 'Not specified'}
- Environment: {asset.environment or 'Unknown'}

**Available Assets** (potential dependencies):
{json.dumps(potential_dependencies[:20], indent=2)}

{pattern_context}

Based on this information, identify:

1. **Dependencies**: Which assets does this asset depend on?
   - For each dependency, provide:
     - depends_on_asset_name: Name of the target asset
     - dependency_type: "network", "database", "service", "data", or "api"
     - criticality: "critical" (cannot function without),
       "high" (degraded function), "medium" (optional), "low" (nice-to-have)
     - bidirectional: true if both assets depend on each other, false otherwise
     - description: Brief explanation of the dependency

2. **Dependency Analysis**:
   - Total number of dependencies
   - Number of critical dependencies
   - Recommended migration wave (assets with fewer dependencies migrate first)

Return analysis in JSON format:
{{
    "dependencies": [
        {{
            "depends_on_asset_name": "DatabaseServer01",
            "dependency_type": "database",
            "criticality": "critical",
            "bidirectional": false,
            "description": "Primary database for application data"
        }}
    ],
    "dependency_count": 1,
    "critical_dependencies": 1,
    "recommended_wave": 2,
    "confidence": 0.8,
    "reasoning": "Explanation of dependency analysis"
}}

IMPORTANT:
- Only include dependencies where there is a clear technical relationship
- Network dependencies: Asset communicates over network
- Database dependencies: Asset reads/writes to database
- Service dependencies: Asset calls API/service endpoints
- Data dependencies: Asset consumes/produces data files
- If no clear dependencies, return empty array
- Provide confidence score based on data quality
"""

    def _parse_dependency_response(
        self, response: str, all_assets: List[Asset]
    ) -> Dict[str, Any]:
        """Parse LLM response into dependency data"""
        try:
            data = json.loads(response)

            # Build asset name to ID mapping
            asset_name_to_id = {
                asset.asset_name: asset.id for asset in all_assets if asset.asset_name
            }

            # Validate and normalize dependencies
            dependencies = data.get("dependencies", [])
            if not isinstance(dependencies, list):
                dependencies = []

            normalized_deps = []
            for dep in dependencies:
                try:
                    dep_name = dep.get("depends_on_asset_name")
                    # Try to resolve asset name to ID
                    dep_asset_id = asset_name_to_id.get(dep_name)

                    if dep_asset_id:  # Only include if we can resolve the asset
                        normalized_dep = {
                            "depends_on_asset_name": dep_name,
                            "depends_on_asset_id": str(dep_asset_id),
                            "dependency_type": dep.get("dependency_type", "network"),
                            "criticality": dep.get("criticality", "medium"),
                            "bidirectional": bool(dep.get("bidirectional", False)),
                            "description": dep.get("description", ""),
                        }
                        normalized_deps.append(normalized_dep)
                except (ValueError, TypeError):
                    continue

            # Count critical dependencies
            critical_count = sum(
                1 for d in normalized_deps if d.get("criticality") == "critical"
            )

            normalized = {
                "dependencies": normalized_deps,
                "dependency_count": len(normalized_deps),
                "critical_dependencies": critical_count,
                "recommended_wave": int(data.get("recommended_wave", 1)),
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

            return normalized

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse dependency response: {response[:100]}..., error: {e}"
            )
            return {
                "dependencies": [],
                "dependency_count": 0,
                "critical_dependencies": 0,
                "recommended_wave": 1,
                "confidence": 0.2,
                "reasoning": "Failed to parse LLM response",
            }
