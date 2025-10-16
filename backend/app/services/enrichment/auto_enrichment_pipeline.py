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

# Batch processing configuration
BATCH_SIZE = 10  # Process 10 assets per batch for optimal performance

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
        Trigger automated enrichment for specified assets with batch processing.

        **Execution Pattern (Batched)**:
        1. Retrieve assets from database
        2. Split assets into batches of BATCH_SIZE (10)
        3. For each batch:
           a. Run all 6 agents concurrently on the batch
           b. Commit results
        4. Recalculate assessment readiness for all assets
        5. Return enrichment statistics

        **Performance Optimization**:
        - Batch size: 10 assets per batch
        - Target: 100 assets in < 10 minutes
        - Memory efficient: Commits after each batch

        Args:
            asset_ids: List of asset UUIDs to enrich

        Returns:
            Dict with enrichment statistics:
            {
                "total_assets": 100,
                "enrichment_results": {
                    "compliance_flags": 95,
                    "licenses": 98,
                    "vulnerabilities": 100,
                    "resilience": 92,
                    "dependencies": 87,
                    "product_links": 90,
                    "field_conflicts": 0
                },
                "elapsed_time_seconds": 480.5,
                "batches_processed": 10
            }
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting batched auto-enrichment for {len(asset_ids)} assets")

        try:
            # Step 1: Query assets with tenant scoping (CRITICAL)
            assets_query = select(Asset).where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(assets_query)
            all_assets = list(result.scalars().all())

            if not all_assets:
                logger.warning(f"No assets found for enrichment with IDs: {asset_ids}")
                return {
                    "total_assets": 0,
                    "enrichment_results": {
                        enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
                    },
                    "elapsed_time_seconds": 0.0,
                    "batches_processed": 0,
                    "error": "No assets found",
                }

            logger.info(f"Retrieved {len(all_assets)} assets for enrichment")

            # Step 2: Split assets into batches
            batches = [
                all_assets[i : i + BATCH_SIZE]
                for i in range(0, len(all_assets), BATCH_SIZE)
            ]
            num_batches = len(batches)
            logger.info(
                f"Processing {len(all_assets)} assets in {num_batches} batches "
                f"(batch size: {BATCH_SIZE})"
            )

            # Initialize aggregated stats
            total_enrichment_stats = {
                enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
            }

            # Step 3: Process each batch sequentially
            for batch_idx, batch_assets in enumerate(batches, 1):
                batch_start = datetime.utcnow()
                logger.info(
                    f"Processing batch {batch_idx}/{num_batches} "
                    f"({len(batch_assets)} assets)"
                )

                # Run ALL enrichment agents concurrently for this batch
                # This is the performance optimization - parallel agent execution
                enrichment_tasks = [
                    enrich_compliance(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_licenses(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_vulnerabilities(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_resilience(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_dependencies(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_product_links(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                    enrich_field_conflicts(
                        batch_assets,
                        self.db,
                        self.agent_pool,
                        self.memory_manager,
                        self.client_account_id,
                        self.engagement_id,
                    ),
                ]

                # Execute batch concurrently with error handling
                batch_results = await asyncio.gather(
                    *enrichment_tasks, return_exceptions=True
                )

                # Aggregate batch results
                for i, result in enumerate(batch_results):
                    enrichment_type = ENRICHMENT_TYPES[i]
                    if isinstance(result, Exception):
                        logger.error(
                            f"Batch {batch_idx} - {enrichment_type} failed: {result}"
                        )
                    else:
                        total_enrichment_stats[enrichment_type] += result
                        logger.debug(
                            f"Batch {batch_idx} - {enrichment_type}: {result} assets"
                        )

                # Commit batch results
                try:
                    await self.db.commit()
                    batch_elapsed = (datetime.utcnow() - batch_start).total_seconds()
                    logger.info(
                        f"Batch {batch_idx}/{num_batches} completed in {batch_elapsed:.2f}s"
                    )
                except Exception as e:
                    logger.error(f"Failed to commit batch {batch_idx}: {e}")
                    await self.db.rollback()

            # Step 4: Recalculate assessment readiness for all assets
            await self._recalculate_readiness(asset_ids)

            # Calculate elapsed time
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Batched auto-enrichment completed for {len(all_assets)} assets "
                f"in {num_batches} batches, total time: {elapsed_time:.2f}s "
                f"(avg {elapsed_time/num_batches:.2f}s per batch)"
            )

            return {
                "total_assets": len(all_assets),
                "enrichment_results": total_enrichment_stats,
                "elapsed_time_seconds": elapsed_time,
                "batches_processed": num_batches,
                "avg_batch_time_seconds": (
                    elapsed_time / num_batches if num_batches > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"Batched auto-enrichment pipeline failed: {e}", exc_info=True)
            return {
                "total_assets": 0,
                "enrichment_results": {
                    enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
                },
                "elapsed_time_seconds": (
                    datetime.utcnow() - start_time
                ).total_seconds(),
                "batches_processed": 0,
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
