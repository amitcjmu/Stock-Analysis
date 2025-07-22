"""
Integration tests for Discovery Flow agent decisions.

This module tests the agent decision-making process during Discovery flow execution,
including data validation, field mapping, and asset classification decisions.
"""

import asyncio
import json
from typing import Any, Dict, List

import pytest

from tests.fixtures.discovery_flow_fixtures import (
    AGENT_DECISIONS,
    MOCK_CMDB_DATA,
    get_mock_file_content,
)
from tests.test_discovery_flow_base import BaseDiscoveryFlowTest, integration_test, requires_llm


@pytest.mark.asyncio
class TestDiscoveryAgentDecisions(BaseDiscoveryFlowTest):
    """Test agent decision-making in Discovery flow."""
    
    @integration_test
    @requires_llm
    async def test_data_validation_agent_decisions(self, mock_deepinfra_llm):
        """Test that Data Validation Agent makes correct decisions about data quality."""
        # Create a discovery flow
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        # Upload test CMDB data
        file_content = get_mock_file_content("csv")
        await self.upload_file(flow_id, file_content, "test_cmdb.csv")
        
        # Wait for data validation phase to complete
        await self.wait_for_phase(flow_id, "data_import", timeout=10)
        
        # Get flow status to check agent decisions
        status = await self.get_flow_status(flow_id)
        
        # Verify data validation decisions
        assert "validation_results" in status
        validation_results = status["validation_results"]
        
        # Check that agent identified data quality issues
        assert "issues_found" in validation_results
        assert len(validation_results["issues_found"]) > 0
        
        # Verify specific issue detection
        issues = validation_results["issues_found"]
        issue_types = [issue["type"] for issue in issues]
        assert "missing_data" in issue_types or "outdated_os" in issue_types
        
        # Check data quality score
        assert "data_quality_score" in validation_results
        assert 0 <= validation_results["data_quality_score"] <= 1
    
    @integration_test
    async def test_field_mapping_agent_suggestions(self, mock_deepinfra_llm):
        """Test that Field Mapping Agent provides intelligent mapping suggestions."""
        # Create flow and upload data
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        file_content = get_mock_file_content("csv")
        await self.upload_file(flow_id, file_content, "test_cmdb.csv")
        
        # Wait for field mapping phase
        await self.wait_for_phase(flow_id, "field_mapping", timeout=15)
        
        # Get field mapping suggestions
        response = self.client.get(
            f"{self.API_BASE_URL}/data-import/field-mapping/suggestions/{flow_id}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        
        suggestions = response.json()
        
        # Verify mapping suggestions structure
        assert "mappings" in suggestions
        mappings = suggestions["mappings"]
        
        # Check key field mappings
        assert "server_name" in mappings
        assert mappings["server_name"]["suggested_mapping"] in ["hostname", "name", "server_id"]
        assert mappings["server_name"]["confidence"] > 0.7
        
        assert "ip_address" in mappings
        assert mappings["ip_address"]["suggested_mapping"] in ["private_ip", "ip", "network_address"]
        
        # Verify alternatives are provided
        for field, mapping in mappings.items():
            assert "alternatives" in mapping
            assert isinstance(mapping["alternatives"], list)
    
    @integration_test
    async def test_asset_classification_decisions(self, mock_deepinfra_llm, mock_crewai_flow):
        """Test that agents correctly classify assets for migration."""
        # Set up mock responses for asset classification
        mock_crewai_flow.kickoff.return_value = {
            "status": "completed",
            "classifications": AGENT_DECISIONS["asset_classification"]["classifications"],
            "migration_candidates": AGENT_DECISIONS["asset_classification"]["migration_candidates"]
        }
        
        # Create flow and complete initial phases
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        # Upload data and complete field mapping
        file_content = get_mock_file_content("csv")
        await self.upload_file(flow_id, file_content, "test_cmdb.csv")
        
        # Trigger asset inventory phase
        response = self.client.post(
            f"{self.API_BASE_URL}/unified-discovery/flow/{flow_id}/continue",
            headers=self.get_auth_headers(),
            json={"phase": "asset_inventory"}
        )
        assert response.status_code == 200
        
        # Wait for asset classification
        await self.wait_for_phase(flow_id, "asset_inventory", timeout=20)
        
        # Get classification results
        status = await self.get_flow_status(flow_id)
        
        # Verify classification decisions
        assert "asset_classifications" in status
        classifications = status["asset_classifications"]
        
        # Check migration strategy assignments
        assert "migration_candidates" in classifications
        candidates = classifications["migration_candidates"]
        
        # Verify intelligent classification based on characteristics
        assert "rehost" in candidates  # Simple lift-and-shift candidates
        assert "replatform" in candidates  # Candidates needing platform changes
        assert "retire" in candidates  # Candidates for retirement
        
        # Check that critical production systems are identified
        rehost_candidates = candidates.get("rehost", [])
        for server in MOCK_CMDB_DATA["servers"]:
            if server["business_criticality"] in ["High", "Critical"] and server["environment"] == "Production":
                assert server["server_name"] in rehost_candidates or \
                       server["server_name"] in candidates.get("replatform", [])
    
    @integration_test
    async def test_dependency_analysis_decisions(self, mock_deepinfra_llm, mock_crewai_flow):
        """Test that agents correctly identify dependencies and migration groups."""
        # Create flow with test data
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        # Upload comprehensive test data including applications
        test_data = json.dumps(MOCK_CMDB_DATA).encode('utf-8')
        await self.upload_file(flow_id, test_data, "test_cmdb.json")
        
        # Progress through phases to dependency analysis
        await self.wait_for_phase(flow_id, "dependency_analysis", timeout=30)
        
        # Get dependency analysis results
        status = await self.get_flow_status(flow_id)
        
        # Verify dependency detection
        assert "dependency_analysis" in status
        dep_analysis = status["dependency_analysis"]
        
        # Check critical path identification
        assert "critical_paths" in dep_analysis
        critical_paths = dep_analysis["critical_paths"]
        assert len(critical_paths) > 0
        
        # Verify migration group formation
        assert "migration_groups" in dep_analysis
        migration_groups = dep_analysis["migration_groups"]
        
        # Check that database and dependent apps are grouped
        db_group = next((g for g in migration_groups if "APP-DB-01" in g["assets"]), None)
        assert db_group is not None
        assert "CustomerDB" in db_group["assets"]  # Database should be with its server
        
        # Verify reasoning is provided
        for group in migration_groups:
            assert "reason" in group
            assert len(group["reason"]) > 0
    
    @integration_test
    async def test_agent_decision_consistency(self, mock_deepinfra_llm):
        """Test that agent decisions are consistent across multiple runs."""
        # Run the same data through the flow multiple times
        results = []
        
        for i in range(3):
            flow_response = await self.create_discovery_flow()
            flow_id = flow_response["flow_id"]
            
            # Use identical data
            file_content = get_mock_file_content("csv")
            await self.upload_file(flow_id, file_content, "test_cmdb.csv")
            
            # Wait for completion
            await self.wait_for_phase(flow_id, "field_mapping", timeout=15)
            
            # Get results
            status = await self.get_flow_status(flow_id)
            results.append(status)
        
        # Verify consistency in field mapping suggestions
        for i in range(1, len(results)):
            prev_mappings = results[i-1].get("field_mappings", {})
            curr_mappings = results[i].get("field_mappings", {})
            
            # Primary suggestions should be consistent
            for field in ["server_name", "ip_address", "operating_system"]:
                if field in prev_mappings and field in curr_mappings:
                    assert prev_mappings[field]["suggested_mapping"] == \
                           curr_mappings[field]["suggested_mapping"]
    
    @integration_test
    async def test_agent_decision_streaming(self):
        """Test real-time streaming of agent decisions via SSE."""
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        # Collect SSE events
        events = []
        event_collection_task = asyncio.create_task(
            self._collect_sse_events(flow_id, events)
        )
        
        # Trigger flow execution
        file_content = get_mock_file_content("csv")
        await self.upload_file(flow_id, file_content, "test_cmdb.csv")
        
        # Wait a bit for events to stream
        await asyncio.sleep(5)
        event_collection_task.cancel()
        
        # Verify agent decision events were streamed
        agent_events = [e for e in events if e.get("event") == "agent_decision"]
        assert len(agent_events) > 0
        
        # Check event structure
        for event in agent_events:
            assert "data" in event
            data = event["data"]
            self.assert_agent_decision(data, data.get("agent", ""))
            
            # Verify decision content
            assert "decision" in data
            assert len(data["decision"]) > 0
            assert "confidence" in data
    
    async def _collect_sse_events(self, flow_id: str, events: List[Dict[str, Any]]):
        """Helper to collect SSE events."""
        try:
            async for event in self.stream_sse_events(flow_id):
                events.append(event)
        except asyncio.CancelledError:
            pass
    
    @integration_test
    async def test_agent_error_handling(self, mock_deepinfra_llm):
        """Test how agents handle errors and edge cases."""
        # Create flow
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        # Upload malformed data
        malformed_csv = b"server_name,ip_address\nSERVER1,not_an_ip\nSERVER2,\n,10.0.0.1"
        
        response = self.client.post(
            f"{self.API_BASE_URL}/data-import/store-import",
            headers={
                "X-Client-Account-ID": str(self.TEST_CLIENT_ACCOUNT_ID),
                "X-Engagement-ID": str(self.TEST_ENGAGEMENT_ID),
                "X-User-ID": str(self.TEST_USER_ID),
                "Authorization": "Bearer test-token"
            },
            files={"file": ("malformed.csv", malformed_csv, "text/csv")},
            data={"flow_id": flow_id}
        )
        
        # Should still accept the file
        assert response.status_code in [200, 201]
        
        # Wait for validation
        await self.wait_for_phase(flow_id, "data_import", timeout=10)
        
        # Check that agents identified issues
        status = await self.get_flow_status(flow_id)
        validation_results = status.get("validation_results", {})
        
        # Should have found data quality issues
        assert validation_results.get("data_quality_score", 1.0) < 0.7
        issues = validation_results.get("issues_found", [])
        assert len(issues) > 0
        
        # Check for specific issue types
        issue_types = [issue["type"] for issue in issues]
        assert "invalid_data" in issue_types or "missing_data" in issue_types
    
    @integration_test
    async def test_agent_learning_from_feedback(self, mock_deepinfra_llm):
        """Test that agents learn from user feedback on decisions."""
        # Create flow and get initial suggestions
        flow_response = await self.create_discovery_flow()
        flow_id = flow_response["flow_id"]
        
        file_content = get_mock_file_content("csv")
        await self.upload_file(flow_id, file_content, "test_cmdb.csv")
        await self.wait_for_phase(flow_id, "field_mapping", timeout=15)
        
        # Provide feedback on a mapping suggestion
        feedback_response = self.client.post(
            f"{self.API_BASE_URL}/unified-discovery/flow/{flow_id}/feedback",
            headers=self.get_auth_headers(),
            json={
                "phase": "field_mapping",
                "field": "server_name",
                "feedback_type": "correction",
                "correct_mapping": "asset_name",
                "reason": "Our standard uses asset_name instead of hostname"
            }
        )
        assert feedback_response.status_code == 200
        
        # Create another flow to see if learning was applied
        new_flow_response = await self.create_discovery_flow()
        new_flow_id = new_flow_response["flow_id"]
        
        # Upload similar data
        await self.upload_file(new_flow_id, file_content, "test_cmdb2.csv")
        await self.wait_for_phase(new_flow_id, "field_mapping", timeout=15)
        
        # Check if suggestion improved
        response = self.client.get(
            f"{self.API_BASE_URL}/data-import/field-mapping/suggestions/{new_flow_id}",
            headers=self.get_auth_headers()
        )
        new_suggestions = response.json()
        
        # Should now suggest or include asset_name as an alternative
        server_name_mapping = new_suggestions["mappings"].get("server_name", {})
        assert server_name_mapping["suggested_mapping"] == "asset_name" or \
               "asset_name" in server_name_mapping.get("alternatives", [])