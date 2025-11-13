"""
Collection Flow SQLAlchemy Models
Contains all database models for the collection flow system.
"""

# Import individual models to maintain backward compatibility
from .collection_flow_model import CollectionFlow
from .gap_analysis_model import CollectionGapAnalysis
from .adaptive_questionnaire_model import AdaptiveQuestionnaire

# Import new models for Collection Flow Adaptive Questionnaire Enhancements
from .collection_question_rules import CollectionQuestionRules
from .collection_answer_history import CollectionAnswerHistory
from .asset_custom_attributes import AssetCustomAttributes
from .collection_background_tasks import CollectionBackgroundTasks

# Re-export for backward compatibility
__all__ = [
    "CollectionFlow",
    "CollectionGapAnalysis",
    "AdaptiveQuestionnaire",
    # New models for Adaptive Questionnaire Enhancements
    "CollectionQuestionRules",
    "CollectionAnswerHistory",
    "AssetCustomAttributes",
    "CollectionBackgroundTasks",
]
