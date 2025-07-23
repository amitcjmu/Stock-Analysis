"""
AI Analysis & Intelligence Services for ADCS
Team B2 Implementation - Agent Team B2

This module provides comprehensive AI-powered analysis capabilities for the Adaptive Data Collection System:

Completed Services:
- B2.1: Gap analysis AI agents using CrewAI framework (GapAnalysisAgent)
- B2.2: Adaptive questionnaire generation service (AdaptiveQuestionnaireGenerator)
- B2.3: Confidence scoring algorithms (ConfidenceScorer)
- B2.4: Business context analysis for questionnaire targeting (BusinessContextAnalyzer)
- B2.5: Learning patterns for questionnaire optimization (LearningOptimizer)
- B2.6: AI validation and hallucination protection (AIValidationService)

All services implement real AI logic using CrewAI framework patterns and support:
- Multi-tenant data isolation
- 22 critical attributes framework integration
- 6R migration strategy optimization
- Progressive questionnaire generation
- Real-time confidence scoring and validation

Built by: Agent Team B2 (AI Analysis & Intelligence)
Status: COMPLETE - All 6 core services implemented
"""

from .ai_validation_service import AIValidationService
from .business_context_analyzer import BusinessContextAnalyzer
from .business_context_analyzer_compat import (
    BusinessContextAnalyzer as BusinessContextAnalyzerCompat,
)
from .confidence_scoring import ConfidenceScorer
from .gap_analysis_agent import GapAnalysisAgent
from .learning_optimizer import LearningOptimizer
from .questionnaire_generator import AdaptiveQuestionnaireGenerator

__all__ = [
    "GapAnalysisAgent",
    "AdaptiveQuestionnaireGenerator",
    "ConfidenceScorer",
    "BusinessContextAnalyzer",
    "LearningOptimizer",
    "AIValidationService",
]
