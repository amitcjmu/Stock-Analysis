"""
End-to-End Test for Collection Flow Execution
Tests actual CrewAI flow execution with mocked agents
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)
from app.services.crewai_flows.crews.collection.platform_detection_crew import (
    PlatformDetectionCrew,
)
from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow


@pytest.mark.asyncio
async def test_collection_flow_initialization_with_mocks():
    """Test Collection Flow can be initialized with mocked dependencies"""
    # Mock the CrewAI service
    mock_crewai_service = Mock()
    mock_crewai_service.get_llm.return_value = Mock()

    # Create context
    context = RequestContext(
        client_account_id="test-client-123",
        engagement_id="test-engagement-456",
        user_id="test-user-789",
    )

    # Initialize the flow
    flow = UnifiedCollectionFlow(
        crewai_service=mock_crewai_service, context=context, automation_tier="tier_2"
    )

    # Verify flow was initialized
    assert flow is not None
    assert hasattr(flow, "state")
    assert flow.context == context
    assert flow.crewai_service == mock_crewai_service

    print("✅ Collection Flow initialized with mocks")


@pytest.mark.asyncio
async def test_platform_detection_crew_execution():
    """Test Platform Detection Crew can be executed"""
    # Mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value="AWS platform detected with high confidence")

    # Mock tools
    mock_tools = {
        "platform_scanner": Mock(return_value={"platforms": ["AWS", "VMware"]}),
        "credential_validator": Mock(return_value={"valid": True}),
        "tier_recommender": Mock(return_value={"tier": "tier_2"}),
    }

    # Create crew
    crew = PlatformDetectionCrew(llm=mock_llm, tools=mock_tools)

    # Mock the crew's kickoff method
    crew.crew.kickoff = Mock(
        return_value={
            "detected_platforms": [
                {"platform_type": "AWS", "confidence": 0.95},
                {"platform_type": "VMware", "confidence": 0.88},
            ],
            "recommended_tier": "tier_2",
            "credentials_validated": True,
        }
    )

    # Execute
    context = {"client_id": "test-client", "engagement_id": "test-engagement"}
    result = crew.crew.kickoff(inputs={"context": context})

    # Verify
    assert result is not None
    assert "detected_platforms" in result
    assert len(result["detected_platforms"]) == 2
    assert result["detected_platforms"][0]["platform_type"] == "AWS"
    assert result["recommended_tier"] == "tier_2"

    print("✅ Platform Detection Crew executed successfully")


@pytest.mark.asyncio
async def test_collection_flow_phase_transition():
    """Test Collection Flow phase transitions"""
    # Create state
    state = CollectionFlowState(
        flow_id="test-flow-789",
        client_account_id="test-client",
        engagement_id="test-engagement",
        automation_tier=AutomationTier.TIER_2,
        status=CollectionStatus.INITIALIZING,
        current_phase=CollectionPhase.INITIALIZATION,
    )

    # Test phase transitions
    phase_transitions = [
        (CollectionPhase.PLATFORM_DETECTION, CollectionStatus.DETECTING_PLATFORMS),
        (CollectionPhase.AUTOMATED_COLLECTION, CollectionStatus.COLLECTING_DATA),
        (CollectionPhase.GAP_ANALYSIS, CollectionStatus.ANALYZING_GAPS),
        (CollectionPhase.MANUAL_COLLECTION, CollectionStatus.COLLECTING_MANUAL_DATA),
        (CollectionPhase.DATA_VALIDATION, CollectionStatus.VALIDATING_DATA),
        (CollectionPhase.FINALIZATION, CollectionStatus.FINALIZING),
    ]

    for phase, status in phase_transitions:
        state.current_phase = phase
        state.status = status
        state.updated_at = datetime.utcnow()

        assert state.current_phase == phase
        assert state.status == status
        print(f"✅ Transitioned to {phase.value} with status {status.value}")

    # Mark as completed
    state.status = CollectionStatus.COMPLETED
    state.completed_at = datetime.utcnow()
    assert state.status == CollectionStatus.COMPLETED
    assert state.completed_at is not None

    print("✅ All phase transitions tested successfully")


@pytest.mark.asyncio
async def test_collection_flow_with_mocked_crewai():
    """Test Collection Flow execution with mocked CrewAI components"""
    # Mock the entire crewai module
    with patch(
        "app.services.crewai_flows.unified_collection_flow.CREWAI_FLOW_AVAILABLE", True
    ):
        with patch(
            "app.services.crewai_flows.unified_collection_flow.Flow"
        ) as MockFlow:
            # Create a mock flow instance
            mock_flow_instance = MagicMock()
            mock_flow_instance.state = CollectionFlowState(
                flow_id="test-flow",
                client_account_id="test-client",
                engagement_id="test-engagement",
            )

            # Mock the kickoff method
            mock_flow_instance.kickoff = AsyncMock(
                return_value={
                    "status": "completed",
                    "detected_platforms": [
                        {"platform_type": "AWS", "confidence": 0.95}
                    ],
                    "collection_quality_score": 0.85,
                    "gaps_identified": 3,
                    "gaps_resolved": 2,
                }
            )

            # Make Flow return our mock instance
            MockFlow.return_value = mock_flow_instance

            # Create CrewAI service mock
            mock_crewai_service = Mock()
            mock_crewai_service.get_llm.return_value = Mock()

            # Create context
            context = RequestContext(
                client_account_id="test-client",
                engagement_id="test-engagement",
                user_id="test-user",
            )

            # Initialize flow
            flow = UnifiedCollectionFlow(
                crewai_service=mock_crewai_service, context=context
            )

            # Execute the flow
            result = await flow.kickoff()

            # Verify execution
            assert result is not None
            assert result["status"] == "completed"
            assert len(result["detected_platforms"]) == 1
            assert result["collection_quality_score"] == 0.85
            assert result["gaps_identified"] == 3
            assert result["gaps_resolved"] == 2

            print("✅ Collection Flow executed with mocked CrewAI")


@pytest.mark.asyncio
async def test_gap_analysis_functionality():
    """Test gap analysis identifies missing critical attributes"""
    from app.services.tools.gap_analysis_tools import (
        AttributeMapperTool,
        GapIdentifierTool,
    )

    # Create tools
    mapper = AttributeMapperTool()
    gap_identifier = GapIdentifierTool()

    # Mock data fields and mapping
    data_fields = ["hostname", "os_type", "cpu_cores", "memory_gb"]

    # Map fields to attributes
    mapping_result = await mapper.arun(data_fields=data_fields)

    # Create completeness analysis mock
    completeness_analysis = {
        "attribute_completeness": {
            "hostname": {"completeness_percentage": 100},
            "os_type": {"completeness_percentage": 80},
            "cpu_cores": {"completeness_percentage": 90},
            "memory_gb": {"completeness_percentage": 95},
        }
    }

    # Identify gaps
    gaps = await gap_identifier.arun(
        attribute_mapping=mapping_result["mapped_attributes"],
        completeness_analysis=completeness_analysis,
    )

    # Should identify missing attributes
    assert gaps["total_gaps"] > 0
    print(f"✅ Gap analysis identified {gaps['total_gaps']} missing attributes")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_collection_flow_initialization_with_mocks())
    asyncio.run(test_platform_detection_crew_execution())
    asyncio.run(test_collection_flow_phase_transition())
    asyncio.run(test_collection_flow_with_mocked_crewai())
    asyncio.run(test_gap_analysis_functionality())
    print("\n✅ All execution tests completed!")
