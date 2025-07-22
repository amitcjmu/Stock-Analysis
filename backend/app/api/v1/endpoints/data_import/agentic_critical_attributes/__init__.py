"""
Agentic Critical Attributes Module

Modularized agentic critical attributes functionality with clear separation:
- routes/: HTTP route handlers for analysis and feedback
- services/: Business logic services for attribute analysis
- agents/: CrewAI agent implementations and coordination
- models/: Pydantic schemas and data models
- utils/: Utility functions and helpers
"""

from fastapi import APIRouter

from .routes.analysis_routes import router as analysis_router
from .routes.feedback_routes import router as feedback_router
from .routes.suggestion_routes import router as suggestion_router
from .services.agent_coordinator import AgentCoordinator
from .services.attribute_analyzer import AttributeAnalyzer
from .services.learning_service import LearningService

# Create main router for the package
router = APIRouter(prefix="/agentic-critical-attributes", tags=["Agentic Critical Attributes"])

# Include all sub-routers
router.include_router(analysis_router, prefix="/analysis")
router.include_router(suggestion_router, prefix="/suggestions")
router.include_router(feedback_router, prefix="/feedback")

__all__ = [
    'router',
    'analysis_router',
    'suggestion_router',
    'feedback_router',
    'AttributeAnalyzer',
    'AgentCoordinator',
    'LearningService'
]