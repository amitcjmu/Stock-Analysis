"""
Unit Tests for Data Cleansing Analysis API Endpoint

Tests the GET /flows/{flow_id}/data-cleansing endpoint
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.data_cleansing import DataCleansingAnalysis
from test_data_cleansing_fixtures import DataCleansingTestFixtures


class TestDataCleansingAnalysisEndpoint(DataCleansingTestFixtures):
    """Test GET /flows/{flow_id}/data-cleansing endpoint"""

    @pytest.mark.asyncio
    async def test_get_analysis_success(
        self,
        mock_session,
        mock_context,
        mock_user,
        sample_flow_id,
        mock_flow,
        mock_data_import,
        mock_field_mappings,
        sample_quality_issues,
        sample_recommendations,
    ):
        """Test successful analysis retrieval"""

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
            mock_session.execute.return_value.scalars.return_value.all.return_value = (
                mock_field_mappings
            )
            mock_session.execute.return_value.scalar.return_value = 1000

            # Mock the analysis function
            with patch(
                "app.api.v1.endpoints.data_cleansing._perform_data_cleansing_analysis"
            ) as mock_analysis:
                expected_analysis = DataCleansingAnalysis(
                    flow_id=sample_flow_id,
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    total_records=1000,
                    total_fields=5,
                    quality_score=85.0,
                    issues_count=2,
                    recommendations_count=1,
                    quality_issues=sample_quality_issues,
                    recommendations=sample_recommendations,
                    field_quality_scores={"hostname": 90.0, "ip_address": 80.0},
                    processing_status="completed",
                    source="fallback",
                )
                mock_analysis.return_value = expected_analysis

                from app.api.v1.endpoints.data_cleansing import (
                    get_data_cleansing_analysis,
                )

                result = await get_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    include_details=True,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user,
                )

                assert isinstance(result, DataCleansingAnalysis)
                assert result.flow_id == sample_flow_id
                assert result.total_records == 1000
                assert result.total_fields == 5
                assert result.quality_score == 85.0
                assert len(result.quality_issues) == 2
                assert len(result.recommendations) == 1

    @pytest.mark.asyncio
    async def test_get_analysis_flow_not_found(
        self, mock_session, mock_context, mock_user, sample_flow_id
    ):
        """Test analysis retrieval with non-existent flow"""

        with patch(
            "app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis

            with pytest.raises(HTTPException) as exc_info:
                await get_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_analysis_no_data_import(
        self, mock_session, mock_context, mock_user, sample_flow_id, mock_flow
    ):
        """Test analysis retrieval with no data import"""

        mock_flow.data_import_id = None

        with patch(
            "app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock database queries returning None
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis

            with pytest.raises(HTTPException) as exc_info:
                await get_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "No data import found" in str(exc_info.value.detail)
