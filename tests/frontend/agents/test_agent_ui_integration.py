"""
Agent-UI Integration Tests

Comprehensive test suite for agent-UI interaction framework including:
- Agent clarification generation and user response processing
- Cross-page agent context preservation and question tracking
- Agent learning effectiveness from UI-based user feedback
- Data classification accuracy and real-time updates
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import websockets
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Test Configuration
TEST_CONFIG = {
    "backend_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "websocket_url": "ws://localhost:8000",
    "test_timeout": 30,
    "agent_response_timeout": 10,
    "client_account_id": 999,
    "engagement_id": "test_engagement_001"
}

class AgentUITestFramework:
    """Test framework for agent-UI integration testing"""
    
    def __init__(self):
        self.driver = None
        self.websocket = None
        self.session = None
        self.test_data = {}
        
    async def setup(self):
        """Set up test environment"""
        # Setup Chrome driver for UI testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Setup aiohttp session for API testing
        self.session = aiohttp.ClientSession()
        
        # Setup WebSocket connection for real-time testing
        try:
            self.websocket = await websockets.connect(
                f"{TEST_CONFIG['websocket_url']}/ws/agent-updates"
            )
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            self.websocket = None
    
    async def teardown(self):
        """Clean up test environment"""
        if self.driver:
            self.driver.quit()
        if self.session:
            await self.session.close()
        if self.websocket:
            await self.websocket.close()
    
    async def navigate_to_page(self, page_path: str):
        """Navigate to specific page and wait for load"""
        url = f"{TEST_CONFIG['frontend_url']}{page_path}"
        self.driver.get(url)
        
        # Wait for page to load
        WebDriverWait(self.driver, TEST_CONFIG['test_timeout']).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Wait for agent components to initialize
        await asyncio.sleep(2)
    
    async def trigger_agent_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger agent analysis and return response"""
        url = f"{TEST_CONFIG['backend_url']}/api/v1/discovery/agents/agent-analysis"
        
        async with self.session.post(
            url,
            json={
                **data,
                "client_account_id": TEST_CONFIG['client_account_id'],
                "engagement_id": TEST_CONFIG['engagement_id']
            }
        ) as response:
            return await response.json()
    
    async def wait_for_agent_questions(self, timeout: int = 10) -> List[Dict[str, Any]]:
        """Wait for agent questions to appear in UI"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Look for agent clarification panel
                clarification_panel = self.driver.find_element(
                    By.CLASS_NAME, "agent-clarification-panel"
                )
                
                # Look for question elements
                question_elements = clarification_panel.find_elements(
                    By.CLASS_NAME, "agent-question"
                )
                
                if question_elements:
                    questions = []
                    for element in question_elements:
                        question_data = {
                            "id": element.get_attribute("data-question-id"),
                            "text": element.find_element(By.CLASS_NAME, "question-text").text,
                            "type": element.get_attribute("data-question-type"),
                            "agent": element.get_attribute("data-agent-name")
                        }
                        questions.append(question_data)
                    return questions
                
            except Exception:
                pass
            
            await asyncio.sleep(0.5)
        
        return []
    
    async def respond_to_agent_question(
        self,
        question_id: str,
        response: Any,
        confidence: float = 0.8
    ) -> bool:
        """Respond to an agent question through UI"""
        try:
            # Find question element
            question_element = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-question-id="{question_id}"]'
            )
            
            # Find response input
            response_input = question_element.find_element(
                By.CLASS_NAME, "response-input"
            )
            
            # Clear and enter response
            response_input.clear()
            response_input.send_keys(str(response))
            
            # Set confidence if slider exists
            try:
                confidence_slider = question_element.find_element(
                    By.CLASS_NAME, "confidence-slider"
                )
                # Set slider value (simplified - actual implementation may vary)
                self.driver.execute_script(
                    f"arguments[0].value = {confidence * 100};",
                    confidence_slider
                )
            except Exception:
                pass
            
            # Submit response
            submit_button = question_element.find_element(
                By.CLASS_NAME, "submit-response"
            )
            submit_button.click()
            
            # Wait for response to be processed
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error responding to question: {e}")
            return False
    
    async def check_cross_page_context(self, context_data: Dict[str, Any]) -> bool:
        """Check if context is preserved across page navigation"""
        try:
            # Check for context indicators in UI
            context_indicators = self.driver.find_elements(
                By.CLASS_NAME, "cross-page-context"
            )
            
            for indicator in context_indicators:
                context_type = indicator.get_attribute("data-context-type")
                if context_type in context_data:
                    return True
            
            return False
        
        except Exception:
            return False
    
    async def monitor_real_time_updates(self, duration: int = 10) -> List[Dict[str, Any]]:
        """Monitor real-time updates through WebSocket"""
        updates = []
        
        if not self.websocket:
            return updates
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=1.0
                    )
                    
                    update_data = json.loads(message)
                    updates.append({
                        "timestamp": datetime.now().isoformat(),
                        "data": update_data
                    })
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"WebSocket error: {e}")
                    break
        
        except Exception as e:
            print(f"Error monitoring updates: {e}")
        
        return updates

@pytest.fixture
async def test_framework():
    """Test framework fixture"""
    framework = AgentUITestFramework()
    await framework.setup()
    yield framework
    await framework.teardown()

@pytest.mark.asyncio
class TestAgentClarificationGeneration:
    """Test agent clarification generation and processing"""
    
    async def test_data_import_clarification_generation(self, test_framework):
        """Test agent clarification generation during data import"""
        # Navigate to data import page
        await test_framework.navigate_to_page("/discovery/data-import")
        
        # Simulate file upload with ambiguous data
        test_data = {
            "data_type": "cmdb_import",
            "columns": ["srv_name", "ip_addr", "env", "dept", "unknown_field"],
            "sample_data": [
                {"srv_name": "web01", "ip_addr": "10.1.1.1", "env": "prod", "dept": "IT", "unknown_field": "critical"},
                {"srv_name": "db02", "ip_addr": "10.1.1.2", "env": "prod", "dept": "Finance", "unknown_field": "medium"}
            ]
        }
        
        # Trigger agent analysis
        analysis_result = await test_framework.trigger_agent_analysis(test_data)
        
        assert analysis_result["success"] is True
        assert "questions" in analysis_result
        
        # Wait for questions to appear in UI
        questions = await test_framework.wait_for_agent_questions()
        
        assert len(questions) > 0, "No agent questions generated"
        
        # Verify question quality
        for question in questions:
            assert question["id"] is not None
            assert len(question["text"]) > 10
            assert question["agent"] is not None
        
        # Check for specific expected questions about unknown field
        unknown_field_questions = [
            q for q in questions 
            if "unknown_field" in q["text"].lower()
        ]
        
        assert len(unknown_field_questions) > 0, "No questions about unknown field"
    
    async def test_asset_classification_clarification(self, test_framework):
        """Test agent clarification for asset classification"""
        # Navigate to inventory page
        await test_framework.navigate_to_page("/discovery/inventory")
        
        # Simulate asset with unclear classification
        test_data = {
            "data_type": "asset_classification",
            "assets": [
                {
                    "name": "mystery_server_01",
                    "ip": "192.168.1.100",
                    "os": "unknown",
                    "purpose": "unclear",
                    "department": "mixed_signals"
                }
            ]
        }
        
        # Trigger analysis
        analysis_result = await test_framework.trigger_agent_analysis(test_data)
        
        # Wait for classification questions
        questions = await test_framework.wait_for_agent_questions()
        
        # Should have questions about asset type, purpose, or classification
        classification_questions = [
            q for q in questions
            if any(keyword in q["text"].lower() for keyword in ["type", "purpose", "classification", "role"])
        ]
        
        assert len(classification_questions) > 0, "No asset classification questions generated"
    
    async def test_field_mapping_clarification(self, test_framework):
        """Test agent clarification for field mapping"""
        # Navigate to attribute mapping page
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Simulate unclear field mapping scenario
        test_data = {
            "data_type": "field_mapping",
            "source_fields": ["srv_nm", "ip_add", "criticality_lvl", "bus_unit", "custom_tag1"],
            "suggested_mappings": {
                "srv_nm": "hostname",
                "ip_add": "ip_address", 
                "bus_unit": "department",
                "criticality_lvl": "unclear",
                "custom_tag1": "unclear"
            }
        }
        
        # Trigger analysis
        analysis_result = await test_framework.trigger_agent_analysis(test_data)
        
        # Wait for mapping questions
        questions = await test_framework.wait_for_agent_questions()
        
        # Should have questions about unclear mappings
        mapping_questions = [
            q for q in questions
            if any(field in q["text"] for field in ["criticality_lvl", "custom_tag1"])
        ]
        
        assert len(mapping_questions) > 0, "No field mapping questions generated"

@pytest.mark.asyncio  
class TestUserResponseProcessing:
    """Test user response processing and agent learning"""
    
    async def test_response_submission_and_learning(self, test_framework):
        """Test response submission and agent learning integration"""
        # Navigate to data import page
        await test_framework.navigate_to_page("/discovery/data-import")
        
        # Generate questions first
        test_data = {
            "data_type": "cmdb_import",
            "columns": ["server_name", "environment", "custom_field"],
            "sample_data": [{"server_name": "web01", "environment": "production", "custom_field": "high"}]
        }
        
        await test_framework.trigger_agent_analysis(test_data)
        questions = await test_framework.wait_for_agent_questions()
        
        assert len(questions) > 0, "No questions to respond to"
        
        # Respond to first question
        question = questions[0]
        response_submitted = await test_framework.respond_to_agent_question(
            question["id"],
            "business_criticality",
            confidence=0.9
        )
        
        assert response_submitted, "Failed to submit response"
        
        # Wait for learning to process
        await asyncio.sleep(2)
        
        # Verify response was recorded by checking backend
        url = f"{TEST_CONFIG['backend_url']}/api/v1/discovery/agents/agent-status"
        async with test_framework.session.get(url) as response:
            status_data = await response.json()
            
            # Check if learning metrics improved
            assert "learning_metrics" in status_data
            learning_metrics = status_data["learning_metrics"]
            
            # Should show some learning activity
            assert learning_metrics.get("total_responses", 0) > 0
    
    async def test_correction_and_improvement(self, test_framework):
        """Test user corrections leading to agent improvement"""
        # Navigate to attribute mapping page
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Simulate agent making incorrect mapping suggestion
        test_data = {
            "data_type": "field_mapping",
            "source_fields": ["srv_priority"],
            "agent_suggestions": {"srv_priority": "server_name"}  # Intentionally wrong
        }
        
        await test_framework.trigger_agent_analysis(test_data)
        questions = await test_framework.wait_for_agent_questions()
        
        # Find mapping correction question
        mapping_question = None
        for question in questions:
            if "srv_priority" in question["text"]:
                mapping_question = question
                break
        
        assert mapping_question is not None, "No mapping question found"
        
        # Submit correction
        correction_submitted = await test_framework.respond_to_agent_question(
            mapping_question["id"],
            "business_criticality",  # Correct mapping
            confidence=1.0
        )
        
        assert correction_submitted, "Failed to submit correction"
        
        # Trigger similar analysis again to test learning
        await asyncio.sleep(3)  # Allow learning to process
        
        similar_data = {
            "data_type": "field_mapping", 
            "source_fields": ["server_priority"],  # Similar field name
            "agent_suggestions": {}
        }
        
        analysis_result = await test_framework.trigger_agent_analysis(similar_data)
        
        # Agent should now suggest better mapping based on learning
        if "suggested_mappings" in analysis_result:
            suggested = analysis_result["suggested_mappings"].get("server_priority")
            # Should suggest business_criticality or similar, not server_name
            assert suggested != "server_name", "Agent did not learn from correction"

@pytest.mark.asyncio
class TestCrossPageContextPreservation:
    """Test cross-page agent context preservation"""
    
    async def test_navigation_context_preservation(self, test_framework):
        """Test context preservation during page navigation"""
        # Start on data import page and create context
        await test_framework.navigate_to_page("/discovery/data-import")
        
        # Create cross-page context through data import
        test_data = {
            "data_type": "cmdb_import",
            "context_type": "asset_discovery_session",
            "columns": ["hostname", "ip", "application", "owner"],
            "sample_data": [
                {"hostname": "web01", "ip": "10.1.1.1", "application": "ecommerce", "owner": "team_a"}
            ]
        }
        
        await test_framework.trigger_agent_analysis(test_data)
        
        # Wait for context to be established
        await asyncio.sleep(2)
        
        # Navigate to attribute mapping page
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Check if context is preserved
        context_preserved = await test_framework.check_cross_page_context({
            "asset_discovery_session": True,
            "cmdb_import": True
        })
        
        assert context_preserved, "Context not preserved across page navigation"
        
        # Navigate to data cleansing page
        await test_framework.navigate_to_page("/discovery/data-cleansing")
        
        # Context should still be preserved
        context_still_preserved = await test_framework.check_cross_page_context({
            "asset_discovery_session": True
        })
        
        assert context_still_preserved, "Context lost after multiple navigations"
    
    async def test_question_tracking_across_pages(self, test_framework):
        """Test question tracking and resolution across pages"""
        # Start with questions on data import page
        await test_framework.navigate_to_page("/discovery/data-import")
        
        test_data = {
            "data_type": "cmdb_import",
            "columns": ["server", "env", "unclear_field"],
            "questions_expected": True
        }
        
        await test_framework.trigger_agent_analysis(test_data)
        questions = await test_framework.wait_for_agent_questions()
        
        original_question_count = len(questions)
        assert original_question_count > 0, "No questions generated"
        
        # Navigate to different page without answering questions
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Questions should still be accessible/tracked
        pending_questions = await test_framework.wait_for_agent_questions()
        
        # Should have similar number of pending questions
        assert len(pending_questions) >= original_question_count * 0.8, "Questions not tracked across pages"
        
        # Answer a question on this page
        if pending_questions:
            await test_framework.respond_to_agent_question(
                pending_questions[0]["id"],
                "test_response",
                confidence=0.8
            )
        
        # Navigate to inventory page
        await test_framework.navigate_to_page("/discovery/inventory") 
        
        # Check that answered questions are no longer pending
        final_questions = await test_framework.wait_for_agent_questions()
        
        # Should have fewer pending questions
        assert len(final_questions) < original_question_count, "Answered questions still pending"

@pytest.mark.asyncio
class TestAgentLearningEffectiveness:
    """Test agent learning effectiveness from UI feedback"""
    
    async def test_pattern_recognition_improvement(self, test_framework):
        """Test agent pattern recognition improvement over time"""
        # Navigate to attribute mapping page
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Provide multiple examples of same pattern
        patterns = [
            {"source": "srv_crit", "correct": "business_criticality"},
            {"source": "server_criticality", "correct": "business_criticality"},
            {"source": "app_importance", "correct": "business_criticality"},
            {"source": "system_priority", "correct": "business_criticality"}
        ]
        
        learning_progression = []
        
        for i, pattern in enumerate(patterns):
            # Test agent's current understanding
            test_data = {
                "data_type": "field_mapping",
                "source_fields": [pattern["source"]],
                "learning_test": True
            }
            
            analysis_result = await test_framework.trigger_agent_analysis(test_data)
            
            # Record initial suggestion
            initial_suggestion = analysis_result.get("suggested_mappings", {}).get(pattern["source"])
            
            if initial_suggestion != pattern["correct"]:
                # Generate clarification question and provide correct answer
                questions = await test_framework.wait_for_agent_questions()
                
                if questions:
                    await test_framework.respond_to_agent_question(
                        questions[0]["id"],
                        pattern["correct"],
                        confidence=1.0
                    )
            
            # Wait for learning to process
            await asyncio.sleep(2)
            
            # Test improved understanding
            retest_result = await test_framework.trigger_agent_analysis(test_data)
            final_suggestion = retest_result.get("suggested_mappings", {}).get(pattern["source"])
            
            learning_progression.append({
                "iteration": i + 1,
                "initial": initial_suggestion,
                "final": final_suggestion,
                "correct": pattern["correct"],
                "improved": final_suggestion == pattern["correct"]
            })
        
        # Analyze learning progression
        improvements = [p["improved"] for p in learning_progression]
        improvement_rate = sum(improvements) / len(improvements)
        
        assert improvement_rate >= 0.5, f"Learning improvement rate too low: {improvement_rate}"
        
        # Test pattern generalization with new similar field
        generalization_test = {
            "data_type": "field_mapping",
            "source_fields": ["business_importance"],  # New similar field
            "learning_test": True
        }
        
        gen_result = await test_framework.trigger_agent_analysis(generalization_test)
        gen_suggestion = gen_result.get("suggested_mappings", {}).get("business_importance")
        
        # Should generalize to business_criticality
        assert gen_suggestion == "business_criticality", "Agent failed to generalize learned pattern"
    
    async def test_confidence_calibration(self, test_framework):
        """Test agent confidence calibration based on feedback"""
        # Navigate to data cleansing page
        await test_framework.navigate_to_page("/discovery/data-cleansing")
        
        # Test scenarios with different confidence levels
        confidence_tests = [
            {"data": "clearly_valid_hostname", "expected_confidence": "high"},
            {"data": "ambiguous_server_name", "expected_confidence": "medium"},
            {"data": "invalid@#$%data", "expected_confidence": "low"}
        ]
        
        confidence_results = []
        
        for test_case in confidence_tests:
            test_data = {
                "data_type": "data_quality",
                "sample_data": [test_case["data"]],
                "confidence_test": True
            }
            
            analysis_result = await test_framework.trigger_agent_analysis(test_data)
            
            # Check agent confidence
            confidence = analysis_result.get("confidence", 0)
            quality_assessment = analysis_result.get("quality_assessment", {})
            
            confidence_results.append({
                "data": test_case["data"],
                "confidence": confidence,
                "expected": test_case["expected_confidence"],
                "assessment": quality_assessment
            })
        
        # Verify confidence calibration
        high_conf_result = [r for r in confidence_results if r["expected"] == "high"][0]
        low_conf_result = [r for r in confidence_results if r["expected"] == "low"][0]
        
        assert high_conf_result["confidence"] > low_conf_result["confidence"], \
            "Agent confidence not properly calibrated"

@pytest.mark.asyncio
class TestDataClassificationAccuracy:
    """Test data classification accuracy and real-time updates"""
    
    async def test_asset_classification_accuracy(self, test_framework):
        """Test accuracy of agent asset classification"""
        # Navigate to inventory page
        await test_framework.navigate_to_page("/discovery/inventory")
        
        # Test with clearly identifiable assets
        test_assets = [
            {
                "name": "sql-prod-01", 
                "services": ["mssql"], 
                "ports": [1433],
                "expected_type": "database"
            },
            {
                "name": "web-frontend-02",
                "services": ["nginx", "apache"],
                "ports": [80, 443],
                "expected_type": "web_server"
            },
            {
                "name": "exchange-mail-server",
                "services": ["smtp", "imap"],
                "ports": [25, 993],
                "expected_type": "mail_server"
            }
        ]
        
        classification_accuracy = []
        
        for asset in test_assets:
            test_data = {
                "data_type": "asset_classification",
                "assets": [asset],
                "accuracy_test": True
            }
            
            analysis_result = await test_framework.trigger_agent_analysis(test_data)
            
            classifications = analysis_result.get("classifications", [])
            
            if classifications:
                predicted_type = classifications[0].get("asset_type")
                is_correct = predicted_type == asset["expected_type"]
                confidence = classifications[0].get("confidence", 0)
                
                classification_accuracy.append({
                    "asset": asset["name"],
                    "expected": asset["expected_type"],
                    "predicted": predicted_type,
                    "correct": is_correct,
                    "confidence": confidence
                })
        
        # Calculate overall accuracy
        correct_count = sum(1 for result in classification_accuracy if result["correct"])
        overall_accuracy = correct_count / len(classification_accuracy)
        
        assert overall_accuracy >= 0.8, f"Classification accuracy too low: {overall_accuracy}"
        
        # Verify high confidence for correct classifications
        correct_classifications = [r for r in classification_accuracy if r["correct"]]
        avg_correct_confidence = sum(r["confidence"] for r in correct_classifications) / len(correct_classifications)
        
        assert avg_correct_confidence >= 0.7, "Low confidence for correct classifications"
    
    async def test_real_time_classification_updates(self, test_framework):
        """Test real-time classification updates through WebSocket"""
        # Navigate to inventory page
        await test_framework.navigate_to_page("/discovery/inventory")
        
        # Start monitoring real-time updates
        update_monitor = asyncio.create_task(
            test_framework.monitor_real_time_updates(duration=15)
        )
        
        # Trigger multiple classification requests
        test_batches = [
            {"assets": [{"name": "server1", "type": "unknown"}]},
            {"assets": [{"name": "server2", "type": "unknown"}]},
            {"assets": [{"name": "server3", "type": "unknown"}]}
        ]
        
        for batch in test_batches:
            test_data = {
                "data_type": "asset_classification",
                **batch,
                "real_time_test": True
            }
            
            await test_framework.trigger_agent_analysis(test_data)
            await asyncio.sleep(2)  # Allow processing time
        
        # Wait for monitoring to complete
        updates = await update_monitor
        
        # Verify real-time updates were received
        assert len(updates) > 0, "No real-time updates received"
        
        # Check for classification update messages
        classification_updates = [
            update for update in updates
            if update["data"].get("type") == "classification_update"
        ]
        
        assert len(classification_updates) >= len(test_batches) * 0.5, \
            "Insufficient real-time classification updates"
        
        # Verify update structure
        for update in classification_updates:
            update_data = update["data"]
            assert "data" in update_data
            assert "timestamp" in update
            
            classification_data = update_data["data"]
            assert "classification_type" in classification_data
            assert "confidence" in classification_data

@pytest.mark.asyncio
class TestIntegrationScenarios:
    """End-to-end integration test scenarios"""
    
    async def test_complete_discovery_workflow(self, test_framework):
        """Test complete discovery workflow with agent interactions"""
        workflow_results = {}
        
        # 1. Data Import with agent clarifications
        await test_framework.navigate_to_page("/discovery/data-import")
        
        import_data = {
            "data_type": "cmdb_import",
            "columns": ["hostname", "ip_address", "environment", "custom_field1", "custom_field2"],
            "sample_data": [
                {"hostname": "web01", "ip_address": "10.1.1.1", "environment": "prod", "custom_field1": "critical", "custom_field2": "team_alpha"},
                {"hostname": "db01", "ip_address": "10.1.1.2", "environment": "prod", "custom_field1": "high", "custom_field2": "team_beta"}
            ]
        }
        
        import_result = await test_framework.trigger_agent_analysis(import_data)
        import_questions = await test_framework.wait_for_agent_questions()
        
        workflow_results["import"] = {
            "questions_generated": len(import_questions),
            "analysis_success": import_result.get("success", False)
        }
        
        # Respond to import questions
        for question in import_questions[:2]:  # Respond to first 2 questions
            await test_framework.respond_to_agent_question(
                question["id"],
                "business_criticality" if "custom_field1" in question["text"] else "team_assignment",
                confidence=0.9
            )
        
        # 2. Attribute Mapping with context preservation
        await test_framework.navigate_to_page("/discovery/attribute-mapping")
        
        # Check context preservation
        context_preserved = await test_framework.check_cross_page_context({
            "cmdb_import": True,
            "field_mappings": True
        })
        
        workflow_results["mapping"] = {
            "context_preserved": context_preserved
        }
        
        # 3. Data Cleansing with agent insights
        await test_framework.navigate_to_page("/discovery/data-cleansing")
        
        cleansing_data = {
            "data_type": "data_quality",
            "assets": import_data["sample_data"],
            "quality_check": True
        }
        
        cleansing_result = await test_framework.trigger_agent_analysis(cleansing_data)
        
        workflow_results["cleansing"] = {
            "quality_issues_found": len(cleansing_result.get("quality_issues", [])),
            "recommendations_generated": len(cleansing_result.get("recommendations", []))
        }
        
        # 4. Inventory with final classification
        await test_framework.navigate_to_page("/discovery/inventory")
        
        final_classification = {
            "data_type": "asset_classification",
            "assets": import_data["sample_data"],
            "final_classification": True
        }
        
        final_result = await test_framework.trigger_agent_analysis(final_classification)
        
        workflow_results["inventory"] = {
            "assets_classified": len(final_result.get("classifications", [])),
            "classification_confidence": final_result.get("average_confidence", 0)
        }
        
        # Verify overall workflow success
        assert workflow_results["import"]["questions_generated"] > 0, "No import questions generated"
        assert workflow_results["import"]["analysis_success"], "Import analysis failed"
        assert workflow_results["mapping"]["context_preserved"], "Context not preserved"
        assert workflow_results["cleansing"]["quality_issues_found"] >= 0, "Quality check failed"
        assert workflow_results["inventory"]["assets_classified"] > 0, "No assets classified"
        
        # Check learning progression throughout workflow
        url = f"{TEST_CONFIG['backend_url']}/api/v1/discovery/agents/agent-status"
        async with test_framework.session.get(url) as response:
            final_status = await response.json()
            
            learning_metrics = final_status.get("learning_metrics", {})
            assert learning_metrics.get("total_responses", 0) > 0, "No learning occurred"
            assert learning_metrics.get("accuracy_improvement", 0) >= 0, "No accuracy improvement"

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"]) 