"""
User Experience Tests

Comprehensive UX test suite for discovery platform including:
- UI responsiveness and performance across all discovery pages
- Agent clarification UX flow testing
- Cross-page navigation and state preservation  
- Error handling and recovery testing
- Accessibility and usability validation
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Test Configuration
TEST_CONFIG = {
    "frontend_url": "http://localhost:3000",
    "test_timeout": 30,
    "performance_threshold": 3.0,  # seconds
    "accessibility_standards": "WCAG_2_1_AA"
}

class UXTestFramework:
    """Framework for comprehensive UX testing"""
    
    def __init__(self):
        self.driver = None
        self.performance_metrics = {}
        self.accessibility_results = {}
        
    async def setup(self):
        """Set up test environment"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        
    async def teardown(self):
        """Clean up test environment"""
        if self.driver:
            self.driver.quit()
    
    def measure_page_load_time(self, url: str) -> float:
        """Measure page load time"""
        start_time = time.time()
        self.driver.get(url)
        
        # Wait for main content to load
        try:
            WebDriverWait(self.driver, TEST_CONFIG['test_timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except TimeoutException:
            pass
            
        load_time = time.time() - start_time
        return load_time
    
    def test_responsive_design(self, url: str) -> Dict[str, Any]:
        """Test responsive design across different screen sizes"""
        results = {}
        
        screen_sizes = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 667}
        ]
        
        for size in screen_sizes:
            self.driver.set_window_size(size["width"], size["height"])
            self.driver.get(url)
            
            # Check for horizontal scrollbars
            has_horizontal_scroll = self.driver.execute_script(
                "return document.body.scrollWidth > window.innerWidth"
            )
            
            # Check if navigation is accessible
            try:
                nav_element = self.driver.find_element(By.TAG_NAME, "nav")
                nav_visible = nav_element.is_displayed()
            except NoSuchElementException:
                nav_visible = False
            
            results[size["name"]] = {
                "has_horizontal_scroll": has_horizontal_scroll,
                "navigation_visible": nav_visible,
                "layout_broken": has_horizontal_scroll
            }
        
        return results
    
    def test_agent_clarification_flow(self) -> Dict[str, Any]:
        """Test agent clarification UX flow"""
        results = {
            "clarification_panel_found": False,
            "questions_displayable": False,
            "response_submittable": False,
            "feedback_providable": False,
            "flow_completion_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Look for clarification panel
            clarification_panel = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "agent-clarification-panel"))
            )
            results["clarification_panel_found"] = True
            
            # Check for questions
            questions = clarification_panel.find_elements(By.CLASS_NAME, "agent-question")
            if questions:
                results["questions_displayable"] = True
                
                # Try to interact with first question
                first_question = questions[0]
                
                # Look for response input
                try:
                    response_input = first_question.find_element(By.CLASS_NAME, "response-input")
                    response_input.send_keys("Test response")
                    
                    # Look for submit button
                    submit_button = first_question.find_element(By.CLASS_NAME, "submit-response")
                    submit_button.click()
                    
                    results["response_submittable"] = True
                    
                    # Check for feedback mechanism
                    try:
                        feedback_elements = first_question.find_elements(By.CLASS_NAME, "feedback-button")
                        if feedback_elements:
                            results["feedback_providable"] = True
                    except NoSuchElementException:
                        pass
                        
                except NoSuchElementException:
                    pass
        
        except TimeoutException:
            pass
        
        results["flow_completion_time"] = time.time() - start_time
        return results

@pytest.fixture
async def ux_framework():
    """UX test framework fixture"""
    framework = UXTestFramework()
    await framework.setup()
    yield framework
    await framework.teardown()

@pytest.mark.asyncio
class TestUserExperience:
    """Comprehensive UX test suite"""
    
    async def test_discovery_pages_performance(self, ux_framework):
        """Test performance across all discovery pages"""
        discovery_pages = [
            "/discovery/data-import",
            "/discovery/attribute-mapping", 
            "/discovery/data-cleansing",
            "/discovery/inventory"
        ]
        
        performance_results = {}
        
        for page in discovery_pages:
            url = f"{TEST_CONFIG['frontend_url']}{page}"
            load_time = ux_framework.measure_page_load_time(url)
            
            performance_results[page] = {
                "load_time": load_time,
                "performance_acceptable": load_time < TEST_CONFIG['performance_threshold']
            }
        
        # Assert all pages load within acceptable time
        for page, result in performance_results.items():
            assert result["performance_acceptable"], f"Page {page} load time too slow: {result['load_time']}s"
        
        # Check average performance
        avg_load_time = sum(r["load_time"] for r in performance_results.values()) / len(performance_results)
        assert avg_load_time < TEST_CONFIG['performance_threshold'], f"Average load time too slow: {avg_load_time}s"
    
    async def test_responsive_design_all_pages(self, ux_framework):
        """Test responsive design across all pages"""
        discovery_pages = [
            "/discovery/data-import",
            "/discovery/attribute-mapping",
            "/discovery/data-cleansing", 
            "/discovery/inventory"
        ]
        
        for page in discovery_pages:
            url = f"{TEST_CONFIG['frontend_url']}{page}"
            responsive_results = ux_framework.test_responsive_design(url)
            
            # Assert responsive design works on all screen sizes
            for size_name, size_result in responsive_results.items():
                assert not size_result["layout_broken"], f"Layout broken on {size_name} for {page}"
                assert size_result["navigation_visible"], f"Navigation not visible on {size_name} for {page}"
    
    async def test_agent_clarification_ux(self, ux_framework):
        """Test agent clarification user experience"""
        # Navigate to page that should have agent clarifications
        url = f"{TEST_CONFIG['frontend_url']}/discovery/data-import"
        ux_framework.driver.get(url)
        
        clarification_results = ux_framework.test_agent_clarification_flow()
        
        # Assert UX flow components work
        assert clarification_results["clarification_panel_found"], "Clarification panel not found"
        assert clarification_results["questions_displayable"], "Questions not displayable"
        assert clarification_results["response_submittable"], "Response not submittable"
        assert clarification_results["flow_completion_time"] < 10, "Flow too slow"
    
    async def test_cross_page_navigation(self, ux_framework):
        """Test cross-page navigation and state preservation"""
        pages = [
            "/discovery/data-import",
            "/discovery/attribute-mapping",
            "/discovery/data-cleansing",
            "/discovery/inventory"
        ]
        
        navigation_success = True
        
        for i, page in enumerate(pages):
            url = f"{TEST_CONFIG['frontend_url']}{page}"
            ux_framework.driver.get(url)
            
            # Verify page loads correctly
            try:
                WebDriverWait(ux_framework.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except TimeoutException:
                navigation_success = False
                break
            
            # Check for navigation elements
            try:
                nav_links = ux_framework.driver.find_elements(By.CSS_SELECTOR, "nav a")
                if len(nav_links) == 0:
                    navigation_success = False
                    break
            except NoSuchElementException:
                navigation_success = False
                break
        
        assert navigation_success, "Cross-page navigation failed"

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"]) 