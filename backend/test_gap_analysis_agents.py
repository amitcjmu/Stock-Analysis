#!/usr/bin/env python3
"""
Test script for Gap Analysis agents and tools
"""

import asyncio
import logging
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_imports():
    """Test that agents can be imported"""
    try:
        from app.services.agents.critical_attribute_assessor_crewai import CriticalAttributeAssessorAgent
        from app.services.agents.gap_prioritization_agent_crewai import GapPrioritizationAgent
        logger.info("✅ Successfully imported Gap Analysis agents")
        
        # Test agent metadata
        assessor_metadata = CriticalAttributeAssessorAgent.agent_metadata()
        logger.info(f"CriticalAttributeAssessor: {assessor_metadata.name} - {assessor_metadata.description}")
        
        prioritizer_metadata = GapPrioritizationAgent.agent_metadata()
        logger.info(f"GapPrioritizationAgent: {prioritizer_metadata.name} - {prioritizer_metadata.description}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import agents: {e}")
        return False

def test_tool_imports():
    """Test that tools can be imported"""
    try:
        from app.services.tools.gap_analysis_tools import (
            AttributeMapperTool,
            CollectionPlannerTool,
            CompletenessAnalyzerTool,
            EffortEstimatorTool,
            GapIdentifierTool,
            ImpactCalculatorTool,
            PriorityRankerTool,
            QualityScorerTool,
        )
        logger.info("✅ Successfully imported Gap Analysis tools")
        
        # Test tool metadata
        tools = [
            AttributeMapperTool,
            CompletenessAnalyzerTool,
            QualityScorerTool,
            GapIdentifierTool,
            ImpactCalculatorTool,
            EffortEstimatorTool,
            PriorityRankerTool,
            CollectionPlannerTool
        ]
        
        for tool_class in tools:
            metadata = tool_class.tool_metadata()
            logger.info(f"{metadata.name}: {metadata.description}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import tools: {e}")
        return False

def test_critical_attributes_framework():
    """Test the critical attributes framework"""
    try:
        from app.services.agents.critical_attribute_assessor_crewai import CRITICAL_ATTRIBUTES_FRAMEWORK
        
        logger.info("\n📋 Critical Attributes Framework:")
        total_attributes = 0
        for category, config in CRITICAL_ATTRIBUTES_FRAMEWORK.items():
            attrs = config["primary"]
            total_attributes += len(attrs)
            logger.info(f"  {category}: {len(attrs)} attributes")
            logger.info(f"    - Business Impact: {config['business_impact']}")
            logger.info(f"    - 6R Relevance: {', '.join(config['6r_relevance'])}")
        
        logger.info(f"\nTotal Critical Attributes: {total_attributes}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load critical attributes framework: {e}")
        return False

async def test_tool_functionality():
    """Test basic tool functionality (without database)"""
    try:
        from app.core.context import RequestContext, set_context
        from app.services.tools.gap_analysis_tools import AttributeMapperTool
        
        # Create a mock context
        mock_context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            request_id="test-request"
        )
        set_context(mock_context)
        
        # Test AttributeMapperTool
        mapper = AttributeMapperTool()
        
        # Sample data fields
        sample_fields = [
            "hostname",
            "server_name",
            "operating_system",
            "cpu_count",
            "ram_size",
            "app_name",
            "owner_team",
            "last_updated"
        ]
        
        logger.info("\n🔧 Testing AttributeMapperTool...")
        result = await mapper.arun(sample_fields)
        
        if "error" not in result:
            logger.info(f"  Mapped {len(result['mapped_attributes'])} attributes")
            logger.info(f"  Coverage: {result['coverage_percentage']:.1f}%")
            logger.info(f"  Unmapped fields: {result['unmapped_fields']}")
            return True
        else:
            logger.error(f"  Tool error: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to test tool functionality: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Testing Gap Analysis Agents and Tools\n")
    
    tests = [
        ("Agent Imports", test_agent_imports),
        ("Tool Imports", test_tool_imports),
        ("Critical Attributes Framework", test_critical_attributes_framework)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        result = test_func()
        results.append((test_name, result))
    
    # Run async test
    logger.info(f"\n{'='*50}")
    logger.info("Running: Tool Functionality Test")
    logger.info(f"{'='*50}")
    tool_result = asyncio.run(test_tool_functionality())
    results.append(("Tool Functionality", tool_result))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("Test Summary")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Gap Analysis agents are ready.")
    else:
        logger.warning("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()