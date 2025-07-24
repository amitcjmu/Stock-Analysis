"""
Test Collection Flow CrewAI Agents
Verifies that all agents are properly implemented and can be imported
"""

import pytest


def test_platform_detection_agents():
    """Test that platform detection agents can be imported"""
    try:
        from app.services.agents.credential_validation_agent_crewai import (
            CredentialValidationAgent,
        )
        from app.services.agents.platform_detection_agent_crewai import (
            PlatformDetectionAgent,
        )
        from app.services.agents.tier_recommendation_agent_crewai import (
            TierRecommendationAgent,
        )

        # Verify agent metadata
        assert (
            PlatformDetectionAgent.agent_metadata().name == "platform_detection_agent"
        )
        assert (
            CredentialValidationAgent.agent_metadata().name
            == "credential_validation_agent"
        )
        assert (
            TierRecommendationAgent.agent_metadata().name == "tier_recommendation_agent"
        )

        print("✅ Platform detection agents loaded successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import platform detection agents: {e}")


def test_collection_orchestration_agent():
    """Test that collection orchestration agent can be imported"""
    try:
        from app.services.agents.collection_orchestrator_agent_crewai import (
            CollectionOrchestratorAgent,
        )

        assert (
            CollectionOrchestratorAgent.agent_metadata().name
            == "collection_orchestrator_agent"
        )
        print("✅ Collection orchestration agent loaded successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import collection orchestration agent: {e}")


def test_gap_analysis_agents():
    """Test that gap analysis agents can be imported"""
    try:
        from app.services.agents.critical_attribute_assessor_crewai import (
            CriticalAttributeAssessorAgent,
        )
        from app.services.agents.gap_prioritization_agent_crewai import (
            GapPrioritizationAgent,
        )

        assert (
            CriticalAttributeAssessorAgent.agent_metadata().name
            == "critical_attribute_assessor"
        )
        assert (
            GapPrioritizationAgent.agent_metadata().name == "gap_prioritization_agent"
        )

        print("✅ Gap analysis agents loaded successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import gap analysis agents: {e}")


def test_manual_collection_agents():
    """Test that manual collection agents can be imported"""
    try:
        from app.services.agents.progress_tracking_agent_crewai import (
            ProgressTrackingAgent,
        )
        from app.services.agents.questionnaire_dynamics_agent_crewai import (
            QuestionnaireDynamicsAgent,
        )
        from app.services.agents.validation_workflow_agent_crewai import (
            ValidationWorkflowAgent,
        )

        assert (
            QuestionnaireDynamicsAgent.agent_metadata().name
            == "questionnaire_dynamics_agent"
        )
        assert (
            ValidationWorkflowAgent.agent_metadata().name == "validation_workflow_agent"
        )
        assert ProgressTrackingAgent.agent_metadata().name == "progress_tracking_agent"

        print("✅ Manual collection agents loaded successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import manual collection agents: {e}")


def test_all_agents_have_required_attributes():
    """Test that all agents have required attributes and methods"""
    agents = [
        "app.services.agents.platform_detection_agent_crewai.PlatformDetectionAgent",
        "app.services.agents.credential_validation_agent_crewai.CredentialValidationAgent",
        "app.services.agents.tier_recommendation_agent_crewai.TierRecommendationAgent",
        "app.services.agents.collection_orchestrator_agent_crewai.CollectionOrchestratorAgent",
        "app.services.agents.critical_attribute_assessor_crewai.CriticalAttributeAssessorAgent",
        "app.services.agents.gap_prioritization_agent_crewai.GapPrioritizationAgent",
        "app.services.agents.questionnaire_dynamics_agent_crewai.QuestionnaireDynamicsAgent",
        "app.services.agents.validation_workflow_agent_crewai.ValidationWorkflowAgent",
        "app.services.agents.progress_tracking_agent_crewai.ProgressTrackingAgent",
    ]

    for agent_path in agents:
        module_path, class_name = agent_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        agent_class = getattr(module, class_name)

        # Check required methods
        assert hasattr(
            agent_class, "agent_metadata"
        ), f"{class_name} missing agent_metadata method"
        assert callable(
            getattr(agent_class, "agent_metadata")
        ), f"{class_name} agent_metadata is not callable"

        # Check metadata structure
        metadata = agent_class.agent_metadata()
        assert hasattr(metadata, "name"), f"{class_name} metadata missing name"
        assert hasattr(
            metadata, "description"
        ), f"{class_name} metadata missing description"
        assert hasattr(
            metadata, "agent_class"
        ), f"{class_name} metadata missing agent_class"
        assert hasattr(
            metadata, "required_tools"
        ), f"{class_name} metadata missing required_tools"
        assert hasattr(
            metadata, "capabilities"
        ), f"{class_name} metadata missing capabilities"

    print("✅ All agents have required attributes")


if __name__ == "__main__":
    test_platform_detection_agents()
    test_collection_orchestration_agent()
    test_gap_analysis_agents()
    test_manual_collection_agents()
    test_all_agents_have_required_attributes()
    print("\n✅ All agent tests passed!")
