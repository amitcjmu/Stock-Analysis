"""
Agent tool registry for collection gaps.

This module provides the registry for agent tools as specified in the documentation.
"""

import logging
from typing import Any, Dict, Type

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class AgentToolRegistry:
    """
    Registry for agent tools used in collection gaps processing.

    This class maintains a centralized registry of tools that can be used
    by CrewAI agents for collection gaps functionality.
    """

    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, name: str, tool: BaseTool) -> None:
        """
        Register a tool in the registry.

        Args:
            name: Tool name identifier
            tool: BaseTool instance to register

        Raises:
            ValueError: If tool name is already registered
        """
        if name in cls._tools:
            raise ValueError(f"Tool {name} already registered")

        cls._tools[name] = tool
        logger.info(f"Registered tool: {name}")

    @classmethod
    def get(cls, name: str) -> BaseTool:
        """
        Get a tool from the registry.

        Args:
            name: Tool name identifier

        Returns:
            BaseTool instance

        Raises:
            KeyError: If tool is not found in registry
        """
        if name not in cls._tools:
            raise KeyError(f"Tool {name} not found in registry")

        return cls._tools[name]

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            name: Tool name identifier

        Returns:
            True if tool was removed, False if not found
        """
        if name in cls._tools:
            del cls._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    @classmethod
    def list_tools(cls) -> Dict[str, str]:
        """
        List all registered tools.

        Returns:
            Dictionary mapping tool names to their class names
        """
        return {name: tool.__class__.__name__ for name, tool in cls._tools.items()}

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (mainly for testing)."""
        cls._tools.clear()
        logger.info("Cleared all registered tools")

    @classmethod
    def get_tools_by_type(cls, tool_type: Type[BaseTool]) -> Dict[str, BaseTool]:
        """
        Get all tools of a specific type.

        Args:
            tool_type: Tool type to filter by

        Returns:
            Dictionary of tools matching the specified type
        """
        return {
            name: tool
            for name, tool in cls._tools.items()
            if isinstance(tool, tool_type)
        }

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            name: Tool name identifier

        Returns:
            True if tool is registered, False otherwise
        """
        return name in cls._tools


# Tool factory functions for common collection gaps tools
def create_gap_analysis_tool() -> BaseTool:
    """
    Create a gap analysis tool.

    This is a stub implementation that would create the actual
    GapAnalysisTool mentioned in the documentation.

    Returns:
        GapAnalysisTool instance (stubbed)
    """

    # Stub implementation - would create actual tool
    class GapAnalysisToolStub(BaseTool):
        name: str = "gap_analysis_tool"
        description: str = "Analyzes data gaps and generates priority recommendations"

        def _run(
            self, subject: Dict[str, Any], existing_data_snapshot: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Analyze gaps in collected data.

            Args:
                subject: Subject scope and IDs
                existing_data_snapshot: Current data state

            Returns:
                Gap analysis results with missing_fields_by_category and priorities
            """
            # Stub implementation
            return {
                "missing_fields_by_category": {
                    "lifecycle": ["end_of_life_date", "vendor_support_status"],
                    "resilience": ["rto_minutes", "rpo_minutes"],
                    "compliance": ["data_classification", "residency_requirements"],
                    "licensing": ["license_type", "renewal_date"],
                },
                "priorities": {
                    "critical": ["end_of_life_date", "rto_minutes"],
                    "high": ["data_classification", "license_type"],
                    "medium": ["vendor_support_status", "rpo_minutes"],
                },
            }

    return GapAnalysisToolStub()


def create_questionnaire_generation_tool() -> BaseTool:
    """
    Create a questionnaire generation tool.

    This is a stub implementation that would create the actual
    QuestionnaireGenerationTool mentioned in the documentation.

    Returns:
        QuestionnaireGenerationTool instance (stubbed)
    """

    class QuestionnaireGenerationToolStub(BaseTool):
        name: str = "questionnaire_generation_tool"
        description: str = "Generates adaptive questionnaires based on identified gaps"

        def _run(
            self, gaps: Dict[str, Any], stakeholder_role: str = "technical"
        ) -> Dict[str, Any]:
            """
            Generate questionnaire sections based on gaps.

            Args:
                gaps: Gap analysis results
                stakeholder_role: Target stakeholder role

            Returns:
                Generated questionnaire with sections and questions
            """
            # Stub implementation
            sections = []

            if "lifecycle" in gaps.get("missing_fields_by_category", {}):
                sections.append(
                    {
                        "section_name": "Product Lifecycle",
                        "questions": [
                            {
                                "question_id": "end_of_life_date",
                                "question_text": "What is the end-of-life date for this product?",
                                "question_type": "date",
                                "required": True,
                                "validation_rules": {"date_format": "YYYY-MM-DD"},
                            },
                            {
                                "question_id": "vendor_support_status",
                                "question_text": "What is the current vendor support status?",
                                "question_type": "select",
                                "options": [
                                    "active",
                                    "extended",
                                    "end_of_life",
                                    "custom",
                                ],
                                "required": True,
                            },
                        ],
                    }
                )

            if "resilience" in gaps.get("missing_fields_by_category", {}):
                sections.append(
                    {
                        "section_name": "Business Continuity",
                        "questions": [
                            {
                                "question_id": "rto_minutes",
                                "question_text": "What is the Recovery Time Objective (RTO) in minutes?",
                                "question_type": "number",
                                "required": True,
                                "validation_rules": {
                                    "min": 0,
                                    "max": 43200,
                                },  # 0 to 30 days
                            },
                            {
                                "question_id": "rpo_minutes",
                                "question_text": "What is the Recovery Point Objective (RPO) in minutes?",
                                "question_type": "number",
                                "required": True,
                                "validation_rules": {"min": 0, "max": 43200},
                            },
                        ],
                    }
                )

            return {
                "questionnaire_id": "generated_questionnaire_001",
                "title": f"Data Collection - {stakeholder_role.title()} Review",
                "sections": sections,
                "estimated_completion_time": len(sections) * 5,  # 5 minutes per section
                "validation_rules": {
                    "required_sections": len(sections),
                    "question_id_uniqueness": True,
                },
            }

    return QuestionnaireGenerationToolStub()


def create_vendor_lifecycle_tool() -> BaseTool:
    """
    Create a vendor lifecycle tool.

    This is a stub implementation that would create the actual
    VendorLifecycleTool mentioned in the documentation.

    Returns:
        VendorLifecycleTool instance (stubbed)
    """

    class VendorLifecycleToolStub(BaseTool):
        name: str = "vendor_lifecycle_tool"
        description: str = (
            "Normalizes vendor/product/version and finds lifecycle milestones"
        )

        def _run(
            self, vendor_name: str, product_name: str, version: str = ""
        ) -> Dict[str, Any]:
            """
            Normalize vendor/product/version and find lifecycle data.

            Args:
                vendor_name: Raw vendor name
                product_name: Raw product name
                version: Raw version string

            Returns:
                Normalized data with lifecycle milestones, provenance, and confidence
            """
            # Stub implementation
            return {
                "normalized": {
                    "vendor_name": vendor_name.strip().title(),
                    "product_name": product_name.strip(),
                    "version": version.strip() if version else "unknown",
                    "normalized_key": (
                        f"{vendor_name.lower().replace(' ', '_')}_"
                        f"{product_name.lower().replace(' ', '_')}"
                    ),
                },
                "lifecycle_milestones": [
                    {
                        "milestone_type": "end_of_life",
                        "milestone_date": "2025-12-31",
                        "source": "vendor_api_mock",
                        "confidence": 0.8,
                    },
                    {
                        "milestone_type": "end_of_support",
                        "milestone_date": "2025-06-30",
                        "source": "vendor_api_mock",
                        "confidence": 0.8,
                    },
                ],
                "provenance": {
                    "data_sources": ["vendor_api_mock", "community_database"],
                    "last_updated": "2024-01-21T00:00:00Z",
                    "confidence_factors": {
                        "official_source": True,
                        "recent_update": True,
                        "multiple_sources": False,
                    },
                },
                "confidence_score": 0.85,
            }

    return VendorLifecycleToolStub()


def create_dependency_graph_tool() -> BaseTool:
    """
    Create a dependency graph tool.

    This is a stub implementation that would create the actual
    DependencyGraphTool mentioned in the documentation.

    Returns:
        DependencyGraphTool instance (stubbed)
    """

    class DependencyGraphToolStub(BaseTool):
        name: str = "dependency_graph_tool"
        description: str = (
            "Suggests likely dependencies and updates critical path hints"
        )

        def _run(self, asset_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
            """
            Suggest dependencies for an asset.

            Args:
                asset_id: Asset identifier
                context: Context information about the asset

            Returns:
                Suggested dependencies with confidence scores
            """
            # Stub implementation
            return {
                "asset_id": asset_id,
                "suggested_dependencies": [
                    {
                        "dependent_asset_id": "database_server_001",
                        "relationship_nature": "data_source",
                        "direction": "upstream",
                        "criticality": "high",
                        "dataflow_type": "sync",
                        "confidence": 0.9,
                        "reasoning": "Application connects to database on same subnet",
                    },
                    {
                        "dependent_asset_id": "load_balancer_001",
                        "relationship_nature": "traffic_routing",
                        "direction": "downstream",
                        "criticality": "medium",
                        "dataflow_type": "async",
                        "confidence": 0.7,
                        "reasoning": "Network traffic patterns suggest load balancer dependency",
                    },
                ],
                "critical_path_hints": {
                    "migration_order_priority": 3,
                    "blocking_dependencies": ["database_server_001"],
                    "parallel_candidates": ["load_balancer_001"],
                    "estimated_migration_window": "4_hours",
                },
            }

    return DependencyGraphToolStub()


# Register default tools
def register_default_tools() -> None:
    """Register default collection gaps tools."""
    try:
        AgentToolRegistry.register("gap_analysis", create_gap_analysis_tool())
        AgentToolRegistry.register(
            "questionnaire_generation", create_questionnaire_generation_tool()
        )
        AgentToolRegistry.register("vendor_lifecycle", create_vendor_lifecycle_tool())
        AgentToolRegistry.register("dependency_graph", create_dependency_graph_tool())
        logger.info("Registered default collection gaps tools")
    except ValueError as e:
        logger.warning(f"Some default tools may already be registered: {e}")


# Auto-register default tools when module is imported
register_default_tools()
