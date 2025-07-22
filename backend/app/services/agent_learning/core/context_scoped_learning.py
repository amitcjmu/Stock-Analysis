"""
Context-Scoped Agent Learning System

Core learning system with context isolation for multi-tenancy.
Provides learning capabilities for CrewAI agents with performance integration.

This module now delegates to specialized learning modules while maintaining
backward compatibility for all existing functionality.
"""

import logging


# Import all learning modules
from .learning import (
    AssetClassificationLearning,
    BaseLearningMixin,
    ClientContextManager,
    DataSourceLearning,
    FeedbackProcessor,
    FieldMappingLearning,
    LearningUtilities,
    PerformanceLearning,
    QualityAssessmentLearning,
)

logger = logging.getLogger(__name__)


class ContextScopedAgentLearning(
    BaseLearningMixin,
    FieldMappingLearning,
    DataSourceLearning,
    QualityAssessmentLearning,
    PerformanceLearning,
    FeedbackProcessor,
    ClientContextManager,
    AssetClassificationLearning,
    LearningUtilities
):
    """
    Agent learning system with context isolation for multi-tenancy.
    
    This class combines all learning functionality through multiple inheritance
    from specialized modules while maintaining the same public interface.
    """
    
    def __init__(self, data_dir: str = "data/learning"):
        """Initialize the learning system with all modules."""
        # Initialize base learning functionality
        BaseLearningMixin.__init__(self, data_dir)
        
        logger.info("Initialized modularized ContextScopedAgentLearning system")