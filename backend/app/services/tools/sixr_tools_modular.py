"""
6R Analysis Tools - Modular & Robust
Specialized tools for CMDB analysis, parameter scoring, question generation, and validation.
"""

import logging
from typing import Any, Dict, List, Optional

from .sixr_handlers import ToolManager

logger = logging.getLogger(__name__)

# Initialize tool manager
tool_manager = ToolManager()


# Health check function
def get_sixr_tools_health() -> Dict[str, Any]:
    """Get health status of 6R tools system."""
    return tool_manager.get_health_status()


# Main tool functions for backward compatibility
def get_sixr_tools() -> List[str]:
    """Get list of available 6R tools."""
    return tool_manager.get_available_tools()


def get_tool_by_name(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get tool information by name."""
    return tool_manager.get_tool_info(tool_name)


def run_cmdb_analysis_tool(
    application_data: Dict[str, Any], analysis_focus: str = "all"
) -> str:
    """Run CMDB analysis tool and return JSON string."""
    try:
        result = tool_manager.execute_cmdb_analysis(application_data, analysis_focus)
        import json

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"CMDB analysis tool failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"})


def run_parameter_scoring_tool(parameters: Dict[str, float], strategy: str) -> str:
    """Run parameter scoring tool and return JSON string."""
    try:
        result = tool_manager.execute_parameter_scoring(parameters, strategy)
        import json

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Parameter scoring tool failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"})


def run_question_generation_tool(
    information_gaps: List[str],
    application_context: Dict[str, Any],
    current_parameters: Dict[str, Any],
) -> str:
    """Run question generation tool and return JSON string."""
    try:
        result = tool_manager.execute_question_generation(
            information_gaps, application_context, current_parameters
        )
        import json

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Question generation tool failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"})


def run_code_analysis_tool(
    file_content: str, file_type: str, analysis_type: str = "complexity"
) -> str:
    """Run code analysis tool and return JSON string."""
    try:
        result = tool_manager.execute_code_analysis(
            file_content, file_type, analysis_type
        )
        import json

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Code analysis tool failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"})


def run_recommendation_validation_tool(
    recommendation: Dict[str, Any],
    application_context: Dict[str, Any],
    validation_criteria: Dict[str, Any],
) -> str:
    """Run recommendation validation tool and return JSON string."""
    try:
        result = tool_manager.execute_recommendation_validation(
            recommendation, application_context, validation_criteria
        )
        import json

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Recommendation validation tool failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"})


# Tool class definitions for CrewAI compatibility
try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    CREWAI_TOOLS_AVAILABLE = True

    class CMDBAnalysisInput(BaseModel):
        """Input schema for CMDB analysis tool."""

        application_data: Dict[str, Any] = Field(
            ..., description="Application data from CMDB"
        )
        analysis_focus: str = Field(
            default="all",
            description="Focus area: technical, business, compliance, or all",
        )

    class CMDBAnalysisTool(BaseTool):
        """Tool for analyzing CMDB data to extract 6R-relevant insights."""

        name: str = "cmdb_analysis_tool"
        description: str = (
            "Analyze CMDB application data to extract insights for 6R migration strategy analysis"
        )
        args_schema: type[BaseModel] = CMDBAnalysisInput

        def _run(
            self, application_data: Dict[str, Any], analysis_focus: str = "all"
        ) -> str:
            """Analyze CMDB data and return structured insights."""
            return run_cmdb_analysis_tool(application_data, analysis_focus)

    class ParameterScoringInput(BaseModel):
        """Input schema for parameter scoring tool."""

        parameters: Dict[str, float] = Field(
            ..., description="6R analysis parameters to score"
        )
        strategy: str = Field(
            ..., description="Target migration strategy for scoring alignment"
        )

    class ParameterScoringTool(BaseTool):
        """Tool for scoring parameter configurations against 6R strategies."""

        name: str = "parameter_scoring_tool"
        description: str = (
            "Score 6R analysis parameters for alignment with migration strategies"
        )
        args_schema: type[BaseModel] = ParameterScoringInput

        def _run(self, parameters: Dict[str, float], strategy: str) -> str:
            """Score parameters for strategy alignment."""
            return run_parameter_scoring_tool(parameters, strategy)

    class QuestionGenerationInput(BaseModel):
        """Input schema for question generation tool."""

        information_gaps: List[str] = Field(
            ..., description="List of information gaps to address"
        )
        application_context: Dict[str, Any] = Field(
            ..., description="Application context information"
        )
        current_parameters: Dict[str, Any] = Field(
            default_factory=dict, description="Current parameter values"
        )

    class QuestionGenerationTool(BaseTool):
        """Tool for generating qualifying questions based on information gaps."""

        name: str = "question_generation_tool"
        description: str = (
            "Generate qualifying questions to fill information gaps in 6R analysis"
        )
        args_schema: type[BaseModel] = QuestionGenerationInput

        def _run(
            self,
            information_gaps: List[str],
            application_context: Dict[str, Any],
            current_parameters: Dict[str, Any] = None,
        ) -> str:
            """Generate qualifying questions based on information gaps."""
            if current_parameters is None:
                current_parameters = {}
            return run_question_generation_tool(
                information_gaps, application_context, current_parameters
            )

    class ValidationInput(BaseModel):
        """Input schema for recommendation validation tool."""

        recommendation: Dict[str, Any] = Field(
            ..., description="6R recommendation to validate"
        )
        context: Dict[str, Any] = Field(
            ..., description="Application and business context"
        )
        constraints: Dict[str, Any] = Field(
            default_factory=dict, description="Business constraints and requirements"
        )

    class RecommendationValidationTool(BaseTool):
        """Tool for validating 6R recommendations against business constraints."""

        name: str = "recommendation_validation_tool"
        description: str = (
            "Validate 6R migration recommendations against business constraints and requirements"
        )
        args_schema: type[BaseModel] = ValidationInput

        def _run(
            self,
            recommendation: Dict[str, Any],
            context: Dict[str, Any],
            constraints: Dict[str, Any] = None,
        ) -> str:
            """Validate recommendation against constraints."""
            if constraints is None:
                constraints = {}
            return run_recommendation_validation_tool(
                recommendation, context, constraints
            )

    # Tool registry for CrewAI
    SIXR_TOOLS = {
        "cmdb_analysis_tool": CMDBAnalysisTool,
        "parameter_scoring_tool": ParameterScoringTool,
        "question_generation_tool": QuestionGenerationTool,
        "recommendation_validation_tool": RecommendationValidationTool,
    }

except ImportError as e:
    logger.warning(f"CrewAI tools not available: {e}")
    CREWAI_TOOLS_AVAILABLE = False

    # Fallback classes when CrewAI is not available
    try:
        from pydantic import BaseModel, Field

        class FallbackBaseTool:
            """Fallback base tool when CrewAI not available."""

            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        class CMDBAnalysisInput(BaseModel):
            """Input schema for CMDB analysis tool."""

            application_data: Dict[str, Any] = Field(
                ..., description="Application data from CMDB"
            )
            analysis_focus: str = Field(
                default="all",
                description="Focus area: technical, business, compliance, or all",
            )

        class CMDBAnalysisTool(FallbackBaseTool):
            """Fallback tool for analyzing CMDB data."""

            def __init__(self):
                super().__init__(
                    name="cmdb_analysis_tool",
                    description="Analyze CMDB application data to extract insights for 6R migration strategy analysis",
                )

            def _run(
                self, application_data: Dict[str, Any], analysis_focus: str = "all"
            ) -> str:
                """Analyze CMDB data and return structured insights."""
                return run_cmdb_analysis_tool(application_data, analysis_focus)

        class ParameterScoringInput(BaseModel):
            """Input schema for parameter scoring tool."""

            parameters: Dict[str, float] = Field(
                ..., description="6R analysis parameters to score"
            )
            strategy: str = Field(
                ..., description="Target migration strategy for scoring alignment"
            )

        class ParameterScoringTool(FallbackBaseTool):
            """Fallback tool for scoring parameter configurations."""

            def __init__(self):
                super().__init__(
                    name="parameter_scoring_tool",
                    description="Score 6R analysis parameters for alignment with migration strategies",
                )

            def _run(self, parameters: Dict[str, float], strategy: str) -> str:
                """Score parameters for strategy alignment."""
                return run_parameter_scoring_tool(parameters, strategy)

        class QuestionGenerationInput(BaseModel):
            """Input schema for question generation tool."""

            information_gaps: List[str] = Field(
                ..., description="List of information gaps to address"
            )
            application_context: Dict[str, Any] = Field(
                ..., description="Application context information"
            )
            current_parameters: Dict[str, Any] = Field(
                default_factory=dict, description="Current parameter values"
            )

        class QuestionGenerationTool(FallbackBaseTool):
            """Fallback tool for generating qualifying questions."""

            def __init__(self):
                super().__init__(
                    name="question_generation_tool",
                    description="Generate qualifying questions to fill information gaps in 6R analysis",
                )

            def _run(
                self,
                information_gaps: List[str],
                application_context: Dict[str, Any],
                current_parameters: Dict[str, Any] = None,
            ) -> str:
                """Generate qualifying questions based on information gaps."""
                if current_parameters is None:
                    current_parameters = {}
                return run_question_generation_tool(
                    information_gaps, application_context, current_parameters
                )

        class ValidationInput(BaseModel):
            """Input schema for recommendation validation tool."""

            recommendation: Dict[str, Any] = Field(
                ..., description="6R recommendation to validate"
            )
            context: Dict[str, Any] = Field(
                ..., description="Application and business context"
            )
            constraints: Dict[str, Any] = Field(
                default_factory=dict,
                description="Business constraints and requirements",
            )

        class RecommendationValidationTool(FallbackBaseTool):
            """Fallback tool for validating 6R recommendations."""

            def __init__(self):
                super().__init__(name="recommendation_validation_tool")

            def _run(
                self,
                recommendation: Dict[str, Any],
                context: Dict[str, Any],
                constraints: Dict[str, Any] = None,
            ) -> str:
                """Validate recommendation against constraints."""
                if constraints is None:
                    constraints = {}
                return run_recommendation_validation_tool(
                    recommendation, context, constraints
                )

    except ImportError:
        logger.warning("Pydantic not available - using basic fallback tools")

        class FallbackBaseTool:
            """Basic fallback tool."""

            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Define basic fallback classes without Pydantic
        CMDBAnalysisInput = dict
        ParameterScoringInput = dict
        QuestionGenerationInput = dict
        ValidationInput = dict

        class CMDBAnalysisTool(FallbackBaseTool):
            def __init__(self):
                super().__init__(name="cmdb_analysis_tool")

        class ParameterScoringTool(FallbackBaseTool):
            def __init__(self):
                super().__init__(name="parameter_scoring_tool")

        class QuestionGenerationTool(FallbackBaseTool):
            def __init__(self):
                super().__init__(name="question_generation_tool")

        class RecommendationValidationTool(FallbackBaseTool):
            def __init__(self):
                super().__init__(name="recommendation_validation_tool")

    # Tool registry for fallback mode
    SIXR_TOOLS = {
        "cmdb_analysis_tool": CMDBAnalysisTool,
        "parameter_scoring_tool": ParameterScoringTool,
        "question_generation_tool": QuestionGenerationTool,
        "recommendation_validation_tool": RecommendationValidationTool,
    }


# Legacy compatibility functions
def get_sixr_tools_legacy() -> List[Any]:
    """Get 6R tools in legacy format."""
    if SIXR_TOOLS:
        return [tool_class() for tool_class in SIXR_TOOLS.values()]
    else:
        return []


# Export all main functions
__all__ = [
    "get_sixr_tools_health",
    "get_sixr_tools",
    "get_tool_by_name",
    "run_cmdb_analysis_tool",
    "run_parameter_scoring_tool",
    "run_question_generation_tool",
    "run_code_analysis_tool",
    "run_recommendation_validation_tool",
    "tool_manager",
    "SIXR_TOOLS",
]
