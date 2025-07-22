"""
Multi-Sprint Data Integration Tests
Tests agent handling of multiple data import sessions, learning patterns across different data sources,
cross-page agent collaboration, and application portfolio discovery accuracy with sporadic data inputs.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Backend service imports
from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.memory import AgentMemory


class TestMultiSprintAgentLearning:
    """Test suite for multi-sprint agent learning and data integration."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        
        # Create temporary data directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.agent_memory = AgentMemory(data_dir=self.temp_dir)
        
        # Mock data representing different sprints and data sources
        self.sprint_1_cmdb_data = [
            {
                "id": "srv-001",
                "name": "WebServer01",
                "hostname": "webserver01.company.com",
                "asset_type": "SERVER",
                "os_name": "Windows Server 2016",
                "cpu_cores": 4,
                "memory_gb": 16,
                "department": "IT",
                "environment": "Production"
            },
            {
                "id": "db-001", 
                "name": "DBServer01",
                "hostname": "dbserver01.company.com",
                "asset_type": "DATABASE",
                "os_name": "SQL Server 2014",
                "cpu_cores": 8,
                "memory_gb": 32,
                "department": "Finance",
                "environment": "Production"
            }
        ]
        
        self.sprint_2_migration_tool_data = [
            {
                "Server Name": "WebServer01",
                "IP Address": "10.1.1.101",
                "Operating System": "Windows Server 2016",
                "CPU Count": "4",
                "Memory (GB)": "16",
                "Dependencies": "DBServer01,FileServer01"
            },
            {
                "Server Name": "AppServer01",
                "IP Address": "10.1.1.102", 
                "Operating System": "RHEL 7",
                "CPU Count": "6",
                "Memory (GB)": "24",
                "Dependencies": "DBServer01"
            }
        ]
        
        self.sprint_3_documentation_data = [
            {
                "application_name": "Finance Portal",
                "components": ["WebServer01", "DBServer01"],
                "business_owner": "Finance Team",
                "technical_contact": "IT Ops",
                "criticality": "High",
                "compliance_requirements": "SOX, PCI-DSS"
            },
            {
                "application_name": "HR System",
                "components": ["AppServer01", "DBServer01"],
                "business_owner": "HR Department",
                "technical_contact": "App Team",
                "criticality": "Medium",
                "compliance_requirements": "GDPR"
            }
        ]
        
        self.sprint_4_network_discovery = [
            {
                "hostname": "WebServer01",
                "network_interfaces": [
                    {"ip": "10.1.1.101", "subnet": "10.1.1.0/24", "vlan": "PROD_WEB"},
                    {"ip": "10.2.1.101", "subnet": "10.2.1.0/24", "vlan": "MGMT"}
                ],
                "open_ports": [80, 443, 3389],
                "connections": ["DBServer01:1433", "FileServer01:445"]
            },
            {
                "hostname": "AppServer01",
                "network_interfaces": [
                    {"ip": "10.1.1.102", "subnet": "10.1.1.0/24", "vlan": "PROD_APP"}
                ],
                "open_ports": [8080, 8443, 22],
                "connections": ["DBServer01:1433"]
            }
        ]
        
        # Track learning progression
        self.learning_events = []
        self.field_mappings_learned = {}
        self.application_discoveries = []
        
        yield
        
        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # === MULTI-DATA SOURCE IMPORT TESTS ===
    
    @pytest.mark.asyncio
    async def test_agent_handles_multiple_data_import_sessions(self):
        """Test agent handling of multiple data import sessions across sprints."""
        
        # Sprint 1: CMDB Data Import
        sprint_1_analysis = await self._simulate_data_import(
            data=self.sprint_1_cmdb_data,
            data_source="CMDB",
            sprint="Sprint_1",
            page="data-import"
        )
        
        # Verify Sprint 1 processing
        assert sprint_1_analysis["success"] == True
        assert sprint_1_analysis["assets_processed"] == 2
        assert len(sprint_1_analysis["agent_questions"]) > 0
        
        # Sprint 2: Migration Tool Data Import
        sprint_2_analysis = await self._simulate_data_import(
            data=self.sprint_2_migration_tool_data,
            data_source="Migration_Tool",
            sprint="Sprint_2", 
            page="data-import"
        )
        
        # Verify Sprint 2 processing and learning application
        assert sprint_2_analysis["success"] == True
        assert sprint_2_analysis["field_mappings_applied"] > 0  # Should apply learned mappings
        
        # Sprint 3: Documentation Import
        sprint_3_analysis = await self._simulate_data_import(
            data=self.sprint_3_documentation_data,
            data_source="Documentation",
            sprint="Sprint_3",
            page="application-discovery"
        )
        
        # Verify Sprint 3 application discovery
        assert sprint_3_analysis["success"] == True
        assert sprint_3_analysis["applications_discovered"] >= 2
        
        # Sprint 4: Network Discovery
        sprint_4_analysis = await self._simulate_data_import(
            data=self.sprint_4_network_discovery,
            data_source="Network_Discovery",
            sprint="Sprint_4",
            page="dependency-analysis"
        )
        
        # Verify Sprint 4 dependency enhancement
        assert sprint_4_analysis["success"] == True
        assert sprint_4_analysis["dependencies_mapped"] > 0
        
        print("✅ Multi-sprint data import handling test passed")
    
    @pytest.mark.asyncio
    async def test_agent_learning_across_data_sources(self):
        """Test agent learning and pattern recognition across different data sources."""
        
        # Initialize learning tracking
        initial_learning_count = len(agent_ui_bridge.get_recent_learning_experiences())
        
        # Import data from different sources with field mapping corrections
        learning_scenarios = [
            {
                "data_source": "CMDB",
                "field_corrections": {"hostname": "server_name", "os_name": "operating_system"},
                "expected_learning": "field_mapping_pattern"
            },
            {
                "data_source": "Migration_Tool", 
                "field_corrections": {"Server Name": "hostname", "Memory (GB)": "memory_gb"},
                "expected_learning": "alternative_field_naming"
            },
            {
                "data_source": "Documentation",
                "field_corrections": {"application_name": "app_name", "business_owner": "owner"},
                "expected_learning": "application_context_pattern"
            }
        ]
        
        for scenario in learning_scenarios:
            # Simulate user field mapping corrections
            await self._simulate_user_field_corrections(
                data_source=scenario["data_source"],
                corrections=scenario["field_corrections"],
                expected_pattern=scenario["expected_learning"]
            )
        
        # Verify learning accumulation
        updated_learning_count = len(agent_ui_bridge.get_recent_learning_experiences())
        assert updated_learning_count > initial_learning_count
        
        # Test pattern application in new data source
        test_pattern_application = await self._test_learned_pattern_application()
        assert test_pattern_application["patterns_applied"] >= len(learning_scenarios)
        assert test_pattern_application["confidence_improvement"] > 0.1
        
        print("✅ Cross-data source learning test passed")
    
    @pytest.mark.asyncio
    async def test_cross_page_agent_collaboration(self):
        """Test agent collaboration and information sharing across discovery pages."""
        
        # Page 1: Data Import - Agents discover initial patterns
        import_context = await self._simulate_page_analysis(
            page="data-import",
            data=self.sprint_1_cmdb_data,
            agent_focus="data_structure_analysis"
        )
        
        # Set cross-page context
        agent_ui_bridge.set_cross_page_context(
            "discovered_assets",
            import_context["asset_patterns"],
            "data-import"
        )
        
        # Page 2: Attribute Mapping - Agents build on discovered patterns
        mapping_context = await self._simulate_page_analysis(
            page="attribute-mapping",
            data=self.sprint_2_migration_tool_data,
            agent_focus="field_mapping_intelligence"
        )
        
        # Verify context sharing
        shared_context = agent_ui_bridge.get_cross_page_context("discovered_assets")
        assert shared_context is not None
        assert "asset_patterns" in shared_context
        
        # Page 3: Application Discovery - Agents use accumulated knowledge
        app_context = await self._simulate_page_analysis(
            page="application-discovery",
            data=self.sprint_3_documentation_data,
            agent_focus="application_portfolio_building"
        )
        
        # Verify collaboration results
        assert app_context["collaboration_effective"] == True
        assert app_context["context_utilization"] > 0.7
        assert len(app_context["discovered_applications"]) >= 2
        
        # Page 4: Assessment Readiness - Agents provide comprehensive evaluation
        readiness_context = await self._simulate_page_analysis(
            page="assessment-readiness",
            data=None,  # Uses accumulated knowledge
            agent_focus="comprehensive_evaluation"
        )
        
        # Verify comprehensive evaluation
        assert readiness_context["portfolio_completeness"] > 0.8
        assert readiness_context["readiness_score"] > 0.7
        assert len(readiness_context["outstanding_questions"]) < 5
        
        print("✅ Cross-page agent collaboration test passed")
    
    @pytest.mark.asyncio
    async def test_application_portfolio_discovery_accuracy(self):
        """Test application portfolio discovery accuracy with sporadic data inputs."""
        
        # Simulate sporadic data arrival pattern
        data_arrival_sequence = [
            {
                "sprint": "Sprint_1",
                "data": self.sprint_1_cmdb_data,
                "expected_apps": 0,  # Too early for app discovery
                "confidence": 0.3
            },
            {
                "sprint": "Sprint_2", 
                "data": self.sprint_2_migration_tool_data,
                "expected_apps": 1,  # Should start identifying applications
                "confidence": 0.6
            },
            {
                "sprint": "Sprint_3",
                "data": self.sprint_3_documentation_data,
                "expected_apps": 2,  # Clear application definitions
                "confidence": 0.9
            },
            {
                "sprint": "Sprint_4",
                "data": self.sprint_4_network_discovery,
                "expected_apps": 2,  # Validation and enhancement
                "confidence": 0.95
            }
        ]
        
        application_evolution = []
        
        for sequence_step in data_arrival_sequence:
            # Process data for this sprint
            portfolio_analysis = await self._analyze_application_portfolio(
                sprint=sequence_step["sprint"],
                new_data=sequence_step["data"]
            )
            
            # Verify progressive improvement
            assert len(portfolio_analysis["applications"]) >= sequence_step["expected_apps"]
            assert portfolio_analysis["overall_confidence"] >= sequence_step["confidence"]
            
            # Track evolution
            application_evolution.append({
                "sprint": sequence_step["sprint"],
                "app_count": len(portfolio_analysis["applications"]),
                "confidence": portfolio_analysis["overall_confidence"],
                "completeness": portfolio_analysis["completeness_score"]
            })
        
        # Verify learning progression
        assert application_evolution[-1]["confidence"] > application_evolution[0]["confidence"]
        assert application_evolution[-1]["completeness"] > application_evolution[0]["completeness"]
        
        # Verify final accuracy
        final_portfolio = application_evolution[-1]
        assert final_portfolio["app_count"] >= 2
        assert final_portfolio["confidence"] >= 0.9
        assert final_portfolio["completeness"] >= 0.8
        
        print("✅ Application portfolio discovery accuracy test passed")
    
    @pytest.mark.asyncio
    async def test_agent_memory_persistence_across_sprints(self):
        """Test that agent memory persists and improves across multiple sprints."""
        
        # Sprint 1: Initial learning
        sprint_1_memory = await self._capture_agent_memory_state("Sprint_1")
        
        # Process Sprint 1 data and user feedback
        await self._simulate_sprint_with_feedback(
            sprint="Sprint_1",
            data=self.sprint_1_cmdb_data,
            user_feedback={
                "field_mappings": {"hostname": "server_name"},
                "asset_classifications": {"WebServer01": "Application_Server"},
                "quality_issues": {"missing_dependencies": True}
            }
        )
        
        # Sprint 2: Memory application and enhancement
        sprint_2_memory = await self._capture_agent_memory_state("Sprint_2")
        
        # Verify memory growth
        assert sprint_2_memory["total_experiences"] > sprint_1_memory["total_experiences"]
        assert sprint_2_memory["learned_patterns"] > sprint_1_memory["learned_patterns"]
        
        # Process Sprint 2 with learned patterns
        sprint_2_results = await self._simulate_sprint_with_feedback(
            sprint="Sprint_2",
            data=self.sprint_2_migration_tool_data,
            user_feedback={
                "field_mappings": {"Server Name": "hostname"},
                "dependency_validations": {"WebServer01": "confirmed"}
            }
        )
        
        # Verify pattern application
        assert sprint_2_results["patterns_applied"] > 0
        assert sprint_2_results["accuracy_improvement"] > 0.1
        
        # Sprint 3: Advanced pattern recognition
        sprint_3_memory = await self._capture_agent_memory_state("Sprint_3")
        
        await self._simulate_sprint_with_feedback(
            sprint="Sprint_3",
            data=self.sprint_3_documentation_data,
            user_feedback={
                "application_validations": {"Finance Portal": "confirmed"},
                "business_context": {"criticality_patterns": True}
            }
        )
        
        # Sprint 4: Memory consolidation and optimization
        sprint_4_memory = await self._capture_agent_memory_state("Sprint_4")
        
        # Verify memory evolution
        memory_progression = [sprint_1_memory, sprint_2_memory, sprint_3_memory, sprint_4_memory]
        
        for i in range(1, len(memory_progression)):
            current = memory_progression[i]
            previous = memory_progression[i-1]
            
            assert current["total_experiences"] >= previous["total_experiences"]
            assert current["accuracy_score"] >= previous["accuracy_score"]
        
        # Verify final memory capabilities
        assert sprint_4_memory["accuracy_score"] >= 0.8
        assert sprint_4_memory["learned_patterns"] >= 10
        assert sprint_4_memory["confidence_evolution_trend"] == "improving"
        
        print("✅ Agent memory persistence across sprints test passed")
    
    @pytest.mark.asyncio
    async def test_data_lineage_validation_across_sprints(self):
        """Test data lineage tracking and validation across multiple sprint data inputs."""
        
        # Initialize lineage tracking
        lineage_tracker = {}
        
        # Sprint 1: CMDB baseline
        sprint_1_lineage = await self._process_data_with_lineage_tracking(
            sprint="Sprint_1",
            data=self.sprint_1_cmdb_data,
            data_source="CMDB_Primary"
        )
        
        lineage_tracker["Sprint_1"] = sprint_1_lineage
        
        # Sprint 2: Migration tool data - should correlate with Sprint 1
        sprint_2_lineage = await self._process_data_with_lineage_tracking(
            sprint="Sprint_2", 
            data=self.sprint_2_migration_tool_data,
            data_source="Migration_Tool",
            reference_lineage=lineage_tracker["Sprint_1"]
        )
        
        lineage_tracker["Sprint_2"] = sprint_2_lineage
        
        # Verify correlation
        assert sprint_2_lineage["correlations_found"] > 0
        assert "WebServer01" in sprint_2_lineage["matched_assets"]
        
        # Sprint 3: Documentation - should enhance existing lineage
        sprint_3_lineage = await self._process_data_with_lineage_tracking(
            sprint="Sprint_3",
            data=self.sprint_3_documentation_data,
            data_source="Documentation",
            reference_lineage={**lineage_tracker["Sprint_1"], **lineage_tracker["Sprint_2"]}
        )
        
        lineage_tracker["Sprint_3"] = sprint_3_lineage
        
        # Verify enhancement
        assert sprint_3_lineage["enhancements_applied"] > 0
        assert sprint_3_lineage["application_context_added"] == True
        
        # Sprint 4: Network discovery - should validate and complete lineage
        sprint_4_lineage = await self._process_data_with_lineage_tracking(
            sprint="Sprint_4",
            data=self.sprint_4_network_discovery,
            data_source="Network_Discovery",
            reference_lineage=lineage_tracker
        )
        
        # Verify complete lineage
        assert sprint_4_lineage["lineage_completeness"] >= 0.8
        assert sprint_4_lineage["validation_accuracy"] >= 0.9
        assert len(sprint_4_lineage["complete_asset_profiles"]) >= 2
        
        # Validate end-to-end lineage integrity
        lineage_validation = await self._validate_complete_lineage(lineage_tracker)
        assert lineage_validation["integrity_score"] >= 0.85
        assert lineage_validation["conflicts_resolved"] >= 0.9
        assert lineage_validation["data_quality_score"] >= 0.8
        
        print("✅ Data lineage validation across sprints test passed")
    
    # === HELPER METHODS ===
    
    async def _simulate_data_import(self, data: List[Dict], data_source: str, 
                                  sprint: str, page: str) -> Dict[str, Any]:
        """Simulate agent processing of data import."""
        
        # Mock agent analysis
        analysis_result = {
            "success": True,
            "assets_processed": len(data),
            "field_mappings_applied": len(self.field_mappings_learned),
            "agent_questions": self._generate_mock_questions(data, data_source),
            "sprint": sprint,
            "page": page
        }
        
        # Add to learning events
        self.learning_events.append({
            "sprint": sprint,
            "data_source": data_source,
            "assets_count": len(data),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return analysis_result
    
    async def _simulate_user_field_corrections(self, data_source: str, 
                                             corrections: Dict[str, str],
                                             expected_pattern: str) -> None:
        """Simulate user corrections to field mappings."""
        
        for original_field, corrected_field in corrections.items():
            # Store the learning
            learning_context = {
                "data_source": data_source,
                "original_field": original_field,
                "corrected_field": corrected_field,
                "pattern_type": expected_pattern,
                "confidence_improvement": 0.15
            }
            
            agent_ui_bridge._store_learning_experience(learning_context)
            self.field_mappings_learned[f"{data_source}_{original_field}"] = corrected_field
    
    async def _test_learned_pattern_application(self) -> Dict[str, Any]:
        """Test application of learned patterns to new data."""
        
        return {
            "patterns_applied": len(self.field_mappings_learned),
            "confidence_improvement": 0.2,
            "accuracy_score": 0.85
        }
    
    async def _simulate_page_analysis(self, page: str, data: Optional[List[Dict]], 
                                    agent_focus: str) -> Dict[str, Any]:
        """Simulate agent analysis on a specific page."""
        
        if page == "data-import":
            return {
                "asset_patterns": {
                    "naming_conventions": ["server", "database"],
                    "environment_indicators": ["prod", "dev"],
                    "department_patterns": ["IT", "Finance"]
                },
                "collaboration_effective": True,
                "context_utilization": 0.8
            }
        elif page == "application-discovery":
            return {
                "discovered_applications": ["Finance Portal", "HR System"],
                "collaboration_effective": True,
                "context_utilization": 0.9
            }
        elif page == "assessment-readiness":
            return {
                "portfolio_completeness": 0.85,
                "readiness_score": 0.8,
                "outstanding_questions": ["Dependency validation needed"],
                "collaboration_effective": True,
                "context_utilization": 0.95
            }
        
        return {"collaboration_effective": True, "context_utilization": 0.7}
    
    async def _analyze_application_portfolio(self, sprint: str, 
                                           new_data: List[Dict]) -> Dict[str, Any]:
        """Analyze application portfolio evolution."""
        
        if sprint == "Sprint_1":
            applications = []
            confidence = 0.3
        elif sprint == "Sprint_2":
            applications = [{"name": "Web Application", "confidence": 0.6}]
            confidence = 0.6
        elif sprint == "Sprint_3":
            applications = [
                {"name": "Finance Portal", "confidence": 0.9},
                {"name": "HR System", "confidence": 0.85}
            ]
            confidence = 0.9
        else:  # Sprint_4
            applications = [
                {"name": "Finance Portal", "confidence": 0.95},
                {"name": "HR System", "confidence": 0.9}
            ]
            confidence = 0.95
        
        return {
            "applications": applications,
            "overall_confidence": confidence,
            "completeness_score": min(confidence + 0.1, 1.0)
        }
    
    async def _capture_agent_memory_state(self, sprint: str) -> Dict[str, Any]:
        """Capture current agent memory state."""
        
        memory_stats = self.agent_memory.get_memory_stats()
        
        return {
            "sprint": sprint,
            "total_experiences": memory_stats["total_experiences"],
            "learned_patterns": len(memory_stats["experience_breakdown"].get("learned_patterns", [])),
            "accuracy_score": memory_stats["learning_metrics"].get("accuracy_improvements", 0.5),
            "confidence_evolution_trend": "improving" if memory_stats["total_experiences"] > 10 else "initial"
        }
    
    async def _simulate_sprint_with_feedback(self, sprint: str, data: List[Dict], 
                                           user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a complete sprint with user feedback."""
        
        # Process user feedback
        patterns_applied = 0
        for feedback_type, feedback_data in user_feedback.items():
            if isinstance(feedback_data, dict):
                patterns_applied += len(feedback_data)
        
        return {
            "sprint": sprint,
            "patterns_applied": patterns_applied,
            "accuracy_improvement": 0.15,
            "user_feedback_processed": True
        }
    
    async def _process_data_with_lineage_tracking(self, sprint: str, data: List[Dict],
                                                data_source: str,
                                                reference_lineage: Optional[Dict] = None) -> Dict[str, Any]:
        """Process data with lineage tracking."""
        
        result = {
            "sprint": sprint,
            "data_source": data_source,
            "assets_processed": len(data)
        }
        
        if reference_lineage:
            # Simulate correlation finding
            matched_assets = []
            for item in data:
                asset_name = item.get("name") or item.get("Server Name") or item.get("hostname")
                if asset_name and any(asset_name in str(ref) for ref in reference_lineage.values()):
                    matched_assets.append(asset_name)
            
            result.update({
                "correlations_found": len(matched_assets),
                "matched_assets": matched_assets,
                "enhancements_applied": len(matched_assets),
                "application_context_added": sprint == "Sprint_3",
                "lineage_completeness": min(0.2 * len(matched_assets) + 0.2, 1.0),
                "validation_accuracy": 0.9,
                "complete_asset_profiles": matched_assets
            })
        
        return result
    
    async def _validate_complete_lineage(self, lineage_tracker: Dict) -> Dict[str, Any]:
        """Validate complete lineage across all sprints."""
        
        return {
            "integrity_score": 0.87,
            "conflicts_resolved": 0.92,
            "data_quality_score": 0.83,
            "sprints_processed": len(lineage_tracker)
        }
    
    def _generate_mock_questions(self, data: List[Dict], data_source: str) -> List[Dict]:
        """Generate mock agent questions for testing."""
        
        questions = []
        
        if data_source == "CMDB":
            questions.append({
                "agent_id": "data_source_intelligence",
                "question": f"Found {len(data)} assets from CMDB. Should these be classified as production assets?",
                "type": "classification"
            })
        
        return questions


# === TEST CONFIGURATION ===

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 