"""
UI Interaction Handler for CrewAI Flow
Handles communication between agents and the user interface.
"""
import logging
from typing import Dict, List, Any, Optional

from app.services.agent_ui_bridge_handlers import (
    QuestionHandler, 
    ClassificationHandler, 
    InsightHandler, 
    ContextHandler,
    StorageManager
)
from app.services.models.agent_communication import (
    QuestionType, 
    ConfidenceLevel, 
    DataClassification,
)

logger = logging.getLogger(__name__)

class UIInteractionHandler:
    def __init__(self, config):
        self.config = config
        settings = getattr(self.config, 'settings', None)
        storage_path = settings.LEARNING_CONTEXT_DIR if settings and hasattr(settings, 'LEARNING_CONTEXT_DIR') else 'data/learning/context_fallback'
        self.storage_manager = StorageManager(str(storage_path))
        self.question_handler = QuestionHandler(self.storage_manager)
        self.classification_handler = ClassificationHandler(self.storage_manager)
        self.insight_handler = InsightHandler(self.storage_manager)
        self.context_handler = ContextHandler(self.storage_manager)
        self._load_persistent_data()

    def add_agent_question(self, flow_state: "DiscoveryFlowState", agent_id: str, agent_name: str, 
                          question_type: QuestionType, page: str,
                          title: str, question: str, context: Dict[str, Any],
                          options: Optional[List[str]] = None,
                          confidence: Optional[ConfidenceLevel] = None,
                          priority: str = "medium") -> str:
        question_id = self.question_handler.add_agent_question(
            agent_id, agent_name, question_type, page, title, question, 
            context, options, confidence, priority
        )
        flow_state.agent_insights.setdefault('questions', []).append(question_id)
        return question_id

    def add_agent_insight(self, flow_state: "DiscoveryFlowState", agent_id: str, agent_name: str, insight_type: str,
                         title: str, description: str, confidence: ConfidenceLevel,
                         supporting_data: Dict[str, Any], page: str = "discovery",
                         actionable: bool = True) -> str:
        insight_id = self.insight_handler.add_agent_insight(
            agent_id, agent_name, insight_type, title, description, 
            confidence, supporting_data, page, actionable,
            flow_state.flow_context.get('client_account_id'), 
            flow_state.flow_context.get('engagement_id'), 
            flow_state.id
        )
        flow_state.agent_insights.setdefault('insights', []).append(insight_id)
        return insight_id
    
    def _load_persistent_data(self) -> None:
        """Load persistent data from storage using handlers."""
        try:
            questions_data = self.storage_manager.load_questions()
            self.question_handler.load_questions(questions_data)
            
            classifications_data = self.storage_manager.load_classifications()
            self.classification_handler.load_classifications(classifications_data)
            
            insights_data = self.storage_manager.load_insights()
            self.insight_handler.load_insights(insights_data)
            
            context_data = self.storage_manager.load_context()
            self.context_handler.load_context_data(context_data)
            
        except Exception as e:
            logger.error(f"Error loading persistent data for UI Interaction Handler: {e}") 