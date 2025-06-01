"""
Agent-UI Communication Bridge
Enables agents to communicate with users through the UI for clarifications, feedback, and iterative learning.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Types of questions agents can ask users."""
    FIELD_MAPPING = "field_mapping"
    DATA_CLASSIFICATION = "data_classification"
    APPLICATION_BOUNDARY = "application_boundary"
    DEPENDENCY_CLARIFICATION = "dependency_clarification"
    BUSINESS_CONTEXT = "business_context"
    QUALITY_VALIDATION = "quality_validation"
    STAKEHOLDER_PREFERENCE = "stakeholder_preference"

class ConfidenceLevel(Enum):
    """Agent confidence levels."""
    HIGH = "high"        # 80-100%
    MEDIUM = "medium"    # 60-79%
    LOW = "low"         # 40-59%
    UNCERTAIN = "uncertain"  # <40%

class DataClassification(Enum):
    """Data quality classifications."""
    GOOD_DATA = "good_data"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNUSABLE = "unusable"

@dataclass
class AgentQuestion:
    """Represents a question from an agent to the user."""
    id: str
    agent_id: str
    agent_name: str
    question_type: QuestionType
    page: str  # discovery page where question appears
    title: str
    question: str
    context: Dict[str, Any]  # Additional context data
    options: Optional[List[str]] = None  # For multiple choice questions
    confidence: Optional[ConfidenceLevel] = None
    priority: str = "medium"  # high, medium, low
    created_at: datetime = None
    answered_at: Optional[datetime] = None
    user_response: Optional[Any] = None
    is_resolved: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class DataItem:
    """Represents a piece of data with agent classification."""
    id: str
    data_type: str  # asset, application, field_mapping, etc.
    classification: DataClassification
    content: Dict[str, Any]
    agent_analysis: Dict[str, Any]
    confidence: ConfidenceLevel
    issues: List[str] = None
    recommendations: List[str] = None
    page: str = "discovery"
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []

@dataclass
class AgentInsight:
    """Represents an insight or discovery from an agent."""
    id: str
    agent_id: str
    agent_name: str
    insight_type: str
    title: str
    description: str
    confidence: ConfidenceLevel
    supporting_data: Dict[str, Any]
    actionable: bool = True
    page: str = "discovery"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class AgentUIBridge:
    """Manages communication between AI agents and the UI."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage files
        self.questions_file = self.data_dir / "agent_questions.json"
        self.classifications_file = self.data_dir / "data_classifications.json"
        self.insights_file = self.data_dir / "agent_insights.json"
        self.context_file = self.data_dir / "agent_context.json"
        
        # In-memory storage
        self.pending_questions: Dict[str, AgentQuestion] = {}
        self.data_classifications: Dict[str, DataItem] = {}
        self.agent_insights: Dict[str, AgentInsight] = {}
        self.cross_page_context: Dict[str, Any] = {}
        
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
        question_id = str(uuid.uuid4())
        
        agent_question = AgentQuestion(
            id=question_id,
            agent_id=agent_id,
            agent_name=agent_name,
            question_type=question_type,
            page=page,
            title=title,
            question=question,
            context=context,
            options=options,
            confidence=confidence,
            priority=priority
        )
        
        self.pending_questions[question_id] = agent_question
        self._save_questions()
        
        logger.info(f"Agent {agent_name} added question: {title}")
        return question_id
    
    def answer_agent_question(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Process user response to an agent question."""
        if question_id not in self.pending_questions:
            return {"success": False, "error": "Question not found"}
        
        question = self.pending_questions[question_id]
        question.user_response = response
        question.answered_at = datetime.utcnow()
        question.is_resolved = True
        
        # Store the learning from this interaction
        learning_context = {
            "question_type": question.question_type.value,
            "agent_id": question.agent_id,
            "page": question.page,
            "context": question.context,
            "user_response": response,
            "timestamp": question.answered_at.isoformat()
        }
        
        self._store_learning_experience(learning_context)
        self._save_questions()
        
        logger.info(f"User answered question {question_id} from {question.agent_name}")
        
        return {
            "success": True,
            "question": asdict(question),
            "learning_stored": True
        }
    
    def get_questions_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all pending questions for a specific page."""
        page_questions = [
            asdict(q) for q in self.pending_questions.values()
            if q.page == page and not q.is_resolved
        ]
        
        # Sort by priority and creation time
        priority_order = {"high": 3, "medium": 2, "low": 1}
        page_questions.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['created_at']),
            reverse=True
        )
        
        return page_questions
    
    # === DATA CLASSIFICATION MANAGEMENT ===
    
    def classify_data_item(self, item_id: str, data_type: str, content: Dict[str, Any],
                          classification: DataClassification, agent_analysis: Dict[str, Any],
                          confidence: ConfidenceLevel, page: str = "discovery",
                          issues: List[str] = None, recommendations: List[str] = None) -> None:
        """Classify a data item based on agent analysis."""
        
        data_item = DataItem(
            id=item_id,
            data_type=data_type,
            classification=classification,
            content=content,
            agent_analysis=agent_analysis,
            confidence=confidence,
            issues=issues or [],
            recommendations=recommendations or [],
            page=page
        )
        
        self.data_classifications[item_id] = data_item
        self._save_classifications()
        
        logger.info(f"Classified {data_type} item {item_id} as {classification.value}")
    
    def get_classified_data_for_page(self, page: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get data classifications organized by type for a specific page."""
        page_items = [
            asdict(item) for item in self.data_classifications.values()
            if item.page == page
        ]
        
        # Organize by classification
        classifications = {
            "good_data": [],
            "needs_clarification": [],
            "unusable": []
        }
        
        for item in page_items:
            classification_key = item['classification']
            classifications[classification_key].append(item)
        
        return classifications
    
    def update_data_classification(self, item_id: str, new_classification: DataClassification,
                                  updated_by: str = "user") -> Dict[str, Any]:
        """Update the classification of a data item."""
        if item_id not in self.data_classifications:
            return {"success": False, "error": "Data item not found"}
        
        old_classification = self.data_classifications[item_id].classification
        self.data_classifications[item_id].classification = new_classification
        
        # Store learning from classification change
        learning_context = {
            "item_id": item_id,
            "old_classification": old_classification.value,
            "new_classification": new_classification.value,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._store_learning_experience(learning_context)
        self._save_classifications()
        
        return {"success": True, "classification_updated": True}
    
    # === AGENT INSIGHTS MANAGEMENT ===
    
    def add_agent_insight(self, agent_id: str, agent_name: str, insight_type: str,
                         title: str, description: str, confidence: ConfidenceLevel,
                         supporting_data: Dict[str, Any], page: str = "discovery",
                         actionable: bool = True) -> str:
        """Add a new insight from an agent."""
        insight_id = str(uuid.uuid4())
        
        insight = AgentInsight(
            id=insight_id,
            agent_id=agent_id,
            agent_name=agent_name,
            insight_type=insight_type,
            title=title,
            description=description,
            confidence=confidence,
            supporting_data=supporting_data,
            actionable=actionable,
            page=page
        )
        
        self.agent_insights[insight_id] = insight
        self._save_insights()
        
        logger.info(f"Agent {agent_name} added insight: {title}")
        return insight_id
    
    def get_insights_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all insights for a specific page."""
        page_insights = [
            asdict(insight) for insight in self.agent_insights.values()
            if insight.page == page
        ]
        
        # Sort by confidence and creation time
        confidence_order = {"high": 4, "medium": 3, "low": 2, "uncertain": 1}
        page_insights.sort(
            key=lambda x: (confidence_order.get(x['confidence'], 0), x['created_at']),
            reverse=True
        )
        
        return page_insights
    
    # === CROSS-PAGE CONTEXT MANAGEMENT ===
    
    def set_cross_page_context(self, key: str, value: Any, page_source: str) -> None:
        """Set context that should be preserved across pages."""
        self.cross_page_context[key] = {
            "value": value,
            "page_source": page_source,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._save_context()
        
        logger.info(f"Set cross-page context {key} from {page_source}")
    
    def get_cross_page_context(self, key: str = None) -> Any:
        """Get cross-page context."""
        if key:
            return self.cross_page_context.get(key, {}).get("value")
        return self.cross_page_context
    
    def clear_cross_page_context(self, key: str = None) -> None:
        """Clear cross-page context."""
        if key and key in self.cross_page_context:
            del self.cross_page_context[key]
        else:
            self.cross_page_context.clear()
        self._save_context()
    
    # === LEARNING AND FEEDBACK ===
    
    def _store_learning_experience(self, learning_context: Dict[str, Any]) -> None:
        """Store learning experience for agents."""
        experience_file = self.data_dir / "agent_learning_experiences.json"
        
        try:
            if experience_file.exists():
                with open(experience_file, 'r') as f:
                    experiences = json.load(f)
            else:
                experiences = []
            
            experiences.append(learning_context)
            
            # Keep only recent experiences (last 1000)
            if len(experiences) > 1000:
                experiences = experiences[-1000:]
            
            with open(experience_file, 'w') as f:
                json.dump(experiences, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing learning experience: {e}")
    
    def get_recent_learning_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning experiences for agent improvement."""
        experience_file = self.data_dir / "agent_learning_experiences.json"
        
        try:
            if experience_file.exists():
                with open(experience_file, 'r') as f:
                    experiences = json.load(f)
                return experiences[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error loading learning experiences: {e}")
            return []
    
    # === UTILITY METHODS ===
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current agent-UI interaction status."""
        return {
            "pending_questions": len([q for q in self.pending_questions.values() if not q.is_resolved]),
            "total_questions": len(self.pending_questions),
            "classified_items": len(self.data_classifications),
            "agent_insights": len(self.agent_insights),
            "cross_page_context_items": len(self.cross_page_context),
            "classifications_by_type": {
                "good_data": len([item for item in self.data_classifications.values() 
                                if item.classification == DataClassification.GOOD_DATA]),
                "needs_clarification": len([item for item in self.data_classifications.values() 
                                          if item.classification == DataClassification.NEEDS_CLARIFICATION]),
                "unusable": len([item for item in self.data_classifications.values() 
                               if item.classification == DataClassification.UNUSABLE])
            }
        }
    
    # === PERSISTENCE METHODS ===
    
    def _load_persistent_data(self) -> None:
        """Load persistent data from storage."""
        try:
            # Load questions
            if self.questions_file.exists():
                with open(self.questions_file, 'r') as f:
                    questions_data = json.load(f)
                    for q_data in questions_data:
                        q_data['question_type'] = QuestionType(q_data['question_type'])
                        if q_data.get('confidence'):
                            q_data['confidence'] = ConfidenceLevel(q_data['confidence'])
                        q_data['created_at'] = datetime.fromisoformat(q_data['created_at'])
                        if q_data.get('answered_at'):
                            q_data['answered_at'] = datetime.fromisoformat(q_data['answered_at'])
                        
                        question = AgentQuestion(**q_data)
                        self.pending_questions[question.id] = question
            
            # Load classifications
            if self.classifications_file.exists():
                with open(self.classifications_file, 'r') as f:
                    classifications_data = json.load(f)
                    for c_data in classifications_data:
                        c_data['classification'] = DataClassification(c_data['classification'])
                        c_data['confidence'] = ConfidenceLevel(c_data['confidence'])
                        
                        data_item = DataItem(**c_data)
                        self.data_classifications[data_item.id] = data_item
            
            # Load insights
            if self.insights_file.exists():
                with open(self.insights_file, 'r') as f:
                    insights_data = json.load(f)
                    for i_data in insights_data:
                        i_data['confidence'] = ConfidenceLevel(i_data['confidence'])
                        i_data['created_at'] = datetime.fromisoformat(i_data['created_at'])
                        
                        insight = AgentInsight(**i_data)
                        self.agent_insights[insight.id] = insight
            
            # Load context
            if self.context_file.exists():
                with open(self.context_file, 'r') as f:
                    self.cross_page_context = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")
    
    def _save_questions(self) -> None:
        """Save questions to persistent storage."""
        try:
            questions_data = []
            for question in self.pending_questions.values():
                q_dict = asdict(question)
                q_dict['question_type'] = question.question_type.value
                if question.confidence:
                    q_dict['confidence'] = question.confidence.value
                q_dict['created_at'] = question.created_at.isoformat()
                if question.answered_at:
                    q_dict['answered_at'] = question.answered_at.isoformat()
                questions_data.append(q_dict)
            
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving questions: {e}")
    
    def _save_classifications(self) -> None:
        """Save classifications to persistent storage."""
        try:
            classifications_data = []
            for data_item in self.data_classifications.values():
                c_dict = asdict(data_item)
                c_dict['classification'] = data_item.classification.value
                c_dict['confidence'] = data_item.confidence.value
                classifications_data.append(c_dict)
            
            with open(self.classifications_file, 'w') as f:
                json.dump(classifications_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving classifications: {e}")
    
    def _save_insights(self) -> None:
        """Save insights to persistent storage."""
        try:
            insights_data = []
            for insight in self.agent_insights.values():
                i_dict = asdict(insight)
                i_dict['confidence'] = insight.confidence.value
                i_dict['created_at'] = insight.created_at.isoformat()
                insights_data.append(i_dict)
            
            with open(self.insights_file, 'w') as f:
                json.dump(insights_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
    
    def _save_context(self) -> None:
        """Save cross-page context to persistent storage."""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(self.cross_page_context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {e}")

# Global instance for the application
agent_ui_bridge = AgentUIBridge() 