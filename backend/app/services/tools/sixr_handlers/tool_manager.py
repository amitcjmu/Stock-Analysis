"""
Tool Manager Handler
Main interface for managing and coordinating all 6R tools.
"""

import logging
from typing import Dict, List, Any, Optional

from .analysis_tools import AnalysisToolsHandler
from .generation_tools import GenerationToolsHandler
from .code_analysis_tools import CodeAnalysisToolsHandler
from .validation_tools import ValidationToolsHandler

logger = logging.getLogger(__name__)

class ToolManager:
    """Main tool manager with graceful fallbacks."""
    
    def __init__(self):
        # Initialize all handlers
        self.analysis_tools = AnalysisToolsHandler()
        self.generation_tools = GenerationToolsHandler()
        self.code_analysis_tools = CodeAnalysisToolsHandler()
        self.validation_tools = ValidationToolsHandler()
        
        logger.info("Tool manager initialized with all handlers")
    
    def is_available(self) -> bool:
        """Check if the tool manager is properly initialized."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all tool handlers."""
        return {
            "status": "healthy",
            "service": "sixr-tools",
            "version": "2.0.0",
            "components": {
                "analysis_tools": self.analysis_tools.is_available(),
                "generation_tools": self.generation_tools.is_available(),
                "code_analysis_tools": self.code_analysis_tools.is_available(),
                "validation_tools": self.validation_tools.is_available()
            }
        }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return [
            "cmdb_analysis_tool",
            "parameter_scoring_tool", 
            "question_generation_tool",
            "code_analysis_tool",
            "recommendation_validation_tool"
        ]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        tool_info = {
            "cmdb_analysis_tool": {
                "name": "CMDB Analysis Tool",
                "description": "Analyze CMDB application data to extract insights for 6R migration strategy",
                "handler": "analysis_tools",
                "inputs": ["application_data", "analysis_focus"]
            },
            "parameter_scoring_tool": {
                "name": "Parameter Scoring Tool", 
                "description": "Score parameter configuration for 6R strategy alignment",
                "handler": "analysis_tools",
                "inputs": ["parameters", "strategy"]
            },
            "question_generation_tool": {
                "name": "Question Generation Tool",
                "description": "Generate qualifying questions based on information gaps",
                "handler": "generation_tools",
                "inputs": ["information_gaps", "application_context", "current_parameters"]
            },
            "code_analysis_tool": {
                "name": "Code Analysis Tool",
                "description": "Analyze code complexity and characteristics for migration planning",
                "handler": "code_analysis_tools",
                "inputs": ["file_content", "file_type", "analysis_type"]
            },
            "recommendation_validation_tool": {
                "name": "Recommendation Validation Tool",
                "description": "Validate 6R migration recommendations against criteria",
                "handler": "validation_tools",
                "inputs": ["recommendation", "application_context", "validation_criteria"]
            }
        }
        
        return tool_info.get(tool_name)
    
    # Tool execution methods
    def execute_cmdb_analysis(self, application_data: Dict[str, Any], 
                            analysis_focus: str = "all") -> Dict[str, Any]:
        """Execute CMDB analysis tool."""
        try:
            return self.analysis_tools.analyze_cmdb_data(application_data, analysis_focus)
        except Exception as e:
            logger.error(f"CMDB analysis execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def execute_parameter_scoring(self, parameters: Dict[str, float], 
                                strategy: str) -> Dict[str, Any]:
        """Execute parameter scoring tool."""
        try:
            return self.analysis_tools.score_parameters(parameters, strategy)
        except Exception as e:
            logger.error(f"Parameter scoring execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def execute_question_generation(self, information_gaps: List[str],
                                  application_context: Dict[str, Any],
                                  current_parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute question generation tool."""
        try:
            return self.generation_tools.generate_qualifying_questions(
                information_gaps, application_context, current_parameters
            )
        except Exception as e:
            logger.error(f"Question generation execution failed: {e}")
            return [{"error": str(e), "status": "failed"}]
    
    def execute_code_analysis(self, file_content: str, file_type: str,
                            analysis_type: str = "complexity") -> Dict[str, Any]:
        """Execute code analysis tool."""
        try:
            return self.code_analysis_tools.analyze_code(file_content, file_type, analysis_type)
        except Exception as e:
            logger.error(f"Code analysis execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def execute_recommendation_validation(self, recommendation: Dict[str, Any],
                                        application_context: Dict[str, Any], 
                                        validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recommendation validation tool."""
        try:
            return self.validation_tools.validate_recommendation(
                recommendation, application_context, validation_criteria
            )
        except Exception as e:
            logger.error(f"Recommendation validation execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    # Utility methods for backward compatibility
    def run_tool(self, tool_name: str, **kwargs) -> Any:
        """Generic tool execution method."""
        try:
            if tool_name == "cmdb_analysis_tool":
                return self.execute_cmdb_analysis(
                    kwargs.get('application_data', {}),
                    kwargs.get('analysis_focus', 'all')
                )
            elif tool_name == "parameter_scoring_tool":
                return self.execute_parameter_scoring(
                    kwargs.get('parameters', {}),
                    kwargs.get('strategy', 'rehost')
                )
            elif tool_name == "question_generation_tool":
                return self.execute_question_generation(
                    kwargs.get('information_gaps', []),
                    kwargs.get('application_context', {}),
                    kwargs.get('current_parameters', {})
                )
            elif tool_name == "code_analysis_tool":
                return self.execute_code_analysis(
                    kwargs.get('file_content', ''),
                    kwargs.get('file_type', 'generic'),
                    kwargs.get('analysis_type', 'complexity')
                )
            elif tool_name == "recommendation_validation_tool":
                return self.execute_recommendation_validation(
                    kwargs.get('recommendation', {}),
                    kwargs.get('application_context', {}),
                    kwargs.get('validation_criteria', {})
                )
            else:
                return {"error": f"Unknown tool: {tool_name}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {"error": str(e), "status": "failed"} 