"""
Integration tests for Two-Phase Gap Analysis Endpoints (PR508).

Tests job state management, progress polling, idempotency, and rate limiting
as required by GPT5 PR feedback.

🤖 Generated with Claude Code
"""

import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.schemas.collection_gap_analysis import AnalyzeGapsRequest, DataGap


class TestJobStateManager:
    """Unit tests for job_state_manager module."""

    @pytest.fixture
    def collection_flow_id(self):
        """Generate a collection flow ID for testing."""
        return uuid4()

    @pytest.fixture
    def job_data(self, collection_flow_id):
        """Generate test job data."""
        return {
            "job_id": f"enhance_{uuid4().hex[:8]}_{int(time.time())}",
            "flow_id": str(uuid4()),
            "collection_flow_id": collection_flow_id,
            "total_gaps": 10,
            "total_assets": 5,
            "idempotency_key": hashlib.sha256(b"test").hexdigest()[:16],
        }

    @pytest.mark.asyncio
    async def test_create_job_state(self, collection_flow_id, job_data):
        """Test creating job state in Redis."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.job_state_manager import (
            create_job_state,
            get_job_state,
        )
        from app.core.redis_config import get_redis_manager

        # Mock Redis manager
        redis_manager = get_redis_manager()
        if not redis_manager.is_available():
            pytest.skip("Redis not available for testing")

        # Create job state
        await create_job_state(**job_data)

        # Verify job state was created
        job_state = await get_job_state(collection_flow_id)
        assert job_state is not None
        assert job_state["job_id"] == job_data["job_id"]
        assert job_state["status"] == "queued"
        assert job_state["total_gaps"] == 10
        assert job_state["total_assets"] == 5
        assert job_state["processed_assets"] == 0
        assert "started_at" in job_state
        assert "updated_at" in job_state

    @pytest.mark.asyncio
    async def test_update_job_state(self, collection_flow_id, job_data):
        """Test updating job state in Redis."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.job_state_manager import (
            create_job_state,
            get_job_state,
            update_job_state,
        )
        from app.core.redis_config import get_redis_manager

        redis_manager = get_redis_manager()
        if not redis_manager.is_available():
            pytest.skip("Redis not available for testing")

        # Create initial job state
        await create_job_state(**job_data)

        # Update job state
        updates = {
            "status": "running",
            "processed_assets": 2,
            "current_asset": "Test Asset",
        }
        await update_job_state(collection_flow_id, updates)

        # Verify updates
        job_state = await get_job_state(collection_flow_id)
        assert job_state["status"] == "running"
        assert job_state["processed_assets"] == 2
        assert job_state["current_asset"] == "Test Asset"

    @pytest.mark.asyncio
    async def test_get_job_state_not_found(self):
        """Test getting non-existent job state returns None."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.job_state_manager import (
            get_job_state,
        )
        from app.core.redis_config import get_redis_manager

        redis_manager = get_redis_manager()
        if not redis_manager.is_available():
            pytest.skip("Redis not available for testing")

        non_existent_id = uuid4()
        job_state = await get_job_state(non_existent_id)
        assert job_state is None


class TestAnalyzeGapsEndpoint:
    """Integration tests for POST /analyze-gaps endpoint."""

    @pytest.fixture
    def mock_context(self):
        """Mock request context."""
        return RequestContext(
            client_account_id=UUID(int=1),
            engagement_id=UUID(int=1),
            user_id=None,
        )

    @pytest.fixture
    def sample_gaps(self):
        """Generate sample gap data."""
        asset_id = uuid4()
        return [
            DataGap(
                asset_id=str(asset_id),
                asset_name="Test Server",
                field_name="os_version",
                gap_type="missing_field",
                gap_category="infrastructure",
                priority=1,  # Integer 1-4
                current_value=None,
                suggested_resolution="Manual collection required",
                confidence_score=None,
                ai_suggestions=None,
            )
            for _ in range(5)
        ]

    @pytest.fixture
    def analyze_request(self, sample_gaps):
        """Generate analyze gaps request."""
        return AnalyzeGapsRequest(
            gaps=sample_gaps,
            selected_asset_ids=[str(gap.asset_id) for gap in sample_gaps],
        )

    @pytest.mark.asyncio
    async def test_analyze_gaps_returns_202_with_job_id(
        self, mock_context, analyze_request
    ):
        """Test /analyze-gaps returns 202 Accepted with job_id."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.gap_analysis_handlers import (
            analyze_gaps,
        )

        mock_db = AsyncMock(spec=AsyncSession)
        background_tasks = BackgroundTasks()

        # Mock resolve_collection_flow
        with patch(
            "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
            ".gap_analysis_handlers.resolve_collection_flow"
        ) as mock_resolve:
            mock_flow = MagicMock()
            mock_flow.id = uuid4()
            mock_resolve.return_value = mock_flow

            # Mock Redis manager
            with patch(
                "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                ".gap_analysis_handlers.get_redis_manager"
            ) as mock_redis:
                mock_redis_manager = MagicMock()
                mock_redis_manager.is_available.return_value = True
                mock_redis.return_value = mock_redis_manager

                # Mock get_job_state (no existing job)
                with patch(
                    "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                    ".gap_analysis_handlers.get_job_state"
                ) as mock_get_state:
                    mock_get_state.return_value = None

                    # Mock create_job_state
                    with patch(
                        "app.api.v1.endpoints.collection_gap_analysis"
                        ".analysis_endpoints.gap_analysis_handlers.create_job_state"
                    ) as mock_create:
                        mock_create.return_value = None

                        # Call endpoint
                        result = await analyze_gaps(
                            flow_id=str(uuid4()),
                            request_body=analyze_request,
                            background_tasks=background_tasks,
                            context=mock_context,
                            db=mock_db,
                        )

                        # Assertions
                        assert result["status"] == "queued"
                        assert "job_id" in result
                        assert result["job_id"].startswith("enhance_")
                        assert "progress_url" in result
                        assert "/enhancement-progress" in result["progress_url"]

    @pytest.mark.asyncio
    async def test_analyze_gaps_idempotency_409_conflict(
        self, mock_context, analyze_request
    ):
        """Test idempotency - resubmitting same gaps returns 409."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.gap_analysis_handlers import (
            analyze_gaps,
        )

        mock_db = AsyncMock(spec=AsyncSession)
        background_tasks = BackgroundTasks()

        with patch(
            "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
            ".gap_analysis_handlers.resolve_collection_flow"
        ) as mock_resolve:
            mock_flow = MagicMock()
            mock_flow.id = uuid4()
            mock_resolve.return_value = mock_flow

            with patch(
                "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                ".gap_analysis_handlers.get_redis_manager"
            ) as mock_redis:
                mock_redis_manager = MagicMock()
                mock_redis_manager.is_available.return_value = True
                mock_redis.return_value = mock_redis_manager

                # Mock existing running job
                with patch(
                    "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                    ".gap_analysis_handlers.get_job_state"
                ) as mock_get_state:
                    mock_get_state.return_value = {
                        "job_id": "existing_job",
                        "status": "running",
                    }

                    # Should raise 409 Conflict
                    with pytest.raises(HTTPException) as exc_info:
                        await analyze_gaps(
                            flow_id=str(uuid4()),
                            request_body=analyze_request,
                            background_tasks=background_tasks,
                            context=mock_context,
                            db=mock_db,
                        )

                    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
                    assert "already running" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analyze_gaps_rate_limiting_429(self, mock_context, analyze_request):
        """Test rate limiting - submitting within 10s returns 429."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.gap_analysis_handlers import (
            analyze_gaps,
        )

        mock_db = AsyncMock(spec=AsyncSession)
        background_tasks = BackgroundTasks()

        with patch(
            "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
            ".gap_analysis_handlers.resolve_collection_flow"
        ) as mock_resolve:
            mock_flow = MagicMock()
            mock_flow.id = uuid4()
            mock_resolve.return_value = mock_flow

            with patch(
                "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                ".gap_analysis_handlers.get_redis_manager"
            ) as mock_redis:
                mock_redis_manager = MagicMock()
                mock_redis_manager.is_available.return_value = True
                mock_redis.return_value = mock_redis_manager

                # Mock recently completed job (within 10s)
                with patch(
                    "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints"
                    ".gap_analysis_handlers.get_job_state"
                ) as mock_get_state:
                    mock_get_state.return_value = {
                        "job_id": "recent_job",
                        "status": "completed",
                        "updated_at": time.time() - 5,  # 5 seconds ago
                    }

                    # Should raise 429 Too Many Requests
                    with pytest.raises(HTTPException) as exc_info:
                        await analyze_gaps(
                            flow_id=str(uuid4()),
                            request_body=analyze_request,
                            background_tasks=background_tasks,
                            context=mock_context,
                            db=mock_db,
                        )

                    assert (
                        exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                    )
                    assert "Rate limit" in exc_info.value.detail
                    assert "5 seconds" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analyze_gaps_rejects_over_200_gaps(self, mock_context, sample_gaps):
        """Test server-side limit enforcement - rejects >200 gaps."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.gap_analysis_handlers import (
            analyze_gaps,
        )

        # Create 201 gaps
        large_gaps = sample_gaps * 41  # 5 * 41 = 205 gaps
        request = AnalyzeGapsRequest(
            gaps=large_gaps[:201],  # Exactly 201
            selected_asset_ids=[str(gap.asset_id) for gap in large_gaps[:201]],
        )

        mock_db = AsyncMock(spec=AsyncSession)
        background_tasks = BackgroundTasks()

        # Should raise 400 Bad Request
        with pytest.raises(HTTPException) as exc_info:
            await analyze_gaps(
                flow_id=str(uuid4()),
                request_body=request,
                background_tasks=background_tasks,
                context=mock_context,
                db=mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Too many gaps" in exc_info.value.detail
        assert "200" in exc_info.value.detail


class TestEnhancementProgressEndpoint:
    """Integration tests for GET /enhancement-progress endpoint."""

    @pytest.fixture
    def mock_context(self):
        """Mock request context."""
        return RequestContext(
            client_account_id=UUID(int=1),
            engagement_id=UUID(int=1),
            user_id=None,
        )

    @pytest.mark.asyncio
    async def test_get_progress_returns_not_started_when_no_job(self, mock_context):
        """Test progress endpoint returns not_started when no job exists."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers import (
            get_enhancement_progress,
        )

        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers.resolve_collection_flow"
        ) as mock_resolve:
            mock_flow = MagicMock()
            mock_flow.id = uuid4()
            mock_resolve.return_value = mock_flow

            with patch(
                "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers.get_job_state"
            ) as mock_get_state:
                mock_get_state.return_value = None

                result = await get_enhancement_progress(
                    flow_id=str(uuid4()),
                    context=mock_context,
                    db=mock_db,
                )

                assert result["status"] == "not_started"
                assert result["processed"] == 0
                assert result["total"] == 0
                assert result["percentage"] == 0

    @pytest.mark.asyncio
    async def test_get_progress_returns_running_state(self, mock_context):
        """Test progress endpoint returns running state with correct mapping."""
        # Lazy import to avoid Redis initialization at collection time
        from app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers import (
            get_enhancement_progress,
        )

        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers.resolve_collection_flow"
        ) as mock_resolve:
            mock_flow = MagicMock()
            mock_flow.id = uuid4()
            mock_resolve.return_value = mock_flow

            with patch(
                "app.api.v1.endpoints.collection_gap_analysis.analysis_endpoints.progress_handlers.get_job_state"
            ) as mock_get_state:
                mock_get_state.return_value = {
                    "job_id": "test_job",
                    "status": "running",
                    "processed_assets": 3,
                    "total_assets": 10,
                    "current_asset": "Web Server 03",
                    "enhanced_count": 15,
                    "gaps_persisted": 12,
                    "updated_at": time.time(),
                }

                result = await get_enhancement_progress(
                    flow_id=str(uuid4()),
                    context=mock_context,
                    db=mock_db,
                )

                # Verify correct field mapping from job state
                assert result["status"] == "running"
                assert result["processed"] == 3  # processed_assets
                assert result["total"] == 10  # total_assets
                assert result["percentage"] == 30  # (3/10) * 100
                assert result["current_asset"] == "Web Server 03"
                assert result["enhanced_count"] == 15
                assert result["gaps_persisted"] == 12
                assert "updated_at" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
