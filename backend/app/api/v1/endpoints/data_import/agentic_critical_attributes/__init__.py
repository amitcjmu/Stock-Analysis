"""
Agentic Critical Attributes Module

Modularized agentic critical attributes functionality with clear separation:
- routes/: HTTP route handlers for analysis and feedback
- services/: Business logic services for attribute analysis
- agents/: CrewAI agent implementations and coordination
- models/: Pydantic schemas and data models
- utils/: Utility functions and helpers
"""

from .routes.analysis_routes import router as analysis_router
from .routes.suggestion_routes import router as suggestion_router
from .routes.feedback_routes import router as feedback_router

from .services.attribute_analyzer import AttributeAnalyzer
from .services.agent_coordinator import AgentCoordinator
from .services.learning_service import LearningService

__all__ = [
    'analysis_router',
    'suggestion_router',
    'feedback_router',
    'AttributeAnalyzer',
    'AgentCoordinator',
    'LearningService'
]