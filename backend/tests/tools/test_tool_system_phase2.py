"""
Tests for Phase 2 Tool System Implementation
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.tools.categories import TOOL_CATEGORIES, get_tools_for_phase
from app.services.tools.factory import ToolFactory
from app.services.tools.registry import ToolMetadata, ToolRegistry


class TestPhase2ToolSystem:
    """Test Phase 2 tool system functionality"""
    
    def test_tool_registry_discovery(self):
        """Test tool registry discovers tools automatically"""
        registry = ToolRegistry()
        tools = registry.list_tools()
        
        # Should discover our core tools
        expected_tools = ['field_matcher', 'pii_scanner', 'schema_analyzer']
        for tool in expected_tools:
            assert tool in tools, f"Tool {tool} should be discovered"
    
    def test_tool_categories(self):
        """Test tool categorization system"""
        registry = ToolRegistry()
        categories = registry.list_categories()
        
        # Should have our defined categories
        expected_categories = ['mapping', 'analysis', 'security', 'validation', 'compliance', 'data_quality']
        for category in expected_categories:
            assert category in categories, f"Category {category} should exist"
    
    def test_tool_factory_creation(self):
        """Test tool factory can create tools"""
        factory = ToolFactory()
        
        # Test creating a field matcher tool
        tool = factory.create_tool('field_matcher')
        assert tool is not None, "Should create field_matcher tool"
        assert hasattr(tool, 'run'), "Tool should have run method"
    
    def test_phase_tool_mapping(self):
        """Test tools are properly mapped to phases"""
        # Test field mapping phase
        field_mapping_tools = get_tools_for_phase('field_mapping')
        assert 'field_matcher' in field_mapping_tools, "field_matcher should be in field_mapping phase"
        
        # Test data validation phase
        validation_tools = get_tools_for_phase('data_validation')
        assert 'schema_analyzer' in validation_tools, "schema_analyzer should be in data_validation phase"
        assert 'pii_scanner' in validation_tools, "pii_scanner should be in data_validation phase"
    
    def test_tool_capabilities(self):
        """Test tool factory capabilities reporting"""
        factory = ToolFactory()
        capabilities = factory.get_tool_capabilities()
        
        assert isinstance(capabilities, dict), "Capabilities should be a dict"
        assert 'mapping' in capabilities, "Should have mapping category"
        assert 'field_matcher' in capabilities['mapping'], "field_matcher should be in mapping category"
    
    def test_agent_factory_integration(self):
        """Test tool integration with agent factory"""
        from app.services.agents.factory import AgentFactory
        
        agent_factory = AgentFactory()
        
        # Should have access to tool registry
        assert hasattr(agent_factory, 'tool_registry'), "Agent factory should have tool registry"
        
        # Should be able to get tools
        tools = agent_factory.tool_registry.list_tools()
        assert len(tools) > 0, "Agent factory should have access to tools"
    
    def test_context_awareness_pattern(self):
        """Test that tools follow context-aware patterns"""
        from app.core.context_aware import ContextAwareTool
        from app.services.tools.base_tool import BaseDiscoveryTool
        
        # Check inheritance
        assert issubclass(BaseDiscoveryTool, ContextAwareTool), "Tools should be context-aware"
        
        # Test tool metadata pattern
        registry = ToolRegistry()
        for tool_name in registry.list_tools():
            metadata = registry._tools.get(tool_name)
            assert metadata.context_aware, f"Tool {tool_name} should be context-aware"
    
    @patch('app.services.tools.registry.logger')
    def test_error_handling(self, mock_logger):
        """Test tool registry error handling"""
        registry = ToolRegistry()
        
        # Test getting non-existent tool
        tool = registry.get_tool('non_existent_tool')
        assert tool is None, "Should return None for non-existent tool"
        
        # Should log error
        mock_logger.error.assert_called()
    
    def test_tool_metadata_structure(self):
        """Test tool metadata follows correct structure"""
        registry = ToolRegistry()
        
        for tool_name in registry.list_tools():
            metadata = registry._tools.get(tool_name)
            
            # Check required fields
            assert hasattr(metadata, 'name'), "Metadata should have name"
            assert hasattr(metadata, 'description'), "Metadata should have description"
            assert hasattr(metadata, 'categories'), "Metadata should have categories"
            assert hasattr(metadata, 'tool_class'), "Metadata should have tool_class"
            
            # Check types
            assert isinstance(metadata.categories, list), "Categories should be a list"
            assert len(metadata.categories) > 0, "Should have at least one category"
    
    def test_phase2_success_criteria(self):
        """Test all Phase 2 success criteria are met"""
        # Tool registry with auto-discovery working
        registry = ToolRegistry()
        assert len(registry.list_tools()) >= 3, "Should discover at least 3 tools"
        
        # Base tool classes provide proper patterns
        from app.services.tools.base_tool import AsyncBaseDiscoveryTool, BaseDiscoveryTool
        assert BaseDiscoveryTool is not None, "BaseDiscoveryTool should exist"
        assert AsyncBaseDiscoveryTool is not None, "AsyncBaseDiscoveryTool should exist"
        
        # Core tools implemented
        tools = registry.list_tools()
        core_tools = ['schema_analyzer', 'field_matcher', 'pii_scanner']
        for tool in core_tools:
            assert tool in tools, f"Core tool {tool} should be implemented"
        
        # Tools respect context boundaries
        for tool_name in tools:
            metadata = registry._tools.get(tool_name)
            assert metadata.context_aware, f"Tool {tool_name} should be context-aware"
        
        # Tool factory creates tools dynamically
        factory = ToolFactory()
        test_tool = factory.create_tool('field_matcher')
        assert test_tool is not None, "Factory should create tools dynamically"
        
        # All tools are properly categorized
        categories = registry.list_categories()
        assert len(categories) >= 4, "Should have at least 4 categories"
        
        print("✅ All Phase 2 success criteria met!")

if __name__ == "__main__":
    # Run basic tests
    test_suite = TestPhase2ToolSystem()
    
    print("🔧 Running Phase 2 Tool System Tests...")
    
    try:
        test_suite.test_tool_registry_discovery()
        print("✅ Tool registry discovery test passed")
        
        test_suite.test_tool_categories()
        print("✅ Tool categories test passed")
        
        test_suite.test_tool_factory_creation()
        print("✅ Tool factory creation test passed")
        
        test_suite.test_phase_tool_mapping()
        print("✅ Phase tool mapping test passed")
        
        test_suite.test_phase2_success_criteria()
        print("✅ Phase 2 success criteria test passed")
        
        print("🎉 All Phase 2 Tool System tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()