"""
Base tool classes for CrewAI integration
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import Field
from app.core.context_aware import ContextAwareTool
from app.services.tools.registry import ToolMetadata
import logging

# Optional CrewAI import
try:
    from crewai.tools import BaseTool
except ImportError:
    # Create a dummy BaseTool class when CrewAI is not available
    class BaseTool:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

logger = logging.getLogger(__name__)

class BaseDiscoveryTool(BaseTool, ContextAwareTool):
    """
    Base class for all discovery tools.
    Provides:
    - CrewAI tool integration
    - Context awareness
    - Standard error handling
    - Metadata registration
    """
    
    # Tool configuration
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    
    def __init__(self, **kwargs):
        """Initialize with both CrewAI and context awareness"""
        # Initialize CrewAI tool
        BaseTool.__init__(self)
        # Initialize context awareness
        ContextAwareTool.__init__(self, **kwargs)
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration - override in subclasses"""
        raise NotImplementedError("Each tool must define its metadata")
    
    def _run(self, *args, **kwargs) -> Any:
        """Execute tool with context and error handling"""
        try:
            self.log_with_context(
                'info', 
                f"Executing tool {self.name}",
                tool_params=kwargs
            )
            
            # Ensure context is available
            if not self.context:
                raise ValueError("No context available for tool execution")
            
            # Execute tool logic
            result = self.run(*args, **kwargs)
            
            self.log_with_context(
                'info',
                f"Tool {self.name} completed successfully"
            )
            
            return result
            
        except Exception as e:
            self.log_with_context(
                'error',
                f"Tool {self.name} failed: {e}",
                error_type=type(e).__name__
            )
            raise
    
    def run(self, *args, **kwargs) -> Any:
        """Implement tool logic in subclasses"""
        raise NotImplementedError("Each tool must implement run method")

class AsyncBaseDiscoveryTool(BaseDiscoveryTool):
    """Base class for async tools"""
    
    async def _arun(self, *args, **kwargs) -> Any:
        """Async execution wrapper"""
        try:
            self.log_with_context(
                'info',
                f"Executing async tool {self.name}",
                tool_params=kwargs
            )
            
            # Ensure context is available
            if not self.context:
                raise ValueError("No context available for tool execution")
            
            # Execute async tool logic
            result = await self.arun(*args, **kwargs)
            
            self.log_with_context(
                'info',
                f"Async tool {self.name} completed successfully"
            )
            
            return result
            
        except Exception as e:
            self.log_with_context(
                'error',
                f"Async tool {self.name} failed: {e}",
                error_type=type(e).__name__
            )
            raise
    
    async def arun(self, *args, **kwargs) -> Any:
        """Implement async tool logic in subclasses"""
        raise NotImplementedError("Each async tool must implement arun method")
    
    def run(self, *args, **kwargs) -> Any:
        """Sync wrapper for async tools"""
        import asyncio
        return asyncio.run(self.arun(*args, **kwargs))