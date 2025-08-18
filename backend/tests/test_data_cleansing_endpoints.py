"""
Unit Tests for Data Cleansing API Endpoints

Tests the three data cleansing endpoints:
- GET /flows/{flow_id}/data-cleansing/stats
- GET /flows/{flow_id}/data-cleansing
- POST /flows/{flow_id}/data-cleansing/trigger
"""

import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Mock crewai module before importing other modules
sys.modules['crewai'] = MagicMock()
sys.modules['crewai.tools'] = MagicMock()
sys.modules['crewai.agent'] = MagicMock()
sys.modules['crewai.task'] = MagicMock()
sys.modules['crewai.crew'] = MagicMock()

from app.api.v1.endpoints.data_cleansing import (
    DataCleansingAnalysis,
    DataCleansingStats,
    TriggerDataCleansingRequest,
    DataQualityIssue,
    DataCleansingRecommendation,
)
from app.core.context import RequestContext
from app.models.client_account import User
from app.models.data_import.core import DataImport
from app.models.data_import.mapping import ImportFieldMapping
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions


class TestDataCleansingEndpoints:
    """Test suite for data cleansing API endpoints"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock request context"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = MagicMock(spec=User)
        user.id = str(uuid.uuid4())
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def sample_flow_id(self):
        """Sample flow ID for testing"""
        return str(uuid.uuid4())

    @pytest.fixture
    def mock_flow(self, sample_flow_id):
        """Create mock discovery flow"""
        flow = MagicMock()
        flow.flow_id = sample_flow_id
        flow.id = str(uuid.uuid4())
        flow.status = "active"
        flow.data_import_id = str(uuid.uuid4())
        return flow

    @pytest.fixture
    def mock_data_import(self):
        """Create mock data import"""
        data_import = MagicMock(spec=DataImport)
        data_import.id = str(uuid.uuid4())
        data_import.total_records = 1000
        data_import.created_at = datetime.utcnow()
        return data_import

    @pytest.fixture
    def mock_field_mappings(self):
        """Create mock field mappings"""
        mappings = []
        for i, field in enumerate(["hostname", "ip_address", "os", "cpu", "memory"]):
            mapping = MagicMock(spec=ImportFieldMapping)
            mapping.id = str(uuid.uuid4())
            mapping.source_field = field
            mapping.target_field = field
            mappings.append(mapping)
        return mappings

    @pytest.fixture
    def sample_quality_issues(self):
        """Sample quality issues for testing"""
        return [
            DataQualityIssue(
                id=str(uuid.uuid4()),
                field_name="hostname",
                issue_type="missing_values",
                severity="medium",
                description="Missing hostname values detected",
                affected_records=50,
                recommendation="Fill missing hostnames with default values",
                auto_fixable=True
            ),
            DataQualityIssue(
                id=str(uuid.uuid4()),
                field_name="ip_address",
                issue_type="invalid_format",
                severity="high",
                description="Invalid IP address formats found",
                affected_records=25,
                recommendation="Validate and correct IP address formats",
                auto_fixable=False
            )
        ]

    @pytest.fixture
    def sample_recommendations(self):
        """Sample recommendations for testing"""
        return [
            DataCleansingRecommendation(
                id=str(uuid.uuid4()),
                category="standardization",
                title="Standardize hostname formats",
                description="Ensure all hostnames follow consistent naming convention",
                priority="high",
                impact="Improves data consistency",
                effort_estimate="2-4 hours",
                fields_affected=["hostname"]
            )
        ]


class TestDataCleansingStatsEndpoint(TestDataCleansingEndpoints):
    """Test GET /flows/{flow_id}/data-cleansing/stats endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_session, mock_context, mock_user, 
                                   sample_flow_id, mock_flow, mock_data_import):
        """Test successful stats retrieval"""
        
        # Mock repository and database queries
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock database queries
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_data_import
            mock_session.execute.return_value.scalar.return_value = 1000

            # Import and call the endpoint function
            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_stats

            result = await get_data_cleansing_stats(
                flow_id=sample_flow_id,
                db=mock_session,
                context=mock_context,
                current_user=mock_user
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
    async def test_get_stats_flow_not_found(self, mock_session, mock_context, mock_user, sample_flow_id):
        """Test stats retrieval with non-existent flow"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_stats

            with pytest.raises(HTTPException) as exc_info:
                await get_data_cleansing_stats(
                    flow_id=sample_flow_id,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_stats_no_data_import(self, mock_session, mock_context, mock_user, 
                                          sample_flow_id, mock_flow):
        """Test stats retrieval with no data import"""
        
        # Mock flow without data import
        mock_flow.data_import_id = None
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
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
                current_user=mock_user
            )

            # Should return empty stats
            assert isinstance(result, DataCleansingStats)
            assert result.total_records == 0
            assert result.clean_records == 0
            assert result.completion_percentage == 0.0


class TestDataCleansingAnalysisEndpoint(TestDataCleansingEndpoints):
    """Test GET /flows/{flow_id}/data-cleansing endpoint"""

    @pytest.mark.asyncio
    async def test_get_analysis_success(self, mock_session, mock_context, mock_user, 
                                      sample_flow_id, mock_flow, mock_data_import, 
                                      mock_field_mappings, sample_quality_issues, 
                                      sample_recommendations):
        """Test successful analysis retrieval"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock database queries
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_data_import
            mock_session.execute.return_value.scalars.return_value.all.return_value = mock_field_mappings
            mock_session.execute.return_value.scalar.return_value = 1000

            # Mock the analysis function
            with patch('app.api.v1.endpoints.data_cleansing._perform_data_cleansing_analysis') as mock_analysis:
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
                    source="fallback"
                )
                mock_analysis.return_value = expected_analysis

                from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis

                result = await get_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    include_details=True,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user
                )

                assert isinstance(result, DataCleansingAnalysis)
                assert result.flow_id == sample_flow_id
                assert result.total_records == 1000
                assert result.total_fields == 5
                assert result.quality_score == 85.0
                assert len(result.quality_issues) == 2
                assert len(result.recommendations) == 1

    @pytest.mark.asyncio
    async def test_get_analysis_flow_not_found(self, mock_session, mock_context, mock_user, sample_flow_id):
        """Test analysis retrieval with non-existent flow"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis

            with pytest.raises(HTTPException) as exc_info:
                await get_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_analysis_no_data_import(self, mock_session, mock_context, mock_user, 
                                             sample_flow_id, mock_flow):
        """Test analysis retrieval with no data import"""
        
        mock_flow.data_import_id = None
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
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
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
            assert "No data import found" in str(exc_info.value.detail)


class TestDataCleansingTriggerEndpoint(TestDataCleansingEndpoints):
    """Test POST /flows/{flow_id}/data-cleansing/trigger endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_analysis_success(self, mock_session, mock_context, mock_user, 
                                          sample_flow_id, mock_flow, mock_data_import, 
                                          mock_field_mappings, sample_quality_issues, 
                                          sample_recommendations):
        """Test successful analysis triggering"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock MasterFlowOrchestrator
            with patch('app.api.v1.endpoints.data_cleansing.MasterFlowOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.execute_phase.return_value = {"status": "success", "result": "completed"}
                mock_orchestrator_class.return_value = mock_orchestrator

                # Mock database queries
                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_data_import
                mock_session.execute.return_value.scalars.return_value.all.return_value = mock_field_mappings
                mock_session.execute.return_value.scalar.return_value = 1000

                # Mock the analysis function
                with patch('app.api.v1.endpoints.data_cleansing._perform_data_cleansing_analysis') as mock_analysis:
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
                        source="agent"
                    )
                    mock_analysis.return_value = expected_analysis

                    from app.api.v1.endpoints.data_cleansing import trigger_data_cleansing_analysis

                    request = TriggerDataCleansingRequest(
                        force_refresh=True,
                        include_agent_analysis=True
                    )

                    result = await trigger_data_cleansing_analysis(
                        flow_id=sample_flow_id,
                        request=request,
                        db=mock_session,
                        context=mock_context,
                        current_user=mock_user
                    )

                    assert isinstance(result, DataCleansingAnalysis)
                    assert result.flow_id == sample_flow_id
                    assert result.source == "agent"
                    assert result.processing_status == "completed"
                    
                    # Verify orchestrator was called
                    mock_orchestrator.execute_phase.assert_called_once_with(
                        flow_id=sample_flow_id,
                        phase_name="data_cleansing",
                        phase_input={
                            "force_refresh": True,
                            "include_agent_analysis": True,
                        }
                    )

    @pytest.mark.asyncio
    async def test_trigger_analysis_orchestrator_failure(self, mock_session, mock_context, mock_user, 
                                                        sample_flow_id, mock_flow):
        """Test analysis triggering with orchestrator failure"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock MasterFlowOrchestrator failure
            with patch('app.api.v1.endpoints.data_cleansing.MasterFlowOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.execute_phase.return_value = {
                    "status": "failed", 
                    "error": "Agent execution failed"
                }
                mock_orchestrator_class.return_value = mock_orchestrator

                from app.api.v1.endpoints.data_cleansing import trigger_data_cleansing_analysis

                request = TriggerDataCleansingRequest()

                result = await trigger_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    request=request,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user
                )

                assert isinstance(result, DataCleansingAnalysis)
                assert result.processing_status == "failed: Agent execution failed"
                assert result.source == "agent_failed"

    @pytest.mark.asyncio
    async def test_trigger_analysis_orchestrator_unavailable(self, mock_session, mock_context, mock_user, 
                                                           sample_flow_id, mock_flow, mock_data_import, 
                                                           mock_field_mappings):
        """Test analysis triggering with orchestrator unavailable"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = mock_flow
            mock_repo_class.return_value = mock_repo

            # Mock MasterFlowOrchestrator import error
            with patch('app.api.v1.endpoints.data_cleansing.MasterFlowOrchestrator', side_effect=ImportError("Service not available")):
                
                # Mock database queries for fallback
                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_data_import
                mock_session.execute.return_value.scalars.return_value.all.return_value = mock_field_mappings

                # Mock the analysis function
                with patch('app.api.v1.endpoints.data_cleansing._perform_data_cleansing_analysis') as mock_analysis:
                    expected_analysis = DataCleansingAnalysis(
                        flow_id=sample_flow_id,
                        analysis_timestamp=datetime.utcnow().isoformat(),
                        total_records=1000,
                        total_fields=5,
                        quality_score=85.0,
                        issues_count=0,
                        recommendations_count=0,
                        quality_issues=[],
                        recommendations=[],
                        field_quality_scores={},
                        processing_status="completed_without_agents",
                        source="fallback"
                    )
                    mock_analysis.return_value = expected_analysis

                    from app.api.v1.endpoints.data_cleansing import trigger_data_cleansing_analysis

                    request = TriggerDataCleansingRequest()

                    result = await trigger_data_cleansing_analysis(
                        flow_id=sample_flow_id,
                        request=request,
                        db=mock_session,
                        context=mock_context,
                        current_user=mock_user
                    )

                    assert isinstance(result, DataCleansingAnalysis)
                    assert result.processing_status == "completed_without_agents"
                    assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_trigger_analysis_flow_not_found(self, mock_session, mock_context, mock_user, sample_flow_id):
        """Test analysis triggering with non-existent flow"""
        
        with patch('app.api.v1.endpoints.data_cleansing.DiscoveryFlowRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_flow_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from app.api.v1.endpoints.data_cleansing import trigger_data_cleansing_analysis

            request = TriggerDataCleansingRequest()

            with pytest.raises(HTTPException) as exc_info:
                await trigger_data_cleansing_analysis(
                    flow_id=sample_flow_id,
                    request=request,
                    db=mock_session,
                    context=mock_context,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)


class TestDataCleansingAnalysisFunction(TestDataCleansingEndpoints):
    """Test _perform_data_cleansing_analysis helper function"""

    @pytest.mark.asyncio
    async def test_perform_analysis_with_data(self, mock_session, mock_data_import, mock_field_mappings, sample_flow_id):
        """Test analysis function with data"""
        
        # Mock database count query
        mock_session.execute.return_value.scalar.return_value = 1000

        from app.api.v1.endpoints.data_cleansing import _perform_data_cleansing_analysis

        result = await _perform_data_cleansing_analysis(
            flow_id=sample_flow_id,
            data_imports=[mock_data_import],
            field_mappings=mock_field_mappings,
            include_details=True,
            db_session=mock_session
        )

        assert isinstance(result, DataCleansingAnalysis)
        assert result.flow_id == sample_flow_id
        assert result.total_records == 1000
        assert result.total_fields == len(mock_field_mappings)
        assert result.quality_score > 0
        assert result.processing_status == "completed_without_agents"
        assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_perform_analysis_no_session(self, mock_data_import, mock_field_mappings, sample_flow_id):
        """Test analysis function without database session"""
        
        from app.api.v1.endpoints.data_cleansing import _perform_data_cleansing_analysis

        result = await _perform_data_cleansing_analysis(
            flow_id=sample_flow_id,
            data_imports=[mock_data_import],
            field_mappings=mock_field_mappings,
            include_details=True
        )

        assert isinstance(result, DataCleansingAnalysis)
        assert result.flow_id == sample_flow_id
        assert result.total_records == 1000  # From mock_data_import.total_records
        assert result.total_fields == len(mock_field_mappings)

    @pytest.mark.asyncio
    async def test_perform_analysis_with_execution_result(self, mock_data_import, mock_field_mappings, sample_flow_id):
        """Test analysis function with successful execution result"""
        
        execution_result = {"status": "success", "agent_results": {"quality_score": 95.0}}

        from app.api.v1.endpoints.data_cleansing import _perform_data_cleansing_analysis

        result = await _perform_data_cleansing_analysis(
            flow_id=sample_flow_id,
            data_imports=[mock_data_import],
            field_mappings=mock_field_mappings,
            include_details=True,
            execution_result=execution_result
        )

        assert isinstance(result, DataCleansingAnalysis)
        assert result.source == "agent"
        assert result.processing_status == "completed"


if __name__ == "__main__":
    pytest.main([__file__])