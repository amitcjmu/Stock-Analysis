"""
Compliance Enrichment Agent - Enriches assets with compliance requirements and data classification.

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for learning (memory=False)
- LLM Tracking: Uses multi_model_service.generate_response()

**Target Table**: asset_compliance_flags
**Fields Populated**:
- compliance_scopes: Array of compliance frameworks (SOC2, HIPAA, GDPR, PCI-DSS)
- data_classification: Sensitivity level (public, internal, confidential, restricted)
- residency: Geographic residency requirements
- evidence_refs: Links to compliance evidence/documentation
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


class ComplianceEnrichmentAgent:
    """
    Enriches assets with compliance flags using AI analysis.

    **Enrichment Target**: asset_compliance_flags table

    **Fields Populated**:
    - compliance_scopes: Array of compliance frameworks (SOC2, HIPAA, GDPR, PCI-DSS)
    - data_classification: Sensitivity level (public, internal, confidential, restricted)
    - residency: Geographic residency requirements
    - evidence_refs: Links to compliance evidence/documentation

    **Agent Strategy**:
    1. Retrieve similar patterns from TenantMemoryManager
    2. Use LLM to analyze asset metadata for compliance requirements
    3. Store enrichment in database (future: asset_compliance_flags table)
    4. Store learned patterns back to TenantMemoryManager
    """

    def __init__(
        self,
        db: AsyncSession,
        agent_pool: TenantScopedAgentPool,
        memory_manager: TenantMemoryManager,
        client_account_id: UUID,
        engagement_id: UUID,
    ):
        """
        Initialize ComplianceEnrichmentAgent.

        Args:
            db: Async database session
            agent_pool: Persistent agent pool (ADR-015)
            memory_manager: Tenant memory manager (ADR-024)
            client_account_id: Multi-tenant client account UUID
            engagement_id: Multi-tenant engagement UUID
        """
        self.db = db
        self.agent_pool = agent_pool
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def enrich_assets(self, assets: List[Asset]) -> int:
        """
        Enrich multiple assets with compliance flags.

        Args:
            assets: List of Asset objects to enrich

        Returns:
            Count of successfully enriched assets
        """
        enriched_count = 0

        for asset in assets:
            try:
                # Step 1: Retrieve similar patterns (ADR-024) (scope is implicit via engagement_id)
                patterns = await self.memory_manager.retrieve_similar_patterns(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_type="COMPLIANCE_ANALYSIS",
                    query_context={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                    },
                )

                # Step 2: Build analysis prompt
                prompt = self._build_compliance_prompt(asset, patterns)

                # Step 3: Call LLM via multi_model_service (MANDATORY)
                response = await multi_model_service.generate_response(
                    prompt=prompt,
                    task_type="compliance_analysis",
                    complexity=TaskComplexity.AGENTIC,
                )

                # Step 4: Parse LLM response
                compliance_data = self._parse_compliance_response(response["response"])

                # Step 5: Store enrichment data
                # TODO: Create/update asset_compliance_flags table entry when schema exists
                # For now, store in asset.custom_attributes
                if asset.custom_attributes is None:
                    asset.custom_attributes = {}

                asset.custom_attributes["compliance_enrichment"] = {
                    "compliance_scopes": compliance_data.get("compliance_scopes", []),
                    "data_classification": compliance_data.get("data_classification"),
                    "residency": compliance_data.get("residency"),
                    "confidence": compliance_data.get("confidence", 0.8),
                    "enriched_at": "now",  # Use timestamp in production
                }

                await self.db.flush()

                # Step 6: Store learned pattern (ADR-024)
                await self.memory_manager.store_learning(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="COMPLIANCE_ANALYSIS",
                    pattern_data={
                        "asset_type": asset.asset_type,
                        "technology_stack": asset.technology_stack or [],
                        "compliance_scopes": compliance_data.get("compliance_scopes"),
                        "data_classification": compliance_data.get(
                            "data_classification"
                        ),
                        "confidence": compliance_data.get("confidence", 0.8),
                    },
                )

                enriched_count += 1
                logger.info(
                    f"Enriched asset {asset.id} with compliance data "
                    f"(scopes: {compliance_data.get('compliance_scopes')}, "
                    f"classification: {compliance_data.get('data_classification')})"
                )

            except Exception as e:
                logger.error(f"Failed to enrich asset {asset.id}: {e}", exc_info=True)
                continue

        return enriched_count

    def _build_compliance_prompt(self, asset: Asset, patterns: List[Dict]) -> str:
        """Build LLM prompt for compliance analysis"""
        # Build context from similar patterns
        pattern_context = ""
        if patterns:
            pattern_context = "\n\nSimilar assets compliance patterns:\n"
            for pattern in patterns[:3]:  # Use top 3 most similar
                pattern_data = pattern.get("pattern_data", {})
                scopes = pattern_data.get("compliance_scopes")
                classification = pattern_data.get("data_classification")
                pattern_context += (
                    f"- {pattern_data.get('asset_type')}: {scopes}, {classification}\n"
                )

        return f"""
Analyze the following asset for compliance requirements and data classification:

Asset Name: {asset.asset_name or 'Unknown'}
Asset Type: {asset.asset_type}
Technology Stack: {asset.technology_stack or 'Not specified'}
Data Sensitivity: {getattr(asset, 'data_sensitivity', None) or 'Unknown'}
Environment: {asset.environment or 'Unknown'}
Location: {getattr(asset, 'location', None) or 'Unknown'}

{pattern_context}

Based on this information, determine:

1. **Compliance Scopes**: Which compliance frameworks apply to this asset?
   - SOC2 (Type I or Type II)
   - HIPAA (if healthcare-related data)
   - GDPR (if EU data processing)
   - PCI-DSS (if payment card data)
   - ISO 27001 (if certified environment)
   - FedRAMP (if US government)
   - Other relevant frameworks

2. **Data Classification**: What is the sensitivity level of data handled by this asset?
   - public: Publicly available data, no restrictions
   - internal: Internal use only, not publicly accessible
   - confidential: Sensitive data requiring access controls
   - restricted: Highly sensitive data with strict controls

3. **Residency Requirements**: Are there geographic data residency requirements?
   - Specific regions (e.g., "EU", "US", "APAC")
   - "None" if no restrictions
   - "Unknown" if cannot be determined

Return your analysis in JSON format:
{{
    "compliance_scopes": ["SOC2", "GDPR"],
    "data_classification": "confidential",
    "residency": "EU",
    "confidence": 0.9,
    "reasoning": "Brief explanation of your analysis"
}}

IMPORTANT:
- If information is insufficient, use conservative estimates
- Err on the side of higher compliance requirements (safer)
- Provide confidence score (0.0-1.0) based on data quality
- Include brief reasoning for your classification
"""

    def _parse_compliance_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into compliance data"""
        try:
            # Try to parse JSON response
            data = json.loads(response)

            # Validate and normalize data
            normalized = {
                "compliance_scopes": data.get("compliance_scopes", []),
                "data_classification": data.get("data_classification", "internal"),
                "residency": data.get("residency"),
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

            # Ensure compliance_scopes is a list
            if not isinstance(normalized["compliance_scopes"], list):
                normalized["compliance_scopes"] = [normalized["compliance_scopes"]]

            return normalized

        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            logger.warning(
                f"Failed to parse JSON compliance response: {response[:100]}..."
            )
            return {
                "compliance_scopes": [],
                "data_classification": "internal",
                "residency": None,
                "confidence": 0.3,
                "reasoning": "Failed to parse LLM response",
            }
        except Exception as e:
            logger.error(f"Error parsing compliance response: {e}", exc_info=True)
            return {
                "compliance_scopes": [],
                "data_classification": "internal",
                "residency": None,
                "confidence": 0.0,
                "reasoning": f"Parsing error: {str(e)}",
            }
