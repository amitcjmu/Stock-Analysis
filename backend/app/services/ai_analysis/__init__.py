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

from .gap_analysis_agent import GapAnalysisAgent
from .questionnaire_generator import AdaptiveQuestionnaireGenerator
from .confidence_scoring import ConfidenceScorer
from .business_context_analyzer_compat import BusinessContextAnalyzer
from .learning_optimizer import LearningOptimizer
from .ai_validation_service import AIValidationService

__all__ = [
    'GapAnalysisAgent',
    'AdaptiveQuestionnaireGenerator', 
    'ConfidenceScorer',
    'BusinessContextAnalyzer',
    'LearningOptimizer',
    'AIValidationService'
]