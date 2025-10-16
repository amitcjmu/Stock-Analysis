"""
Resilience Enrichment Agent - Enriches assets with HA/DR configuration data.

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for learning (memory=False)
- LLM Tracking: Uses multi_model_service.generate_response()

**Target Table**: asset_resilience
**Fields Populated**:
- resilience_score: Overall resilience score (0-10)
- ha_configuration: 'active-active', 'active-passive', 'none'
- backup_status: 'automated', 'manual', 'none'
- dr_tier: Disaster recovery tier (0-4)
- rto: Recovery Time Objective (minutes)
- rpo: Recovery Point Objective (minutes)
"""

import json
import logging
from typing import Any, Dict, List
from uuid import UUID

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


class ResilienceEnrichmentAgent:
    """
    Enriches assets with HA/DR configuration and resilience data.

    **Enrichment Target**: asset_resilience table

    **Fields Populated**:
    - resilience_score: Overall resilience score (0-10)
    - ha_configuration: High availability setup
    - backup_status: Backup configuration status
    - dr_tier: Disaster recovery tier
    - rto/rpo: Recovery objectives

    **Agent Strategy**:
    1. Analyze asset criticality and environment
    2. Infer likely HA/DR configuration based on best practices
    3. Use LLM to estimate resilience score
    4. Store resilience data
    5. Update asset risk profile
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
        Enrich multiple assets with resilience information.

        Args:
            assets: List of Asset objects to enrich

        Returns:
            Count of successfully enriched assets
        """
        enriched_count = 0

        for asset in assets:
            try:
                # Step 1: Retrieve similar resilience patterns (scope is implicit via engagement_id)
                patterns = await self.memory_manager.retrieve_similar_patterns(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_type="RESILIENCE_ANALYSIS",
                    query_context={
                        "asset_type": asset.asset_type,
                        "business_criticality": asset.business_criticality,
                        "environment": asset.environment,
                    },
                )

                # Step 2: Build analysis prompt
                prompt = self._build_resilience_prompt(asset, patterns)

                # Step 3: Call LLM (automatic tracking)
                response = await multi_model_service.generate_response(
                    prompt=prompt,
                    task_type="resilience_analysis",
                    complexity=TaskComplexity.AGENTIC,
                )

                # Step 4: Parse response
                resilience_data = self._parse_resilience_response(response["response"])

                # Step 5: Store enrichment data
                if asset.custom_attributes is None:
                    asset.custom_attributes = {}

                asset.custom_attributes["resilience_enrichment"] = {
                    "resilience_score": resilience_data.get("resilience_score"),
                    "ha_configuration": resilience_data.get("ha_configuration"),
                    "backup_status": resilience_data.get("backup_status"),
                    "dr_tier": resilience_data.get("dr_tier"),
                    "rto": resilience_data.get("rto"),
                    "rpo": resilience_data.get("rpo"),
                    "confidence": resilience_data.get("confidence", 0.6),
                    "enriched_at": "now",
                }

                await self.db.flush()

                # Step 6: Store learned pattern
                await self.memory_manager.store_learning(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="RESILIENCE_ANALYSIS",
                    pattern_data={
                        "asset_type": asset.asset_type,
                        "business_criticality": asset.business_criticality,
                        "environment": asset.environment,
                        "resilience_score": resilience_data.get("resilience_score"),
                        "ha_configuration": resilience_data.get("ha_configuration"),
                        "dr_tier": resilience_data.get("dr_tier"),
                        "confidence": resilience_data.get("confidence", 0.6),
                    },
                )

                enriched_count += 1
                logger.info(
                    f"Enriched asset {asset.id} with resilience data "
                    f"(score: {resilience_data.get('resilience_score')}, "
                    f"HA: {resilience_data.get('ha_configuration')})"
                )

            except Exception as e:
                logger.error(f"Failed to enrich asset {asset.id}: {e}", exc_info=True)
                continue

        return enriched_count

    def _build_resilience_prompt(self, asset: Asset, patterns: List[Dict]) -> str:
        """Build LLM prompt for resilience analysis"""
        pattern_context = ""
        if patterns:
            pattern_context = "\n\nSimilar assets resilience patterns:\n"
            for pattern in patterns[:3]:
                pattern_data = pattern.get("pattern_data", {})
                env = pattern_data.get("environment")
                crit = pattern_data.get("business_criticality")
                score = pattern_data.get("resilience_score")
                ha = pattern_data.get("ha_configuration")
                pattern_context += f"- {env} ({crit}): Score {score}, HA: {ha}\n"

        return f"""
Analyze the following asset to determine its resilience and HA/DR configuration:

Asset Name: {asset.asset_name or 'Unknown'}
Asset Type: {asset.asset_type}
Business Criticality: {asset.business_criticality or 'Unknown'}
Environment: {asset.environment or 'Unknown'}
Technology Stack: {asset.technology_stack or 'Not specified'}

{pattern_context}

Based on this information, infer:

1. **Resilience Score** (0-10 scale):
   - 0-3: Low resilience, single point of failure
   - 4-6: Moderate resilience, basic redundancy
   - 7-8: High resilience, multi-zone availability
   - 9-10: Very high resilience, multi-region/active-active

2. **HA Configuration**:
   - active-active: Multiple active instances with load balancing
   - active-passive: Primary with standby failover
   - clustered: Multi-node cluster
   - none: No high availability setup

3. **Backup Status**:
   - automated: Automated backup with retention policy
   - manual: Manual backup processes
   - none: No backup configured

4. **DR Tier** (Disaster Recovery Tier, 0-4):
   - Tier 0: Continuous availability (multi-region active-active)
   - Tier 1: Hot standby (RTO < 1 hour, RPO < 15 min)
   - Tier 2: Warm standby (RTO < 4 hours, RPO < 1 hour)
   - Tier 3: Cold standby (RTO < 24 hours, RPO < 4 hours)
   - Tier 4: No DR plan

5. **RTO (Recovery Time Objective)**: Maximum acceptable downtime in minutes
6. **RPO (Recovery Point Objective)**: Maximum acceptable data loss in minutes

Return analysis in JSON format:
{{
    "resilience_score": 7.5,
    "ha_configuration": "active-passive",
    "backup_status": "automated",
    "dr_tier": 1,
    "rto": 60,
    "rpo": 15,
    "confidence": 0.7,
    "reasoning": "Brief explanation based on business criticality and environment"
}}

IMPORTANT:
- Production environments typically have higher resilience requirements
- Critical business assets should have DR tier 0-2
- Non-production can have DR tier 3-4
- Estimate based on industry best practices if data is incomplete
"""

    def _parse_resilience_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into resilience data"""
        try:
            data = json.loads(response)

            normalized = {
                "resilience_score": float(data.get("resilience_score", 5.0)),
                "ha_configuration": data.get("ha_configuration", "none"),
                "backup_status": data.get("backup_status", "none"),
                "dr_tier": int(data.get("dr_tier", 4)),
                "rto": (
                    int(data.get("rto", 1440)) if data.get("rto") else None
                ),  # 24h default
                "rpo": (
                    int(data.get("rpo", 240)) if data.get("rpo") else None
                ),  # 4h default
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

            # Validate ranges
            normalized["resilience_score"] = max(
                0.0, min(10.0, normalized["resilience_score"])
            )
            normalized["dr_tier"] = max(0, min(4, normalized["dr_tier"]))

            return normalized

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse resilience response: {response[:100]}..., error: {e}"
            )
            return {
                "resilience_score": 5.0,
                "ha_configuration": "none",
                "backup_status": "none",
                "dr_tier": 4,
                "rto": None,
                "rpo": None,
                "confidence": 0.3,
                "reasoning": "Failed to parse LLM response",
            }
