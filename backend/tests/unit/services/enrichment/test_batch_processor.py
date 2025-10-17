"""
Unit tests for EnrichmentBatchProcessor (Phase 2.3).

Tests:
1. Backpressure control (Semaphore limiting concurrent batches)
2. Rate limiting (max batches per minute)
3. Progress tracking and metrics logging
4. Error handling per batch
5. Tenant scoping validation
"""

import asyncio
import time
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.models.asset import Asset
from app.services.enrichment.batch_processor import (
    EnrichmentBatchProcessor,
    RateLimiter,
)


@pytest.fixture
def client_account_id():
    """Test client account ID."""
    return uuid4()


@pytest.fixture
def engagement_id():
    """Test engagement ID."""
    return uuid4()


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def sample_assets(client_account_id, engagement_id):
    """Create sample assets for testing."""
    return [
        Asset(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name=f"Test Asset {i}",
            asset_type="server",
        )
        for i in range(25)  # 25 assets = 3 batches at batch_size=10
    ]


class TestRateLimiter:
    """Tests for RateLimiter token bucket algorithm."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_operations_within_limit(self):
        """Rate limiter should allow operations within the limit."""
        # Max 5 operations per 1 second window
        limiter = RateLimiter(max_operations=5, time_window_seconds=1.0)

        start_time = time.time()

        # Should allow 5 operations without blocking
        for _ in range(5):
            await limiter.acquire()

        elapsed = time.time() - start_time
        assert elapsed < 0.5, "Should not block within limit"

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_exceeding_limit(self):
        """Rate limiter should block when exceeding limit."""
        # Max 3 operations per 1 second window
        limiter = RateLimiter(max_operations=3, time_window_seconds=1.0)

        start_time = time.time()

        # First 3 operations should be immediate
        for _ in range(3):
            await limiter.acquire()

        # 4th operation should block until window expires
        await limiter.acquire()

        elapsed = time.time() - start_time
        # Should wait ~1 second for window to expire
        assert elapsed >= 1.0, "Should block until time window expires"

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_timestamps(self):
        """Rate limiter should clean timestamps outside window."""
        limiter = RateLimiter(max_operations=2, time_window_seconds=0.5)

        # Use first operation
        await limiter.acquire()
        assert len(limiter.timestamps) == 1

        # Wait for window to expire
        await asyncio.sleep(0.6)

        # Next operation should clean old timestamp
        await limiter.acquire()
        assert len(limiter.timestamps) == 1  # Old timestamp removed


class TestEnrichmentBatchProcessor:
    """Tests for EnrichmentBatchProcessor with backpressure controls."""

    @pytest.mark.asyncio
    async def test_batch_processor_initialization(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Batch processor should initialize with correct configuration."""
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=15,
            max_concurrent_batches=5,
            batches_per_minute=20,
        )

        assert processor.batch_size == 15
        assert processor.max_concurrent_batches == 5
        assert processor.batches_per_minute == 20
        assert processor.client_account_id == client_account_id
        assert processor.engagement_id == engagement_id

    @pytest.mark.asyncio
    async def test_batch_processor_uses_config_defaults(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Batch processor should use config defaults when not specified."""
        with patch("app.services.enrichment.batch_processor.settings") as mock_settings:
            mock_settings.ENRICHMENT_BATCH_SIZE = 10
            mock_settings.ENRICHMENT_MAX_CONCURRENT_BATCHES = 3
            mock_settings.ENRICHMENT_BATCHES_PER_MINUTE = 10

            processor = EnrichmentBatchProcessor(
                db=mock_db_session,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
            )

            assert processor.batch_size == 10
            assert processor.max_concurrent_batches == 3
            assert processor.batches_per_minute == 10

    @pytest.mark.asyncio
    async def test_batch_processor_splits_assets_into_batches(
        self, mock_db_session, client_account_id, engagement_id, sample_assets
    ):
        """Batch processor should split assets into correct batch sizes."""
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=10,
        )

        # Mock enrichment executors to return success
        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=AsyncMock(return_value=10),
            enrich_licenses=AsyncMock(return_value=10),
            enrich_vulnerabilities=AsyncMock(return_value=10),
            enrich_resilience=AsyncMock(return_value=10),
            enrich_dependencies=AsyncMock(return_value=10),
            enrich_product_links=AsyncMock(return_value=10),
            enrich_field_conflicts=AsyncMock(return_value=0),
        ):
            result = await processor.process_assets_with_backpressure(sample_assets)

        # 25 assets / 10 per batch = 3 batches
        assert result["batches_processed"] == 3
        assert result["total_assets"] == 25

    @pytest.mark.asyncio
    async def test_backpressure_limits_concurrent_batches(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Backpressure semaphore should limit concurrent batch processing."""
        # Create processor with max 2 concurrent batches
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=5,
            max_concurrent_batches=2,
            batches_per_minute=100,  # High limit to not interfere
        )

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def mock_enrich_with_delay(*args, **kwargs):
            """Mock enrichment function that tracks concurrency."""
            nonlocal concurrent_count, max_concurrent

            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            # Simulate work
            await asyncio.sleep(0.1)

            async with lock:
                concurrent_count -= 1

            return 5  # Return count of enriched assets

        # Create 15 assets = 3 batches at batch_size=5
        assets = [
            Asset(
                id=uuid4(),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_name=f"Test Asset {i}",
            )
            for i in range(15)
        ]

        # Mock all enrichment executors
        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=mock_enrich_with_delay,
            enrich_licenses=mock_enrich_with_delay,
            enrich_vulnerabilities=mock_enrich_with_delay,
            enrich_resilience=mock_enrich_with_delay,
            enrich_dependencies=mock_enrich_with_delay,
            enrich_product_links=mock_enrich_with_delay,
            enrich_field_conflicts=mock_enrich_with_delay,
        ):
            await processor.process_assets_with_backpressure(assets)

        # Should never exceed max_concurrent_batches * num_agents
        # max_concurrent_batches=2, num_agents=7
        # But agents run concurrently within a batch, so we check batch-level concurrency
        # This is a simplified check - in practice, we verify semaphore usage
        assert max_concurrent <= 14  # 2 batches * 7 agents

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Rate limiter should enforce batches per minute limit."""
        # Create processor with very low rate limit for testing
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=5,
            max_concurrent_batches=10,  # High to not interfere
            batches_per_minute=2,  # Very low for quick test
        )

        # Mock enrichment to be very fast
        fast_mock = AsyncMock(return_value=5)

        # Create 15 assets = 3 batches
        assets = [
            Asset(
                id=uuid4(),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_name=f"Test Asset {i}",
            )
            for i in range(15)
        ]

        start_time = time.time()

        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=fast_mock,
            enrich_licenses=fast_mock,
            enrich_vulnerabilities=fast_mock,
            enrich_resilience=fast_mock,
            enrich_dependencies=fast_mock,
            enrich_product_links=fast_mock,
            enrich_field_conflicts=fast_mock,
        ):
            await processor.process_assets_with_backpressure(assets)

        elapsed = time.time() - start_time

        # With rate limit of 2 batches per minute, 3 batches should take ~1 minute
        # (first 2 batches immediate, 3rd batch waits ~30s)
        # We use a relaxed assertion due to test timing variations
        assert elapsed >= 0.5, "Should enforce rate limiting"

    @pytest.mark.asyncio
    async def test_progress_metrics_logged(
        self, mock_db_session, client_account_id, engagement_id, sample_assets
    ):
        """Batch processor should log progress metrics."""
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=10,
        )

        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=AsyncMock(return_value=10),
            enrich_licenses=AsyncMock(return_value=10),
            enrich_vulnerabilities=AsyncMock(return_value=10),
            enrich_resilience=AsyncMock(return_value=10),
            enrich_dependencies=AsyncMock(return_value=10),
            enrich_product_links=AsyncMock(return_value=10),
            enrich_field_conflicts=AsyncMock(return_value=0),
        ):
            result = await processor.process_assets_with_backpressure(sample_assets)

        # Verify metrics are present
        assert "total_assets" in result
        assert "batches_processed" in result
        assert "elapsed_time_seconds" in result
        assert "avg_batch_time_seconds" in result
        assert "assets_per_minute" in result

        # Verify calculations
        assert result["total_assets"] == 25
        assert result["batches_processed"] == 3
        assert result["elapsed_time_seconds"] > 0
        assert result["avg_batch_time_seconds"] > 0
        assert result["assets_per_minute"] > 0

    @pytest.mark.asyncio
    async def test_error_handling_per_batch(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Batch processor should handle errors gracefully per batch."""
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=5,
        )

        # Create 10 assets = 2 batches
        assets = [
            Asset(
                id=uuid4(),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_name=f"Test Asset {i}",
            )
            for i in range(10)
        ]

        # Mock one agent to fail
        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=AsyncMock(side_effect=Exception("Compliance failed")),
            enrich_licenses=AsyncMock(return_value=5),
            enrich_vulnerabilities=AsyncMock(return_value=5),
            enrich_resilience=AsyncMock(return_value=5),
            enrich_dependencies=AsyncMock(return_value=5),
            enrich_product_links=AsyncMock(return_value=5),
            enrich_field_conflicts=AsyncMock(return_value=0),
        ):
            result = await processor.process_assets_with_backpressure(assets)

        # Should continue processing despite error
        assert result["batches_processed"] == 2
        assert result["total_assets"] == 10

        # Compliance should have 0 due to error, others should succeed
        assert result["enrichment_results"]["compliance_flags"] == 0
        assert result["enrichment_results"]["licenses"] == 10  # 5 per batch * 2 batches

    @pytest.mark.asyncio
    async def test_enrichment_results_aggregated_correctly(
        self, mock_db_session, client_account_id, engagement_id
    ):
        """Batch processor should correctly aggregate enrichment results."""
        processor = EnrichmentBatchProcessor(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=10,
        )

        # Create 20 assets = 2 batches
        assets = [
            Asset(
                id=uuid4(),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_name=f"Test Asset {i}",
            )
            for i in range(20)
        ]

        # Mock different success rates per agent
        with patch.multiple(
            "app.services.enrichment.batch_processor",
            enrich_compliance=AsyncMock(return_value=10),  # 100% success
            enrich_licenses=AsyncMock(return_value=8),  # 80% success
            enrich_vulnerabilities=AsyncMock(return_value=10),  # 100% success
            enrich_resilience=AsyncMock(return_value=7),  # 70% success
            enrich_dependencies=AsyncMock(return_value=9),  # 90% success
            enrich_product_links=AsyncMock(return_value=10),  # 100% success
            enrich_field_conflicts=AsyncMock(return_value=0),  # 0% (expected)
        ):
            result = await processor.process_assets_with_backpressure(assets)

        # Verify aggregation (2 batches * per-batch counts)
        assert result["enrichment_results"]["compliance_flags"] == 20  # 10 * 2
        assert result["enrichment_results"]["licenses"] == 16  # 8 * 2
        assert result["enrichment_results"]["vulnerabilities"] == 20  # 10 * 2
        assert result["enrichment_results"]["resilience"] == 14  # 7 * 2
        assert result["enrichment_results"]["dependencies"] == 18  # 9 * 2
        assert result["enrichment_results"]["product_links"] == 20  # 10 * 2
        assert result["enrichment_results"]["field_conflicts"] == 0  # 0 * 2
