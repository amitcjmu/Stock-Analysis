"""
AutoEnrichmentPipeline - Automated enrichment pipeline for assets using AI agents.

**CRITICAL ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents (NO per-call Crew instantiation)
- ADR-024: Uses TenantMemoryManager for agent learning (CrewAI memory=False)
- LLM Tracking: ALL LLM calls use multi_model_service.generate_response()

**Enrichment Tables** (7 total):
1. asset_compliance_flags - Compliance requirements, data classification
2. asset_licenses - Software licensing information
3. asset_vulnerabilities - Security vulnerabilities (CVE tracking)
4. asset_resilience - HA/DR configuration
5. asset_dependencies - Asset relationship mapping
6. asset_product_links - Vendor product catalog matching
7. asset_field_conflicts - Multi-source conflict resolution

**Performance Target**: 100 assets < 10 minutes
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

# Import enrichment executors (modularized for 400-line limit compliance)
from app.services.enrichment.enrichment_executors import (
    enrich_compliance,
    enrich_dependencies,
    enrich_field_conflicts,
    enrich_licenses,
    enrich_product_links,
    enrich_resilience,
    enrich_vulnerabilities,
)

logger = logging.getLogger(__name__)

# Enrichment types for tracking
ENRICHMENT_TYPES = [
    "compliance_flags",
    "licenses",
    "vulnerabilities",
    "resilience",
    "dependencies",
    "product_links",
    "field_conflicts",
]

# Critical attributes for assessment readiness (22 total)
CRITICAL_ATTRIBUTES = {
    "infrastructure": [
        "application_name",
        "technology_stack",
        "operating_system",
        "cpu_cores",
        "memory_gb",
        "storage_gb",
    ],
    "application": [
        "business_criticality",
        "application_type",
        "architecture_pattern",
        "dependencies",
        "user_base",
        "data_sensitivity",
        "compliance_requirements",
        "sla_requirements",
    ],
    "business": [
        "business_owner",
        "annual_operating_cost",
        "business_value",
        "strategic_importance",
    ],
    "technical_debt": [
        "code_quality_score",
        "last_update_date",
        "support_status",
        "known_vulnerabilities",
    ],
}


class AutoEnrichmentPipeline:
    """
    Automated enrichment pipeline for assets using AI agents.

    **CRITICAL ADR COMPLIANCE**:
    - Uses TenantScopedAgentPool for persistent agents (ADR-015)
    - Uses TenantMemoryManager for agent learning (ADR-024, memory=False)
    - Uses multi_model_service for ALL LLM calls (automatic tracking)

    **Enrichment Tables** (7 total):
    1. asset_compliance_flags - Compliance requirements, data classification
    2. asset_licenses - Software licensing information
    3. asset_vulnerabilities - Security vulnerabilities (CVE tracking)
    4. asset_resilience - HA/DR configuration
    5. asset_dependencies - Asset relationship mapping
    6. asset_product_links - Vendor product catalog matching
    7. asset_field_conflicts - Multi-source conflict resolution

    **Performance Target**: 100 assets < 10 minutes
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        """
        Initialize enrichment pipeline with database session and tenant context.

        Args:
            db: Async SQLAlchemy session
            client_account_id: Multi-tenant client account UUID
            engagement_id: Multi-tenant engagement UUID
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize TenantScopedAgentPool (ADR-015)
        # Agents are retrieved from pool, not instantiated per execution
        self.agent_pool = TenantScopedAgentPool

        # Initialize TenantMemoryManager (ADR-024)
        # CrewAI memory is DISABLED, use TenantMemoryManager instead
        self.memory_manager = TenantMemoryManager(
            crewai_service=None,  # Not using CrewAI memory
            database_session=db,
        )

        logger.info(
            f"Initialized AutoEnrichmentPipeline for client {client_account_id}, "
            f"engagement {engagement_id}"
        )

    async def trigger_auto_enrichment(self, asset_ids: List[UUID]) -> Dict[str, Any]:
        """
        Trigger automated enrichment for specified assets.

        **Execution Pattern**:
        1. Retrieve assets from database
        2. For each enrichment type, run agent concurrently with asyncio.gather()
        3. Store learned patterns via TenantMemoryManager
        4. Recalculate assessment readiness
        5. Return enrichment statistics

        Args:
            asset_ids: List of asset UUIDs to enrich

        Returns:
            Dict with enrichment statistics:
            {
                "total_assets": 10,
                "enrichment_results": {
                    "compliance_flags": 8,
                    "licenses": 7,
                    "vulnerabilities": 10,
                    "resilience": 6,
                    "dependencies": 9,
                    "product_links": 5,
                    "field_conflicts": 0
                },
                "elapsed_time_seconds": 45.2
            }
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting auto-enrichment for {len(asset_ids)} assets")

        try:
            # Step 1: Query assets with tenant scoping (CRITICAL)
            assets_query = select(Asset).where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(assets_query)
            assets = result.scalars().all()

            if not assets:
                logger.warning(f"No assets found for enrichment with IDs: {asset_ids}")
                return {
                    "total_assets": 0,
                    "enrichment_results": {
                        enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
                    },
                    "elapsed_time_seconds": 0.0,
                    "error": "No assets found",
                }

            logger.info(f"Retrieved {len(assets)} assets for enrichment")

            # Step 2: Run ALL enrichment agents concurrently
            # This is the performance optimization - parallel execution
            # Call executor functions with necessary context
            enrichment_tasks = [
                enrich_compliance(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_licenses(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_vulnerabilities(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_resilience(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_dependencies(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_product_links(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
                enrich_field_conflicts(
                    assets,
                    self.db,
                    self.agent_pool,
                    self.memory_manager,
                    self.client_account_id,
                    self.engagement_id,
                ),
            ]

            # Execute concurrently with error handling
            results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

            # Step 3: Aggregate results
            enrichment_stats = {}
            for i, result in enumerate(results):
                enrichment_type = ENRICHMENT_TYPES[i]
                if isinstance(result, Exception):
                    logger.error(f"Enrichment task {enrichment_type} failed: {result}")
                    enrichment_stats[enrichment_type] = 0
                else:
                    enrichment_stats[enrichment_type] = result
                    logger.info(
                        f"Enrichment task {enrichment_type} completed: {result} assets"
                    )

            # Step 4: Recalculate assessment readiness
            await self._recalculate_readiness(asset_ids)

            # Calculate elapsed time
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Auto-enrichment completed for {len(assets)} assets in {elapsed_time:.2f}s"
            )

            return {
                "total_assets": len(assets),
                "enrichment_results": enrichment_stats,
                "elapsed_time_seconds": elapsed_time,
            }

        except Exception as e:
            logger.error(f"Auto-enrichment pipeline failed: {e}", exc_info=True)
            return {
                "total_assets": 0,
                "enrichment_results": {
                    enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
                },
                "elapsed_time_seconds": (
                    datetime.utcnow() - start_time
                ).total_seconds(),
                "error": str(e),
            }

    async def _recalculate_readiness(self, asset_ids: List[UUID]) -> None:
        """
        Recalculate assessment readiness after enrichment.

        Updates:
        - assessment_readiness: 'ready', 'not_ready', 'in_progress'
        - assessment_readiness_score: 0.0-1.0 based on 22 critical attributes
        - assessment_blockers: List of missing critical attributes
        - completeness_score: Percentage of 22 attributes present

        Args:
            asset_ids: List of asset UUIDs to recalculate
        """
        logger.info(f"Recalculating assessment readiness for {len(asset_ids)} assets")

        try:
            # Query assets with tenant scoping
            assets_query = select(Asset).where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(assets_query)
            assets = result.scalars().all()

            for asset in assets:
                # Check 22 critical attributes
                missing_attributes = []
                present_count = 0
                total_count = sum(len(attrs) for attrs in CRITICAL_ATTRIBUTES.values())

                for category, attributes in CRITICAL_ATTRIBUTES.items():
                    for attr in attributes:
                        # Check if attribute is present and not None
                        if hasattr(asset, attr) and getattr(asset, attr) is not None:
                            present_count += 1
                        else:
                            missing_attributes.append(f"{category}.{attr}")

                # Calculate completeness score (0.0 - 1.0)
                completeness_score = (
                    present_count / total_count if total_count > 0 else 0.0
                )

                # Calculate assessment readiness score
                # < 50% = LOW, 50-74% = MODERATE, >= 75% = GOOD
                assessment_readiness_score = completeness_score

                # Determine assessment readiness status
                if completeness_score < 0.5:
                    assessment_readiness = "not_ready"
                elif completeness_score < 0.75:
                    assessment_readiness = "in_progress"
                else:
                    assessment_readiness = "ready"

                # Update asset with new readiness data
                update_stmt = (
                    update(Asset)
                    .where(
                        Asset.id == asset.id,
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                    )
                    .values(
                        assessment_readiness=assessment_readiness,
                        assessment_readiness_score=assessment_readiness_score,
                        completeness_score=completeness_score,
                        assessment_blockers=missing_attributes,
                    )
                )
                await self.db.execute(update_stmt)

                logger.debug(
                    f"Asset {asset.id}: readiness={assessment_readiness}, "
                    f"score={assessment_readiness_score:.2f}, "
                    f"missing={len(missing_attributes)}"
                )

            # Commit all updates
            await self.db.commit()

            logger.info(f"Assessment readiness recalculated for {len(assets)} assets")

        except Exception as e:
            logger.error(
                f"Failed to recalculate assessment readiness: {e}", exc_info=True
            )
            await self.db.rollback()
