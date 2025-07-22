"""
Integration tests for the new agentic Discovery flow.
Tests the removal of hardcoded thresholds and dynamic agent decision-making.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.api.v1.endpoints.discovery_flows.query_endpoints import router as discovery_router
from app.core.database import Base
from app.models.discovery_models import DiscoveryFlow
from app.models.master_flow import MasterFlow
from app.services.crewai_flows.unified_discovery_flow.unified_discovery_flow import UnifiedDiscoveryFlow
from app.services.flow_orchestration.status_manager import FlowStatusManager
from app.services.master_flow_orchestrator import MasterFlowOrchestrator


# Test database setup
@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for agent decisions."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "decision": "approve",
        "confidence": 0.95,
        "reasoning": "High quality mapping with strong semantic alignment",
        "suggestions": ["Consider adding additional context for edge cases"]
    })))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_mapping_data():
    """Sample field mapping data for testing."""
    return {
        "source_fields": [
            {"name": "hostname", "type": "string", "sample": "server01.example.com"},
            {"name": "ip_address", "type": "string", "sample": "192.168.1.100"},
            {"name": "cpu_cores", "type": "integer", "sample": "8"},
            {"name": "memory_gb", "type": "integer", "sample": "32"},
            {"name": "storage_tb", "type": "float", "sample": "2.5"}
        ],
        "target_schema": {
            "host_name": {"type": "string", "required": True},
            "ip": {"type": "string", "required": True},
            "cpu_count": {"type": "integer", "required": True},
            "ram_gb": {"type": "integer", "required": True},
            "disk_tb": {"type": "float", "required": False}
        },
        "mappings": [
            {"source": "hostname", "target": "host_name", "confidence": 0.98},
            {"source": "ip_address", "target": "ip", "confidence": 0.99},
            {"source": "cpu_cores", "target": "cpu_count", "confidence": 0.85},
            {"source": "memory_gb", "target": "ram_gb", "confidence": 0.92},
            {"source": "storage_tb", "target": "disk_tb", "confidence": 0.88}
        ]
    }


class TestAgenticDiscoveryFlow:
    """Test suite for the new agentic Discovery flow."""
    
    @pytest.mark.asyncio
    async def test_no_hardcoded_thresholds(self, test_session, mock_openai_client):
        """Test that hardcoded thresholds are removed and agents make dynamic decisions."""
        # Create master flow
        master_flow = MasterFlow(
            flow_id="master_test_001",
            flow_type="discovery",
            status="in_progress",
            client_account_id=1,
            engagement_id=1,
            created_by=1,
            config={}
        )
        test_session.add(master_flow)
        
        # Create discovery flow
        discovery_flow = DiscoveryFlow(
            flow_id="disc_test_001",
            master_flow_id="master_test_001",
            client_account_id=1,
            engagement_id=1,
            created_by=1,
            status="field_mapping",
            config={},
            state_data={}
        )
        test_session.add(discovery_flow)
        await test_session.commit()
        
        # Initialize the flow with mocked OpenAI
        with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_openai_client):
            flow = UnifiedDiscoveryFlow()
            flow.flow_id = "disc_test_001"
            flow.client_account_id = 1
            flow.engagement_id = 1
            
            # Test field mapping phase - should use agent decision, not hardcoded threshold
            result = await flow._execute_field_mapping_phase(sample_mapping_data())
            
            # Verify agent was called to make decision
            mock_openai_client.chat.completions.create.assert_called()
            
            # Verify decision was based on agent response, not hardcoded threshold
            assert result["status"] == "completed"
            assert result["agent_decision"]["decision"] == "approve"
            assert result["agent_decision"]["confidence"] == 0.95
            assert "reasoning" in result["agent_decision"]
            
            # Verify no hardcoded threshold logic was used
            assert "threshold" not in str(result).lower()
            assert result["agent_decision"]["reasoning"] == "High quality mapping with strong semantic alignment"
    
    
    @pytest.mark.asyncio
    async def test_agent_dynamic_decision_making(self, test_session, mock_openai_client):
        """Test that agents make contextual decisions based on data quality."""
        # Test different confidence scenarios
        test_scenarios = [
            {
                "confidence": 0.95,
                "decision": "approve",
                "reasoning": "Excellent mapping quality with clear semantic matches"
            },
            {
                "confidence": 0.65,
                "decision": "review",
                "reasoning": "Moderate confidence, manual review recommended for ambiguous mappings"
            },
            {
                "confidence": 0.35,
                "decision": "reject",
                "reasoning": "Low confidence due to significant schema mismatches"
            }
        ]
        
        for scenario in test_scenarios:
            # Update mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
                "decision": scenario["decision"],
                "confidence": scenario["confidence"],
                "reasoning": scenario["reasoning"],
                "suggestions": []
            })))]
            mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_openai_client):
                flow = UnifiedDiscoveryFlow()
                flow.flow_id = f"disc_test_{scenario['decision']}"
                flow.client_account_id = 1
                flow.engagement_id = 1
                
                result = await flow._execute_field_mapping_phase(sample_mapping_data())
                
                # Verify agent decision matches scenario
                assert result["agent_decision"]["decision"] == scenario["decision"]
                assert result["agent_decision"]["confidence"] == scenario["confidence"]
                assert result["agent_decision"]["reasoning"] == scenario["reasoning"]
    
    
    @pytest.mark.asyncio
    async def test_sse_realtime_updates(self, test_session):
        """Test SSE real-time updates during flow execution."""
        # Create flows
        master_flow = MasterFlow(
            flow_id="master_sse_001",
            flow_type="discovery",
            status="in_progress",
            client_account_id=1,
            engagement_id=1,
            created_by=1,
            config={}
        )
        test_session.add(master_flow)
        
        discovery_flow = DiscoveryFlow(
            flow_id="disc_sse_001",
            master_flow_id="master_sse_001",
            client_account_id=1,
            engagement_id=1,
            created_by=1,
            status="data_import",
            config={},
            state_data={
                "current_phase": "data_import",
                "phases": {
                    "data_import": {"status": "in_progress", "progress": 45}
                }
            }
        )
        test_session.add(discovery_flow)
        await test_session.commit()
        
        # Mock the status manager
        status_manager = FlowStatusManager(test_session, 1, 1)
        
        # Collect SSE events
        events = []
        async def collect_events():
            async for event in status_manager.stream_discovery_status("disc_sse_001"):
                events.append(json.loads(event.data))
                if len(events) >= 3:  # Collect a few events
                    break
        
        # Run collector in background
        collector_task = asyncio.create_task(collect_events())
        
        # Simulate flow updates
        await asyncio.sleep(0.1)
        
        # Update flow progress
        discovery_flow.state_data["phases"]["data_import"]["progress"] = 75
        await test_session.commit()
        await asyncio.sleep(0.1)
        
        # Complete phase
        discovery_flow.state_data["phases"]["data_import"]["status"] = "completed"
        discovery_flow.state_data["phases"]["data_import"]["progress"] = 100
        discovery_flow.status = "field_mapping"
        discovery_flow.state_data["current_phase"] = "field_mapping"
        await test_session.commit()
        await asyncio.sleep(0.1)
        
        # Wait for events
        try:
            await asyncio.wait_for(collector_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass
        
        # Verify SSE events were streamed
        assert len(events) > 0
        
        # Verify event structure
        for event in events:
            assert "flow_id" in event
            assert "status" in event
            assert "current_phase" in event
            assert "phases" in event
            assert event["flow_id"] == "disc_sse_001"
    
    
    @pytest.mark.asyncio
    async def test_agent_learning_from_feedback(self, test_session, mock_openai_client):
        """Test that agents incorporate user feedback for improved decisions."""
        # Initial mapping with agent decision
        initial_decision = {
            "decision": "review",
            "confidence": 0.72,
            "reasoning": "Some ambiguous mappings require clarification",
            "suggestions": ["Review cpu_cores to cpu_count mapping"]
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(initial_decision)))]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_openai_client):
            flow = UnifiedDiscoveryFlow()
            flow.flow_id = "disc_feedback_001"
            flow.client_account_id = 1
            flow.engagement_id = 1
            
            # First pass - agent suggests review
            result1 = await flow._execute_field_mapping_phase(sample_mapping_data())
            assert result1["agent_decision"]["decision"] == "review"
            
            # Simulate user feedback
            user_feedback = {
                "mappings_confirmed": True,
                "corrections": [
                    {"source": "cpu_cores", "target": "cpu_count", "user_confirmed": True}
                ],
                "notes": "CPU mapping is correct for our use case"
            }
            
            # Update agent response based on feedback
            improved_decision = {
                "decision": "approve",
                "confidence": 0.94,
                "reasoning": "Mappings confirmed by user feedback, cpu_cores to cpu_count verified",
                "learning_applied": True
            }
            
            mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(improved_decision)))]
            
            # Second pass with feedback
            mapping_with_feedback = sample_mapping_data()
            mapping_with_feedback["user_feedback"] = user_feedback
            
            result2 = await flow._execute_field_mapping_phase(mapping_with_feedback)
            
            # Verify agent learned from feedback
            assert result2["agent_decision"]["decision"] == "approve"
            assert result2["agent_decision"]["confidence"] > result1["agent_decision"]["confidence"]
            assert "learning_applied" in result2["agent_decision"]
            assert result2["agent_decision"]["learning_applied"] is True
    
    
    @pytest.mark.asyncio
    async def test_master_flow_integration(self, test_session, mock_openai_client):
        """Test integration with master flow orchestrator."""
        # Create master flow through orchestrator
        orchestrator = MasterFlowOrchestrator(test_session)
        
        master_flow = await orchestrator.create_master_flow(
            flow_type="discovery",
            client_account_id=1,
            engagement_id=1,
            created_by=1,
            config={"source_type": "servicenow"}
        )
        
        # Verify master flow created
        assert master_flow.flow_id.startswith("master_")
        assert master_flow.flow_type == "discovery"
        assert master_flow.status == "initialized"
        
        # Start discovery flow
        discovery_flow = await orchestrator.start_discovery_flow(
            master_flow_id=master_flow.flow_id,
            client_account_id=1,
            engagement_id=1,
            created_by=1
        )
        
        # Verify discovery flow linked to master
        assert discovery_flow.master_flow_id == master_flow.flow_id
        assert discovery_flow.flow_id.startswith("disc_")
        
        # Test flow execution with agent decisions
        with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_openai_client):
            flow = UnifiedDiscoveryFlow()
            flow.flow_id = discovery_flow.flow_id
            flow.client_account_id = 1
            flow.engagement_id = 1
            
            # Execute field mapping
            result = await flow._execute_field_mapping_phase(sample_mapping_data())
            
            # Verify agent made decision
            assert "agent_decision" in result
            assert result["agent_decision"]["decision"] in ["approve", "review", "reject"]
            
            # Update master flow status
            await orchestrator.update_master_flow_status(
                master_flow.flow_id,
                "completed",
                {"discovery_completed": True}
            )
            
            # Verify cascade update
            await test_session.refresh(master_flow)
            assert master_flow.status == "completed"
    
    
    @pytest.mark.asyncio
    async def test_error_handling_without_thresholds(self, test_session):
        """Test error handling uses agent decisions, not fallback thresholds."""
        # Mock OpenAI to fail
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI API error"))
        
        with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_client):
            flow = UnifiedDiscoveryFlow()
            flow.flow_id = "disc_error_001"
            flow.client_account_id = 1
            flow.engagement_id = 1
            
            # Execute should handle error gracefully
            result = await flow._execute_field_mapping_phase(sample_mapping_data())
            
            # Verify error handled without falling back to hardcoded thresholds
            assert result["status"] == "error"
            assert "error" in result
            assert "threshold" not in str(result).lower()
            assert "OpenAI API error" in result["error"]
            
            # Verify it suggests manual review, not threshold-based decision
            assert result.get("fallback_action") == "manual_review"


@pytest.mark.asyncio
async def test_complete_flow_execution(test_session, mock_openai_client, sample_mapping_data):
    """Test complete discovery flow execution with all phases."""
    # Setup
    orchestrator = MasterFlowOrchestrator(test_session)
    
    # Create master flow
    master_flow = await orchestrator.create_master_flow(
        flow_type="discovery",
        client_account_id=1,
        engagement_id=1,
        created_by=1,
        config={"source_type": "servicenow"}
    )
    
    # Start discovery flow
    discovery_flow = await orchestrator.start_discovery_flow(
        master_flow_id=master_flow.flow_id,
        client_account_id=1,
        engagement_id=1,
        created_by=1
    )
    
    # Mock successful agent decisions for all phases
    phase_decisions = {
        "data_import": {
            "decision": "approve",
            "confidence": 0.98,
            "reasoning": "Data quality excellent, all required fields present"
        },
        "field_mapping": {
            "decision": "approve",
            "confidence": 0.95,
            "reasoning": "High quality mappings with clear semantic alignment"
        },
        "data_cleansing": {
            "decision": "approve",
            "confidence": 0.92,
            "reasoning": "Data cleansing successful, minimal issues found"
        },
        "transformation": {
            "decision": "approve",
            "confidence": 0.96,
            "reasoning": "Transformations applied successfully"
        }
    }
    
    current_phase = "data_import"
    
    def update_mock_response(phase):
        nonlocal current_phase
        current_phase = phase
        decision = phase_decisions.get(phase, phase_decisions["data_import"])
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(decision)))]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch('app.services.crewai_flows.unified_discovery_flow.phases.field_mapping.OpenAI', return_value=mock_openai_client):
        flow = UnifiedDiscoveryFlow()
        flow.flow_id = discovery_flow.flow_id
        flow.client_account_id = 1
        flow.engagement_id = 1
        
        # Execute all phases
        results = {}
        
        # Data import phase
        update_mock_response("data_import")
        results["data_import"] = await flow._execute_data_import_phase({"file_path": "/tmp/test.csv"})
        
        # Field mapping phase
        update_mock_response("field_mapping")
        results["field_mapping"] = await flow._execute_field_mapping_phase(sample_mapping_data)
        
        # Data cleansing phase
        update_mock_response("data_cleansing")
        results["data_cleansing"] = await flow._execute_data_cleansing_phase(sample_mapping_data)
        
        # Transformation phase
        update_mock_response("transformation")
        results["transformation"] = await flow._execute_transformation_phase(sample_mapping_data)
        
        # Verify all phases used agent decisions
        for phase, result in results.items():
            assert "agent_decision" in result
            assert result["agent_decision"]["decision"] == "approve"
            assert result["agent_decision"]["confidence"] > 0.9
            assert "reasoning" in result["agent_decision"]
            assert "threshold" not in str(result).lower()
        
        # Complete the flow
        await orchestrator.update_master_flow_status(
            master_flow.flow_id,
            "completed",
            {"all_phases_completed": True, "results": results}
        )
        
        # Verify completion
        await test_session.refresh(master_flow)
        assert master_flow.status == "completed"
        assert master_flow.metadata["all_phases_completed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])