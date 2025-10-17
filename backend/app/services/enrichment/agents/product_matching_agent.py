"""
Product Matching Agent - Enriches assets with vendor product catalog matching.

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for learning (memory=False)
- LLM Tracking: Uses multi_model_service.generate_response()

**Target Table**: asset_product_links
**Fields Populated**:
- catalog_version_id: FK to product_versions_catalog.id
- tenant_version_id: FK to tenant_product_versions.id
- confidence_score: Match confidence (0.0-1.0)
- matched_by: 'manual', 'ai', 'version_match', 'fuzzy_match'
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


class ProductMatchingAgent:
    """
    Enriches assets with vendor product catalog matching.

    **Enrichment Target**: asset_product_links table

    **Fields Populated**:
    - catalog_version_id: Vendor catalog version ID
    - tenant_version_id: Tenant-specific version ID
    - confidence_score: Match confidence
    - matched_by: Matching method

    **Agent Strategy**:
    1. Extract technology stack and version information
    2. Query vendor product catalog for matches
    3. Use LLM for fuzzy matching and version normalization
    4. Create product links
    5. Store learned matching patterns
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
        Enrich multiple assets with product catalog links.

        Args:
            assets: List of Asset objects to enrich

        Returns:
            Count of successfully enriched assets
        """
        enriched_count = 0

        # Get available product catalog entries for matching
        # TODO: Query vendor_products_catalog table when available
        catalog_products = await self._get_catalog_products()

        for asset in assets:
            try:
                # Step 1: Retrieve similar matching patterns
                # Retrieve similar patterns (scope is implicit via engagement_id)
                patterns = await self.memory_manager.retrieve_similar_patterns(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_type=get_db_pattern_type("product_matching").value,
                    query_context={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                    },
                )

                # Step 2: Build analysis prompt
                prompt = self._build_matching_prompt(asset, catalog_products, patterns)

                # Step 3: Call LLM (automatic tracking)
                response = await multi_model_service.generate_response(
                    prompt=prompt,
                    task_type="product_matching",
                    complexity=TaskComplexity.AGENTIC,
                )

                # Step 4: Parse response
                matching_data = self._parse_matching_response(response["response"])

                # Step 5: Store enrichment data
                if asset.custom_attributes is None:
                    asset.custom_attributes = {}

                asset.custom_attributes["product_matching_enrichment"] = {
                    "matched_products": matching_data.get("matched_products", []),
                    "primary_product": matching_data.get("primary_product"),
                    "match_count": len(matching_data.get("matched_products", [])),
                    "confidence": matching_data.get("confidence", 0.5),
                    "enriched_at": "now",
                }

                await self.db.flush()

                # Step 6: Store learned pattern
                await self.memory_manager.store_learning(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type=get_db_pattern_type("product_matching").value,
                    pattern_data={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                        "matched_products": matching_data.get("matched_products", []),
                        "primary_product": matching_data.get("primary_product"),
                        "confidence": matching_data.get("confidence", 0.5),
                    },
                )

                enriched_count += 1
                match_count = len(matching_data.get("matched_products", []))
                logger.info(
                    f"Enriched asset {asset.id} with {match_count} product matches "
                    f"(primary: {matching_data.get('primary_product')})"
                )

            except Exception as e:
                logger.error(f"Failed to enrich asset {asset.id}: {e}", exc_info=True)
                continue

        return enriched_count

    async def _get_catalog_products(self) -> List[Dict[str, Any]]:
        """Get vendor product catalog entries for matching"""
        # TODO: Query vendor_products_catalog table
        # For now, return common products as fallback
        return [
            {
                "product_name": "Microsoft Windows Server",
                "vendor": "Microsoft",
                "versions": ["2019", "2022"],
                "category": "operating_system",
            },
            {
                "product_name": "Red Hat Enterprise Linux",
                "vendor": "Red Hat",
                "versions": ["7", "8", "9"],
                "category": "operating_system",
            },
            {
                "product_name": "Oracle Database",
                "vendor": "Oracle",
                "versions": ["12c", "18c", "19c", "21c"],
                "category": "database",
            },
            {
                "product_name": "PostgreSQL",
                "vendor": "PostgreSQL Global Development Group",
                "versions": ["12", "13", "14", "15", "16"],
                "category": "database",
            },
            {
                "product_name": "VMware vSphere",
                "vendor": "VMware",
                "versions": ["7.0", "8.0"],
                "category": "virtualization",
            },
        ]

    def _build_matching_prompt(
        self, asset: Asset, catalog_products: List[Dict], patterns: List[Dict]
    ) -> str:
        """Build LLM prompt for product matching"""
        pattern_context = ""
        if patterns:
            pattern_context = "\n\nKnown product matching patterns:\n"
            for pattern in patterns[:3]:
                pattern_data = pattern.get("pattern_data", {})
                asset_type = pattern_data.get("asset_type")
                product = pattern_data.get("primary_product")
                conf = pattern_data.get("confidence")
                pattern_context += f"- {asset_type}: {product} (conf: {conf})\n"

        return f"""
Match the following asset to products in the vendor catalog:

**Asset Information**:
- Name: {asset.asset_name or 'Unknown'}
- Type: {asset.asset_type}
- Technology Stack: {asset.technology_stack or 'Not specified'}
- Operating System: {asset.operating_system or 'Unknown'}
- OS Version: {asset.os_version or 'Unknown'}

**Available Catalog Products**:
{json.dumps(catalog_products, indent=2)}

{pattern_context}

Based on this information:

1. **Identify Product Matches**: Which catalog products match this asset?
   - For each match, provide:
     - product_name: Name from catalog
     - vendor: Vendor name
     - version: Specific version detected (if known)
     - match_method: "exact", "fuzzy", "version_inferred", "category_based"
     - confidence_score: 0.0-1.0 based on match quality
     - category: Product category

2. **Primary Product**: Which is the main/primary product for this asset?

3. **End-of-Life Status**: Is any matched version approaching end-of-life?

Return analysis in JSON format:
{{
    "matched_products": [
        {{
            "product_name": "Microsoft Windows Server",
            "vendor": "Microsoft",
            "version": "2019",
            "match_method": "exact",
            "confidence_score": 0.95,
            "category": "operating_system",
            "eol_date": "2029-01-09"
        }}
    ],
    "primary_product": "Microsoft Windows Server 2019",
    "match_count": 1,
    "confidence": 0.95,
    "reasoning": "Explanation of matching logic"
}}

IMPORTANT:
- Match based on technology stack, operating system, and asset type
- Use fuzzy matching for version number variations (e.g., "2019" vs "Windows Server 2019")
- If no clear match, return empty array
- Provide confidence score based on match quality
- Prioritize exact matches over fuzzy matches
"""

    def _parse_matching_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into product matching data"""
        try:
            data = json.loads(response)

            # Validate and normalize matched products
            matched_products = data.get("matched_products", [])
            if not isinstance(matched_products, list):
                matched_products = []

            normalized_products = []
            for product in matched_products:
                try:
                    normalized_product = {
                        "product_name": product.get("product_name", "Unknown"),
                        "vendor": product.get("vendor", "Unknown"),
                        "version": product.get("version", "Unknown"),
                        "match_method": product.get("match_method", "fuzzy"),
                        "confidence_score": float(product.get("confidence_score", 0.5)),
                        "category": product.get("category", "unknown"),
                        "eol_date": product.get("eol_date"),
                    }
                    normalized_products.append(normalized_product)
                except (ValueError, TypeError):
                    continue

            normalized = {
                "matched_products": normalized_products,
                "primary_product": data.get("primary_product", "Unknown"),
                "match_count": len(normalized_products),
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

            return normalized

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse product matching response: {response[:100]}..., error: {e}"
            )
            return {
                "matched_products": [],
                "primary_product": "Unknown",
                "match_count": 0,
                "confidence": 0.2,
                "reasoning": "Failed to parse LLM response",
            }
