"""
Batch Processor for Asset Enrichment with Backpressure Controls.

**Phase 2.3 Implementation - October 2025**:
- Backpressure: Semaphore limiting concurrent batch processing
- Rate Limiting: Token bucket algorithm for batches per minute
- Progress Tracking: Enrichment status updates after each batch
- Performance Target: 100 assets < 5 minutes

**CRITICAL ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for agent learning (memory=False)
- Multi-tenant scoping on all database operations
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import Asset
from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

# Import enrichment executors
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


class RateLimiter:
    """
    Token bucket rate limiter for batch processing.

    Allows a maximum number of operations per time window (e.g., 10 batches per minute).
    """

    def __init__(self, max_operations: int, time_window_seconds: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_operations: Maximum number of operations allowed per time window
            time_window_seconds: Time window in seconds (default 60.0 = 1 minute)
        """
        self.max_operations = max_operations
        self.time_window_seconds = time_window_seconds
        self.timestamps: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to proceed with an operation.

        Blocks until permission is granted (rate limit not exceeded).
        """
        async with self._lock:
            current_time = time.time()

            # Remove timestamps outside the time window
            self.timestamps = [
                ts
                for ts in self.timestamps
                if current_time - ts < self.time_window_seconds
            ]

            # If at capacity, wait until oldest timestamp expires
            while len(self.timestamps) >= self.max_operations:
                oldest_ts = self.timestamps[0]
                wait_time = self.time_window_seconds - (current_time - oldest_ts)

                if wait_time > 0:
                    logger.debug(
                        f"Rate limit reached. Waiting {wait_time:.2f}s "
                        f"({len(self.timestamps)}/{self.max_operations} operations in window)"
                    )
                    await asyncio.sleep(wait_time + 0.1)  # Add small buffer

                # Refresh current time and clean timestamps
                current_time = time.time()
                self.timestamps = [
                    ts
                    for ts in self.timestamps
                    if current_time - ts < self.time_window_seconds
                ]

            # Add current timestamp
            self.timestamps.append(current_time)


class EnrichmentBatchProcessor:
    """
    Batch processor for asset enrichment with backpressure and rate limiting.

    **Performance Optimizations (Phase 2.3)**:
    - Backpressure: Semaphore limits concurrent batches (default 3)
    - Rate Limiting: Max batches per minute (default 10)
    - Progress Tracking: Updates enrichment_status after each batch
    - Metrics Logging: Batch duration, assets processed, errors

    **Tenant Scoping**: ALL operations include client_account_id + engagement_id
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
        batch_size: int | None = None,
        max_concurrent_batches: int | None = None,
        batches_per_minute: int | None = None,
    ):
        """
        Initialize batch processor with configurable limits.

        Args:
            db: Async SQLAlchemy session
            client_account_id: Multi-tenant client account UUID
            engagement_id: Multi-tenant engagement UUID
            batch_size: Assets per batch (default from config: 10)
            max_concurrent_batches: Max concurrent batches (default from config: 3)
            batches_per_minute: Max batches per minute (default from config: 10)
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Configuration from settings with overrides
        self.batch_size = batch_size or settings.ENRICHMENT_BATCH_SIZE
        self.max_concurrent_batches = (
            max_concurrent_batches or settings.ENRICHMENT_MAX_CONCURRENT_BATCHES
        )
        self.batches_per_minute = (
            batches_per_minute or settings.ENRICHMENT_BATCHES_PER_MINUTE
        )

        # Initialize backpressure semaphore
        self._batch_semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            max_operations=self.batches_per_minute, time_window_seconds=60.0
        )

        # Initialize TenantScopedAgentPool (ADR-015)
        self.agent_pool = TenantScopedAgentPool

        # Initialize TenantMemoryManager (ADR-024)
        self.memory_manager = TenantMemoryManager(
            crewai_service=None,  # Not using CrewAI memory
            database_session=db,
        )

        logger.info(
            f"Initialized EnrichmentBatchProcessor: "
            f"batch_size={self.batch_size}, "
            f"max_concurrent={self.max_concurrent_batches}, "
            f"rate_limit={self.batches_per_minute}/min, "
            f"tenant={client_account_id}/{engagement_id}"
        )

    async def process_assets_with_backpressure(
        self, assets: List[Asset]
    ) -> Dict[str, Any]:
        """
        Process assets in batches with backpressure controls and rate limiting.

        **Execution Flow**:
        1. Split assets into batches (default 10 per batch)
        2. For each batch (with backpressure + rate limiting):
           a. Run all 7 enrichment agents concurrently
           b. Update enrichment_status in database
           c. Log progress metrics (batch_num, duration, assets_processed)
        3. Return aggregated enrichment statistics

        **Performance Metrics Logged**:
        - Total batches processed
        - Average batch duration
        - Assets enriched per minute
        - Errors per batch

        Args:
            assets: List of Asset objects to enrich (tenant-scoped)

        Returns:
            Dict with enrichment statistics:
            {
                "total_assets": 100,
                "enrichment_results": {
                    "compliance_flags": 95,
                    "licenses": 98,
                    ...
                },
                "elapsed_time_seconds": 280.5,
                "batches_processed": 10,
                "avg_batch_time_seconds": 28.05,
                "assets_per_minute": 21.4
            }
        """
        start_time = datetime.utcnow()
        total_assets = len(assets)

        logger.info(
            f"Starting batched enrichment: {total_assets} assets, "
            f"batch_size={self.batch_size}, "
            f"max_concurrent={self.max_concurrent_batches}, "
            f"rate_limit={self.batches_per_minute}/min"
        )

        try:
            # Step 1: Split assets into batches
            batches = [
                assets[i : i + self.batch_size]
                for i in range(0, total_assets, self.batch_size)
            ]
            num_batches = len(batches)

            # Calculate ETA
            estimated_seconds_per_batch = 22  # From Phase 5 Day 26 testing
            estimated_total_seconds = num_batches * estimated_seconds_per_batch
            logger.info(
                f"Processing {total_assets} assets in {num_batches} batches. "
                f"Estimated completion: {estimated_total_seconds}s "
                f"({estimated_total_seconds / 60:.1f} min)"
            )

            # Initialize aggregated stats
            total_enrichment_stats = {
                enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
            }

            # Step 2: Process each batch with backpressure and rate limiting
            for batch_idx, batch_assets in enumerate(batches, 1):
                # Apply backpressure control (max concurrent batches)
                async with self._batch_semaphore:
                    # Apply rate limiting (max batches per minute)
                    await self._rate_limiter.acquire()

                    batch_start = datetime.utcnow()
                    remaining_batches = num_batches - batch_idx
                    eta_seconds = remaining_batches * estimated_seconds_per_batch

                    logger.info(
                        f"Processing batch {batch_idx}/{num_batches} "
                        f"({len(batch_assets)} assets) - "
                        f"ETA: {eta_seconds / 60:.1f} min remaining"
                    )

                    # Run ALL enrichment agents concurrently for this batch
                    batch_stats = await self._enrich_batch(batch_assets)

                    # Aggregate batch results
                    for enrichment_type in ENRICHMENT_TYPES:
                        total_enrichment_stats[enrichment_type] += batch_stats.get(
                            enrichment_type, 0
                        )

                    # Commit batch results
                    try:
                        await self.db.commit()

                        batch_elapsed = (
                            datetime.utcnow() - batch_start
                        ).total_seconds()
                        logger.info(
                            f"Batch {batch_idx}/{num_batches} completed in {batch_elapsed:.2f}s. "
                            f"Stats: {batch_stats}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to commit batch {batch_idx}: {e}")
                        await self.db.rollback()

            # Calculate final metrics
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            avg_batch_time = elapsed_time / num_batches if num_batches > 0 else 0
            assets_per_minute = (
                (total_assets / elapsed_time) * 60 if elapsed_time > 0 else 0
            )

            logger.info(
                f"Enrichment completed: {total_assets} assets in {num_batches} batches, "
                f"total time: {elapsed_time:.2f}s ({elapsed_time / 60:.1f} min), "
                f"avg batch time: {avg_batch_time:.2f}s, "
                f"throughput: {assets_per_minute:.1f} assets/min"
            )

            return {
                "total_assets": total_assets,
                "enrichment_results": total_enrichment_stats,
                "elapsed_time_seconds": elapsed_time,
                "batches_processed": num_batches,
                "avg_batch_time_seconds": avg_batch_time,
                "assets_per_minute": assets_per_minute,
            }

        except Exception as e:
            logger.error(f"Batched enrichment failed: {e}", exc_info=True)
            return {
                "total_assets": total_assets,
                "enrichment_results": {
                    enrichment_type: 0 for enrichment_type in ENRICHMENT_TYPES
                },
                "elapsed_time_seconds": (
                    datetime.utcnow() - start_time
                ).total_seconds(),
                "batches_processed": 0,
                "error": str(e),
            }

    async def _enrich_batch(self, batch_assets: List[Asset]) -> Dict[str, int]:
        """
        Enrich a single batch of assets using all 7 enrichment agents concurrently.

        Args:
            batch_assets: List of Asset objects for this batch

        Returns:
            Dict with enrichment counts per type:
            {
                "compliance_flags": 10,
                "licenses": 10,
                "vulnerabilities": 10,
                "resilience": 8,
                "dependencies": 9,
                "product_links": 10,
                "field_conflicts": 0
            }
        """
        # Run all enrichment agents concurrently for this batch
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
        batch_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

        # Aggregate batch results
        batch_stats = {}
        for i, result in enumerate(batch_results):
            enrichment_type = ENRICHMENT_TYPES[i]
            if isinstance(result, Exception):
                logger.error(f"{enrichment_type} failed: {result}")
                batch_stats[enrichment_type] = 0
            else:
                batch_stats[enrichment_type] = result
                logger.debug(f"{enrichment_type}: {result} assets enriched")

        return batch_stats
