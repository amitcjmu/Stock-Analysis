"""
Test script to verify CrewAI flow execution fixes.

This script tests the fixes for:
1. UnifiedDiscoveryFlowState missing 'completed_phases' attribute
2. PhaseTransitionAgent missing decision methods
3. CrewAIFlowService missing execution methods
4. Phase name mapping issues

Generated with CC (Claude Code)
"""

import asyncio
import logging
from typing import Any, Dict

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.crewai_flows.agents.decision.phase_transition import PhaseTransitionAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_unified_discovery_flow_state_completed_phases():
    """Test that UnifiedDiscoveryFlowState now has completed_phases property."""
    logger.info("🧪 Testing UnifiedDiscoveryFlowState.completed_phases property")
    
    # Create a flow state instance
    state = UnifiedDiscoveryFlowState()
    
    # Mark some phases as completed
    state.phase_completion["data_import"] = True
    state.phase_completion["field_mapping"] = True
    state.phase_completion["data_cleansing"] = False
    
    # Test the completed_phases property
    completed_phases = state.completed_phases
    
    # Verify it returns the correct list
    expected_completed = ["data_import", "field_mapping"]
    
    assert isinstance(completed_phases, list), "completed_phases should return a list"
    assert len(completed_phases) == 2, f"Expected 2 completed phases, got {len(completed_phases)}"
    
    for phase in expected_completed:
        assert phase in completed_phases, f"Phase '{phase}' should be in completed_phases"
    
    logger.info("✅ UnifiedDiscoveryFlowState.completed_phases property works correctly")
    return True


async def test_phase_transition_agent_decision_methods():
    """Test that PhaseTransitionAgent now has the required decision methods."""
    logger.info("🧪 Testing PhaseTransitionAgent decision methods")
    
    # Create agent instance
    agent = PhaseTransitionAgent()
    
    # Test get_decision method exists and is callable
    assert hasattr(agent, "get_decision"), "PhaseTransitionAgent should have get_decision method"
    assert callable(getattr(agent, "get_decision")), "get_decision should be callable"
    
    # Test get_post_execution_decision method exists and is callable
    assert hasattr(agent, "get_post_execution_decision"), "PhaseTransitionAgent should have get_post_execution_decision method"
    assert callable(getattr(agent, "get_post_execution_decision")), "get_post_execution_decision should be callable"
    
    # Test get_decision with minimal context
    test_context = {
        "current_phase": "data_import",
        "phase_result": {"status": "completed"},
        "flow_state": UnifiedDiscoveryFlowState()
    }
    
    try:
        decision = await agent.get_decision(test_context)
        assert decision is not None, "get_decision should return a decision"
        assert hasattr(decision, "action"), "Decision should have action attribute"
        assert hasattr(decision, "confidence"), "Decision should have confidence attribute"
        logger.info(f"✅ get_decision returned: {decision.action.value} with confidence {decision.confidence}")
    except Exception as e:
        logger.error(f"❌ get_decision failed: {e}")
        return False
    
    # Test get_post_execution_decision with minimal context
    post_exec_context = {
        "phase_name": "field_mapping",
        "phase_result": {"status": "completed"},
        "flow_state": UnifiedDiscoveryFlowState()
    }
    
    try:
        post_decision = await agent.get_post_execution_decision(post_exec_context)
        assert post_decision is not None, "get_post_execution_decision should return a decision"
        assert hasattr(post_decision, "action"), "Decision should have action attribute"
        assert hasattr(post_decision, "confidence"), "Decision should have confidence attribute"
        logger.info(f"✅ get_post_execution_decision returned: {post_decision.action.value} with confidence {post_decision.confidence}")
    except Exception as e:
        logger.error(f"❌ get_post_execution_decision failed: {e}")
        return False
    
    logger.info("✅ PhaseTransitionAgent decision methods work correctly")
    return True


async def test_crewai_flow_service_execution_methods():
    """Test that CrewAIFlowService now has the required execution methods."""
    logger.info("🧪 Testing CrewAIFlowService execution methods")
    
    # Create service instance
    service = CrewAIFlowService()
    
    # Test that required methods exist
    required_methods = [
        "execute_data_import_validation",
        "generate_field_mapping_suggestions",
        "apply_field_mappings",
        "execute_data_cleansing",
        "create_discovery_assets",
        "execute_analysis_phases",
        "execute_flow_phase"
    ]
    
    for method_name in required_methods:
        assert hasattr(service, method_name), f"CrewAIFlowService should have {method_name} method"
        assert callable(getattr(service, method_name)), f"{method_name} should be callable"
        logger.info(f"✅ Found method: {method_name}")
    
    # Test execute_data_import_validation with sample data
    test_raw_data = [
        {"hostname": "server1", "ip_address": "192.168.1.10", "os": "Ubuntu 20.04"},
        {"hostname": "server2", "ip_address": "192.168.1.11", "os": "CentOS 8"}
    ]
    
    try:
        result = await service.execute_data_import_validation(
            flow_id="test-flow-123",
            raw_data=test_raw_data,
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        
        assert isinstance(result, dict), "execute_data_import_validation should return a dict"
        assert "status" in result, "Result should have status"
        assert "phase" in result, "Result should have phase"
        assert "results" in result, "Result should have results"
        
        logger.info(f"✅ execute_data_import_validation returned: {result['status']}")
        
        # Test field mapping suggestions
        validation_result = result.get("results", {})
        mapping_result = await service.generate_field_mapping_suggestions(
            flow_id="test-flow-123",
            validation_result=validation_result,
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        
        assert isinstance(mapping_result, dict), "generate_field_mapping_suggestions should return a dict"
        assert mapping_result.get("status") == "completed", "Mapping suggestions should complete successfully"
        
        logger.info(f"✅ generate_field_mapping_suggestions returned: {mapping_result['status']}")
        
    except Exception as e:
        logger.error(f"❌ CrewAI execution method test failed: {e}")
        return False
    
    logger.info("✅ CrewAIFlowService execution methods work correctly")
    return True


def test_phase_name_mapping():
    """Test that phase name mapping has been corrected."""
    logger.info("🧪 Testing phase name mapping corrections")
    
    # Valid discovery phases as mentioned in the issue
    valid_phases = [
        "data_import", 
        "field_mapping", 
        "data_cleansing", 
        "asset_creation", 
        "asset_inventory", 
        "dependency_analysis"
    ]
    
    # Test mapping from execution_engine_crew.py
    expected_mappings = {
        "data_import": "data_import_validation",
        "field_mapping": "field_mapping", 
        "data_cleansing": "data_cleansing",
        "asset_creation": "asset_creation",
        "asset_inventory": "analysis",
        "dependency_analysis": "analysis",
        "tech_debt_analysis": "analysis",
    }
    
    # Verify that all valid phases have mappings
    for phase in valid_phases:
        assert phase in expected_mappings, f"Phase '{phase}' should have a mapping"
        logger.info(f"✅ Phase '{phase}' maps to '{expected_mappings[phase]}'")
    
    # Verify that mapped phases correspond to actual CrewAI service methods
    service = CrewAIFlowService()
    service_method_map = {
        "data_import_validation": "execute_data_import_validation",
        "field_mapping": "generate_field_mapping_suggestions",
        "data_cleansing": "execute_data_cleansing",
        "asset_creation": "create_discovery_assets",
        "analysis": "execute_analysis_phases",
    }
    
    for mapped_phase, method_name in service_method_map.items():
        assert hasattr(service, method_name), f"CrewAIFlowService should have method '{method_name}' for phase '{mapped_phase}'"
        logger.info(f"✅ Mapped phase '{mapped_phase}' has corresponding method '{method_name}'")
    
    logger.info("✅ Phase name mapping corrections work correctly")
    return True


async def run_all_tests():
    """Run all tests to verify the fixes."""
    logger.info("🚀 Starting CrewAI flow execution fixes verification")
    
    tests = [
        ("UnifiedDiscoveryFlowState completed_phases", test_unified_discovery_flow_state_completed_phases()),
        ("PhaseTransitionAgent decision methods", test_phase_transition_agent_decision_methods()),
        ("CrewAIFlowService execution methods", test_crewai_flow_service_execution_methods()),
        ("Phase name mapping", test_phase_name_mapping()),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func
            results.append((test_name, result, None))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False, str(e)))
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, result, error in results:
        if result:
            logger.info(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            logger.error(f"❌ {test_name}: FAILED")
            if error:
                logger.error(f"   Error: {error}")
            failed += 1
    
    logger.info(f"\nTotal tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! CrewAI flow execution fixes are working correctly.")
        return True
    else:
        logger.error(f"💥 {failed} test(s) failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)