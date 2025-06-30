"""
Tool category definitions and management
"""

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class ToolCategory:
    """Tool category definition"""
    name: str
    description: str
    typical_tools: List[str]
    required_for_phases: List[str]

# Define standard tool categories
TOOL_CATEGORIES = {
    "analysis": ToolCategory(
        name="analysis",
        description="Tools for data and structure analysis",
        typical_tools=["schema_analyzer", "data_profiler", "pattern_detector"],
        required_for_phases=["data_validation", "field_mapping"]
    ),
    "validation": ToolCategory(
        name="validation",
        description="Tools for data validation and quality checks",
        typical_tools=["schema_validator", "data_quality_checker", "constraint_validator"],
        required_for_phases=["data_validation", "data_cleansing"]
    ),
    "mapping": ToolCategory(
        name="mapping",
        description="Tools for field and data mapping",
        typical_tools=["field_matcher", "semantic_mapper", "mapping_validator"],
        required_for_phases=["field_mapping"]
    ),
    "security": ToolCategory(
        name="security",
        description="Security and compliance tools",
        typical_tools=["pii_scanner", "encryption_checker", "access_validator"],
        required_for_phases=["data_validation", "tech_debt_assessment"]
    ),
    "transformation": ToolCategory(
        name="transformation",
        description="Data transformation and cleansing tools",
        typical_tools=["data_cleanser", "format_converter", "normalizer"],
        required_for_phases=["data_cleansing"]
    ),
    "discovery": ToolCategory(
        name="discovery",
        description="Asset and dependency discovery tools",
        typical_tools=["asset_scanner", "dependency_analyzer", "relationship_mapper"],
        required_for_phases=["asset_inventory", "dependency_analysis"]
    )
}

def get_tools_for_phase(phase: str) -> Set[str]:
    """Get all tools typically needed for a phase"""
    tools = set()
    for category in TOOL_CATEGORIES.values():
        if phase in category.required_for_phases:
            tools.update(category.typical_tools)
    return tools