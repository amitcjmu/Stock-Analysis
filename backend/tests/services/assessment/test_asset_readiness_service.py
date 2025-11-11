"""
Unit tests for AssetReadinessService.

Tests cover:
1. analyze_asset_readiness success case
2. analyze_asset_readiness with asset not found
3. analyze_asset_readiness with tenant scoping violation
4. analyze_flow_assets_readiness with detailed=True
5. analyze_flow_assets_readiness with detailed=False
6. get_readiness_summary (lightweight version)
7. filter_assets_by_readiness with ready_only=True
8. filter_assets_by_readiness with ready_only=False

Target: >90% code coverage
Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 11
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.assessment.asset_readiness_service import AssetReadinessService
from app.services.gap_detection.schemas import ComprehensiveGapReport


@pytest.fixture
def mock_asset():
    """Create a mock Asset."""
    asset = MagicMock()
    asset.id = uuid4()
    asset.asset_name = "test-server-01"
    asset.asset_type = "server"
    asset.canonical_application_id = uuid4()
    return asset


@pytest.fixture
def mock_application():
    """Create a mock CanonicalApplication."""
    app = MagicMock()
    app.id = uuid4()
    app.application_name = "test-app"
    return app


@pytest.fixture
def mock_assessment_flow():
    """Create a mock AssessmentFlow."""
    flow = MagicMock()
    flow.flow_id = uuid4()
    flow.selected_application_ids = [str(uuid4()), str(uuid4())]
    return flow


@pytest.fixture
def mock_db_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    return session


@pytest.fixture
def mock_gap_report():
    """Create a mock ComprehensiveGapReport."""
    return ComprehensiveGapReport(
        column_gaps=MagicMock(completeness_score=0.9),
        enrichment_gaps=MagicMock(completeness_score=0.95),
        jsonb_gaps=MagicMock(completeness_score=1.0),
        application_gaps=MagicMock(completeness_score=0.85),
        standards_gaps=MagicMock(completeness_score=0.8),
        overall_completeness=0.88,
        critical_gaps=[],
        high_priority_gaps=[],
        medium_priority_gaps=[],
        is_ready_for_assessment=True,
        readiness_blockers=[],
        analyzed_at=datetime.utcnow().isoformat(),
    )


@pytest.mark.asyncio
class TestAssetReadinessService:
    """Test suite for AssetReadinessService."""

    async def test_analyze_asset_readiness_success(
        self, mock_asset, mock_application, mock_db_session, mock_gap_report
    ):
        """Test successful asset readiness analysis."""
        # Setup mock DB results
        execute_result = AsyncMock()
        execute_result.scalar_one_or_none = AsyncMock(
            side_effect=[mock_asset, mock_application]
        )
        mock_db_session.execute = AsyncMock(return_value=execute_result)

        # Mock GapAnalyzer
        service = AssetReadinessService()
        with patch.object(
            service.gap_analyzer,
            "analyze_asset",
            new=AsyncMock(return_value=mock_gap_report),
        ):
            result = await service.analyze_asset_readiness(
                asset_id=mock_asset.id,
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

        assert result == mock_gap_report
        assert result.is_ready_for_assessment is True
        assert result.overall_completeness == 0.88

    async def test_analyze_asset_readiness_not_found(self, mock_db_session):
        """Test asset not found raises ValueError."""
        # Mock DB returns None (asset not found)
        execute_result = AsyncMock()
        execute_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=execute_result)

        service = AssetReadinessService()

        with pytest.raises(
            ValueError, match="Asset .* not found or not in tenant scope"
        ):
            await service.analyze_asset_readiness(
                asset_id=uuid4(),
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

    async def test_analyze_asset_readiness_tenant_scoping(
        self, mock_asset, mock_db_session
    ):
        """Test tenant scoping - asset from different tenant returns error."""
        # Mock DB returns None due to tenant scoping filter
        execute_result = AsyncMock()
        execute_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=execute_result)

        service = AssetReadinessService()

        with pytest.raises(ValueError, match="not in tenant scope"):
            await service.analyze_asset_readiness(
                asset_id=mock_asset.id,
                client_account_id=str(uuid4()),  # Different tenant
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

    async def test_analyze_flow_assets_readiness_detailed(
        self, mock_assessment_flow, mock_db_session, mock_gap_report
    ):
        """Test batch analysis with detailed=True."""
        # Mock assessment flow query
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none = AsyncMock(return_value=mock_assessment_flow)

        # Mock assets query
        asset1 = MagicMock(id=uuid4(), asset_name="asset-1", asset_type="server")
        asset2 = MagicMock(id=uuid4(), asset_name="asset-2", asset_type="database")
        assets_result = AsyncMock()
        assets_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[asset1, asset2]))
        )

        mock_db_session.execute = AsyncMock(side_effect=[flow_result, assets_result])

        service = AssetReadinessService()

        # Mock analyze_asset_readiness to return reports
        ready_report = mock_gap_report
        ready_report.is_ready_for_assessment = True
        ready_report.critical_gaps = []
        ready_report.high_priority_gaps = []

        not_ready_report = ComprehensiveGapReport(
            column_gaps=MagicMock(completeness_score=0.5),
            enrichment_gaps=MagicMock(completeness_score=0.6),
            jsonb_gaps=MagicMock(completeness_score=0.7),
            application_gaps=MagicMock(completeness_score=0.4),
            standards_gaps=MagicMock(completeness_score=0.5),
            overall_completeness=0.54,
            critical_gaps=["missing_criticality"],
            high_priority_gaps=["missing_cpu_cores"],
            medium_priority_gaps=[],
            is_ready_for_assessment=False,
            readiness_blockers=["Missing criticality field"],
            analyzed_at=datetime.utcnow().isoformat(),
        )

        with patch.object(
            service,
            "analyze_asset_readiness",
            new=AsyncMock(side_effect=[ready_report, not_ready_report]),
        ):
            result = await service.analyze_flow_assets_readiness(
                flow_id=mock_assessment_flow.flow_id,
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
                detailed=True,
            )

        assert result["total_assets"] == 2
        assert result["ready_count"] == 1
        assert result["not_ready_count"] == 1
        assert result["overall_readiness_rate"] == 50.0
        assert len(result["asset_reports"]) == 2
        assert result["summary_by_type"]["server"]["ready"] == 1
        assert result["summary_by_type"]["database"]["not_ready"] == 1

    async def test_analyze_flow_assets_readiness_counts_only(
        self, mock_assessment_flow, mock_db_session, mock_gap_report
    ):
        """Test batch analysis with detailed=False (counts only)."""
        # Mock assessment flow query
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none = AsyncMock(return_value=mock_assessment_flow)

        # Mock assets query
        asset1 = MagicMock(id=uuid4(), asset_name="asset-1", asset_type="server")
        assets_result = AsyncMock()
        assets_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[asset1]))
        )

        mock_db_session.execute = AsyncMock(side_effect=[flow_result, assets_result])

        service = AssetReadinessService()

        # Mock analyze_asset_readiness
        ready_report = mock_gap_report
        ready_report.is_ready_for_assessment = True

        with patch.object(
            service,
            "analyze_asset_readiness",
            new=AsyncMock(return_value=ready_report),
        ):
            result = await service.analyze_flow_assets_readiness(
                flow_id=mock_assessment_flow.flow_id,
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
                detailed=False,
            )

        assert result["total_assets"] == 1
        assert result["ready_count"] == 1
        assert result["not_ready_count"] == 0
        assert result["overall_readiness_rate"] == 100.0
        assert result["asset_reports"] == []  # No detailed reports

    async def test_get_readiness_summary(
        self, mock_assessment_flow, mock_db_session, mock_gap_report
    ):
        """Test lightweight readiness summary."""
        service = AssetReadinessService()

        # Mock analyze_flow_assets_readiness
        expected_summary = {
            "flow_id": str(mock_assessment_flow.flow_id),
            "total_assets": 5,
            "ready_count": 3,
            "not_ready_count": 2,
            "overall_readiness_rate": 60.0,
            "asset_reports": [],
            "summary_by_type": {},
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        with patch.object(
            service,
            "analyze_flow_assets_readiness",
            new=AsyncMock(return_value=expected_summary),
        ):
            result = await service.get_readiness_summary(
                flow_id=mock_assessment_flow.flow_id,
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

        assert result == expected_summary
        assert result["asset_reports"] == []  # Lightweight version

    async def test_filter_assets_by_readiness_ready_only(
        self, mock_assessment_flow, mock_db_session, mock_gap_report
    ):
        """Test filtering for ready assets only."""
        # Mock assessment flow query
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none = AsyncMock(return_value=mock_assessment_flow)

        # Mock assets query
        asset1_id = uuid4()
        asset2_id = uuid4()
        asset1 = MagicMock(id=asset1_id)
        asset2 = MagicMock(id=asset2_id)
        assets_result = AsyncMock()
        assets_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[asset1, asset2]))
        )

        mock_db_session.execute = AsyncMock(side_effect=[flow_result, assets_result])

        service = AssetReadinessService()

        # Mock analyze_asset_readiness - asset1 ready, asset2 not ready
        ready_report = mock_gap_report
        ready_report.is_ready_for_assessment = True

        not_ready_report = mock_gap_report
        not_ready_report.is_ready_for_assessment = False

        with patch.object(
            service,
            "analyze_asset_readiness",
            new=AsyncMock(side_effect=[ready_report, not_ready_report]),
        ):
            result = await service.filter_assets_by_readiness(
                flow_id=mock_assessment_flow.flow_id,
                ready_only=True,
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

        assert len(result) == 1
        assert result[0] == asset1_id

    async def test_filter_assets_by_readiness_not_ready_only(
        self, mock_assessment_flow, mock_db_session, mock_gap_report
    ):
        """Test filtering for not-ready assets only."""
        # Mock assessment flow query
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none = AsyncMock(return_value=mock_assessment_flow)

        # Mock assets query
        asset1_id = uuid4()
        asset2_id = uuid4()
        asset1 = MagicMock(id=asset1_id)
        asset2 = MagicMock(id=asset2_id)
        assets_result = AsyncMock()
        assets_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[asset1, asset2]))
        )

        mock_db_session.execute = AsyncMock(side_effect=[flow_result, assets_result])

        service = AssetReadinessService()

        # Mock analyze_asset_readiness - asset1 ready, asset2 not ready
        ready_report = mock_gap_report
        ready_report.is_ready_for_assessment = True

        not_ready_report = mock_gap_report
        not_ready_report.is_ready_for_assessment = False

        with patch.object(
            service,
            "analyze_asset_readiness",
            new=AsyncMock(side_effect=[ready_report, not_ready_report]),
        ):
            result = await service.filter_assets_by_readiness(
                flow_id=mock_assessment_flow.flow_id,
                ready_only=False,  # Get NOT ready assets
                client_account_id=str(uuid4()),
                engagement_id=str(uuid4()),
                db=mock_db_session,
            )

        assert len(result) == 1
        assert result[0] == asset2_id
