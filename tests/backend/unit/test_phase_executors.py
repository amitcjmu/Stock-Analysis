"""
Unit Tests for Phase Executors - High Impact Components

This module provides comprehensive unit tests for all phase executors in the
discovery flow, covering individual methods, error handling, and edge cases.

Test Coverage:
- DataImportValidationExecutor
- FieldMappingExecutor
- DataCleansingExecutor
- AssetInventoryExecutor
- DependencyAnalysisExecutor
- TechDebtExecutor
- PhaseExecutionManager
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Any, Dict, List
import uuid

# Import phase executors
from app.services.crewai_flows.handlers.phase_executors.data_import_validation.executor import DataImportValidationExecutor
from app.services.crewai_flows.handlers.phase_executors.field_mapping_executor import FieldMappingExecutor
from app.services.crewai_flows.handlers.phase_executors.data_cleansing.executor import DataCleansingExecutor
from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor import AssetInventoryExecutor
from app.services.crewai_flows.handlers.phase_executors.dependency_analysis_executor import DependencyAnalysisExecutor
from app.services.crewai_flows.handlers.phase_executors.tech_debt_executor import TechDebtExecutor
from app.services.crewai_flows.handlers.phase_executors.phase_execution_manager import PhaseExecutionManager


class MockState:
    """Mock state object for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.client_account_id = str(uuid.uuid4())
        self.engagement_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.current_phase = "initialization"
        self.progress_percentage = 0.0
        self.status = "running"
        self.raw_data = []
        self.metadata = {}
        self.phase_data = {}
        self.phase_completion = {}
        self.data_validation_results = {}
        self.field_mappings = {}
        self.cleaned_data = []
        self.data_quality_metrics = {}
        self.asset_inventory = {}
        self.dependencies = []
        self.tech_debt_analysis = {}
        self.errors = []
        self.agent_insights = []

    def add_error(self, phase: str, error: str, details: Dict = None):
        """Add error to state"""
        self.errors.append({
            "phase": phase,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })


class MockCrewManager:
    """Mock crew manager for testing"""

    def __init__(self):
        self.crews = {}

    def create_crew_on_demand(self, crew_type: str, **kwargs):
        """Create mock crew"""
        mock_crew = Mock()
        mock_crew.kickoff = AsyncMock(return_value={"status": "success", "data": {}})
        return mock_crew


class MockFlowBridge:
    """Mock flow bridge for testing"""

    def __init__(self):
        self.state_updates = []

    async def sync_state_update(self, state, phase_name: str, crew_results: Any = None):
        """Mock state sync"""
        self.state_updates.append({
            "phase": phase_name,
            "state": state,
            "results": crew_results
        })


@pytest.fixture
def mock_state():
    """Create mock state for testing"""
    return MockState()


@pytest.fixture
def mock_crew_manager():
    """Create mock crew manager for testing"""
    return MockCrewManager()


@pytest.fixture
def mock_flow_bridge():
    """Create mock flow bridge for testing"""
    return MockFlowBridge()


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


class TestDataImportValidationExecutor:
    """Test DataImportValidationExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return DataImportValidationExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge
        assert hasattr(executor, 'validation_checks')
        assert hasattr(executor, 'file_analyzer')
        assert hasattr(executor, 'report_generator')

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "data_import"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert pytest.approx(executor.get_progress_percentage(), rel=1e-3, abs=1e-3) == 16.7

    def test_get_phase_timeout(self, executor):
        """Test phase timeout"""
        assert executor._get_phase_timeout() == 300

    def test_prepare_crew_input(self, executor, sample_raw_data):
        """Test crew input preparation"""
        executor.state.raw_data = sample_raw_data
        executor.state.metadata = {"source": "test"}

        input_data = executor._prepare_crew_input()

        assert "raw_data" in input_data
        assert "metadata" in input_data
        assert "validation_requirements" in input_data
        assert input_data["validation_requirements"]["check_pii"] is True
        assert input_data["validation_requirements"]["check_security"] is True

    @pytest.mark.asyncio
    async def test_store_results_success(self, executor, sample_raw_data):
        """Test storing successful validation results"""
        results = {
            "is_valid": True,
            "reason": "Validation passed",
            "file_analysis": {
                "field_analysis": {
                    "hostname": {"type": "string", "confidence": 0.95},
                    "ip_address": {"type": "string", "confidence": 0.90}
                },
                "detected_type": "CSV",
                "confidence": 0.95
            },
            "validated_data": sample_raw_data
        }

        await executor._store_results(results)

        assert executor.state.phase_data["data_import"] == results
        assert executor.state.data_validation_results == results
        assert executor.state.phase_completion["data_import"] is True
        assert "detected_columns" in executor.state.metadata
        assert executor.state.raw_data == sample_raw_data

    @pytest.mark.asyncio
    async def test_store_results_failure(self, executor):
        """Test storing failed validation results"""
        results = {
            "is_valid": False,
            "reason": "Invalid data format",
            "file_analysis": {},
            "validation_summary": {"overall_quality_score": 0.3}
        }

        await executor._store_results(results)

        assert executor.state.phase_data["data_import"] == results
        assert executor.state.data_validation_results == results
        assert executor.state.phase_completion.get("data_import", False) is False
        assert len(executor.state.errors) == 1
        assert executor.state.errors[0]["phase"] == "data_import"
        assert executor.state.errors[0]["error"] == "Invalid data format"

    def test_add_validation_insights(self, executor):
        """Test adding validation insights"""
        results = {
            "file_analysis": {
                "detected_type": "CSV",
                "confidence": 0.95,
                "recommended_agent": "CMDB_Data_Analyst_Agent"
            },
            "validation_summary": {
                "overall_quality_score": 0.85,
                "issues_found": 2
            }
        }

        executor._add_validation_insights(results)

        assert len(executor.state.agent_insights) == 2
        assert executor.state.agent_insights[0]["agent"] == "DataImportValidationExecutor"
        assert executor.state.agent_insights[0]["phase"] == "data_import"
        assert "CSV data type" in executor.state.agent_insights[0]["insight"]


class TestFieldMappingExecutor:
    """Test FieldMappingExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return FieldMappingExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge
        assert hasattr(executor, '_modular_executor')
        assert executor.client_account_id == mock_state.client_account_id
        assert executor.engagement_id == mock_state.engagement_id

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "attribute_mapping"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert executor.get_progress_percentage() == 16.7

    def test_get_phase_timeout(self, executor):
        """Test phase timeout"""
        assert executor._get_phase_timeout() == 300

    def test_prepare_crew_input(self, executor, sample_raw_data):
        """Test crew input preparation"""
        executor.state.raw_data = sample_raw_data
        executor.state.field_mappings = {"hostname": "server_name"}

        input_data = executor._prepare_crew_input()

        assert "raw_data" in input_data
        assert "field_mappings" in input_data
        assert "mapping_type" in input_data
        assert input_data["mapping_type"] == "comprehensive_field_mapping"

    @pytest.mark.asyncio
    async def test_store_results_success(self, executor):
        """Test storing successful field mapping results"""
        results = {
            "field_mappings": {
                "hostname": {
                    "target_field": "server_name",
                    "confidence": 0.95,
                    "semantic_type": "identifier"
                },
                "ip_address": {
                    "target_field": "network_address",
                    "confidence": 0.90,
                    "semantic_type": "network"
                }
            },
            "mapping_summary": {
                "total_fields": 5,
                "mapped_fields": 4,
                "unmapped_fields": 1,
                "confidence_threshold": 0.8
            }
        }

        await executor._store_results(results)

        assert executor.state.field_mappings == results["field_mappings"]
        assert executor.state.phase_data["attribute_mapping"] == results
        assert executor.state.phase_completion["attribute_mapping"] is True

    @pytest.mark.asyncio
    async def test_store_results_failure(self, executor):
        """Test storing failed field mapping results"""
        results = {
            "status": "error",
            "error_code": "MAPPING_FAILED",
            "message": "Field mapping failed due to invalid data"
        }

        await executor._store_results(results)

        assert executor.state.phase_data["attribute_mapping"] == results
        assert executor.state.phase_completion.get("attribute_mapping", False) is False
        assert len(executor.state.errors) == 1
        assert executor.state.errors[0]["phase"] == "attribute_mapping"


class TestDataCleansingExecutor:
    """Test DataCleansingExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return DataCleansingExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "data_cleansing"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert executor.get_progress_percentage() == 33.3

    def test_prepare_crew_input(self, executor, sample_raw_data):
        """Test crew input preparation"""
        executor.state.raw_data = sample_raw_data
        executor.state.field_mappings = {"hostname": "server_name"}

        input_data = executor._prepare_crew_input()

        assert "raw_data" in input_data
        assert "field_mappings" in input_data
        assert "cleansing_type" in input_data
        assert input_data["cleansing_type"] == "comprehensive_data_cleansing"

    @pytest.mark.asyncio
    async def test_execute_fallback_disabled(self, executor):
        """Test that fallback execution is disabled"""
        with pytest.raises(RuntimeError, match="Data cleansing fallback disabled"):
            await executor.execute_fallback()

    @pytest.mark.asyncio
    async def test_store_results_success(self, executor):
        """Test storing successful data cleansing results"""
        cleaned_data = [
            {"id": 1, "hostname": "server-01", "ip_address": "192.168.1.10"},
            {"id": 2, "hostname": "server-02", "ip_address": "192.168.1.11"}
        ]

        results = {
            "cleaned_data": cleaned_data,
            "quality_metrics": {
                "data_quality_score": 0.95,
                "standardized_records": 2,
                "validation_errors": 0
            }
        }

        await executor._store_results(results)

        assert executor.state.cleaned_data == cleaned_data
        assert executor.state.data_quality_metrics == results["quality_metrics"]

    @pytest.mark.asyncio
    async def test_store_results_no_cleaned_data(self, executor):
        """Test storing results without cleaned data fails"""
        results = {
            "status": "error",
            "message": "No cleaned data available"
        }

        with pytest.raises(RuntimeError, match="Data cleansing crew did not return cleaned_data"):
            await executor._store_results(results)

    @pytest.mark.asyncio
    async def test_mark_phase_complete(self, executor):
        """Test marking phase as complete"""
        with patch('app.services.crewai_flows.handlers.phase_executors.data_cleansing.database_operations.DatabaseOperations') as mock_db_ops:
            mock_db_instance = AsyncMock()
            mock_db_ops.return_value = mock_db_instance

            await executor._mark_phase_complete("data_cleansing")

            assert executor.state.phase_completion["data_cleansing"] is True
            mock_db_instance.persist_phase_completion_to_database.assert_called_once_with("data_cleansing")


class TestAssetInventoryExecutor:
    """Test AssetInventoryExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return AssetInventoryExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "asset_inventory"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert executor.get_progress_percentage() == 70.0

    def test_prepare_crew_input(self, executor):
        """Test crew input preparation"""
        input_data = executor._prepare_crew_input()
        assert input_data["phase"] == "asset_inventory"

    @pytest.mark.asyncio
    async def test_execute_with_crew_delegated(self, executor):
        """Test that execute_with_crew delegates to direct execution"""
        result = await executor.execute_with_crew({})
        assert result["status"] == "delegated_to_direct_execution"

    @pytest.mark.asyncio
    async def test_store_results(self, executor):
        """Test storing results"""
        results = {
            "assets_created": 5,
            "asset_types": ["server", "database", "application"],
            "inventory_summary": {"total_assets": 5, "classification_accuracy": 0.95}
        }

        
        await executor._store_results(results)
        assert executor.state.phase_data["asset_inventory"] == results
        assert executor.state.phase_completion["asset_inventory"] is True


class TestDependencyAnalysisExecutor:
    """Test DependencyAnalysisExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return DependencyAnalysisExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "dependencies"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert executor.get_progress_percentage() == 66.7

    def test_prepare_crew_input(self, executor):
        """Test crew input preparation"""
        executor.state.asset_inventory = {"total_assets": 5}
        input_data = executor._prepare_crew_input()
        assert "asset_inventory" in input_data
        assert input_data["asset_inventory"]["total_assets"] == 5

    @pytest.mark.asyncio
    async def test_execute_fallback_disabled(self, executor):
        """Test that fallback execution is disabled"""
        with pytest.raises(RuntimeError, match="Dependency analysis requires CrewAI"):
            await executor.execute_fallback()

    def test_process_crew_result(self, executor):
        """Test processing crew results"""
        crew_result = {
            "success": True,
            "dependencies": [
                {
                    "source_id": "app-1",
                    "source_name": "Web App",
                    "target_id": "db-1",
                    "target_name": "Database",
                    "dependency_type": "database_connection",
                    "confidence_score": 0.95,
                    "is_app_to_app": False
                }
            ],
            "summary": {
                "total_dependencies": 1,
                "app_server_dependencies": 1,
                "app_app_dependencies": 0
            }
        }

        result = executor._process_crew_result(crew_result)

        assert result["status"] == "success"
        assert "app_server_mapping" in result
        assert "cross_application_mapping" in result
        assert "all_dependencies" in result
        assert len(result["app_server_mapping"]) == 1
        assert len(result["cross_application_mapping"]) == 0


class TestTechDebtExecutor:
    """Test TechDebtExecutor"""

    @pytest.fixture
    def executor(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create executor instance"""
        return TechDebtExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, executor, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test executor initialization"""
        assert executor.state == mock_state
        assert executor.crew_manager == mock_crew_manager
        assert executor.flow_bridge == mock_flow_bridge

    def test_get_phase_name(self, executor):
        """Test phase name retrieval"""
        assert executor.get_phase_name() == "tech_debt_assessment"

    def test_get_progress_percentage(self, executor):
        """Test progress percentage"""
        assert executor.get_progress_percentage() == 83.3

    def test_prepare_crew_input(self, executor):
        """Test crew input preparation"""
        executor.state.dependencies = [{"type": "database_connection"}]
        executor.state.asset_inventory = {"total_assets": 5}

        input_data = executor._prepare_crew_input()
        assert "dependencies" in input_data
        assert "asset_inventory" in input_data

    @pytest.mark.asyncio
    async def test_store_results(self, executor):
        """Test storing tech debt results"""
        results = {
            "tech_debt_analysis": {
                "legacy_technologies": 3,
                "modernization_candidates": 2,
                "risk_score": 0.75,
                "effort_estimate": "medium"
            },
            "debt_categories": {
                "technology_obsolescence": 2,
                "security_vulnerabilities": 1
            }
        }

        await executor._store_results(results)

        assert executor.state.tech_debt_analysis == results["tech_debt_analysis"]
        assert executor.state.phase_data["tech_debt_assessment"] == results


class TestPhaseExecutionManager:
    """Test PhaseExecutionManager"""

    @pytest.fixture
    def manager(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Create manager instance"""
        return PhaseExecutionManager(mock_state, mock_crew_manager, mock_flow_bridge)

    def test_initialization(self, manager, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test manager initialization"""
        assert manager.state == mock_state
        assert manager.crew_manager == mock_crew_manager
        assert manager.flow_bridge == mock_flow_bridge
        assert hasattr(manager, 'data_import_validation_executor')
        assert hasattr(manager, 'field_mapping_executor')
        assert hasattr(manager, 'data_cleansing_executor')
        assert hasattr(manager, 'asset_inventory_executor')
        assert hasattr(manager, 'dependency_analysis_executor')
        assert hasattr(manager, 'tech_debt_executor')

    @pytest.mark.asyncio
    async def test_execute_data_import_validation_phase(self, manager):
        """Test data import validation phase execution"""
        previous_result = {"status": "initialized"}

        with patch.object(manager.data_import_validation_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "data_import"}

            result = await manager.execute_data_import_validation_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "data_import"
            mock_execute.assert_called_once_with(previous_result)

    @pytest.mark.asyncio
    async def test_execute_field_mapping_phase(self, manager):
        """Test field mapping phase execution"""
        previous_result = {"status": "data_import_completed"}

        with patch.object(manager.field_mapping_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "field_mapping"}

            result = await manager.execute_field_mapping_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "field_mapping"
            mock_execute.assert_called_once_with(previous_result, "full")

    @pytest.mark.asyncio
    async def test_execute_data_cleansing_phase(self, manager):
        """Test data cleansing phase execution"""
        previous_result = {"status": "field_mapping_completed"}

        with patch.object(manager.data_cleansing_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "data_cleansing"}

            result = await manager.execute_data_cleansing_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "data_cleansing"
            mock_execute.assert_called_once_with(previous_result)

    @pytest.mark.asyncio
    async def test_execute_asset_inventory_phase(self, manager):
        """Test asset inventory phase execution"""
        previous_result = {"status": "data_cleansing_completed"}

        with patch.object(manager.asset_inventory_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "asset_inventory"}

            result = await manager.execute_asset_inventory_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "asset_inventory"
            mock_execute.assert_called_once_with(previous_result)

    @pytest.mark.asyncio
    async def test_execute_dependency_analysis_phase(self, manager):
        """Test dependency analysis phase execution"""
        previous_result = {"status": "asset_inventory_completed"}

        with patch.object(manager.dependency_analysis_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "dependency_analysis"}

            result = await manager.execute_dependency_analysis_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "dependency_analysis"
            mock_execute.assert_called_once_with(previous_result)

    @pytest.mark.asyncio
    async def test_execute_tech_debt_analysis_phase(self, manager):
        """Test tech debt analysis phase execution"""
        previous_result = {"status": "dependency_analysis_completed"}

        with patch.object(manager.tech_debt_executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success", "phase": "tech_debt_assessment"}

            result = await manager.execute_tech_debt_analysis_phase(previous_result)

            assert result["status"] == "success"
            assert result["phase"] == "tech_debt_assessment"
            mock_execute.assert_called_once_with(previous_result)

    def test_get_phase_executor(self, manager):
        """Test getting phase executor by name"""
        executor = manager.get_phase_executor("data_import_validation")
        assert executor == manager.data_import_validation_executor

        executor = manager.get_phase_executor("field_mapping")
        assert executor == manager.field_mapping_executor

        executor = manager.get_phase_executor("data_cleansing")
        assert executor == manager.data_cleansing_executor

        executor = manager.get_phase_executor("asset_inventory")
        assert executor == manager.asset_inventory_executor

        executor = manager.get_phase_executor("dependency_analysis")
        assert executor == manager.dependency_analysis_executor

        executor = manager.get_phase_executor("tech_debt_assessment")
        assert executor == manager.tech_debt_executor

        # Test unknown phase
        with pytest.raises(ValueError, match="Unknown phase"):
            manager.get_phase_executor("unknown_phase")


class TestPhaseExecutorErrorHandling:
    """Test error handling across all phase executors"""

    @pytest.mark.asyncio
    async def test_executor_error_propagation(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test that errors are properly propagated from executors"""
        executor = DataImportValidationExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

        # Test with invalid results
        invalid_results = {
            "is_valid": False,
            "reason": "Test error",
            "file_analysis": {}
        }

        await executor._store_results(invalid_results)

        assert len(mock_state.errors) == 1
        assert mock_state.errors[0]["phase"] == "data_import"
        assert mock_state.errors[0]["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_executor_state_consistency(self, mock_state, mock_crew_manager, mock_flow_bridge):
        """Test that executor maintains state consistency"""
        executor = FieldMappingExecutor(mock_state, mock_crew_manager, mock_flow_bridge)

        # Test state updates
        results = {
            "field_mappings": {"test": "mapping"},
            "status": "success"
        }

        await executor._store_results(results)

        assert mock_state.field_mappings == {"test": "mapping"}
        assert mock_state.phase_completion["attribute_mapping"] is True
        assert "attribute_mapping" in mock_state.phase_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
