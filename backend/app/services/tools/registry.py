"""
Central Tool Registry with auto-discovery
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any, Set
from dataclasses import dataclass
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolMetadata:
    """Metadata for registered tools"""
    name: str
    description: str
    tool_class: Type[BaseTool]
    categories: List[str]
    required_params: List[str]
    optional_params: List[str]
    context_aware: bool = True
    async_tool: bool = False

class ToolRegistry:
    """
    Central registry for all CrewAI tools with auto-discovery.
    Features:
    - Automatic tool discovery on startup
    - Category-based tool organization
    - Dynamic tool instantiation
    - Parameter validation
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._categories = {}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.discover_tools()
    
    def discover_tools(self) -> None:
        """Auto-discover all tools in the tools directory"""
        tools_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(tools_dir):
            if filename.endswith('_tool.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(
                        f'.{module_name}', 
                        package='app.services.tools'
                    )
                    
                    # Find all Tool subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseTool) and 
                            obj != BaseTool and
                            obj.__name__ not in ['BaseDiscoveryTool', 'AsyncBaseDiscoveryTool'] and
                            hasattr(obj, 'tool_metadata') and
                            not inspect.isabstract(obj)):
                            
                            try:
                                metadata = obj.tool_metadata()
                                self.register_tool(metadata)
                                logger.info(f"Discovered tool: {metadata.name}")
                            except Exception as e:
                                logger.error(f"Failed to get metadata for {name}: {e}")
                            
                except Exception as e:
                    logger.error(f"Failed to load tool module {module_name}: {e}")
    
    def register_tool(self, metadata: ToolMetadata) -> None:
        """Register a tool with the registry"""
        self._tools[metadata.name] = metadata
        
        # Update category index
        for category in metadata.categories:
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(metadata.name)
    
    def get_tool(
        self, 
        name: str,
        **kwargs
    ) -> Optional[BaseTool]:
        """Get an instantiated tool by name"""
        if name not in self._tools:
            logger.error(f"Tool {name} not found in registry")
            return None
        
        metadata = self._tools[name]
        
        try:
            # Validate required parameters
            missing_params = [
                param for param in metadata.required_params 
                if param not in kwargs
            ]
            if missing_params:
                raise ValueError(f"Missing required parameters: {missing_params}")
            
            # Instantiate tool
            tool = metadata.tool_class(**kwargs)
            logger.debug(f"Instantiated tool: {name}")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to instantiate tool {name}: {e}")
            return None
    
    def get_tools_by_category(self, category: str) -> List[ToolMetadata]:
        """Get all tools in a category"""
        tool_names = self._categories.get(category, set())
        return [self._tools[name] for name in tool_names]
    
    def get_tools_for_agent(self, required_tools: List[str]) -> List[BaseTool]:
        """Get instantiated tools for an agent"""
        tools = []
        for tool_name in required_tools:
            tool = self.get_tool(tool_name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Required tool {tool_name} not available")
        return tools
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """List all tool categories"""
        return list(self._categories.keys())

# Global registry instance
tool_registry = ToolRegistry()