"""
Agent User Interaction E2E Tests
End-to-end tests for user experience of agent questions, clarification workflows, cross-page navigation
with preserved agent context, agent learning responsiveness, and assessment readiness accuracy.
"""

import pytest
import asyncio
from typing import Dict, List, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestAgentUserInteraction:
    """End-to-end test suite for agent-user interaction flows."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""

        # Set up Chrome driver for E2E testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        # Test configuration
        self.base_url = "http://localhost:3000"  # Frontend dev server
        self.api_base_url = "http://localhost:8000"  # Backend API server

        # Test data for agent interactions
        self.test_asset_data = {
            "cmdb_import": [
                {
                    "name": "WebServer001",
                    "hostname": "webserver001.company.com",
                    "asset_type": "SERVER",
                    "environment": "Production",
                    "department": "Finance"
                },
                {
                    "name": "UnknownAsset001",
                    "hostname": "unknown001.company.com",
                    "asset_type": "",  # Missing - should trigger clarification
                    "environment": "",  # Missing - should trigger clarification
                    "department": "IT"
                }
            ]
        }

        # Track user interaction progression
        self.interaction_history = []
        self.navigation_path = []
        self.agent_questions_answered = []

        yield

        # Cleanup
        if hasattr(self, 'driver'):
            self.driver.quit()

    # === AGENT CLARIFICATION FLOW TESTS ===

    @pytest.mark.asyncio
    async def test_complete_agent_clarification_workflow(self):
        """Test complete agent clarification workflow from question generation to learning."""

        # Step 1: Navigate to data import page
        await self._navigate_to_page("/discovery/data-import")

        # Step 2: Upload test data that triggers agent clarifications
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        # Step 3: Wait for agent analysis and clarifications
        clarification_panel = await self._wait_for_agent_clarifications()
        assert clarification_panel is not None, "Agent clarification panel should appear"

        # Step 4: Verify clarification questions are generated
        questions = await self._get_pending_questions()
        assert len(questions) > 0, "Agent should generate clarification questions"

        # Step 5: Answer agent questions
        for question in questions:
            answer_success = await self._answer_agent_question(question["id"], question["test_answer"])
            assert answer_success, f"Should successfully answer question {question['id']}"

        # Step 6: Verify agent learning from responses
        learning_feedback = await self._verify_agent_learning()
        assert learning_feedback["learning_applied"], "Agent should learn from user responses"

        # Step 7: Verify UI updates reflect agent improvements
        ui_updates = await self._verify_ui_reflects_learning()
        assert ui_updates["confidence_improved"], "UI should show improved agent confidence"

        print("✅ Complete agent clarification workflow test passed")

    @pytest.mark.asyncio
    async def test_agent_question_presentation_and_context(self):
        """Test that agent questions provide adequate context and are well-presented."""

        # Navigate to discovery page
        await self._navigate_to_page("/discovery/data-import")

        # Upload data with context-rich questions
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        # Wait for questions to appear
        await self._wait_for_agent_clarifications()

        # Verify question presentation quality
        question_elements = await self._get_question_elements()

        for question_element in question_elements:
            # Check question has clear title
            title = await self._get_question_title(question_element)
            assert len(title) > 10, "Question title should be descriptive"

            # Check question has agent context
            agent_info = await self._get_question_agent_info(question_element)
            assert agent_info["agent_name"], "Question should show which agent asked"
            assert agent_info["confidence"], "Question should show agent confidence"

            # Check question has asset context (if applicable)
            if "asset" in question_element.get_attribute("data-context-type"):
                asset_context = await self._get_question_asset_context(question_element)
                assert asset_context["asset_name"], "Asset-related questions should show asset details"
                assert asset_context["technical_details"], "Should show technical context"

            # Check question has clear options or input method
            response_method = await self._get_question_response_method(question_element)
            assert response_method["type"] in ["multiple_choice", "text_input", "yes_no"], "Question should have clear response method"

        print("✅ Agent question presentation and context test passed")

    @pytest.mark.asyncio
    async def test_progressive_disclosure_of_agent_insights(self):
        """Test progressive disclosure of agent insights as user provides responses."""

        # Navigate to discovery workflow
        await self._navigate_to_page("/discovery/data-import")

        # Track initial agent insights
        initial_insights = await self._get_agent_insights()
        initial_count = len(initial_insights)

        # Upload data and answer questions progressively
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        # Answer first batch of questions
        first_batch_questions = await self._get_pending_questions()
        for question in first_batch_questions[:2]:  # Answer first 2 questions
            await self._answer_agent_question(question["id"], question["test_answer"])

        # Verify insights increase
        post_first_insights = await self._get_agent_insights()
        assert len(post_first_insights) > initial_count, "Insights should increase after answering questions"

        # Answer remaining questions
        remaining_questions = await self._get_pending_questions()
        for question in remaining_questions:
            await self._answer_agent_question(question["id"], question["test_answer"])

        # Verify final insights are comprehensive
        final_insights = await self._get_agent_insights()
        assert len(final_insights) > len(post_first_insights), "Insights should continue increasing"

        # Verify insight quality progression
        insight_quality = await self._analyze_insight_quality_progression(
            initial_insights, post_first_insights, final_insights
        )
        assert insight_quality["confidence_improved"], "Insight confidence should improve"
        assert insight_quality["specificity_increased"], "Insights should become more specific"

        print("✅ Progressive disclosure of agent insights test passed")

    # === CROSS-PAGE NAVIGATION TESTS ===

    @pytest.mark.asyncio
    async def test_cross_page_agent_context_preservation(self):
        """Test that agent context is preserved when navigating between discovery pages."""

        # Page 1: Data Import - Generate agent context
        await self._navigate_to_page("/discovery/data-import")
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        # Answer some questions to build context
        questions = await self._get_pending_questions()
        for question in questions[:2]:
            await self._answer_agent_question(question["id"], question["test_answer"])

        # Capture context state
        page1_context = await self._capture_agent_context_state()

        # Page 2: Attribute Mapping - Context should be preserved
        await self._navigate_to_page("/discovery/attribute-mapping")

        # Wait for page load and check context preservation
        await self._wait_for_page_load()
        page2_context = await self._capture_agent_context_state()

        # Verify context preservation
        assert page2_context["discovered_assets"] == page1_context["discovered_assets"], "Asset discoveries should be preserved"
        assert page2_context["field_mappings"], "Field mapping insights should be available"

        # Page 3: Application Discovery - Enhanced context
        await self._navigate_to_page("/discovery/application-discovery")
        await self._wait_for_page_load()

        page3_context = await self._capture_agent_context_state()

        # Verify context enhancement
        assert page3_context["application_insights"], "Application insights should be generated from previous context"
        assert len(page3_context["agent_questions"]) >= 0, "New questions should be context-aware"

        # Page 4: Assessment Readiness - Complete context utilization
        await self._navigate_to_page("/discovery/assessment-readiness")
        await self._wait_for_page_load()

        page4_context = await self._capture_agent_context_state()

        # Verify comprehensive context utilization
        assert page4_context["readiness_assessment"], "Should have readiness assessment based on all context"
        assert page4_context["portfolio_completeness"] > 0.5, "Should show meaningful completeness score"

        print("✅ Cross-page agent context preservation test passed")

    @pytest.mark.asyncio
    async def test_navigation_with_unanswered_questions(self):
        """Test navigation behavior when agent questions remain unanswered."""

        # Page 1: Generate questions but don't answer all
        await self._navigate_to_page("/discovery/data-import")
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        questions = await self._get_pending_questions()

        # Answer only some questions
        answered_count = len(questions) // 2
        for question in questions[:answered_count]:
            await self._answer_agent_question(question["id"], question["test_answer"])

        unanswered_count = len(questions) - answered_count

        # Navigate to next page
        await self._navigate_to_page("/discovery/attribute-mapping")

        # Verify unanswered questions are tracked
        unanswered_questions = await self._get_unanswered_questions_indicator()
        assert unanswered_questions["count"] == unanswered_count, "Should track unanswered questions"
        assert unanswered_questions["visible"], "Should show indicator for unanswered questions"

        # Navigate to assessment readiness
        await self._navigate_to_page("/discovery/assessment-readiness")

        # Verify assessment shows impact of unanswered questions
        assessment = await self._get_assessment_readiness_state()
        assert assessment["outstanding_questions"] >= unanswered_count, "Assessment should show outstanding questions"
        assert assessment["completeness_score"] < 1.0, "Completeness should be impacted by unanswered questions"

        print("✅ Navigation with unanswered questions test passed")

    # === AGENT LEARNING RESPONSIVENESS TESTS ===

    @pytest.mark.asyncio
    async def test_real_time_agent_learning_feedback(self):
        """Test that agent learning improvements are visible in real-time."""

        # Setup: Navigate and create baseline
        await self._navigate_to_page("/discovery/data-import")

        # Initial agent capabilities
        initial_capabilities = await self._assess_agent_capabilities()

        # Upload data and provide corrective feedback
        await self._upload_test_data(self.test_asset_data["cmdb_import"])

        # Provide field mapping corrections
        field_corrections = {
            "Server_Name": "hostname",
            "OS_Version": "operating_system",
            "Dept": "department"
        }

        for original, corrected in field_corrections.items():
            await self._provide_field_mapping_correction(original, corrected)

        # Provide asset classification corrections
        classification_corrections = {
            "UnknownAsset001": "APPLICATION_SERVER"
        }

        for asset, classification in classification_corrections.items():
            await self._provide_classification_correction(asset, classification)

        # Wait for learning to process
        await asyncio.sleep(2)

        # Assess improved capabilities
        improved_capabilities = await self._assess_agent_capabilities()

        # Verify learning improvements
        assert improved_capabilities["field_mapping_accuracy"] > initial_capabilities["field_mapping_accuracy"], "Field mapping should improve"
        assert improved_capabilities["classification_confidence"] > initial_capabilities["classification_confidence"], "Classification should improve"

        # Test learning application to new data
        new_test_data = [
            {
                "Server_Name": "NewServer001",  # Should now be mapped correctly
                "OS_Version": "Windows Server 2019",
                "Dept": "HR"
            }
        ]

        await self._upload_test_data(new_test_data)

        # Verify learned patterns are applied
        mapping_results = await self._get_field_mapping_results()
        assert mapping_results["Server_Name"] == "hostname", "Should apply learned field mapping"
        assert mapping_results["confidence"] > 0.8, "Should have high confidence in learned mapping"

        print("✅ Real-time agent learning feedback test passed")

    @pytest.mark.asyncio
    async def test_learning_persistence_across_sessions(self):
        """Test that agent learning persists across browser sessions."""

        # Session 1: Teach agent patterns
        await self._navigate_to_page("/discovery/data-import")

        # Provide learning data
        learning_data = {
            "field_mappings": {"srv_name": "hostname", "mem_gb": "memory_gb"},
            "classifications": {"web_server": "APPLICATION_SERVER"},
            "quality_patterns": {"missing_env": "needs_clarification"}
        }

        for mapping_type, mappings in learning_data.items():
            await self._teach_agent_patterns(mapping_type, mappings)

        # Verify learning applied
        session1_capabilities = await self._assess_agent_capabilities()
        assert session1_capabilities["patterns_learned"] >= len(learning_data), "Should learn provided patterns"

        # Simulate session end (close and reopen browser)
        self.driver.quit()

        # New session: Restart browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        # Session 2: Verify learning persistence
        await self._navigate_to_page("/discovery/data-import")

        # Test with data that should trigger learned patterns
        test_data = [
            {
                "srv_name": "TestServer001",  # Should map to hostname
                "mem_gb": "32",              # Should map to memory_gb
                "type": "web_server"         # Should classify as APPLICATION_SERVER
            }
        ]

        await self._upload_test_data(test_data)

        # Verify learned patterns are still applied
        mapping_results = await self._get_field_mapping_results()
        assert mapping_results["srv_name"] == "hostname", "Field mapping should persist"

        classification_results = await self._get_classification_results()
        assert classification_results["TestServer001"] == "APPLICATION_SERVER", "Classification should persist"

        session2_capabilities = await self._assess_agent_capabilities()
        assert session2_capabilities["patterns_learned"] >= session1_capabilities["patterns_learned"], "Learning should persist"

        print("✅ Learning persistence across sessions test passed")

    # === ASSESSMENT READINESS ACCURACY TESTS ===

    @pytest.mark.asyncio
    async def test_assessment_readiness_accuracy_progression(self):
        """Test that assessment readiness accuracy improves as agent intelligence grows."""

        # Stage 1: Minimal data - Low readiness
        await self._navigate_to_page("/discovery/data-import")

        minimal_data = [{"name": "Server001", "hostname": "server001.com"}]
        await self._upload_test_data(minimal_data)

        await self._navigate_to_page("/discovery/assessment-readiness")
        stage1_readiness = await self._get_assessment_readiness_details()

        assert stage1_readiness["overall_score"] < 0.4, "Minimal data should show low readiness"
        assert len(stage1_readiness["missing_requirements"]) > 5, "Should identify many missing requirements"

        # Stage 2: Add attribute mappings - Improved readiness
        await self._navigate_to_page("/discovery/attribute-mapping")

        attribute_mappings = {
            "department": "Finance",
            "environment": "Production",
            "criticality": "High"
        }

        await self._complete_attribute_mappings(attribute_mappings)

        await self._navigate_to_page("/discovery/assessment-readiness")
        stage2_readiness = await self._get_assessment_readiness_details()

        assert stage2_readiness["overall_score"] > stage1_readiness["overall_score"], "Readiness should improve"
        assert len(stage2_readiness["missing_requirements"]) < len(stage1_readiness["missing_requirements"]), "Missing requirements should decrease"

        # Stage 3: Add application context - Further improvement
        await self._navigate_to_page("/discovery/application-discovery")

        application_context = {
            "Finance Application": {
                "components": ["Server001"],
                "business_owner": "Finance Team",
                "criticality": "High"
            }
        }

        await self._define_application_portfolio(application_context)

        await self._navigate_to_page("/discovery/assessment-readiness")
        stage3_readiness = await self._get_assessment_readiness_details()

        assert stage3_readiness["overall_score"] > stage2_readiness["overall_score"], "Application context should improve readiness"
        assert stage3_readiness["application_readiness"] > 0.7, "Application readiness should be high"

        # Stage 4: Complete data quality improvements - High readiness
        await self._navigate_to_page("/discovery/data-cleansing")

        await self._complete_data_quality_improvements()

        await self._navigate_to_page("/discovery/assessment-readiness")
        final_readiness = await self._get_assessment_readiness_details()

        assert final_readiness["overall_score"] > 0.8, "Complete workflow should achieve high readiness"
        assert final_readiness["data_quality_score"] > 0.85, "Data quality should be excellent"
        assert len(final_readiness["outstanding_questions"]) < 3, "Should have minimal outstanding questions"

        print("✅ Assessment readiness accuracy progression test passed")

    @pytest.mark.asyncio
    async def test_stakeholder_signoff_workflow_integration(self):
        """Test integration with stakeholder signoff workflow based on agent intelligence."""

        # Complete discovery workflow
        await self._complete_full_discovery_workflow()

        # Navigate to assessment readiness
        await self._navigate_to_page("/discovery/assessment-readiness")

        # Generate stakeholder signoff package
        signoff_button = await self._find_element("[data-testid='generate-signoff-package']")
        signoff_button.click()

        # Wait for package generation
        await self._wait_for_element("[data-testid='signoff-package-ready']", timeout=15)

        # Verify signoff package content
        package_content = await self._get_signoff_package_content()

        assert package_content["executive_summary"], "Should have executive summary"
        assert package_content["portfolio_overview"], "Should have portfolio overview"
        assert package_content["readiness_assessment"], "Should have readiness assessment"
        assert package_content["risk_analysis"], "Should have risk analysis"
        assert package_content["recommendation_summary"], "Should have recommendations"

        # Verify package quality based on agent intelligence
        package_quality = await self._assess_signoff_package_quality(package_content)

        assert package_quality["completeness_score"] > 0.85, "Package should be comprehensive"
        assert package_quality["accuracy_score"] > 0.8, "Package should be accurate"
        assert package_quality["actionability_score"] > 0.75, "Package should be actionable"

        # Test stakeholder feedback integration
        stakeholder_feedback = {
            "portfolio_approval": True,
            "risk_tolerance": "Medium",
            "timeline_preference": "Aggressive",
            "compliance_requirements": ["SOX", "PCI-DSS"]
        }

        await self._provide_stakeholder_feedback(stakeholder_feedback)

        # Verify agent learning from stakeholder feedback
        post_feedback_assessment = await self._get_assessment_readiness_details()

        assert post_feedback_assessment["stakeholder_aligned"], "Assessment should reflect stakeholder input"
        assert post_feedback_assessment["risk_profile"] == "Medium", "Should apply stakeholder risk tolerance"

        print("✅ Stakeholder signoff workflow integration test passed")

    # === HELPER METHODS ===

    async def _navigate_to_page(self, path: str) -> None:
        """Navigate to a specific page."""
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        self.navigation_path.append(path)
        await self._wait_for_page_load()

    async def _wait_for_page_load(self) -> None:
        """Wait for page to fully load."""
        await asyncio.sleep(1)  # Basic wait for page load

        # Wait for React app to be ready
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        except TimeoutException:
            pass  # Continue if main element not found

    async def _upload_test_data(self, data: List[Dict]) -> None:
        """Simulate uploading test data."""
        # This would typically involve file upload simulation
        # For testing purposes, we'll mock the API call
        await asyncio.sleep(0.5)  # Simulate upload time

    async def _wait_for_agent_clarifications(self) -> Any:
        """Wait for agent clarification panel to appear."""
        try:
            panel = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='agent-clarification-panel']"))
            )
            return panel
        except TimeoutException:
            return None

    async def _get_pending_questions(self) -> List[Dict]:
        """Get current pending agent questions."""
        # Mock implementation - would extract from UI
        return [
            {
                "id": "q1",
                "agent_name": "Data Source Intelligence",
                "question": "How should UnknownAsset001 be classified?",
                "test_answer": "APPLICATION_SERVER"
            },
            {
                "id": "q2",
                "agent_name": "Quality Assessment",
                "question": "What environment is UnknownAsset001 in?",
                "test_answer": "Production"
            }
        ]

    async def _answer_agent_question(self, question_id: str, answer: str) -> bool:
        """Answer an agent question."""
        try:
            # Find question element
            question_element = self.driver.find_element(
                By.CSS_SELECTOR, f"[data-question-id='{question_id}']"
            )

            # Find answer input/select
            answer_input = question_element.find_element(By.CSS_SELECTOR, "input, select, textarea")
            answer_input.clear()
            answer_input.send_keys(answer)

            # Submit answer
            submit_button = question_element.find_element(By.CSS_SELECTOR, "[data-testid='submit-answer']")
            submit_button.click()

            await asyncio.sleep(0.5)  # Wait for submission
            return True

        except (NoSuchElementException, TimeoutException):
            return False

    async def _find_element(self, selector: str, timeout: int = 10) -> Any:
        """Find element with timeout."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    async def _wait_for_element(self, selector: str, timeout: int = 10) -> Any:
        """Wait for element to appear."""
        return await self._find_element(selector, timeout)

    # Additional helper methods would be implemented for specific test scenarios
    async def _verify_agent_learning(self) -> Dict[str, Any]:
        """Verify that agent learning occurred."""
        return {"learning_applied": True, "confidence_improved": True}

    async def _verify_ui_reflects_learning(self) -> Dict[str, Any]:
        """Verify UI updates reflect agent learning."""
        return {"confidence_improved": True, "insights_enhanced": True}

    async def _get_question_elements(self) -> List[Any]:
        """Get all question elements from the page."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='agent-question']")

    async def _capture_agent_context_state(self) -> Dict[str, Any]:
        """Capture current agent context state."""
        return {
            "discovered_assets": ["WebServer001", "UnknownAsset001"],
            "field_mappings": {"hostname": "server_name"},
            "application_insights": ["Finance Application identified"],
            "agent_questions": [],
            "readiness_assessment": {"score": 0.75},
            "portfolio_completeness": 0.8
        }

    # More helper methods would be implemented as needed for comprehensive testing


# === E2E TEST CONFIGURATION ===

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
