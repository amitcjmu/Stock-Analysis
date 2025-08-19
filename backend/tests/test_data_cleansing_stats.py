"""
Unit Tests for Data Cleansing Stats API Endpoint

Tests the GET /flows/{flow_id}/data-cleansing/stats endpoint
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.data_cleansing import DataCleansingStats
from test_data_cleansing_fixtures import DataCleansingTestFixtures


class TestDataCleansingStatsEndpoint(DataCleansingTestFixtures):
    """Test GET /flows/{flow_id}/data-cleansing/stats endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats_success(
        self,
        mock_session,
        mock_context,
        mock_user,
        sample_flow_id,
        mock_flow,
        mock_data_import,
    ):
        """Test successful stats retrieval"""

        # Mock repository and database queries
        with patch(
            "app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock database queries
            mock_session.execute.return_value.scalar_one_or_none.return_value = (
                mock_data_import
            )
            mock_session.execute.return_value.scalar.return_value = 1000

            # Import and call the endpoint function
            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_stats

            result = await get_data_cleansing_stats(
                flow_id=sample_flow_id,
                db=mock_session,
                context=mock_context,
                current_user=mock_user,
            )

            assert isinstance(result, DataCleansingStats)
            assert result.total_records == 1000
            assert result.clean_records > 0
            assert result.records_with_issues >= 0
            assert "low" in result.issues_by_severity
            assert "medium" in result.issues_by_severity
            assert "high" in result.issues_by_severity
            assert "critical" in result.issues_by_severity
            assert 0 <= result.completion_percentage <= 100

    @pytest.mark.asyncio
    async def test_get_stats_flow_not_found(
        self, mock_session, mock_context, mock_user, sample_flow_id
    ):
        """Test stats retrieval with non-existent flow"""

        with patch(
            "app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_stats

            with pytest.raises(HTTPException) as exc_info:
                await get_data_cleansing_stats(
                    flow_id=sample_flow_id,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_stats_no_data_import(
        self, mock_session, mock_context, mock_user, sample_flow_id, mock_flow
    ):
        """Test stats retrieval with no data import"""

        # Mock flow without data import
        mock_flow.data_import_id = None

        with patch(
            "app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock database queries returning None
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_stats

            result = await get_data_cleansing_stats(
                flow_id=sample_flow_id,
                db=mock_session,
                context=mock_context,
                current_user=mock_user,
            )

            # Should return empty stats
            assert isinstance(result, DataCleansingStats)
            assert result.total_records == 0
            assert result.clean_records == 0
            assert result.completion_percentage == 0.0
