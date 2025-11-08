"""
Unit tests for Assessment Flow Readiness API endpoints.

Tests cover:
1. GET /assessment-flow/{flow_id}/asset-readiness/{asset_id} - Success
2. GET /assessment-flow/{flow_id}/asset-readiness/{asset_id} - 404 Not Found
3. GET /assessment-flow/{flow_id}/asset-readiness/{asset_id} - Tenant scoping
4. GET /assessment-flow/{flow_id}/readiness-summary?detailed=true - Success
5. GET /assessment-flow/{flow_id}/readiness-summary?detailed=false - Success
6. GET /assessment-flow/{flow_id}/ready-assets?ready_only=true - Success
7. GET /assessment-flow/{flow_id}/ready-assets?ready_only=false - Success

Target: >90% code coverage
Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 11
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.services.gap_detection.schemas import ComprehensiveGapReport


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
        high_priority_gaps=["missing_cpu_cores"],
        medium_priority_gaps=[],
        is_ready_for_assessment=True,
        readiness_blockers=[],
        analyzed_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def mock_readiness_summary():
    """Create a mock readiness summary."""
    return {
        "flow_id": str(uuid4()),
        "total_assets": 10,
        "ready_count": 7,
        "not_ready_count": 3,
        "overall_readiness_rate": 70.0,
        "asset_reports": [],
        "summary_by_type": {
            "server": {"ready": 5, "not_ready": 2},
            "database": {"ready": 2, "not_ready": 1},
        },
        "analyzed_at": datetime.utcnow().isoformat(),
    }


class TestAssessmentFlowReadinessAPI:
    """Test suite for Assessment Flow Readiness API endpoints."""

    def test_get_asset_readiness_success(
        self, client: TestClient, auth_headers, mock_gap_report
    ):
        """Test GET /assessment-flow/{flow_id}/asset-readiness/{asset_id} success."""
        flow_id = uuid4()
        asset_id = uuid4()

        # Mock AssetReadinessService.analyze_asset_readiness
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_asset_readiness = AsyncMock(
                return_value=mock_gap_report
            )
            mock_service_class.return_value = mock_service

            # Mock current_user to have engagement_id
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/asset-readiness/{asset_id}",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["overall_completeness"] == 0.88
        assert data["is_ready_for_assessment"] is True
        assert len(data["high_priority_gaps"]) == 1

    def test_get_asset_readiness_not_found(self, client: TestClient, auth_headers):
        """Test GET /assessment-flow/{flow_id}/asset-readiness/{asset_id} - 404."""
        flow_id = uuid4()
        asset_id = uuid4()

        # Mock AssetReadinessService to raise ValueError
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_asset_readiness = AsyncMock(
                side_effect=ValueError(
                    f"Asset {asset_id} not found or not in tenant scope"
                )
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/asset-readiness/{asset_id}",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_asset_readiness_tenant_scoping(self, client: TestClient, auth_headers):
        """Test tenant scoping - different tenant returns 404."""
        flow_id = uuid4()
        asset_id = uuid4()

        # Mock AssetReadinessService to raise ValueError for tenant scope
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_asset_readiness = AsyncMock(
                side_effect=ValueError("Asset not in tenant scope")
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/asset-readiness/{asset_id}",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_readiness_summary_detailed(
        self, client: TestClient, auth_headers, mock_readiness_summary
    ):
        """Test GET /assessment-flow/{flow_id}/readiness-summary?detailed=true."""
        flow_id = uuid4()

        # Add detailed reports
        detailed_summary = mock_readiness_summary.copy()
        detailed_summary["asset_reports"] = [
            {
                "asset_id": str(uuid4()),
                "asset_name": "asset-1",
                "asset_type": "server",
                "is_ready": True,
                "overall_completeness": 0.95,
                "readiness_blockers": [],
                "critical_gaps_count": 0,
                "high_priority_gaps_count": 1,
            }
        ]

        # Mock AssetReadinessService.analyze_flow_assets_readiness
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_flow_assets_readiness = AsyncMock(
                return_value=detailed_summary
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/readiness-summary?detailed=true",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_assets"] == 10
        assert data["ready_count"] == 7
        assert data["overall_readiness_rate"] == 70.0
        assert len(data["asset_reports"]) == 1

    def test_get_readiness_summary_counts_only(
        self, client: TestClient, auth_headers, mock_readiness_summary
    ):
        """Test GET /assessment-flow/{flow_id}/readiness-summary?detailed=false."""
        flow_id = uuid4()

        # Mock AssetReadinessService.analyze_flow_assets_readiness
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_flow_assets_readiness = AsyncMock(
                return_value=mock_readiness_summary
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/readiness-summary?detailed=false",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_assets"] == 10
        assert data["ready_count"] == 7
        assert data["asset_reports"] == []  # No detailed reports

    def test_get_ready_assets_ready_only(self, client: TestClient, auth_headers):
        """Test GET /assessment-flow/{flow_id}/ready-assets?ready_only=true."""
        flow_id = uuid4()
        ready_asset_ids = [uuid4(), uuid4(), uuid4()]

        # Mock AssetReadinessService.filter_assets_by_readiness
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.filter_assets_by_readiness = AsyncMock(
                return_value=ready_asset_ids
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/ready-assets?ready_only=true",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all(isinstance(UUID(asset_id), UUID) for asset_id in data)

    def test_get_ready_assets_not_ready_only(self, client: TestClient, auth_headers):
        """Test GET /assessment-flow/{flow_id}/ready-assets?ready_only=false."""
        flow_id = uuid4()
        not_ready_asset_ids = [uuid4(), uuid4()]

        # Mock AssetReadinessService.filter_assets_by_readiness
        with patch(
            "app.api.v1.endpoints.assessment_flow_readiness.AssetReadinessService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.filter_assets_by_readiness = AsyncMock(
                return_value=not_ready_asset_ids
            )
            mock_service_class.return_value = mock_service

            # Mock current_user
            with patch(
                "app.api.v1.endpoints.assessment_flow_readiness.get_current_user"
            ) as mock_get_user:
                mock_user = MagicMock()
                mock_user.engagement_id = uuid4()
                mock_get_user.return_value = mock_user

                response = client.get(
                    f"/api/v1/assessment-flow/{flow_id}/ready-assets?ready_only=false",
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(isinstance(UUID(asset_id), UUID) for asset_id in data)
