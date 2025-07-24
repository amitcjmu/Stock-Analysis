"""
Unit tests for AI Analysis Services
Tests AI-powered analysis services including 6R analysis, parameter updates,
question processing, and bulk analysis operations in the ADCS system.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    AnalysisService,
)
from app.schemas.sixr_analysis import AnalysisStatus


# Mock classes
class MockSixRAnalysis:
    """Mock SixRAnalysis model"""

    def __init__(self, id=1, status=AnalysisStatus.PENDING):
        self.id = id
        self.status = status
        self.progress_percentage = 0.0
        self.application_ids = [1, 2, 3]
        self.application_data = []
        self.current_iteration = 1
        self.final_recommendation = None
        self.confidence_score = None


class MockSixRParameters:
    """Mock SixRParameters model"""

    def __init__(self):
        self.analysis_id = 1
        self.iteration_number = 1
        self.business_value = 5
        self.technical_complexity = 5
        self.migration_urgency = 5
        self.compliance_requirements = 5
        self.cost_sensitivity = 5
        self.risk_tolerance = 5
        self.innovation_priority = 5
        self.application_type = "web_application"


class MockAsset:
    """Mock Asset model"""

    def __init__(self, id=1):
        self.id = id
        self.name = f"Application {id}"
        self.asset_type = "application"
        self.location = "on-premise"
        self.environment = "production"
        self.department = "IT"
        self.criticality = "high"
        self.technology_stack = ["java", "oracle"]
        self.complexity_score = 7
        self.operating_system = "linux"
        self.ip_address = "192.168.1.100"
        self.cpu_cores = 8
        self.memory_gb = 16
        self.storage_gb = 500
        self.network_dependencies = ["database", "api"]
        self.database_dependencies = ["oracle-db"]
        self.external_integrations = ["payment-gateway"]
        self.compliance_requirements = ["pci-dss"]
        self.last_patched = datetime.now()
        self.support_model = "vendor"
        self.backup_frequency = "daily"
        self.dr_tier = "tier-1"


class MockSixRRecommendation:
    """Mock SixRRecommendation model"""

    def __init__(self):
        self.analysis_id = 1
        self.iteration_number = 1
        self.recommended_strategy = "rehost"
        self.confidence_score = 0.85
        self.strategy_scores = {"rehost": 0.85, "replatform": 0.70}
        self.key_factors = ["low complexity", "urgent timeline"]
        self.assumptions = ["stable application", "minimal changes needed"]
        self.next_steps = ["assess infrastructure", "plan migration"]


# Fixtures
@pytest.fixture
def analysis_service():
    """Create analysis service instance"""
    return AnalysisService()


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock()
    return session


@pytest.fixture
def mock_decision_engine():
    """Create mock decision engine"""
    engine = MagicMock()
    engine.analyze_parameters = MagicMock(
        return_value={
            "recommended_strategy": "rehost",
            "confidence_score": 0.85,
            "strategy_scores": {
                "rehost": 0.85,
                "replatform": 0.70,
                "refactor": 0.60,
                "repurchase": 0.50,
                "retire": 0.30,
                "retain": 0.40,
            },
            "key_factors": ["low complexity", "urgent timeline", "cost sensitive"],
            "assumptions": ["stable application", "minimal changes needed"],
            "next_steps": ["assess infrastructure", "plan migration", "test strategy"],
            "estimated_effort": "low",
            "estimated_timeline": "1-3 months",
            "estimated_cost_impact": "low",
            "risk_factors": ["minimal downtime required"],
            "business_benefits": ["quick migration", "cost effective"],
            "technical_benefits": ["minimal changes", "proven approach"],
        }
    )
    return engine


@pytest.fixture
def sample_parameters():
    """Create sample analysis parameters"""
    return {
        "business_value": 5,
        "technical_complexity": 3,
        "migration_urgency": 8,
        "compliance_requirements": 5,
        "cost_sensitivity": 7,
        "risk_tolerance": 4,
        "innovation_priority": 3,
        "application_type": "web_application",
    }


@pytest.fixture
def sample_question_responses():
    """Create sample question responses"""
    return [
        {
            "question_id": "q1",
            "response": "yes",
            "confidence": 0.9,
            "source": "user_input",
        },
        {
            "question_id": "q2",
            "response": "high",
            "confidence": 0.85,
            "source": "user_input",
        },
        {
            "question_id": "q3",
            "response": "100-500",
            "confidence": 0.95,
            "source": "discovery_data",
        },
    ]


class TestAnalysisServiceInitialAnalysis:
    """Test initial analysis functionality"""

    @pytest.mark.asyncio
    async def test_run_initial_analysis_success(
        self, analysis_service, mock_db_session, mock_decision_engine, sample_parameters
    ):
        """Test successful initial analysis run"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_params = MockSixRParameters()
        mock_asset = MockAsset(id=1)

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = mock_asset

        mock_db_session.execute.side_effect = [
            mock_result,  # Get analysis
            mock_asset_result,  # Get asset 1
            mock_asset_result,  # Get asset 2
            mock_asset_result,  # Get asset 3
            mock_result,  # Get parameters
        ]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_initial_analysis(
                    analysis_id, sample_parameters, user
                )

        # Assert
        assert mock_db_session.commit.call_count >= 3  # Status updates + final commit
        assert mock_decision_engine.analyze_parameters.called
        assert mock_db_session.add.called  # Recommendation added

        # Verify analysis was updated
        assert mock_analysis.status == AnalysisStatus.COMPLETED
        assert mock_analysis.progress_percentage == 100.0
        assert mock_analysis.final_recommendation == "rehost"
        assert mock_analysis.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_run_initial_analysis_missing_asset(
        self, analysis_service, mock_db_session, mock_decision_engine, sample_parameters
    ):
        """Test initial analysis with missing asset data"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_params = MockSixRParameters()

        # Mock database queries - asset not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = None  # Asset not found

        mock_db_session.execute.side_effect = [
            mock_result,  # Get analysis
            mock_asset_result,  # Get asset 1 (not found)
            mock_asset_result,  # Get asset 2 (not found)
            mock_asset_result,  # Get asset 3 (not found)
            mock_result,  # Get parameters
        ]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_initial_analysis(
                    analysis_id, sample_parameters, user
                )

        # Assert
        assert mock_db_session.commit.called
        assert mock_decision_engine.analyze_parameters.called
        # Verify fallback data was used
        assert len(mock_analysis.application_data) == 3
        assert all(
            app["name"].startswith("Application")
            for app in mock_analysis.application_data
        )

    @pytest.mark.asyncio
    async def test_run_initial_analysis_not_found(
        self, analysis_service, mock_db_session
    ):
        """Test initial analysis when analysis record not found"""
        # Arrange
        analysis_id = 999
        user = "test_user"

        # Mock database query - analysis not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Patch AsyncSessionLocal
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            # Act
            await analysis_service.run_initial_analysis(analysis_id, {}, user)

        # Assert
        assert mock_db_session.execute.called
        assert not mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_run_initial_analysis_database_error(
        self, analysis_service, mock_db_session
    ):
        """Test initial analysis with database error"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)

        # Mock database error
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_analysis
        mock_db_session.execute.side_effect = [mock_result, Exception("Database error")]

        # Create a second session for error handling
        mock_error_session = MagicMock()
        mock_error_session.execute = AsyncMock()
        mock_error_session.commit = AsyncMock()
        mock_error_session.rollback = AsyncMock()
        mock_error_session.__aenter__ = AsyncMock(return_value=mock_error_session)
        mock_error_session.__aexit__ = AsyncMock()

        mock_error_result = MagicMock()
        mock_error_result.scalar_one_or_none.return_value = mock_analysis
        mock_error_session.execute.return_value = mock_error_result

        # Patch AsyncSessionLocal to return different sessions
        sessions = [mock_db_session, mock_error_session]
        session_index = 0

        def get_session():
            nonlocal session_index
            session = sessions[session_index]
            session_index += 1
            return session

        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            side_effect=get_session,
        ):
            # Act
            await analysis_service.run_initial_analysis(analysis_id, {}, user)

        # Assert
        assert mock_db_session.rollback.called
        assert mock_analysis.status == AnalysisStatus.FAILED


class TestAnalysisServiceParameterUpdate:
    """Test parameter update analysis functionality"""

    @pytest.mark.asyncio
    async def test_run_parameter_update_analysis_success(
        self, analysis_service, mock_db_session, mock_decision_engine, sample_parameters
    ):
        """Test successful parameter update analysis"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_analysis.application_data = [{"id": 1, "name": "App1"}]
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_parameter_update_analysis(
                    analysis_id, sample_parameters, user
                )

        # Assert
        assert mock_db_session.commit.call_count >= 2
        assert mock_decision_engine.analyze_parameters.called
        assert mock_db_session.add.called
        assert mock_analysis.status == AnalysisStatus.COMPLETED
        assert mock_analysis.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_run_parameter_update_analysis_no_params(
        self, analysis_service, mock_db_session
    ):
        """Test parameter update analysis when parameters not found"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)

        # Mock database queries - no parameters found
        mock_analysis_result = MagicMock()
        mock_analysis_result.scalar_one_or_none.return_value = mock_analysis

        mock_params_result = MagicMock()
        mock_params_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_analysis_result, mock_params_result]

        # Patch AsyncSessionLocal
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            # Act
            await analysis_service.run_parameter_update_analysis(analysis_id, {}, user)

        # Assert
        assert mock_db_session.commit.call_count == 1  # Only status update
        assert not mock_db_session.add.called


class TestAnalysisServiceQuestionProcessing:
    """Test question response processing functionality"""

    @pytest.mark.asyncio
    async def test_process_question_responses_success(
        self,
        analysis_service,
        mock_db_session,
        mock_decision_engine,
        sample_question_responses,
    ):
        """Test successful question response processing"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_analysis.application_data = [{"id": 1, "name": "App1"}]
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_analysis_result = MagicMock()
        mock_analysis_result.scalar_one_or_none.return_value = mock_analysis

        mock_params_result = MagicMock()
        mock_params_result.scalar_one_or_none.return_value = mock_params

        mock_db_session.execute.side_effect = [mock_analysis_result, mock_params_result]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.process_question_responses(
                    analysis_id, sample_question_responses, user
                )

        # Assert
        assert mock_db_session.commit.called
        assert mock_db_session.add.call_count == 4  # 3 responses + 1 recommendation
        assert mock_decision_engine.analyze_parameters.called

        # Verify decision engine received question context
        call_args = mock_decision_engine.analyze_parameters.call_args
        assert "responses" in call_args[0][1]
        assert call_args[0][1]["responses"] == sample_question_responses

    @pytest.mark.asyncio
    async def test_process_question_responses_empty(
        self, analysis_service, mock_db_session
    ):
        """Test processing empty question responses"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_analysis
        mock_db_session.execute.return_value = mock_result

        # Patch AsyncSessionLocal
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            # Act
            await analysis_service.process_question_responses(analysis_id, [], user)

        # Assert
        assert mock_db_session.commit.called
        assert not mock_db_session.add.called  # No responses to add


class TestAnalysisServiceIterationAnalysis:
    """Test iteration analysis functionality"""

    @pytest.mark.asyncio
    async def test_run_iteration_analysis_success(
        self, analysis_service, mock_db_session, mock_decision_engine
    ):
        """Test successful iteration analysis"""
        # Arrange
        analysis_id = 1
        iteration_number = 2
        user = "test_user"
        request_data = {
            "parameters": {"business_value": 7, "technical_complexity": 4},
            "iteration_notes": "Updated based on stakeholder feedback",
        }

        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_analysis.application_data = [{"id": 1, "name": "App1"}]
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_iteration_analysis(
                    analysis_id, iteration_number, request_data, user
                )

        # Assert
        assert mock_db_session.commit.called
        assert mock_analysis.current_iteration == iteration_number
        assert mock_decision_engine.analyze_parameters.called

        # Verify context includes iteration info
        call_args = mock_decision_engine.analyze_parameters.call_args
        context = call_args[0][1]
        assert context["iteration_number"] == iteration_number
        assert context["iteration_notes"] == "Updated based on stakeholder feedback"

    @pytest.mark.asyncio
    async def test_run_iteration_analysis_parameter_update(
        self, analysis_service, mock_db_session, mock_decision_engine
    ):
        """Test iteration analysis with parameter updates"""
        # Arrange
        analysis_id = 1
        iteration_number = 3
        user = "test_user"
        request_data = {
            "parameters": {
                "business_value": 8,
                "migration_urgency": 9,
                "cost_sensitivity": 3,
            }
        }

        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_iteration_analysis(
                    analysis_id, iteration_number, request_data, user
                )

        # Assert
        assert mock_params.business_value == 8
        assert mock_params.migration_urgency == 9
        assert mock_params.cost_sensitivity == 3


class TestAnalysisServiceBulkOperations:
    """Test bulk analysis operations"""

    @pytest.mark.asyncio
    async def test_run_bulk_analysis_single_batch(self, analysis_service):
        """Test bulk analysis with single batch"""
        # Arrange
        analysis_ids = [1, 2, 3]
        batch_size = 5
        user = "test_user"

        # Mock run_initial_analysis
        with patch.object(
            analysis_service, "run_initial_analysis", new_callable=AsyncMock
        ) as mock_run:
            # Act
            await analysis_service.run_bulk_analysis(analysis_ids, batch_size, user)

        # Assert
        assert mock_run.call_count == 3
        expected_calls = [call(1, {}, user), call(2, {}, user), call(3, {}, user)]
        mock_run.assert_has_calls(expected_calls, any_order=True)

    @pytest.mark.asyncio
    async def test_run_bulk_analysis_multiple_batches(self, analysis_service):
        """Test bulk analysis with multiple batches"""
        # Arrange
        analysis_ids = [1, 2, 3, 4, 5, 6, 7]
        batch_size = 3
        user = "test_user"

        # Mock run_initial_analysis and sleep
        with patch.object(
            analysis_service, "run_initial_analysis", new_callable=AsyncMock
        ) as mock_run:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # Act
                await analysis_service.run_bulk_analysis(analysis_ids, batch_size, user)

        # Assert
        assert mock_run.call_count == 7
        assert mock_sleep.call_count == 2  # Called between batches

    @pytest.mark.asyncio
    async def test_run_bulk_analysis_with_errors(self, analysis_service):
        """Test bulk analysis with some failures"""
        # Arrange
        analysis_ids = [1, 2, 3, 4]
        batch_size = 2
        user = "test_user"

        # Mock run_initial_analysis to fail for some IDs
        async def mock_run_analysis(analysis_id, params, user):
            if analysis_id == 2:
                raise Exception("Analysis failed")
            return None

        with patch.object(
            analysis_service, "run_initial_analysis", side_effect=mock_run_analysis
        ):
            # Act - should not raise exception due to gather with return_exceptions=True
            await analysis_service.run_bulk_analysis(analysis_ids, batch_size, user)

        # Assert - function completes without raising


class TestAnalysisServiceEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_analysis_with_no_application_data(
        self, analysis_service, mock_db_session, mock_decision_engine
    ):
        """Test analysis with empty application data"""
        # Arrange
        analysis_id = 1
        user = "test_user"
        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_analysis.application_ids = []  # No applications
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Patch AsyncSessionLocal and decision engine
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            with patch.object(
                analysis_service, "decision_engine", mock_decision_engine
            ):
                # Act
                await analysis_service.run_initial_analysis(analysis_id, {}, user)

        # Assert
        assert mock_decision_engine.analyze_parameters.called
        # Verify None was passed for application context
        call_args = mock_decision_engine.analyze_parameters.call_args
        assert call_args[0][1] is None

    @pytest.mark.asyncio
    async def test_concurrent_analysis_runs(self, analysis_service):
        """Test concurrent analysis runs"""
        # Arrange
        analysis_ids = [1, 2, 3, 4, 5]
        user = "test_user"

        # Track call order
        call_order = []

        async def mock_run_analysis(analysis_id, params, user):
            call_order.append(f"start_{analysis_id}")
            await asyncio.sleep(0.1)  # Simulate work
            call_order.append(f"end_{analysis_id}")

        with patch.object(
            analysis_service, "run_initial_analysis", side_effect=mock_run_analysis
        ):
            # Act
            await analysis_service.run_bulk_analysis(analysis_ids, 3, user)

        # Assert - verify concurrent execution within batches
        # First batch (1, 2, 3) should start before any complete
        assert call_order.index("start_1") < call_order.index("end_1")
        assert call_order.index("start_2") < call_order.index("end_1")
        assert call_order.index("start_3") < call_order.index("end_1")

    def test_decision_engine_initialization(self):
        """Test decision engine is properly initialized"""
        # Act
        service = AnalysisService()

        # Assert
        assert hasattr(service, "decision_engine")
        assert service.decision_engine is not None

    @pytest.mark.asyncio
    async def test_analysis_with_invalid_parameter_type(
        self, analysis_service, mock_db_session
    ):
        """Test analysis with invalid parameter type in request"""
        # Arrange
        analysis_id = 1
        iteration_number = 2
        user = "test_user"
        request_data = {
            "parameters": {"invalid_param": "should_be_ignored", "business_value": 7}
        }

        mock_analysis = MockSixRAnalysis(id=analysis_id)
        mock_params = MockSixRParameters()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_analysis, mock_params]
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Patch AsyncSessionLocal
        with patch(
            "app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service.AsyncSessionLocal",
            return_value=mock_db_session,
        ):
            # Act - should not raise exception
            await analysis_service.run_iteration_analysis(
                analysis_id, iteration_number, request_data, user
            )

        # Assert
        assert mock_params.business_value == 7
        # Invalid parameter should be ignored
        assert not hasattr(mock_params, "invalid_param")
