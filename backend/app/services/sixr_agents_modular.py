"""
6R Analysis CrewAI Agents - Modular & Robust
Specialized agents for discovery, analysis, question generation, and refinement.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .sixr_agents_handlers import (
    AgentManagerHandler,
    TaskCoordinatorHandler,
    ResponseHandlerHandler
)

logger = logging.getLogger(__name__)

class SixRAnalysisAgents:
    """6R Analysis CrewAI agents orchestrator with modular architecture."""
    
    def __init__(self, llm_service: Optional[Any] = None):
        # Initialize handlers
        self.agent_manager = AgentManagerHandler()
        self.task_coordinator = TaskCoordinatorHandler(self.agent_manager)
        self.response_handler = ResponseHandlerHandler()
        
        # Legacy compatibility
        self.llm = self.agent_manager.get_llm()
        self.decision_engine = self.agent_manager.get_decision_engine()
        self.agents = self.agent_manager.get_agents()
        
        logger.info("6R Analysis Agents initialized with modular handlers")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of 6R agents system."""
        agent_status = self.agent_manager.get_agent_status()
        
        return {
            "status": "healthy",
            "service": "sixr-agents",
            "version": "2.0.0",
            "agent_manager": self.agent_manager.is_available(),
            "task_coordinator": self.task_coordinator.is_available(),
            "response_handler": self.response_handler.is_available(),
            "agents_initialized": agent_status["agents_initialized"],
            "available_agents": agent_status["available_agents"],
            "llm_configured": agent_status["llm_configured"],
            "decision_engine_ready": agent_status["decision_engine_ready"],
            "service_available": agent_status["service_available"]
        }
    
    # Main workflow methods
    def run_discovery(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run discovery analysis workflow."""
        try:
            return self.task_coordinator.run_discovery_workflow(cmdb_data)
        except Exception as e:
            logger.error(f"Discovery workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "discovery",
                "fallback_mode": True
            }
    
    def run_initial_analysis(self, parameters: Any, application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run initial 6R analysis workflow."""
        try:
            return self.task_coordinator.run_initial_analysis_workflow(parameters, application_context)
        except Exception as e:
            logger.error(f"Initial analysis workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "initial_analysis",
                "fallback_mode": True
            }
    
    def run_question_generation(self, analysis_gaps: List[str], application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run question generation workflow."""
        try:
            result = self.task_coordinator.run_question_generation_workflow(analysis_gaps, application_context)
            
            # Parse questions using response handler
            if result.get("status") == "completed" and "questions" in result:
                parsed_questions = self.response_handler.parse_generated_questions(result["questions"])
                result["questions"] = parsed_questions
            
            return result
        except Exception as e:
            logger.error(f"Question generation workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "question_generator",
                "fallback_mode": True
            }
    
    def run_input_processing(self, responses: List[Dict[str, Any]], current_parameters: Any) -> Dict[str, Any]:
        """Run input processing workflow."""
        try:
            result = self.task_coordinator.run_input_processing_workflow(responses, current_parameters)
            
            # Parse parameter updates using response handler
            if result.get("status") == "completed" and "parameter_updates" in result:
                parsed_updates = self.response_handler.parse_parameter_updates(str(result["parameter_updates"]))
                result["parameter_updates"] = parsed_updates
            
            return result
        except Exception as e:
            logger.error(f"Input processing workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "input_processing",
                "fallback_mode": True
            }
    
    # Task creation methods (for compatibility)
    def create_discovery_task(self, cmdb_data: Dict[str, Any]) -> Any:
        """Create discovery analysis task."""
        return self.task_coordinator.create_discovery_task(cmdb_data)
    
    def create_initial_analysis_task(self, parameters: Any, application_context: Dict[str, Any]) -> Any:
        """Create initial 6R analysis task."""
        return self.task_coordinator.create_initial_analysis_task(parameters, application_context)
    
    def create_question_generation_task(self, analysis_gaps: List[str], application_context: Dict[str, Any]) -> Any:
        """Create question generation task."""
        return self.task_coordinator.create_question_generation_task(analysis_gaps, application_context)
    
    def create_input_processing_task(self, responses: List[Dict[str, Any]], current_parameters: Any) -> Any:
        """Create input processing task."""
        return self.task_coordinator.create_input_processing_task(responses, current_parameters)
    
    # Response processing methods
    def _parse_generated_questions(self, result: str) -> List[Dict[str, Any]]:
        """Parse and structure questions from agent output."""
        return self.response_handler.parse_generated_questions(result)
    
    def _parse_parameter_updates(self, raw_result: str) -> Dict[str, Any]:
        """Parse parameter updates from agent output."""
        return self.response_handler.parse_parameter_updates(raw_result)
    
    def process_stakeholder_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process stakeholder responses into parameter updates."""
        return self.response_handler.process_stakeholder_responses(responses)
    
    # Utility methods
    def get_default_questions(self) -> List[Dict[str, Any]]:
        """Get default qualifying questions."""
        try:
            from app.schemas.sixr_analysis import QualifyingQuestion, QuestionType, QuestionOption
            
            default_questions = [
                QualifyingQuestion(
                    id="technical_complexity",
                    question="How would you rate the technical complexity of this application?",
                    question_type=QuestionType.SCALE,
                    category="Technical Assessment",
                    priority=1,
                    required=True,
                    scale={"min": 1, "max": 5, "labels": {"1": "Very Simple", "5": "Very Complex"}},
                    help_text="Consider architecture, dependencies, technology stack, and integration complexity"
                ),
                QualifyingQuestion(
                    id="migration_timeline",
                    question="What is your preferred timeline for migrating this application?",
                    question_type=QuestionType.SELECT,
                    category="Migration Planning",
                    priority=1,
                    required=True,
                    options=[
                        QuestionOption(value="urgent", label="Urgent - Within 3 months"),
                        QuestionOption(value="near_term", label="Near-term - 3-6 months"),
                        QuestionOption(value="medium_term", label="Medium-term - 6-12 months"),
                        QuestionOption(value="long_term", label="Long-term - Over 12 months")
                    ],
                    help_text="Consider business drivers, resource availability, and project dependencies"
                ),
                QualifyingQuestion(
                    id="dependency_complexity",
                    question="How many dependencies does this application have?",
                    question_type=QuestionType.SELECT,
                    category="Technical Assessment",
                    priority=2,
                    required=False,
                    options=[
                        QuestionOption(value="none", label="No dependencies"),
                        QuestionOption(value="few", label="1-3 dependencies"),
                        QuestionOption(value="moderate", label="4-10 dependencies"),
                        QuestionOption(value="many", label="More than 10 dependencies")
                    ],
                    help_text="Consider databases, external APIs, shared services, and other applications"
                ),
                QualifyingQuestion(
                    id="compliance_type",
                    question="What compliance frameworks apply to this application?",
                    question_type=QuestionType.MULTISELECT,
                    category="Compliance",
                    priority=2,
                    required=False,
                    options=[
                        QuestionOption(value="sox", label="SOX"),
                        QuestionOption(value="pci", label="PCI DSS"),
                        QuestionOption(value="hipaa", label="HIPAA"),
                        QuestionOption(value="gdpr", label="GDPR"),
                        QuestionOption(value="none", label="No specific compliance requirements")
                    ],
                    help_text="Select all applicable compliance frameworks"
                ),
                QualifyingQuestion(
                    id="business_criticality",
                    question="What is the business impact if this application is unavailable?",
                    question_type=QuestionType.SELECT,
                    category="Business Impact",
                    priority=1,
                    required=True,
                    options=[
                        QuestionOption(value="low", label="Minimal impact - can be down for days"),
                        QuestionOption(value="medium", label="Moderate impact - can be down for hours"),
                        QuestionOption(value="high", label="High impact - can be down for minutes"),
                        QuestionOption(value="critical", label="Critical - must be always available")
                    ],
                    help_text="Consider revenue impact, customer experience, and operational disruption"
                )
            ]
            
            return default_questions
            
        except ImportError:
            # Fallback questions when schemas not available
            return self.response_handler._generate_default_questions()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return self.agent_manager.get_agent_status()
    
    def validate_response_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize response format."""
        return self.response_handler.validate_response_format(response)
    
    def generate_response_summary(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of processed responses."""
        return self.response_handler.generate_response_summary(responses)

# Legacy compatibility and health check function
def get_sixr_agents_health() -> Dict[str, Any]:
    """Get health status of 6R agents system."""
    try:
        agents = SixRAnalysisAgents()
        return agents.get_health_status()
    except Exception as e:
        return {
            "status": "error",
            "service": "sixr-agents",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Export main class for backward compatibility
__all__ = ["SixRAnalysisAgents", "get_sixr_agents_health"] 