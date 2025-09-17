"""
Dependency Analysis Tools for Discovery Flow

Provides comprehensive tools for persistent agents to analyze dependencies,
build dependency graphs, and identify communication patterns between assets.

This module maintains backward compatibility by exporting all original classes
and functions from the modularized structure.
"""

# Import from modularized structure
from .analyzer import DependencyAnalyzer
from .factory import create_dependency_analysis_tools
from .tools import (
    DependencyAnalysisTool,
    DependencyGraphBuilderTool,
    MigrationWavePlannerTool,
    DummyDependencyAnalysisTool,
    DummyDependencyGraphBuilderTool,
    DummyMigrationWavePlannerTool,
)
from .base import CREWAI_TOOLS_AVAILABLE, BaseTool

# Export everything that was available in the original file
__all__ = [
    # Core analyzer class
    "DependencyAnalyzer",
    # Factory function
    "create_dependency_analysis_tools",
    # Tool classes
    "DependencyAnalysisTool",
    "DependencyGraphBuilderTool",
    "MigrationWavePlannerTool",
    # Dummy classes
    "DummyDependencyAnalysisTool",
    "DummyDependencyGraphBuilderTool",
    "DummyMigrationWavePlannerTool",
    # Base components
    "CREWAI_TOOLS_AVAILABLE",
    "BaseTool",
]
