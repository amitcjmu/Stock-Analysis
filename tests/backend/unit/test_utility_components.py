"""
Unit Tests for Utility Components - High Impact

This module provides comprehensive unit tests for utility components
in the discovery flow, covering notification, data processing, and state utilities.

Test Coverage:
- NotificationUtils
- DataUtilities
- StateUtils
- DefensiveMethodResolver
- CommunicationUtils
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Any, Dict, List
import uuid

# Import utility components
from app.services.crewai_flows.unified_discovery_flow.notification_utilities import NotificationUtils
from app.services.crewai_flows.unified_discovery_flow.data_utilities import DataUtilities
from app.services.crewai_flows.unified_discovery_flow.handlers.state_utils import StateUtils
from app.services.crewai_flows.unified_discovery_flow.defensive_method_resolver import DefensiveMethodResolver


class MockFlowInstance:
    """Mock flow instance for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.state = MockState()
        self.context = MockContext()
        self.notifications_sent = []
        self.state_updates = []

    async def send_notification(self, notification_type: str, data: Dict):
        """Mock notification sending"""
        self.notifications_sent.append({
            "type": notification_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })


class MockState:
    """Mock state for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.current_phase = "initialization"
        self.progress_percentage = 0.0
        self.status = "running"
        self.raw_data = []
        self.cleaned_data = []
        self.phase_data = {}
        self.phase_completion = {}
        self.errors = []
        self.warnings = []
        self.agent_insights = []
        self.execution_times = {}
        self.collaboration_log = []

    def add_error(self, phase: str, error: str, details: Dict = None):
        """Add error to state"""
        self.errors.append({
            "phase": phase,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    def add_warning(self, phase: str, warning: str):
        """Add warning to state"""
        self.warnings.append({
            "phase": phase,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })

    def add_agent_insight(self, agent_name: str, insight: str, confidence: float = 0.8):
        """Add agent insight to state"""
        self.agent_insights.append({
            "agent": agent_name,
            "insight": insight,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })


class MockContext:
    """Mock context for testing"""

    def __init__(self):
        self.client_account_id = str(uuid.uuid4())
        self.engagement_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())


class MockDatabaseSession:
    """Mock database session for testing"""

    def __init__(self):
        self.executed_queries = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, query, params=None):
        """Mock query execution"""
        self.executed_queries.append({"query": query, "params": params})
        return MockResult()

    async def commit(self):
        """Mock commit"""
        self.committed = True

    async def rollback(self):
        """Mock rollback"""
        self.rolled_back = True


class MockResult:
    """Mock query result"""

    def __init__(self):
        self.rowcount = 1
        self.fetchall = Mock(return_value=[])
        self.fetchone = Mock(return_value=None)


@pytest.fixture
def mock_flow_instance():
    """Create mock flow instance"""
    return MockFlowInstance()


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return MockDatabaseSession()


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


class TestNotificationUtils:
    """Test NotificationUtils functionality"""

    @pytest.fixture
    def notification_utils(self, mock_flow_instance):
        """Create notification utils instance"""
        return NotificationUtils(mock_flow_instance)

    def test_initialization(self, notification_utils, mock_flow_instance):
        """Test notification utils initialization"""
        assert notification_utils.flow_instance == mock_flow_instance
        assert notification_utils.state == mock_flow_instance.state
        assert notification_utils.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_send_flow_start_notification(self, notification_utils):
        """Test sending flow start notification"""
        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.send_flow_start_notification()

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "flow_start"
            assert "flow_id" in call_args[1]
            assert "client_account_id" in call_args[1]
            assert "engagement_id" in call_args[1]

    @pytest.mark.asyncio
    async def test_send_flow_completion_notification(self, notification_utils):
        """Test sending flow completion notification"""
        final_result = {
            "status": "completed",
            "total_phases": 6,
            "completed_phases": 6,
            "success_rate": 1.0
        }

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.send_flow_completion_notification(final_result)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "flow_completion"
            assert call_args[1]["final_result"] == final_result

    @pytest.mark.asyncio
    async def test_send_approval_request_notification(self, notification_utils):
        """Test sending approval request notification"""
        approval_data = {
            "phase": "field_mapping",
            "approval_type": "field_mapping_approval",
            "data": {"field_mappings": {"hostname": "server_name"}},
            "deadline": "2024-01-15T10:00:00Z"
        }

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.send_approval_request_notification(approval_data)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "approval_request"
            assert call_args[1]["approval_data"] == approval_data

    @pytest.mark.asyncio
    async def test_send_progress_update(self, notification_utils):
        """Test sending progress update"""
        progress = 50
        phase = "data_cleansing"
        message = "Data cleansing in progress"

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.send_progress_update(progress, phase, message)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "progress_update"
            assert call_args[1]["progress"] == progress
            assert call_args[1]["phase"] == phase
            assert call_args[1]["message"] == message

    @pytest.mark.asyncio
    async def test_update_flow_status(self, notification_utils):
        """Test updating flow status"""
        status = "processing"

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.update_flow_status(status)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "status_update"
            assert call_args[1]["status"] == status
            assert notification_utils.state.status == status

    @pytest.mark.asyncio
    async def test_send_error_notification(self, notification_utils):
        """Test sending error notification"""
        error_message = "Data validation failed"
        phase = "data_import"

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.send_error_notification(error_message, phase)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "error"
            assert call_args[1]["error_message"] == error_message
            assert call_args[1]["phase"] == phase

    @pytest.mark.asyncio
    async def test_broadcast_flow_event(self, notification_utils):
        """Test broadcasting flow events"""
        event_type = "phase_completed"
        event_data = {
            "phase": "data_import",
            "duration_ms": 1500,
            "records_processed": 100
        }

        with patch.object(notification_utils, '_send_notification') as mock_send:
            await notification_utils.broadcast_flow_event(event_type, event_data)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "flow_event"
            assert call_args[1]["event_type"] == event_type
            assert call_args[1]["event_data"] == event_data


class TestDataUtilities:
    """Test DataUtilities functionality"""

    @pytest.fixture
    def data_utilities(self, mock_flow_instance):
        """Create data utilities instance"""
        return DataUtilities(mock_flow_instance)

    def test_initialization(self, data_utilities, mock_flow_instance):
        """Test data utilities initialization"""
        assert data_utilities.flow_instance == mock_flow_instance
        assert data_utilities.state == mock_flow_instance.state
        assert data_utilities.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_load_raw_data_from_database(self, data_utilities, mock_db_session, sample_raw_data):
        """Test loading raw data from database"""
        with patch.object(data_utilities, '_execute_query') as mock_query:
            mock_query.return_value = sample_raw_data

            result = await data_utilities.load_raw_data_from_database(mock_db_session)

            assert result == sample_raw_data
            assert data_utilities.state.raw_data == sample_raw_data
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_data_structure(self, data_utilities, sample_raw_data):
        """Test data structure validation"""
        data_utilities.state.raw_data = sample_raw_data

        result = data_utilities.validate_data_structure()

        assert result["is_valid"] is True
        assert "field_analysis" in result
        assert "data_quality_score" in result
        assert result["field_analysis"]["hostname"]["type"] == "string"
        assert result["field_analysis"]["ip_address"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_clean_data_records(self, data_utilities, sample_raw_data):
        """Test data record cleaning"""
        data_utilities.state.raw_data = sample_raw_data

        cleaned_data = data_utilities.clean_data_records()

        assert len(cleaned_data) == len(sample_raw_data)
        assert all("id" in record for record in cleaned_data)
        assert all("hostname" in record for record in cleaned_data)
        assert all("ip_address" in record for record in cleaned_data)

    @pytest.mark.asyncio
    async def test_transform_data_format(self, data_utilities, sample_raw_data):
        """Test data format transformation"""
        field_mappings = {
            "hostname": "server_name",
            "ip_address": "network_address",
            "os": "operating_system"
        }

        transformed_data = data_utilities.transform_data_format(sample_raw_data, field_mappings)

        assert len(transformed_data) == len(sample_raw_data)
        assert all("server_name" in record for record in transformed_data)
        assert all("network_address" in record for record in transformed_data)
        assert all("operating_system" in record for record in transformed_data)

    @pytest.mark.asyncio
    async def test_calculate_data_quality_metrics(self, data_utilities, sample_raw_data):
        """Test data quality metrics calculation"""
        metrics = data_utilities.calculate_data_quality_metrics(sample_raw_data)

        assert "completeness_score" in metrics
        assert "consistency_score" in metrics
        assert "accuracy_score" in metrics
        assert "overall_quality_score" in metrics
        assert all(0 <= score <= 1 for score in metrics.values())


class TestStateUtils:
    """Test StateUtils functionality"""

    @pytest.fixture
    def state_utils(self, mock_flow_instance):
        """Create state utils instance"""
        return StateUtils(mock_flow_instance)

    def test_initialization(self, state_utils, mock_flow_instance):
        """Test state utils initialization"""
        assert state_utils.flow_instance == mock_flow_instance
        assert state_utils.state == mock_flow_instance.state
        assert state_utils.context == mock_flow_instance.context

    @pytest.mark.asyncio
    async def test_record_phase_execution_time(self, state_utils):
        """Test recording phase execution time"""
        phase = "data_import"
        execution_time_ms = 1500.5

        await state_utils.record_phase_execution_time(phase, execution_time_ms)

        assert state_utils.state.execution_times[phase] == execution_time_ms

    @pytest.mark.asyncio
    async def test_append_agent_collaboration(self, state_utils):
        """Test appending agent collaboration"""
        entry = {
            "agent": "DataValidator",
            "action": "validated_schema",
            "timestamp": datetime.now().isoformat(),
            "details": {"records_processed": 100}
        }

        await state_utils.append_agent_collaboration(entry)

        assert len(state_utils.state.collaboration_log) == 1
        assert state_utils.state.collaboration_log[0] == entry

    @pytest.mark.asyncio
    async def test_update_phase_progress(self, state_utils):
        """Test updating phase progress"""
        phase = "data_cleansing"
        progress = 75.5

        state_utils.update_phase_progress(phase, progress)

        assert state_utils.state.current_phase == phase
        assert state_utils.state.progress_percentage == progress

    @pytest.mark.asyncio
    async def test_add_phase_insight(self, state_utils):
        """Test adding phase insights"""
        phase = "data_import"
        insight = "High quality data detected"
        confidence = 0.95

        state_utils.add_phase_insight(phase, insight, confidence)

        assert len(state_utils.state.agent_insights) == 1
        assert state_utils.state.agent_insights[0]["phase"] == phase
        assert state_utils.state.agent_insights[0]["insight"] == insight
        assert state_utils.state.agent_insights[0]["confidence"] == confidence

    @pytest.mark.asyncio
    async def test_mark_phase_complete(self, state_utils):
        """Test marking phase as complete"""
        phase = "data_import"

        state_utils.mark_phase_complete(phase)

        assert state_utils.state.phase_completion[phase] is True

    @pytest.mark.asyncio
    async def test_get_phase_summary(self, state_utils):
        """Test getting phase summary"""
        # Add some phase data
        state_utils.state.phase_data["data_import"] = {"status": "completed"}
        state_utils.state.phase_data["field_mapping"] = {"status": "completed"}
        state_utils.state.phase_completion["data_import"] = True
        state_utils.state.phase_completion["field_mapping"] = True

        summary = state_utils.get_phase_summary()

        assert "completed_phases" in summary
        assert "total_phases" in summary
        assert "completion_percentage" in summary
        assert summary["completed_phases"] == 2
        assert summary["total_phases"] >= 2


class TestDefensiveMethodResolver:
    """Test DefensiveMethodResolver functionality"""

    def test_initialization(self):
        """Test defensive method resolver initialization"""
        target_object = Mock()
        target_object.method1 = Mock()
        target_object.method2 = Mock()
        target_object._private_method = Mock()

        resolver = DefensiveMethodResolver(target_object)

        assert resolver.target_object == target_object
        assert "method1" in resolver.available_methods
        assert "method2" in resolver.available_methods
        assert "_private_method" not in resolver.available_methods

    def test_resolve_method_exact_match(self):
        """Test resolving method with exact match"""
        target_object = Mock()
        target_object.exact_method = Mock()

        resolver = DefensiveMethodResolver(target_object)

        method = resolver.resolve_method("exact_method")
        assert method == target_object.exact_method

    def test_resolve_method_case_insensitive(self):
        """Test resolving method with case insensitive matching"""
        target_object = Mock()
        target_object.MethodName = Mock()

        resolver = DefensiveMethodResolver(target_object)

        method = resolver.resolve_method("methodname")
        assert method == target_object.MethodName

    def test_resolve_method_partial_match(self):
        """Test resolving method with partial matching"""
        target_object = Mock()
        target_object.generate_field_mapping_suggestions = Mock()

        resolver = DefensiveMethodResolver(target_object)

        method = resolver.resolve_method("field_mapping")
        assert method == target_object.generate_field_mapping_suggestions

    def test_resolve_method_not_found(self):
        """Test resolving method that doesn't exist"""
        target_object = Mock()
        target_object.existing_method = Mock()

        resolver = DefensiveMethodResolver(target_object)

        method = resolver.resolve_method("nonexistent_method")
        assert method is None

    def test_resolve_method_with_variants(self):
        """Test resolving method with multiple variants"""
        target_object = Mock()
        target_object.generate_field_mapping_suggestions = Mock()
        target_object.generate_field_mapping_suggestion = Mock()  # Common typo
        target_object.generate_mapping_suggestions = Mock()

        resolver = DefensiveMethodResolver(target_object)

        # Should find the exact match first
        method = resolver.resolve_method("generate_field_mapping_suggestions")
        assert method == target_object.generate_field_mapping_suggestions

        # Should find the typo variant
        method = resolver.resolve_method("generate_field_mapping_suggestion")
        assert method == target_object.generate_field_mapping_suggestion

        # Should find the partial match
        method = resolver.resolve_method("mapping_suggestions")
        assert method == target_object.generate_mapping_suggestions


class TestUtilityComponentsIntegration:
    """Test integration between utility components"""

    @pytest.mark.asyncio
    async def test_complete_utility_workflow(self, mock_flow_instance, sample_raw_data):
        """Test complete utility workflow"""
        # Initialize utilities
        notification_utils = NotificationUtils(mock_flow_instance)
        data_utilities = DataUtilities(mock_flow_instance)
        state_utils = StateUtils(mock_flow_instance)

        # Set up data
        data_utilities.state.raw_data = sample_raw_data

        # Send flow start notification
        await notification_utils.send_flow_start_notification()

        # Record execution time
        await state_utils.record_phase_execution_time("data_import", 1500.5)

        # Validate data structure
        validation_result = data_utilities.validate_data_structure()
        assert validation_result["is_valid"] is True

        # Clean data records
        cleaned_data = data_utilities.clean_data_records()
        assert len(cleaned_data) == len(sample_raw_data)

        # Update phase progress
        state_utils.update_phase_progress("data_cleansing", 50.0)

        # Add phase insight
        state_utils.add_phase_insight("data_cleansing", "Data cleaning completed", 0.95)

        # Mark phase complete
        state_utils.mark_phase_complete("data_cleansing")

        # Send progress update
        await notification_utils.send_progress_update(50.0, "data_cleansing", "Data cleaning in progress")

        # Verify state updates
        assert mock_flow_instance.state.current_phase == "data_cleansing"
        assert mock_flow_instance.state.progress_percentage == 50.0
        assert mock_flow_instance.state.phase_completion["data_cleansing"] is True
        assert len(mock_flow_instance.state.execution_times) == 1
        assert len(mock_flow_instance.state.agent_insights) == 1
        assert len(mock_flow_instance.state.collaboration_log) == 0  # No collaboration logged yet

    @pytest.mark.asyncio
    async def test_error_handling_in_utilities(self, mock_flow_instance):
        """Test error handling in utilities"""
        notification_utils = NotificationUtils(mock_flow_instance)
        state_utils = StateUtils(mock_flow_instance)

        # Send error notification
        await notification_utils.send_error_notification("Test error", "data_import")

        # Add error to state
        state_utils.state.add_error("data_import", "Test error", {"details": "test"})

        # Verify error handling
        assert len(mock_flow_instance.state.errors) == 1
        assert mock_flow_instance.state.errors[0]["phase"] == "data_import"
        assert mock_flow_instance.state.errors[0]["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_defensive_method_resolution(self):
        """Test defensive method resolution with real flow instance"""
        mock_flow_instance = MockFlowInstance()

        # Add some methods to the flow instance
        mock_flow_instance.generate_field_mapping_suggestions = Mock()
        mock_flow_instance.execute_data_cleansing = Mock()
        mock_flow_instance.create_discovery_assets = Mock()

        resolver = DefensiveMethodResolver(mock_flow_instance)

        # Test various method resolution scenarios
        method1 = resolver.resolve_method("generate_field_mapping_suggestions")
        assert method1 == mock_flow_instance.generate_field_mapping_suggestions

        method2 = resolver.resolve_method("field_mapping")  # Partial match
        assert method2 == mock_flow_instance.generate_field_mapping_suggestions

        method3 = resolver.resolve_method("data_cleansing")  # Partial match
        assert method3 == mock_flow_instance.execute_data_cleansing

        method4 = resolver.resolve_method("nonexistent_method")
        assert method4 is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
