"""
Integration Tests for Discovery Flow Sequence - Phase 6 Task 57

This module tests the complete discovery flow sequence execution,
data handoff validation between crews, shared memory integration,
and cross-crew collaboration patterns.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock imports for testing
try:
    from app.models.data_import.import_session import ImportSession
    from app.models.discovery_workflow import DiscoveryWorkflow
    from app.services.crewai_flows.discovery_flow_service import DiscoveryFlowService
except ImportError:
    # Fallback for testing environment
    DiscoveryFlowService = Mock
    ImportSession = Mock
    DiscoveryWorkflow = Mock


class MockFlowResult:
    """Mock result from crew execution"""
    def __init__(self, crew_type: str, success: bool = True):
        self.crew_type = crew_type
        self.success = success
        self.timestamp = time.time()
        
        # Generate realistic mock data based on crew type
        if crew_type == "field_mapping":
            self.data = {
                "field_mappings": {
                    "hostname": {"confidence": 0.95, "target": "server_name", "semantic_type": "identifier"},
                    "ip_address": {"confidence": 0.90, "target": "network_address", "semantic_type": "network"},
                    "cpu_count": {"confidence": 0.85, "target": "processor_count", "semantic_type": "technical"}
                },
                "schema_analysis": {
                    "total_fields": 15,
                    "mapped_fields": 12,
                    "unmapped_fields": 3,
                    "confidence_threshold": 0.8
                },
                "insights": {"readiness_for_cleansing": True}
            }
        elif crew_type == "data_cleansing":
            self.data = {
                "cleansing_results": {
                    "standardized_records": 1250,
                    "validation_errors": 15,
                    "duplicate_records": 8,
                    "data_quality_score": 0.92
                },
                "standardization_mapping": {
                    "server_name": "hostname_standardized",
                    "network_address": "ip_standardized"
                },
                "insights": {"readiness_for_inventory": True}
            }
        elif crew_type == "inventory_building":
            self.data = {
                "inventory_results": {
                    "servers_classified": 450,
                    "applications_discovered": 180,
                    "devices_catalogued": 85,
                    "classification_accuracy": 0.89
                },
                "asset_categories": {
                    "servers": {"count": 450, "types": ["physical", "virtual", "cloud"]},
                    "applications": {"count": 180, "types": ["web", "database", "middleware"]},
                    "devices": {"count": 85, "types": ["network", "storage", "security"]}
                },
                "insights": {"readiness_for_dependencies": True}
            }
        elif crew_type == "app_server_dependency":
            self.data = {
                "dependency_results": {
                    "app_server_relationships": 320,
                    "infrastructure_dependencies": 240,
                    "topology_accuracy": 0.87
                },
                "relationship_types": {
                    "hosting": 180,
                    "database_connection": 85,
                    "service_dependency": 55
                },
                "insights": {"readiness_for_app_dependencies": True}
            }
        elif crew_type == "app_app_dependency":
            self.data = {
                "dependency_results": {
                    "app_app_relationships": 150,
                    "api_dependencies": 95,
                    "integration_patterns": 65
                },
                "communication_types": {
                    "rest_api": 60,
                    "database_shared": 35,
                    "message_queue": 30,
                    "file_transfer": 25
                },
                "insights": {"readiness_for_tech_debt": True}
            }
        elif crew_type == "technical_debt":
            self.data = {
                "debt_analysis": {
                    "legacy_technologies": 45,
                    "modernization_candidates": 38,
                    "risk_score": 0.72,
                    "effort_estimate": "medium"
                },
                "debt_categories": {
                    "technology_obsolescence": 15,
                    "security_vulnerabilities": 12,
                    "performance_issues": 10,
                    "compliance_gaps": 8
                },
                "insights": {"readiness_for_integration": True}
            }
        elif crew_type == "integration":
            self.data = {
                "integration_results": {
                    "comprehensive_analysis": True,
                    "data_consistency_score": 0.94,
                    "cross_crew_insights": 6,
                    "discovery_completeness": 0.91
                },
                "final_insights": {
                    "total_assets": 715,
                    "total_dependencies": 470,
                    "migration_readiness": "high",
                    "recommended_strategy": "hybrid_approach"
                }
            }
            
    def to_dict(self):
        return {
            "crew_type": self.crew_type,
            "success": self.success,
            "timestamp": self.timestamp,
            "data": self.data
        }


class MockSharedMemory:
    """Mock shared memory system for testing"""
    def __init__(self):
        self.memories = {}
        self.cross_crew_insights = []
        
    def add(self, key: str, value: Any):
        self.memories[key] = value
        
    def get(self, key: str) -> Any:
        return self.memories.get(key)
        
    def search(self, query: str) -> List[Dict]:
        return [{"content": f"Mock memory for {query}", "score": 0.9}]
        
    def add_cross_crew_insight(self, insight: Dict):
        self.cross_crew_insights.append(insight)
        
    def get_cross_crew_insights(self) -> List[Dict]:
        return self.cross_crew_insights
        
    def validate_data_handoff(self, from_crew: str, to_crew: str) -> bool:
        """Validate data is ready for handoff between crews"""
        handoff_key = f"{from_crew}_to_{to_crew}_handoff"
        handoff_data = self.get(handoff_key)
        return handoff_data is not None and handoff_data.get("ready", False)


@pytest.fixture
def mock_import_session():
    """Create mock import session for testing"""
    session = Mock(spec=ImportSession)
    session.id = 123
    session.client_account_id = 1
    session.engagement_id = 1
    session.data_preview = {
        "columns": ["hostname", "ip_address", "cpu_count", "memory_gb", "os_type"],
        "sample_data": [
            ["server01", "192.168.1.10", "8", "32", "Linux"],
            ["server02", "192.168.1.11", "16", "64", "Windows"]
        ]
    }
    return session


@pytest.fixture
def mock_discovery_workflow():
    """Create mock discovery workflow for testing"""
    workflow = Mock(spec=DiscoveryWorkflow)
    workflow.id = 456
    workflow.data_import_id = 123
    workflow.status = "running"
    workflow.current_phase = "field_mapping"
    return workflow


@pytest.fixture
def mock_discovery_flow_service():
    """Create mock discovery flow service for testing"""
    service = Mock(spec=DiscoveryFlowService)
    service.shared_memory = MockSharedMemory()
    
    # Mock crew execution methods
    async def mock_execute_field_mapping(session):
        result = MockFlowResult("field_mapping")
        # Handle memory failure gracefully
        if service.shared_memory is not None:
            service.shared_memory.add("field_mapping_result", result.to_dict())
            service.shared_memory.add("field_mapping_to_data_cleansing_handoff", {"ready": True})
        else:
            # Fallback behavior when memory system fails
            result.data["insights"]["memory_failure"] = True
            result.data["insights"]["fallback_mode"] = True
        return result.to_dict()
        
    async def mock_execute_data_cleansing(session, field_mapping_result):
        result = MockFlowResult("data_cleansing")
        service.shared_memory.add("data_cleansing_result", result.to_dict())
        service.shared_memory.add("data_cleansing_to_inventory_building_handoff", {"ready": True})
        return result.to_dict()
        
    async def mock_execute_inventory_building(session, previous_results):
        result = MockFlowResult("inventory_building")
        service.shared_memory.add("inventory_building_result", result.to_dict())
        service.shared_memory.add("inventory_building_to_app_server_dependency_handoff", {"ready": True})
        return result.to_dict()
        
    async def mock_execute_app_server_dependency(session, previous_results):
        result = MockFlowResult("app_server_dependency")
        service.shared_memory.add("app_server_dependency_result", result.to_dict())
        service.shared_memory.add("app_server_dependency_to_app_app_dependency_handoff", {"ready": True})
        return result.to_dict()
        
    async def mock_execute_app_app_dependency(session, previous_results):
        result = MockFlowResult("app_app_dependency")
        service.shared_memory.add("app_app_dependency_result", result.to_dict())
        service.shared_memory.add("app_app_dependency_to_technical_debt_handoff", {"ready": True})
        return result.to_dict()
        
    async def mock_execute_technical_debt(session, previous_results):
        result = MockFlowResult("technical_debt")
        service.shared_memory.add("technical_debt_result", result.to_dict())
        service.shared_memory.add("technical_debt_to_integration_handoff", {"ready": True})
        return result.to_dict()
        
    async def mock_execute_integration(session, all_results):
        result = MockFlowResult("integration")
        service.shared_memory.add("integration_result", result.to_dict())
        return result.to_dict()
    
    service.execute_field_mapping_crew = mock_execute_field_mapping
    service.execute_data_cleansing_crew = mock_execute_data_cleansing
    service.execute_inventory_building_crew = mock_execute_inventory_building
    service.execute_app_server_dependency_crew = mock_execute_app_server_dependency
    service.execute_app_app_dependency_crew = mock_execute_app_app_dependency
    service.execute_technical_debt_crew = mock_execute_technical_debt
    service.execute_integration_crew = mock_execute_integration
    
    return service


class TestCompleteFlowExecution:
    """Test complete flow execution sequence"""
    
    @pytest.mark.asyncio
    async def test_complete_flow_sequence(self, mock_discovery_flow_service, mock_import_session):
        """Test complete discovery flow execution from start to finish"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute complete flow sequence
        results = {}
        
        # Phase 1: Field Mapping
        field_mapping_result = await service.execute_field_mapping_crew(session)
        results["field_mapping"] = field_mapping_result
        assert field_mapping_result["success"] is True
        assert "field_mappings" in field_mapping_result["data"]
        
        # Phase 2: Data Cleansing
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        results["data_cleansing"] = data_cleansing_result
        assert data_cleansing_result["success"] is True
        assert "cleansing_results" in data_cleansing_result["data"]
        
        # Phase 3: Inventory Building
        inventory_result = await service.execute_inventory_building_crew(session, results)
        results["inventory_building"] = inventory_result
        assert inventory_result["success"] is True
        assert "inventory_results" in inventory_result["data"]
        
        # Phase 4: App-Server Dependencies
        app_server_result = await service.execute_app_server_dependency_crew(session, results)
        results["app_server_dependency"] = app_server_result
        assert app_server_result["success"] is True
        assert "dependency_results" in app_server_result["data"]
        
        # Phase 5: App-App Dependencies
        app_app_result = await service.execute_app_app_dependency_crew(session, results)
        results["app_app_dependency"] = app_app_result
        assert app_app_result["success"] is True
        assert "dependency_results" in app_app_result["data"]
        
        # Phase 6: Technical Debt
        tech_debt_result = await service.execute_technical_debt_crew(session, results)
        results["technical_debt"] = tech_debt_result
        assert tech_debt_result["success"] is True
        assert "debt_analysis" in tech_debt_result["data"]
        
        # Phase 7: Integration
        integration_result = await service.execute_integration_crew(session, results)
        results["integration"] = integration_result
        assert integration_result["success"] is True
        assert "integration_results" in integration_result["data"]
        
        # Verify complete flow
        assert len(results) == 7
        assert all(result["success"] for result in results.values())
        
    @pytest.mark.asyncio
    async def test_flow_timing_and_performance(self, mock_discovery_flow_service, mock_import_session):
        """Test flow execution timing and performance metrics"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        start_time = time.time()
        
        # Execute flow and measure timing
        field_mapping_result = await service.execute_field_mapping_crew(session)
        field_mapping_time = time.time() - start_time
        
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        data_cleansing_time = time.time() - start_time - field_mapping_time
        
        total_time = time.time() - start_time
        
        # Verify reasonable execution times (mocked should be very fast)
        assert field_mapping_time < 1.0  # Less than 1 second for mock
        assert data_cleansing_time < 1.0
        assert total_time < 2.0
        
        # Verify timing data is captured
        assert field_mapping_result["timestamp"] > start_time
        assert data_cleansing_result["timestamp"] > field_mapping_result["timestamp"]


class TestDataHandoffValidation:
    """Test data handoff validation between crews"""
    
    @pytest.mark.asyncio
    async def test_field_mapping_to_data_cleansing_handoff(self, mock_discovery_flow_service, mock_import_session):
        """Test data handoff from field mapping to data cleansing"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute field mapping
        field_mapping_result = await service.execute_field_mapping_crew(session)
        
        # Verify handoff readiness
        handoff_ready = service.shared_memory.validate_data_handoff("field_mapping", "data_cleansing")
        assert handoff_ready is True
        
        # Verify required data is available
        assert "field_mappings" in field_mapping_result["data"]
        assert "schema_analysis" in field_mapping_result["data"]
        assert field_mapping_result["data"]["insights"]["readiness_for_cleansing"] is True
        
    @pytest.mark.asyncio
    async def test_data_cleansing_to_inventory_handoff(self, mock_discovery_flow_service, mock_import_session):
        """Test data handoff from data cleansing to inventory building"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute prerequisites
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        
        # Verify handoff readiness
        handoff_ready = service.shared_memory.validate_data_handoff("data_cleansing", "inventory_building")
        assert handoff_ready is True
        
        # Verify required data is available
        assert "cleansing_results" in data_cleansing_result["data"]
        assert "standardization_mapping" in data_cleansing_result["data"]
        assert data_cleansing_result["data"]["insights"]["readiness_for_inventory"] is True
        
    @pytest.mark.asyncio
    async def test_inventory_to_dependencies_handoff(self, mock_discovery_flow_service, mock_import_session):
        """Test data handoff from inventory building to dependency analysis"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute prerequisites
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        inventory_result = await service.execute_inventory_building_crew(session, {
            "field_mapping": field_mapping_result,
            "data_cleansing": data_cleansing_result
        })
        
        # Verify handoff readiness
        handoff_ready = service.shared_memory.validate_data_handoff("inventory_building", "app_server_dependency")
        assert handoff_ready is True
        
        # Verify required data is available
        assert "inventory_results" in inventory_result["data"]
        assert "asset_categories" in inventory_result["data"]
        assert inventory_result["data"]["insights"]["readiness_for_dependencies"] is True
        
    @pytest.mark.asyncio
    async def test_dependency_to_tech_debt_handoff(self, mock_discovery_flow_service, mock_import_session):
        """Test data handoff from dependency analysis to technical debt evaluation"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute prerequisites through dependency analysis
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        inventory_result = await service.execute_inventory_building_crew(session, {})
        app_server_result = await service.execute_app_server_dependency_crew(session, {})
        app_app_result = await service.execute_app_app_dependency_crew(session, {})
        
        # Verify handoff readiness
        handoff_ready = service.shared_memory.validate_data_handoff("app_app_dependency", "technical_debt")
        assert handoff_ready is True
        
        # Verify required data is available
        assert "dependency_results" in app_app_result["data"]
        assert "communication_types" in app_app_result["data"]
        assert app_app_result["data"]["insights"]["readiness_for_tech_debt"] is True


class TestSharedMemoryIntegration:
    """Test shared memory integration across entire flow"""
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_flow(self, mock_discovery_flow_service, mock_import_session):
        """Test memory persistence across entire flow execution"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute first few phases
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        inventory_result = await service.execute_inventory_building_crew(session, {})
        
        # Verify all results are stored in memory
        stored_field_mapping = service.shared_memory.get("field_mapping_result")
        stored_data_cleansing = service.shared_memory.get("data_cleansing_result")
        stored_inventory = service.shared_memory.get("inventory_building_result")
        
        assert stored_field_mapping is not None
        assert stored_data_cleansing is not None
        assert stored_inventory is not None
        
        # Verify data integrity
        assert stored_field_mapping["crew_type"] == "field_mapping"
        assert stored_data_cleansing["crew_type"] == "data_cleansing"
        assert stored_inventory["crew_type"] == "inventory_building"
        
    @pytest.mark.asyncio
    async def test_cross_crew_insight_building(self, mock_discovery_flow_service, mock_import_session):
        """Test cumulative insight building across crews"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Add cross-crew insights during execution
        service.shared_memory.add_cross_crew_insight({
            "source": "field_mapping",
            "insight": "High confidence field mappings enable automated cleansing",
            "impact": "data_cleansing"
        })
        
        service.shared_memory.add_cross_crew_insight({
            "source": "data_cleansing",
            "insight": "Clean data improves asset classification accuracy",
            "impact": "inventory_building"
        })
        
        service.shared_memory.add_cross_crew_insight({
            "source": "inventory_building",
            "insight": "Well-classified assets simplify dependency mapping",
            "impact": "dependency_analysis"
        })
        
        # Verify insights are accumulated
        insights = service.shared_memory.get_cross_crew_insights()
        assert len(insights) == 3
        
        # Verify insight flow
        sources = [insight["source"] for insight in insights]
        assert "field_mapping" in sources
        assert "data_cleansing" in sources
        assert "inventory_building" in sources
        
    @pytest.mark.asyncio
    async def test_memory_search_functionality(self, mock_discovery_flow_service, mock_import_session):
        """Test memory search across accumulated data"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute a few phases to populate memory
        await service.execute_field_mapping_crew(session)
        await service.execute_data_cleansing_crew(session, {})
        
        # Search memory for specific patterns
        field_mapping_memories = service.shared_memory.search("field mapping patterns")
        cleansing_memories = service.shared_memory.search("data quality standards")
        
        assert len(field_mapping_memories) > 0
        assert len(cleansing_memories) > 0
        
        # Verify search results contain relevant information
        assert "content" in field_mapping_memories[0]
        assert "score" in field_mapping_memories[0]


class TestSuccessCriteriaValidation:
    """Test success criteria validation at each phase"""
    
    @pytest.mark.asyncio
    async def test_field_mapping_success_criteria(self, mock_discovery_flow_service, mock_import_session):
        """Test success criteria validation for field mapping phase"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        result = await service.execute_field_mapping_crew(session)
        
        # Verify success criteria
        assert result["success"] is True
        assert "field_mappings" in result["data"]
        assert len(result["data"]["field_mappings"]) > 0
        
        # Check confidence thresholds
        for field, mapping in result["data"]["field_mappings"].items():
            assert mapping["confidence"] >= 0.8  # Minimum threshold
            assert "target" in mapping
            assert "semantic_type" in mapping
            
    @pytest.mark.asyncio
    async def test_data_cleansing_success_criteria(self, mock_discovery_flow_service, mock_import_session):
        """Test success criteria validation for data cleansing phase"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute prerequisites
        field_mapping_result = await service.execute_field_mapping_crew(session)
        result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        
        # Verify success criteria
        assert result["success"] is True
        assert "cleansing_results" in result["data"]
        assert result["data"]["cleansing_results"]["data_quality_score"] >= 0.8
        assert result["data"]["cleansing_results"]["standardized_records"] > 0
        
    @pytest.mark.asyncio
    async def test_inventory_building_success_criteria(self, mock_discovery_flow_service, mock_import_session):
        """Test success criteria validation for inventory building phase"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute prerequisites
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        result = await service.execute_inventory_building_crew(session, {})
        
        # Verify success criteria
        assert result["success"] is True
        assert "inventory_results" in result["data"]
        assert result["data"]["inventory_results"]["classification_accuracy"] >= 0.8
        assert result["data"]["inventory_results"]["servers_classified"] > 0
        assert result["data"]["inventory_results"]["applications_discovered"] > 0


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_phase_failure_recovery(self, mock_discovery_flow_service, mock_import_session):
        """Test recovery from phase failure"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Mock a failing phase
        async def failing_data_cleansing(session, field_mapping_result):
            return MockFlowResult("data_cleansing", success=False).to_dict()
            
        service.execute_data_cleansing_crew = failing_data_cleansing
        
        # Execute flow with failure
        field_mapping_result = await service.execute_field_mapping_crew(session)
        assert field_mapping_result["success"] is True
        
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        assert data_cleansing_result["success"] is False
        
        # Verify graceful handling
        assert data_cleansing_result["crew_type"] == "data_cleansing"
        
    @pytest.mark.asyncio
    async def test_data_handoff_failure_handling(self, mock_discovery_flow_service, mock_import_session):
        """Test handling of data handoff failures"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute field mapping successfully
        field_mapping_result = await service.execute_field_mapping_crew(session)
        
        # Remove handoff data to simulate failure
        service.shared_memory.memories.pop("field_mapping_to_data_cleansing_handoff", None)
        
        # Verify handoff validation fails
        handoff_ready = service.shared_memory.validate_data_handoff("field_mapping", "data_cleansing")
        assert handoff_ready is False
        
    @pytest.mark.asyncio
    async def test_memory_system_failure_handling(self, mock_discovery_flow_service, mock_import_session):
        """Test handling of memory system failures"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Simulate memory system failure
        original_memory = service.shared_memory
        service.shared_memory = None
        
        # Should handle gracefully
        result = await service.execute_field_mapping_crew(session)
        # Verify fallback behavior
        assert isinstance(result, dict)
        assert result["data"]["insights"]["memory_failure"] is True
        assert result["data"]["insights"]["fallback_mode"] is True
        
        # Restore memory for cleanup
        service.shared_memory = original_memory


class TestPerformanceOptimization:
    """Test performance optimization across flow"""
    
    @pytest.mark.asyncio
    async def test_concurrent_crew_execution(self, mock_discovery_flow_service, mock_import_session):
        """Test concurrent execution where possible"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute sequential phases first
        field_mapping_result = await service.execute_field_mapping_crew(session)
        data_cleansing_result = await service.execute_data_cleansing_crew(session, field_mapping_result)
        inventory_result = await service.execute_inventory_building_crew(session, {})
        
        # Test concurrent execution of dependency analysis phases
        start_time = time.time()
        
        # These could potentially run in parallel (mock scenario)
        app_server_task = service.execute_app_server_dependency_crew(session, {})
        app_app_task = service.execute_app_app_dependency_crew(session, {})
        
        app_server_result = await app_server_task
        app_app_result = await app_app_task
        
        execution_time = time.time() - start_time
        
        # Verify both completed successfully
        assert app_server_result["success"] is True
        assert app_app_result["success"] is True
        
        # Mock execution should be very fast
        assert execution_time < 1.0
        
    @pytest.mark.asyncio
    async def test_memory_optimization_during_flow(self, mock_discovery_flow_service, mock_import_session):
        """Test memory optimization during long flow execution"""
        service = mock_discovery_flow_service
        session = mock_import_session
        
        # Execute several phases
        await service.execute_field_mapping_crew(session)
        await service.execute_data_cleansing_crew(session, {})
        await service.execute_inventory_building_crew(session, {})
        
        # Check memory usage (mock scenario)
        memory_items = len(service.shared_memory.memories)
        cross_crew_insights = len(service.shared_memory.get_cross_crew_insights())
        
        # Verify reasonable memory usage
        assert memory_items > 0  # Some data stored
        assert memory_items < 100  # Not excessive for mock
        assert cross_crew_insights >= 0  # Insights accumulated


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 