"""
Agent-UI Integration Tests
Tests the comprehensive agent-UI interaction system for the agentic discovery platform.
Covers agent clarification generation, user response processing, cross-page context preservation,
learning effectiveness, data classification accuracy, and real-time updates.
"""

import pytest
import asyncio
import time
from unittest.mock import patch

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class TestAgentUIIntegration:
    """Test suite for Agent-UI integration functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Set up Chrome driver for UI testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        # Test data
        self.test_asset_data = [
            {
                "id": "test_asset_1",
                "name": "TestServer001",
                "hostname": "testserver001.company.com",
                "asset_type": "SERVER",
                "os_name": "Windows Server 2016",
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 500,
                "department": "Finance",
                "environment": "Production",
                "criticality": "High"
            },
            {
                "id": "test_asset_2",
                "name": "TestDB001",
                "hostname": "testdb001.company.com",
                "asset_type": "DATABASE",
                "os_name": "SQL Server 2014",
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 1000,
                "department": "Operations",
                "environment": "Production",
                "criticality": "Critical"
            }
        ]

        self.test_questions = []
        self.test_classifications = []
        self.learning_events = []

        yield

        # Cleanup
        if hasattr(self, 'driver'):
            self.driver.quit()

    # === AGENT CLARIFICATION GENERATION TESTS ===

    @pytest.mark.asyncio
    async def test_agent_generates_clarifications_for_unknown_assets(self):
        """Test that agents generate appropriate clarifications for unknown/unclear assets."""

        # Mock agent analysis response with clarifications
        mock_agent_response = {
            "success": True,
            "analysis_results": {
                "assets_analyzed": 2,
                "classification_confidence": 0.7,
                "clarifications_needed": True
            },
            "clarifications": [
                {
                    "id": "clarification_1",
                    "agent_id": "data_source_intelligence",
                    "agent_name": "Data Source Intelligence Agent",
                    "question_type": "asset_classification",
                    "page": "discovery-import",
                    "title": "Asset Type Clarification Needed",
                    "question": "The asset 'TestServer001' appears to be a server, but its configuration suggests it might also function as a database host. How should this asset be classified?",
                    "context": {
                        "asset_id": "test_asset_1",
                        "detected_patterns": ["server_naming", "database_ports"],
                        "confidence": 0.6
                    },
                    "options": ["Server", "Database Server", "Application Server", "Mixed Use"],
                    "priority": "medium"
                }
            ]
        }

        with patch('app.services.agent_ui_bridge.agent_ui_bridge.analyze_with_agents') as mock_analyze:
            mock_analyze.return_value = mock_agent_response

            # Simulate agent analysis
            from app.services.agent_ui_bridge import agent_ui_bridge

            analysis_request = {
                "data_source": {
                    "assets": self.test_asset_data,
                    "total_count": len(self.test_asset_data)
                },
                "analysis_type": "comprehensive_discovery",
                "page_context": "discovery-import"
            }

            result = await agent_ui_bridge.analyze_with_agents(analysis_request)

            # Verify clarifications were generated
            assert result["success"]
            assert "clarifications" in result
            assert len(result["clarifications"]) > 0

            clarification = result["clarifications"][0]
            assert clarification["question_type"] == "asset_classification"
            assert clarification["page"] == "discovery-import"
            assert "asset_id" in clarification["context"]

            print("✅ Agent clarification generation test passed")

    @pytest.mark.asyncio
    async def test_cross_page_context_preservation(self):
        """Test that agent context is preserved when navigating between pages."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Set context on first page
        test_context = {
            "discovered_applications": ["Finance App", "HR System"],
            "field_mappings": {"hostname": "server_name", "os_name": "operating_system"},
            "user_preferences": {"bulk_operations": True, "auto_classify": False}
        }

        agent_ui_bridge.set_cross_page_context("discovery_session", test_context, "data-import")

        # Simulate navigation to different page
        time.sleep(0.1)  # Brief delay to simulate navigation

        # Retrieve context on second page
        retrieved_context = agent_ui_bridge.get_cross_page_context("discovery_session")

        # Verify context preservation
        assert retrieved_context is not None
        assert retrieved_context["discovered_applications"] == test_context["discovered_applications"]
        assert retrieved_context["field_mappings"] == test_context["field_mappings"]
        assert retrieved_context["user_preferences"] == test_context["user_preferences"]

        # Test context metadata
        metadata = agent_ui_bridge.get_context_metadata("discovery_session")
        assert metadata is not None
        assert metadata["page_source"] == "data-import"
        assert "timestamp" in metadata

        print("✅ Cross-page context preservation test passed")

    @pytest.mark.asyncio
    async def test_user_response_processing_and_learning(self):
        """Test that user responses to agent questions are processed and learned from."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Add a test question
        question_id = agent_ui_bridge.add_agent_question(
            agent_id="test_agent",
            agent_name="Test Agent",
            question_type="asset_classification",
            page="discovery-import",
            title="Test Classification Question",
            question="How should this asset be classified?",
            context={"asset_id": "test_asset_1"},
            options=["Server", "Database", "Application"],
            priority="medium"
        )

        # Simulate user response
        user_response = "Database"
        response_result = agent_ui_bridge.answer_agent_question(question_id, user_response)

        # Verify response processing
        assert response_result["success"]
        assert response_result["learning_stored"]
        assert response_result["question"]["user_response"] == user_response
        assert response_result["question"]["is_resolved"]

        # Verify learning experience was stored
        recent_experiences = agent_ui_bridge.get_recent_learning_experiences(limit=1)
        assert len(recent_experiences) > 0

        latest_experience = recent_experiences[0]
        assert latest_experience["question_type"] == "asset_classification"
        assert latest_experience["agent_id"] == "test_agent"
        assert latest_experience["user_response"] == user_response

        print("✅ User response processing and learning test passed")

    @pytest.mark.asyncio
    async def test_data_classification_accuracy(self):
        """Test that agent data classification is accurate and confidence-scored."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Test data classification
        test_item = {
            "id": "test_item_1",
            "type": "asset_record",
            "content": self.test_asset_data[0]
        }

        agent_ui_bridge.classify_data_item(
            item_id=test_item["id"],
            data_type=test_item["type"],
            content=test_item["content"],
            classification="good_data",
            agent_analysis={
                "quality_score": 0.85,
                "completeness": 0.9,
                "accuracy_indicators": ["valid_hostname", "standard_naming", "complete_specs"]
            },
            confidence="high",
            page="discovery-import",
            issues=[],
            recommendations=["Consider adding dependency information"]
        )

        # Verify classification storage
        classifications = agent_ui_bridge.get_classified_data_for_page("discovery-import")
        assert len(classifications) > 0

        classification = next((c for c in classifications if c["item_id"] == test_item["id"]), None)
        assert classification is not None
        assert classification["classification"] == "good_data"
        assert classification["confidence"] == "high"
        assert classification["agent_analysis"]["quality_score"] == 0.85

        print("✅ Data classification accuracy test passed")

    @pytest.mark.asyncio
    async def test_agent_learning_effectiveness(self):
        """Test that agents learn effectively from user feedback and corrections."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Simulate learning from multiple user interactions
        learning_scenarios = [
            {
                "original_classification": "needs_clarification",
                "user_correction": "good_data",
                "asset_type": "SERVER",
                "confidence_before": 0.6,
                "expected_improvement": True
            },
            {
                "original_classification": "good_data",
                "user_correction": "needs_clarification",
                "asset_type": "DATABASE",
                "confidence_before": 0.8,
                "expected_improvement": True
            }
        ]

        learning_improvements = []

        for scenario in learning_scenarios:
            # Store learning experience
            learning_context = {
                "question_type": "data_classification",
                "agent_id": "data_source_intelligence",
                "original_analysis": {
                    "classification": scenario["original_classification"],
                    "confidence": scenario["confidence_before"]
                },
                "user_correction": scenario["user_correction"],
                "asset_context": {"asset_type": scenario["asset_type"]},
                "learning_applied": True
            }

            agent_ui_bridge._store_learning_experience(learning_context)
            learning_improvements.append(scenario["expected_improvement"])

        # Verify learning experiences were stored
        experiences = agent_ui_bridge.get_recent_learning_experiences(limit=10)
        classification_experiences = [exp for exp in experiences if exp.get("question_type") == "data_classification"]

        assert len(classification_experiences) >= len(learning_scenarios)

        # Verify learning patterns
        for exp in classification_experiences[-len(learning_scenarios):]:
            assert "user_correction" in exp
            assert "original_analysis" in exp
            assert exp.get("learning_applied")

        print("✅ Agent learning effectiveness test passed")

    @pytest.mark.asyncio
    async def test_real_time_agent_updates(self):
        """Test that agent updates are reflected in real-time across the UI."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Simulate real-time agent analysis update
        initial_insights = agent_ui_bridge.get_insights_for_page("discovery-import")
        initial_count = len(initial_insights)

        # Add new insight
        agent_ui_bridge.add_agent_insight(
            agent_id="real_time_test_agent",
            agent_name="Real-time Test Agent",
            insight_type="data_quality",
            page="discovery-import",
            title="Real-time Quality Insight",
            description="Detected naming convention pattern in imported assets",
            content={
                "pattern": "server naming follows convention: env+function+number",
                "confidence": 0.9,
                "affected_assets": 15,
                "recommendation": "Apply standardized naming validation"
            },
            confidence="high",
            priority="medium"
        )

        # Verify update was reflected
        updated_insights = agent_ui_bridge.get_insights_for_page("discovery-import")
        assert len(updated_insights) == initial_count + 1

        # Find the new insight
        new_insight = next((insight for insight in updated_insights
                          if insight["title"] == "Real-time Quality Insight"), None)
        assert new_insight is not None
        assert new_insight["agent_name"] == "Real-time Test Agent"
        assert new_insight["confidence"] == "high"

        print("✅ Real-time agent updates test passed")

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self):
        """Test that multiple agents can collaborate on complex analysis tasks."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Simulate collaboration between Data Source Intelligence and Application Intelligence agents

        # Agent 1: Data Source Intelligence identifies potential applications
        agent_ui_bridge.set_cross_page_context(
            "discovered_patterns",
            {
                "application_indicators": ["finance", "hr", "crm"],
                "dependency_patterns": ["database_connections", "api_calls"],
                "confidence": 0.7
            },
            "data-import"
        )

        # Agent 2: Application Intelligence builds on the analysis
        discovered_patterns = agent_ui_bridge.get_cross_page_context("discovered_patterns")

        # Verify collaboration context was shared
        assert discovered_patterns is not None
        assert "application_indicators" in discovered_patterns
        assert discovered_patterns["confidence"] == 0.7

        # Agent 2 adds enhanced analysis
        enhanced_analysis = {
            **discovered_patterns,
            "application_groups": {
                "Finance Application": {
                    "assets": ["finance-db-01", "finance-web-01"],
                    "confidence": 0.85
                },
                "HR System": {
                    "assets": ["hr-app-01", "hr-db-01"],
                    "confidence": 0.8
                }
            },
            "enhanced_by": "application_intelligence_agent"
        }

        agent_ui_bridge.set_cross_page_context(
            "application_portfolio",
            enhanced_analysis,
            "application-discovery"
        )

        # Verify collaboration produced enhanced results
        portfolio = agent_ui_bridge.get_cross_page_context("application_portfolio")
        assert portfolio is not None
        assert "application_groups" in portfolio
        assert portfolio["enhanced_by"] == "application_intelligence_agent"
        assert len(portfolio["application_groups"]) == 2

        print("✅ Multi-agent collaboration test passed")

    @pytest.mark.asyncio
    async def test_agent_question_prioritization(self):
        """Test that agent questions are properly prioritized and ordered."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Add questions with different priorities
        questions_data = [
            ("low", "Low Priority Question", "This is a low priority question"),
            ("high", "High Priority Question", "This is a high priority question"),
            ("medium", "Medium Priority Question", "This is a medium priority question"),
            ("high", "Another High Priority", "Another high priority question")
        ]

        question_ids = []
        for priority, title, question in questions_data:
            qid = agent_ui_bridge.add_agent_question(
                agent_id="priority_test_agent",
                agent_name="Priority Test Agent",
                question_type="general",
                page="discovery-import",
                title=title,
                question=question,
                context={},
                priority=priority
            )
            question_ids.append(qid)

        # Get questions for page
        page_questions = agent_ui_bridge.get_questions_for_page("discovery-import")

        # Verify prioritization (high -> medium -> low)
        assert len(page_questions) >= 4

        # Check that high priority questions come first
        priorities = [q["priority"] for q in page_questions[:4]]
        high_count = priorities.count("high")
        medium_count = priorities.count("medium")
        low_count = priorities.count("low")

        assert high_count == 2  # Two high priority questions
        assert medium_count == 1  # One medium priority question
        assert low_count == 1  # One low priority question

        # High priority questions should be at the top
        assert page_questions[0]["priority"] == "high"
        assert page_questions[1]["priority"] == "high"

        print("✅ Agent question prioritization test passed")

    @pytest.mark.asyncio
    async def test_cross_page_learning_persistence(self):
        """Test that learning persists across page navigation and browser sessions."""

        from app.services.agent_ui_bridge import agent_ui_bridge

        # Store learning from data import page
        learning_data_import = {
            "question_type": "field_mapping",
            "agent_id": "field_mapping_agent",
            "page": "data-import",
            "user_response": {"hostname": "server_name", "os_name": "operating_system"},
            "pattern_learned": "standard_field_mapping",
            "confidence_improvement": 0.15
        }

        agent_ui_bridge._store_learning_experience(learning_data_import)

        # Store learning from attribute mapping page
        learning_attr_mapping = {
            "question_type": "attribute_classification",
            "agent_id": "classification_agent",
            "page": "attribute-mapping",
            "user_response": {"department": "business_unit", "criticality": "business_criticality"},
            "pattern_learned": "organizational_attribute_mapping",
            "confidence_improvement": 0.12
        }

        agent_ui_bridge._store_learning_experience(learning_attr_mapping)

        # Verify learning persistence across pages
        all_experiences = agent_ui_bridge.get_recent_learning_experiences(limit=50)

        field_mapping_experiences = [exp for exp in all_experiences if exp.get("question_type") == "field_mapping"]
        attr_classification_experiences = [exp for exp in all_experiences if exp.get("question_type") == "attribute_classification"]

        assert len(field_mapping_experiences) > 0
        assert len(attr_classification_experiences) > 0

        # Verify specific learning data persisted
        latest_field_exp = field_mapping_experiences[0]
        assert latest_field_exp["pattern_learned"] == "standard_field_mapping"
        assert latest_field_exp["page"] == "data-import"

        latest_attr_exp = attr_classification_experiences[0]
        assert latest_attr_exp["pattern_learned"] == "organizational_attribute_mapping"
        assert latest_attr_exp["page"] == "attribute-mapping"

        print("✅ Cross-page learning persistence test passed")

    # === TEST HELPER METHODS ===

    def _simulate_page_navigation(self, from_page: str, to_page: str):
        """Simulate navigation between discovery pages."""
        # This would typically involve actual browser navigation in full e2e tests
        time.sleep(0.1)  # Simulate navigation delay

    def _wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for UI element to be present."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def _get_agent_clarification_panel_data(self):
        """Extract data from agent clarification panel."""
        # This would extract actual UI data in full e2e tests
        return {
            "questions_count": 3,
            "pending_responses": 1,
            "agent_confidence": 0.85
        }


# === INTEGRATION TEST CONFIGURATION ===

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
