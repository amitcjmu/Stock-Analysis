"""
Unit Tests for Phase Handlers - High Impact Components

This module provides comprehensive unit tests for phase handlers in the
discovery flow, covering handler execution, error handling, and coordination.

Test Coverage:
- PhaseHandlers
- DataValidationHandler
- FieldMappingGenerator
- AnalysisHandler
- DataProcessingHandler
- CommunicationUtils
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Any, Dict, List
import uuid

# Import phase handlers
from app.services.crewai_flows.unified_discovery_flow.handlers.phase_handlers import PhaseHandlers
from app.services.crewai_flows.unified_discovery_flow.handlers.data_validation_handler import DataValidationHandler
from app.services.crewai_flows.unified_discovery_flow.handlers.field_mapping_generator.base import FieldMappingGenerator
from app.services.crewai_flows.unified_discovery_flow.handlers.analysis_handler import AnalysisHandler
from app.services.crewai_flows.unified_discovery_flow.handlers.data_processing_handler import DataProcessingHandler
from app.services.crewai_flows.unified_discovery_flow.handlers.communication_utils import CommunicationUtils


class MockFlowInstance:
    """Mock flow instance for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.state = MockState()
        self.context = MockContext()
        self.notification_utils = MockNotificationUtils()
        self.state_utils = MockStateUtils()

    async def send_phase_insight(self, phase: str, title: str, description: str, progress: float, data: Dict):
        """Mock phase insight sending"""
        pass

    async def send_phase_error(self, phase: str, error_message: str):
        """Mock phase error sending"""
        pass


class MockState:
    """Mock state for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.current_phase = "initialization"
        self.progress_percentage = 0.0
        self.status = "running"
        self.raw_data = []
        self.field_mappings = {}
        self.cleaned_data = []
        self.asset_inventory = {}
        self.dependencies = []
        self.errors = []
        self.agent_insights = []
        self.phase_data = {}
        self.phase_completion = {}

    def add_error(self, phase: str, error: str, details: Dict = None):
        """Add error to state"""
        self.errors.append({
            "phase": phase,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })


class MockContext:
    """Mock context for testing"""

    def __init__(self):
        self.client_account_id = str(uuid.uuid4())
        self.engagement_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())


class MockNotificationUtils:
    """Mock notification utils for testing"""

    def __init__(self):
        self.notifications_sent = []

    async def send_phase_insight(self, phase: str, title: str, description: str, progress: float, data: Dict):
        """Mock phase insight sending"""
        self.notifications_sent.append({
            "type": "insight",
            "phase": phase,
            "title": title,
            "description": description,
            "progress": progress,
            "data": data
        })

    async def send_phase_error(self, phase: str, error_message: str):
        """Mock phase error sending"""
        self.notifications_sent.append({
            "type": "error",
            "phase": phase,
            "error_message": error_message
        })


class MockStateUtils:
    """Mock state utils for testing"""

    def __init__(self):
        self.execution_times = {}
        self.collaboration_log = []

    async def record_phase_execution_time(self, phase: str, execution_time_ms: float):
        """Mock execution time recording"""
        self.execution_times[phase] = execution_time_ms

    async def append_agent_collaboration(self, entry: Dict):
        """Mock agent collaboration logging"""
        self.collaboration_log.append(entry)


@pytest.fixture
def mock_flow_instance():
    """Create mock flow instance"""
    return MockFlowInstance()


@pytest.fixture
def sample_raw_data():
    """Sample raw data for testing"""
    return [
        {
            "hostname": "server-01",
            "ip_address": "192.168.1.10",
            "os": "Ubuntu 20.04",
            "cpu_cores": 4,
            "memory_gb": 16
        },
        {
            "hostname": "server-02",
            "ip_address": "192.168.1.11",
            "os": "CentOS 8",
            "cpu_cores": 8,
            "memory_gb": 32
        }
    ]


class TestPhaseHandlers:
    """Test PhaseHandlers functionality"""

    @pytest.fixture
    def phase_handlers(self, mock_flow_instance):
        """Create phase handlers instance"""
        return PhaseHandlers(mock_flow_instance)

    def test_initialization(self, phase_handlers, mock_flow_instance):
        """Test phase handlers initialization"""
        assert phase_handlers.flow_instance == mock_flow_instance
        assert phase_handlers.state == mock_flow_instance.state
        assert phase_handlers.context == mock_flow_instance.context
        assert phase_handlers.notification_utils == mock_flow_instance.notification_utils
        assert phase_handlers.state_utils == mock_flow_instance.state_utils

    @pytest.mark.asyncio
    async def test_execute_data_import_validation(self, phase_handlers, sample_raw_data):
        """Test data import validation execution"""
        phase_handlers.state.raw_data = sample_raw_data

        with patch.object(phase_handlers, '_send_phase_insight') as mock_insight:
            with patch.object(phase_handlers, '_record_phase_execution_time') as mock_time:
                result = await phase_handlers.execute_data_import_validation()

                assert result["status"] == "success"
                assert "validation_results" in result
                assert "file_analysis" in result
                mock_insight.assert_called_once()
                mock_time.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_data_cleansing(self, phase_handlers, sample_raw_data):
        """Test data cleansing execution"""
        mapping_result = {
            "field_mappings": {
                "hostname": {"target_field": "server_name", "confidence": 0.95}
            }
        }

        phase_handlers.state.raw_data = sample_raw_data
        phase_handlers.state.field_mappings = mapping_result["field_mappings"]

        with patch.object(phase_handlers, '_send_phase_insight') as mock_insight:
            result = await phase_handlers.execute_data_cleansing(mapping_result)

            assert result["status"] == "success"
            assert "cleansed_data" in result
            assert "quality_metrics" in result
            mock_insight.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_discovery_assets(self, phase_handlers):
        """Test discovery asset creation"""
        cleansing_result = {
            "cleansed_data": [
                {"id": 1, "hostname": "server-01", "ip": "192.168.1.10"},
                {"id": 2, "hostname": "server-02", "ip": "192.168.1.11"}
            ],
            "quality_metrics": {"data_quality_score": 0.95}
        }

        phase_handlers.state.cleaned_data = cleansing_result["cleansed_data"]

        with patch.object(phase_handlers, '_send_phase_insight') as mock_insight:
            result = await phase_handlers.create_discovery_assets(cleansing_result)

            assert result["status"] == "success"
            assert "assets_created" in result
            assert "asset_inventory" in result
            mock_insight.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parallel_analysis(self, phase_handlers):
        """Test parallel analysis execution"""
        asset_promotion_result = {
            "assets_promoted": 5,
            "asset_types": ["server", "database", "application"]
        }

        phase_handlers.state.asset_inventory = asset_promotion_result

        with patch.object(phase_handlers, '_send_phase_insight') as mock_insight:
            result = await phase_handlers.execute_parallel_analysis(asset_promotion_result)

            assert result["status"] == "success"
            assert "dependency_analysis" in result
            assert "tech_debt_assessment" in result
            mock_insight.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_phase_insight(self, phase_handlers):
        """Test sending phase insights"""
        phase = "data_import"
        title = "Data Validation Complete"
        description = "Successfully validated 100 records"
        progress = 16.67
        data = {"records_validated": 100, "quality_score": 0.95}

        await phase_handlers._send_phase_insight(phase, title, description, progress, data)

        notifications = phase_handlers.notification_utils.notifications_sent
        assert len(notifications) == 1
        assert notifications[0]["type"] == "insight"
        assert notifications[0]["phase"] == phase
        assert notifications[0]["title"] == title
        assert notifications[0]["description"] == description
        assert notifications[0]["progress"] == progress
        assert notifications[0]["data"] == data

    @pytest.mark.asyncio
    async def test_send_phase_error(self, phase_handlers):
        """Test sending phase errors"""
        phase = "data_cleansing"
        error_message = "Data cleansing failed due to invalid format"

        await phase_handlers._send_phase_error(phase, error_message)

        notifications = phase_handlers.notification_utils.notifications_sent
        assert len(notifications) == 1
        assert notifications[0]["type"] == "error"
        assert notifications[0]["phase"] == phase
        assert notifications[0]["error_message"] == error_message

    @pytest.mark.asyncio
    async def test_add_phase_transition(self, phase_handlers):
        """Test adding phase transitions"""
        phase = "field_mapping"
        status = "completed"
        metadata = {"records_processed": 100}

        await phase_handlers._add_phase_transition(phase, status, metadata)

        # Verify state was updated
        assert phase_handlers.state.current_phase == phase
        assert phase_handlers.state.status == status

    @pytest.mark.asyncio
    async def test_record_phase_execution_time(self, phase_handlers):
        """Test recording phase execution time"""
        phase = "data_import"
        execution_time_ms = 1500.5

        await phase_handlers._record_phase_execution_time(phase, execution_time_ms)

        # Verify execution time was recorded
        assert phase_handlers.state_utils.execution_times[phase] == execution_time_ms

    @pytest.mark.asyncio
    async def test_add_error_entry(self, phase_handlers):
        """Test adding error entries"""
        phase = "data_cleansing"
        error = "Validation failed"
        details = {"field": "hostname", "reason": "invalid_format"}

        await phase_handlers._add_error_entry(phase, error, details)

        # Verify error was added to state
        assert len(phase_handlers.state.errors) == 1
        assert phase_handlers.state.errors[0]["phase"] == phase
        assert phase_handlers.state.errors[0]["error"] == error
        assert phase_handlers.state.errors[0]["details"] == details

    @pytest.mark.asyncio
    async def test_append_agent_collaboration(self, phase_handlers):
        """Test appending agent collaboration"""
        entry = {
            "agent": "DataValidator",
            "action": "validated_schema",
            "timestamp": datetime.now().isoformat(),
            "details": {"records_processed": 100}
        }

        await phase_handlers._append_agent_collaboration(entry)

        # Verify collaboration was logged
        assert len(phase_handlers.state_utils.collaboration_log) == 1
        assert phase_handlers.state_utils.collaboration_log[0] == entry


class TestDataValidationHandler:
    """Test DataValidationHandler functionality"""

    @pytest.fixture
    def validation_handler(self, mock_flow_instance):
        """Create validation handler instance"""
        return DataValidationHandler(mock_flow_instance)

    def test_initialization(self, validation_handler, mock_flow_instance):
        """Test validation handler initialization"""
        assert validation_handler.flow_instance == mock_flow_instance
        assert validation_handler.state == mock_flow_instance.state
        assert validation_handler.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_execute_data_import_validation(self, validation_handler, sample_raw_data):
        """Test data import validation execution"""
        validation_handler.state.raw_data = sample_raw_data

        with patch.object(validation_handler, '_execute_mapping_application') as mock_mapping:
            mock_mapping.return_value = {"status": "success"}

            result = await validation_handler.execute_data_import_validation()

            assert result["status"] == "success"
            assert "validation_results" in result
            assert "file_analysis" in result
            mock_mapping.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_mapping_application(self, validation_handler):
        """Test mapping application execution"""
        validation_result = {
            "is_valid": True,
            "validated_data": [{"hostname": "server-01", "ip": "192.168.1.10"}]
        }

        result = await validation_handler._execute_mapping_application(validation_result)

        assert result["status"] == "success"
        assert "mapping_results" in result


class TestFieldMappingGenerator:
    """Test FieldMappingGenerator functionality"""

    @pytest.fixture
    def mapping_generator(self, mock_flow_instance):
        """Create mapping generator instance"""
        return FieldMappingGenerator(mock_flow_instance)

    def test_initialization(self, mapping_generator, mock_flow_instance):
        """Test mapping generator initialization"""
        assert mapping_generator.flow_instance == mock_flow_instance
        assert mapping_generator.state == mock_flow_instance.state
        assert mapping_generator.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_generate_field_mapping_suggestions(self, mapping_generator, sample_raw_data):
        """Test field mapping suggestions generation"""
        mapping_generator.state.raw_data = sample_raw_data

        with patch.object(mapping_generator, '_analyze_data_structure') as mock_analyze:
            mock_analyze.return_value = {
                "fields": ["hostname", "ip_address", "os"],
                "field_types": {"hostname": "string", "ip_address": "string", "os": "string"}
            }

            result = await mapping_generator.generate_field_mapping_suggestions()

            assert result["status"] == "success"
            assert "field_mappings" in result
            assert "mapping_confidence" in result
            mock_analyze.assert_called_once()


class TestAnalysisHandler:
    """Test AnalysisHandler functionality"""

    @pytest.fixture
    def analysis_handler(self, mock_flow_instance):
        """Create analysis handler instance"""
        return AnalysisHandler(mock_flow_instance)

    def test_initialization(self, analysis_handler, mock_flow_instance):
        """Test analysis handler initialization"""
        assert analysis_handler.flow_instance == mock_flow_instance
        assert analysis_handler.state == mock_flow_instance.state
        assert analysis_handler.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_execute_parallel_analysis(self, analysis_handler):
        """Test parallel analysis execution"""
        asset_promotion_result = {
            "assets_promoted": 5,
            "asset_types": ["server", "database", "application"]
        }

        analysis_handler.state.asset_inventory = asset_promotion_result

        with patch.object(analysis_handler, '_execute_dependency_analysis') as mock_deps:
            with patch.object(analysis_handler, '_execute_tech_debt_analysis') as mock_tech:
                mock_deps.return_value = {"dependencies": []}
                mock_tech.return_value = {"risk_score": 0.75}

                result = await analysis_handler.execute_parallel_analysis(asset_promotion_result)

                assert result["status"] == "success"
                assert "dependency_analysis" in result
                assert "tech_debt_assessment" in result
                mock_deps.assert_called_once()
                mock_tech.assert_called_once()


class TestDataProcessingHandler:
    """Test DataProcessingHandler functionality"""

    @pytest.fixture
    def processing_handler(self, mock_flow_instance):
        """Create processing handler instance"""
        return DataProcessingHandler(mock_flow_instance)

    def test_initialization(self, processing_handler, mock_flow_instance):
        """Test processing handler initialization"""
        assert processing_handler.flow_instance == mock_flow_instance
        assert processing_handler.state == mock_flow_instance.state
        assert processing_handler.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_execute_data_cleansing(self, processing_handler, sample_raw_data):
        """Test data cleansing execution"""
        mapping_result = {
            "field_mappings": {
                "hostname": {"target_field": "server_name", "confidence": 0.95}
            }
        }

        processing_handler.state.raw_data = sample_raw_data
        processing_handler.state.field_mappings = mapping_result["field_mappings"]

        with patch.object(processing_handler, '_clean_data_records') as mock_clean:
            mock_clean.return_value = [
                {"id": 1, "hostname": "server-01", "ip": "192.168.1.10"},
                {"id": 2, "hostname": "server-02", "ip": "192.168.1.11"}
            ]

            result = await processing_handler.execute_data_cleansing(mapping_result)

            assert result["status"] == "success"
            assert "cleansed_data" in result
            assert "quality_metrics" in result
            mock_clean.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_discovery_assets(self, processing_handler):
        """Test discovery asset creation"""
        cleansing_result = {
            "cleansed_data": [
                {"id": 1, "hostname": "server-01", "ip": "192.168.1.10"},
                {"id": 2, "hostname": "server-02", "ip": "192.168.1.11"}
            ],
            "quality_metrics": {"data_quality_score": 0.95}
        }

        processing_handler.state.cleaned_data = cleansing_result["cleansed_data"]

        with patch.object(processing_handler, '_create_asset_records') as mock_create:
            mock_create.return_value = [
                {"asset_id": "asset-1", "name": "server-01", "type": "server"},
                {"asset_id": "asset-2", "name": "server-02", "type": "server"}
            ]

            result = await processing_handler.create_discovery_assets(cleansing_result)

            assert result["status"] == "success"
            assert "assets_created" in result
            assert "asset_inventory" in result
            mock_create.assert_called_once()


class TestCommunicationUtils:
    """Test CommunicationUtils functionality"""

    @pytest.fixture
    def communication_utils(self, mock_flow_instance):
        """Create communication utils instance"""
        return CommunicationUtils(mock_flow_instance)

    def test_initialization(self, communication_utils, mock_flow_instance):
        """Test communication utils initialization"""
        assert communication_utils.flow_instance == mock_flow_instance
        assert communication_utils.state == mock_flow_instance.state
        assert communication_utils.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_send_phase_insight(self, communication_utils):
        """Test sending phase insights"""
        phase = "data_import"
        title = "Data Validation Complete"
        description = "Successfully validated 100 records"
        progress = 16.67
        data = {"records_validated": 100, "quality_score": 0.95}

        await communication_utils.send_phase_insight(phase, title, description, progress, data)

        notifications = communication_utils.notification_utils.notifications_sent
        assert len(notifications) == 1
        assert notifications[0]["type"] == "insight"
        assert notifications[0]["phase"] == phase
        assert notifications[0]["title"] == title
        assert notifications[0]["description"] == description
        assert notifications[0]["progress"] == progress
        assert notifications[0]["data"] == data

    @pytest.mark.asyncio
    async def test_send_phase_error(self, communication_utils):
        """Test sending phase errors"""
        phase = "data_cleansing"
        error_message = "Data cleansing failed due to invalid format"

        await communication_utils.send_phase_error(phase, error_message)

        notifications = communication_utils.notification_utils.notifications_sent
        assert len(notifications) == 1
        assert notifications[0]["type"] == "error"
        assert notifications[0]["phase"] == phase
        assert notifications[0]["error_message"] == error_message


class TestPhaseHandlersIntegration:
    """Test integration between phase handlers"""

    @pytest.mark.asyncio
    async def test_complete_phase_sequence(self, mock_flow_instance, sample_raw_data):
        """Test complete phase sequence execution"""
        phase_handlers = PhaseHandlers(mock_flow_instance)
        phase_handlers.state.raw_data = sample_raw_data

        # Execute data import validation
        validation_result = await phase_handlers.execute_data_import_validation()
        assert validation_result["status"] == "success"

        # Execute field mapping
        mapping_result = {
            "field_mappings": {
                "hostname": {"target_field": "server_name", "confidence": 0.95}
            }
        }

        # Execute data cleansing
        cleansing_result = await phase_handlers.execute_data_cleansing(mapping_result)
        assert cleansing_result["status"] == "success"

        # Create discovery assets
        asset_result = await phase_handlers.create_discovery_assets(cleansing_result)
        assert asset_result["status"] == "success"

        # Execute parallel analysis
        analysis_result = await phase_handlers.execute_parallel_analysis(asset_result)
        assert analysis_result["status"] == "success"

        # Verify all phases completed
        assert len(mock_flow_instance.notification_utils.notifications_sent) > 0
        assert len(mock_flow_instance.state_utils.execution_times) > 0

    @pytest.mark.asyncio
    async def test_error_handling_across_phases(self, mock_flow_instance):
        """Test error handling across phases"""
        phase_handlers = PhaseHandlers(mock_flow_instance)

        # Simulate error in data validation
        phase_handlers.state.raw_data = []  # Empty data should cause error

        with patch.object(phase_handlers, '_send_phase_error') as mock_error:
            result = await phase_handlers.execute_data_import_validation()

            # Should handle error gracefully
            assert result["status"] == "error" or "error" in result
            mock_error.assert_called()

        # Verify error was added to state
        assert len(mock_flow_instance.state.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
