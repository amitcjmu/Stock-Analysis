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

**Performance Target**: 100 assets < 5 minutes (Phase 2.3 optimization)
**Phase 2.3 Updates (October 2025)**:
- Uses EnrichmentBatchProcessor with backpressure controls
- Rate limiting: 10 batches per minute (configurable)
- Concurrent batch limit: 3 batches (configurable)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset

# Import Phase 2.3 batch processor with backpressure controls
from app.services.enrichment.batch_processor import EnrichmentBatchProcessor

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

    **Performance Target**: 100 assets < 5 minutes (Phase 2.3 optimization)
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

        # Initialize EnrichmentBatchProcessor with backpressure controls (Phase 2.3)
        self.batch_processor = EnrichmentBatchProcessor(
            db=db,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        logger.info(
            f"Initialized AutoEnrichmentPipeline for client {client_account_id}, "
            f"engagement {engagement_id} with Phase 2.3 backpressure controls"
        )

    async def trigger_auto_enrichment(self, asset_ids: List[UUID]) -> Dict[str, Any]:
        """
        Trigger automated enrichment for specified assets with batch processing.

        **Phase 2.3 Optimizations (October 2025)**:
        - Uses EnrichmentBatchProcessor with backpressure controls
        - Semaphore limits concurrent batches (default 3)
        - Rate limiting: max batches per minute (default 10)
        - Progress tracking with ETA logging
        - Performance target: 100 assets < 5 minutes

        **Execution Pattern**:
        1. Retrieve assets from database (tenant-scoped)
        2. Pass to EnrichmentBatchProcessor for batch processing
        3. Recalculate assessment readiness for all assets
        4. Return enrichment statistics

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
                "elapsed_time_seconds": 280.5,
                "batches_processed": 10,
                "avg_batch_time_seconds": 28.05,
                "assets_per_minute": 21.4
            }
        """
        start_time = datetime.utcnow()
        logger.info(
            f"Starting Phase 2.3 auto-enrichment for {len(asset_ids)} assets "
            f"with backpressure controls"
        )

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

            # Step 2: Process assets using batch processor with backpressure
            enrichment_stats = (
                await self.batch_processor.process_assets_with_backpressure(all_assets)
            )

            # Step 3: Recalculate assessment readiness for all assets
            await self._recalculate_readiness(asset_ids)

            # Add readiness recalculation to stats
            enrichment_stats["readiness_recalculated"] = len(all_assets)

            logger.info(f"Phase 2.3 auto-enrichment completed: {enrichment_stats}")

            return enrichment_stats

        except Exception as e:
            logger.error(
                f"Phase 2.3 auto-enrichment pipeline failed: {e}", exc_info=True
            )
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


# In-memory lock to prevent concurrent enrichment for same flow (Phase 3.1)
_enrichment_locks: Dict[str, asyncio.Lock] = {}


async def trigger_auto_enrichment_background(
    db: AsyncSession,
    flow_id: str,
    client_account_id: str | UUID,
    engagement_id: str | UUID,
    asset_ids: List[UUID],
) -> None:
    """
    Background task for auto-enrichment on flow initialization (Phase 3.1).

    Uses per-flow lock to prevent concurrent enrichment.
    Logs errors but doesn't fail flow creation.

    **CRITICAL ADR COMPLIANCE**:
    - Uses EnrichmentBatchProcessor with backpressure (Phase 2.3)
    - Tenant scoping on all database operations
    - NO asyncio.run() in async context (BANNED PATTERN)

    Args:
        db: Database session
        flow_id: Assessment flow ID
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID
        asset_ids: List of asset UUIDs to enrich
    """
    # Acquire per-flow lock
    if flow_id not in _enrichment_locks:
        _enrichment_locks[flow_id] = asyncio.Lock()

    lock = _enrichment_locks[flow_id]

    # Try to acquire lock (non-blocking)
    if lock.locked():
        logger.warning(
            f"Auto-enrichment already in progress for flow {flow_id}, skipping"
        )
        return

    async with lock:
        try:
            logger.info(
                f"Starting auto-enrichment for flow {flow_id} "
                f"({len(asset_ids)} assets)"
            )

            # Convert IDs to UUID if needed
            if isinstance(client_account_id, (str, int)):
                client_account_uuid = UUID(str(client_account_id))
            else:
                client_account_uuid = client_account_id

            if isinstance(engagement_id, str):
                engagement_uuid = UUID(engagement_id)
            else:
                engagement_uuid = engagement_id

            # Initialize AutoEnrichmentPipeline with Phase 2.3 batch processor
            enrichment_pipeline = AutoEnrichmentPipeline(
                db=db,
                client_account_id=client_account_uuid,
                engagement_id=engagement_uuid,
            )

            # Process with backpressure controls (Phase 2.3)
            result = await enrichment_pipeline.trigger_auto_enrichment(asset_ids)

            logger.info(
                f"Auto-enrichment completed for flow {flow_id}: "
                f"{result['total_assets']} assets, "
                f"{result['batches_processed']} batches, "
                f"{result['elapsed_time_seconds']:.1f}s"
            )

        except Exception as e:
            logger.error(
                f"Auto-enrichment failed for flow {flow_id}: {str(e)}", exc_info=True
            )
            # Don't re-raise - background task failure shouldn't block flow creation
        finally:
            # Clean up lock after completion
            if flow_id in _enrichment_locks:
                del _enrichment_locks[flow_id]
