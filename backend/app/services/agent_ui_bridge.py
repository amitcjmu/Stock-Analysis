"""
Agent-UI Communication Bridge
Enables agents to communicate with users through the UI for clarifications, feedback, and iterative learning.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .agent_ui_bridge_handlers import (
    QuestionHandler, 
    ClassificationHandler, 
    InsightHandler, 
    ContextHandler,
    AnalysisHandler,
    StorageManager
)
from .models.agent_communication import (
    QuestionType, 
    ConfidenceLevel, 
    DataClassification,
    AgentQuestion,
    DataItem,
    AgentInsight
)

logger = logging.getLogger(__name__)

class AgentUIBridge:
    """Manages communication between AI agents and the UI."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize storage manager
        self.storage_manager = StorageManager(str(self.data_dir))
        
        # Initialize handlers
        self.question_handler = QuestionHandler(self.storage_manager)
        self.classification_handler = ClassificationHandler(self.storage_manager)
        self.insight_handler = InsightHandler(self.storage_manager)
        self.context_handler = ContextHandler(self.storage_manager)
        self.analysis_handler = AnalysisHandler(self.storage_manager)
        
        # Load existing data
        self._load_persistent_data()
    
    # === AGENT QUESTION MANAGEMENT ===
    
    def add_agent_question(self, agent_id: str, agent_name: str, 
                          question_type: QuestionType, page: str,
                          title: str, question: str, context: Dict[str, Any],
                          options: Optional[List[str]] = None,
                          confidence: Optional[ConfidenceLevel] = None,
                          priority: str = "medium") -> str:
        """Add a new question from an agent."""
        return self.question_handler.add_agent_question(
            agent_id, agent_name, question_type, page, title, question, 
            context, options, confidence, priority
        )
    
    def answer_agent_question(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Process user response to an agent question."""
        return self.question_handler.answer_agent_question(question_id, response)
    
    def get_questions_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all pending questions for a specific page."""
        return self.question_handler.get_questions_for_page(page)
    
    # === DATA CLASSIFICATION MANAGEMENT ===
    
    def classify_data_item(self, item_id: str, data_type: str, content: Dict[str, Any],
                          classification: DataClassification, agent_analysis: Dict[str, Any],
                          confidence: ConfidenceLevel, page: str = "discovery",
                          issues: List[str] = None, recommendations: List[str] = None) -> None:
        """Classify a data item based on agent analysis."""
        self.classification_handler.classify_data_item(
            item_id, data_type, content, classification, agent_analysis, 
            confidence, page, issues, recommendations
        )
    
    def get_classified_data_for_page(self, page: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get data classifications organized by type for a specific page."""
        return self.classification_handler.get_classified_data_for_page(page)
    
    def update_data_classification(self, item_id: str, new_classification: DataClassification,
                                  updated_by: str = "user") -> Dict[str, Any]:
        """Update the classification of a data item."""
        return self.classification_handler.update_data_classification(item_id, new_classification, updated_by)
    
    # === AGENT INSIGHTS MANAGEMENT ===
    
    def add_agent_insight(self, agent_id: str, agent_name: str, insight_type: str,
                         title: str, description: str, confidence: ConfidenceLevel,
                         supporting_data: Dict[str, Any], page: str = "discovery",
                         actionable: bool = True, client_account_id: str = None,
                         engagement_id: str = None, flow_id: str = None) -> str:
        """Add a new insight from an agent (will be reviewed before presentation)."""
        return self.insight_handler.add_agent_insight(
            agent_id, agent_name, insight_type, title, description, 
            confidence, supporting_data, page, actionable,
            client_account_id, engagement_id, flow_id
        )
    
    def get_insights_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all insights for a specific page (reviewed and validated)."""
        # Get insights from handler
        page_insights = self.insight_handler.get_insights_for_page(page)
        
        # Apply presentation review to filter and improve insights
        if page_insights:
            try:
                # Use simplified presentation review without individual agent
                # This can be enhanced with CrewAI crews in the future
                logger.info(f"Applying simplified presentation review for {len(page_insights)} insights")
                
                # Basic filtering - remove low confidence insights
                reviewed_insights = []
                for insight in page_insights:
                    confidence_value = insight.get('confidence', 'medium')
                    if confidence_value in ['high', 'very_high'] or len(page_insights) <= 3:
                        reviewed_insights.append(insight)
                
                logger.info(f"Presentation review: {len(reviewed_insights)}/{len(page_insights)} insights approved for {page}")
                return reviewed_insights
                
            except Exception as e:
                logger.error(f"Error in presentation review: {e}")
                # Fall back to original insights if review fails
                pass
        
        return page_insights
    
    # === CROSS-PAGE CONTEXT MANAGEMENT ===
    
    def set_cross_page_context(self, key: str, value: Any, page_source: str) -> None:
        """Set context that should be preserved across pages."""
        self.context_handler.set_cross_page_context(key, value, page_source)
    
    def get_cross_page_context(self, key: str = None) -> Any:
        """Get cross-page context."""
        return self.context_handler.get_cross_page_context(key)
    
    def clear_cross_page_context(self, key: str = None) -> None:
        """Clear cross-page context."""
        self.context_handler.clear_cross_page_context(key)
    
    # === LEARNING AND FEEDBACK ===
    
    def _store_learning_experience(self, learning_context: Dict[str, Any]) -> None:
        """Store learning experience for agents."""
        self.context_handler.store_learning_experience(learning_context)
    
    def get_recent_learning_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning experiences for agent improvement."""
        return self.context_handler.get_recent_learning_experiences(limit)
    
    # === AGENT PROCESSING METHODS ===
    
    async def analyze_with_agents(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data using available agents and return intelligent insights."""
        return await self.analysis_handler.analyze_with_agents(analysis_request)
    
    async def process_with_agents(self, processing_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process data using agent-driven operations."""
        return await self.analysis_handler.process_with_agents(processing_request)
    

    
    # === UTILITY METHODS ===
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current agent-UI interaction status."""
        question_stats = self.question_handler.get_question_statistics()
        classification_stats = self.classification_handler.get_classification_statistics()
        insight_stats = self.insight_handler.get_insight_statistics()
        coordination_stats = self.context_handler.get_agent_coordination_summary()
        
        return {
            "questions": question_stats,
            "classifications": classification_stats,
            "insights": insight_stats,
            "coordination": coordination_stats,
            "storage": self.storage_manager.get_storage_statistics()
        }
    
    # === PERSISTENCE METHODS ===
    
    def _load_persistent_data(self) -> None:
        """Load persistent data from storage using handlers."""
        try:
            # Load data into handlers
            questions_data = self.storage_manager.load_questions()
            self.question_handler.load_questions(questions_data)
            
            classifications_data = self.storage_manager.load_classifications()
            self.classification_handler.load_classifications(classifications_data)
            
            insights_data = self.storage_manager.load_insights()
            self.insight_handler.load_insights(insights_data)
            
            context_data = self.storage_manager.load_context()
            self.context_handler.load_context_data(context_data)
            
            learning_data = self.storage_manager.load_learning_experiences()
            # Learning experiences are loaded into context handler
            
        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")

# Global instance for the application
agent_ui_bridge = AgentUIBridge() 