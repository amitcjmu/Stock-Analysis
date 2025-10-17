"""
Licensing Enrichment Agent - Enriches assets with software licensing information.

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for learning (memory=False)
- LLM Tracking: Uses multi_model_service.generate_response()

**Target Table**: asset_licenses
**Fields Populated**:
- license_type: 'perpetual', 'subscription', 'concurrent', 'open_source'
- license_count: Number of licenses
- annual_cost: Annual licensing cost
- expiration_date: License expiration date
- vendor_name: Software vendor name
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
from app.services.enrichment.constants import get_db_pattern_type
from app.services.multi_model_service import TaskComplexity, multi_model_service
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class LicensingEnrichmentAgent:
    """
    Enriches assets with software licensing information.

    **Enrichment Target**: asset_licenses table

    **Fields Populated**:
    - license_type: Type of license (perpetual, subscription, etc.)
    - license_count: Number of licenses
    - annual_cost: Annual licensing cost
    - expiration_date: License expiration date
    - vendor_name: Software vendor

    **Agent Strategy**:
    1. Analyze technology stack for known software products
    2. Retrieve similar licensing patterns from TenantMemoryManager
    3. Use LLM to infer licensing model and costs
    4. Store enrichment data
    5. Store learned patterns
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
        Enrich multiple assets with licensing information.

        Args:
            assets: List of Asset objects to enrich

        Returns:
            Count of successfully enriched assets
        """
        enriched_count = 0

        for asset in assets:
            try:
                # Step 1: Retrieve similar patterns (scope is implicit via engagement_id)
                patterns = await self.memory_manager.retrieve_similar_patterns(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_type=get_db_pattern_type("licensing_analysis").value,
                    query_context={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                    },
                )

                # Step 2: Build analysis prompt
                prompt = self._build_licensing_prompt(asset, patterns)

                # Step 3: Call LLM (automatic tracking)
                response = await multi_model_service.generate_response(
                    prompt=prompt,
                    task_type="licensing_analysis",
                    complexity=TaskComplexity.AGENTIC,
                )

                # Step 4: Parse response
                licensing_data = self._parse_licensing_response(response["response"])

                # Step 5: Store enrichment data
                if asset.custom_attributes is None:
                    asset.custom_attributes = {}

                asset.custom_attributes["licensing_enrichment"] = {
                    "license_type": licensing_data.get("license_type"),
                    "license_count": licensing_data.get("license_count"),
                    "annual_cost": licensing_data.get("annual_cost"),
                    "expiration_date": licensing_data.get("expiration_date"),
                    "vendor_name": licensing_data.get("vendor_name"),
                    "confidence": licensing_data.get("confidence", 0.7),
                    "enriched_at": "now",
                }

                await self.db.flush()

                # Step 6: Store learned pattern
                await self.memory_manager.store_learning(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type=get_db_pattern_type("licensing_analysis").value,
                    pattern_data={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                        "license_type": licensing_data.get("license_type"),
                        "vendor_name": licensing_data.get("vendor_name"),
                        "annual_cost": licensing_data.get("annual_cost"),
                        "confidence": licensing_data.get("confidence", 0.7),
                    },
                )

                enriched_count += 1
                logger.info(
                    f"Enriched asset {asset.id} with licensing data "
                    f"(type: {licensing_data.get('license_type')}, "
                    f"vendor: {licensing_data.get('vendor_name')})"
                )

            except Exception as e:
                logger.error(f"Failed to enrich asset {asset.id}: {e}", exc_info=True)
                continue

        return enriched_count

    def _build_licensing_prompt(self, asset: Asset, patterns: List[Dict]) -> str:
        """Build LLM prompt for licensing analysis"""
        pattern_context = ""
        if patterns:
            pattern_context = "\n\nSimilar assets licensing patterns:\n"
            for pattern in patterns[:3]:
                pattern_data = pattern.get("pattern_data", {})
                vendor = pattern_data.get("vendor_name")
                lic_type = pattern_data.get("license_type")
                cost = pattern_data.get("annual_cost", "N/A")
                pattern_context += f"- {vendor}: {lic_type}, ${cost}/year\n"

        return f"""
Analyze the following asset to determine software licensing information:

Asset Name: {asset.asset_name or 'Unknown'}
Asset Type: {asset.asset_type}
Technology Stack: {asset.technology_stack or 'Not specified'}
Operating System: {asset.operating_system or 'Unknown'}

{pattern_context}

Based on this information, infer:

1. **License Type**: What type of software license is likely used?
   - perpetual: One-time purchase, lifetime use
   - subscription: Ongoing subscription (monthly/annual)
   - concurrent: Per-concurrent-user licensing
   - open_source: Open source software (no licensing cost)
   - proprietary_free: Proprietary but free to use

2. **Vendor Name**: Primary software vendor (e.g., Microsoft, Oracle, Red Hat)

3. **License Count**: Estimated number of licenses (based on asset specs)

4. **Annual Cost**: Estimated annual licensing cost in USD
   - For open source: $0
   - For commercial: research typical pricing

5. **Expiration Date**: If subscription, typical renewal cycle (e.g., "1 year from now", "Unknown")

Return analysis in JSON format:
{{
    "license_type": "subscription",
    "vendor_name": "Microsoft",
    "license_count": 1,
    "annual_cost": 1200.00,
    "expiration_date": "2026-01-01",
    "confidence": 0.8,
    "reasoning": "Brief explanation"
}}

IMPORTANT:
- For open source software, set annual_cost to 0
- If cost cannot be determined, use null
- Provide realistic cost estimates based on market rates
- Include confidence score based on data quality
"""

    def _parse_licensing_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into licensing data"""
        try:
            data = json.loads(response)

            normalized = {
                "license_type": data.get("license_type", "unknown"),
                "vendor_name": data.get("vendor_name", "Unknown"),
                "license_count": int(data.get("license_count", 1)),
                "annual_cost": (
                    float(data.get("annual_cost", 0.0))
                    if data.get("annual_cost") is not None
                    else None
                ),
                "expiration_date": data.get("expiration_date"),
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

            return normalized

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse licensing response: {response[:100]}..., error: {e}"
            )
            return {
                "license_type": "unknown",
                "vendor_name": "Unknown",
                "license_count": 1,
                "annual_cost": None,
                "expiration_date": None,
                "confidence": 0.3,
                "reasoning": "Failed to parse LLM response",
            }
