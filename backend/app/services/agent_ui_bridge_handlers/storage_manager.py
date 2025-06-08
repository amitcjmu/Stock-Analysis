"""
Storage Manager for Agent-UI Bridge
Manages data persistence and storage operations.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages storage operations for agent-UI communication data."""
    
    def __init__(self, storage_path: str = "/tmp/agent_ui_bridge"):
        self.storage_path = storage_path
        self.ensure_storage_directory()
        
        # In-memory caches
        self._questions_cache = {}
        self._classifications_cache = {}
        self._insights_cache = {}
        self._context_cache = {}
        self._learning_experiences = []
    
    def ensure_storage_directory(self) -> None:
        """Ensure storage directory exists."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create storage directory {self.storage_path}: {e}")
            # Fall back to temp directory
            self.storage_path = "/tmp"
    
    def save_questions(self, questions: Dict[str, Any]) -> bool:
        """Save questions to storage."""
        try:
            self._questions_cache = questions.copy()
            
            # Convert questions to serializable format
            serializable_questions = {}
            for qid, question in questions.items():
                if hasattr(question, '__dict__'):
                    # Convert dataclass to dict
                    q_dict = question.__dict__.copy()
                    # Convert datetime objects to ISO strings
                    if q_dict.get('created_at'):
                        q_dict['created_at'] = q_dict['created_at'].isoformat()
                    if q_dict.get('answered_at'):
                        q_dict['answered_at'] = q_dict['answered_at'].isoformat()
                    # Convert enums to strings
                    if hasattr(q_dict.get('question_type'), 'value'):
                        q_dict['question_type'] = q_dict['question_type'].value
                    if hasattr(q_dict.get('confidence'), 'value'):
                        q_dict['confidence'] = q_dict['confidence'].value
                    serializable_questions[qid] = q_dict
                else:
                    serializable_questions[qid] = question
            
            file_path = os.path.join(self.storage_path, "agent_questions.json")
            with open(file_path, 'w') as f:
                json.dump(serializable_questions, f, indent=2)
            
            logger.info(f"Saved {len(questions)} questions to storage")
            return True
            
        except Exception as e:
            logger.error(f"Error saving questions: {e}")
            return False
    
    def load_questions(self) -> Dict[str, Any]:
        """Load questions from storage."""
        try:
            file_path = os.path.join(self.storage_path, "agent_questions.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    questions = json.load(f)
                self._questions_cache = questions
                logger.info(f"Loaded {len(questions)} questions from storage")
                return questions
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
        
        return {}
    
    def save_classifications(self, classifications: Dict[str, Any]) -> bool:
        """Save data classifications to storage."""
        try:
            self._classifications_cache = classifications.copy()
            
            # Convert classifications to serializable format
            serializable_classifications = {}
            for item_id, item in classifications.items():
                if hasattr(item, '__dict__'):
                    # Convert dataclass to dict
                    item_dict = item.__dict__.copy()
                    # Convert datetime objects to ISO strings
                    if item_dict.get('created_at'):
                        item_dict['created_at'] = item_dict['created_at'].isoformat()
                    if item_dict.get('updated_at'):
                        item_dict['updated_at'] = item_dict['updated_at'].isoformat()
                    # Convert enums to strings
                    if hasattr(item_dict.get('classification'), 'value'):
                        item_dict['classification'] = item_dict['classification'].value
                    if hasattr(item_dict.get('confidence'), 'value'):
                        item_dict['confidence'] = item_dict['confidence'].value
                    serializable_classifications[item_id] = item_dict
                else:
                    serializable_classifications[item_id] = item
            
            file_path = os.path.join(self.storage_path, "data_classifications.json")
            with open(file_path, 'w') as f:
                json.dump(serializable_classifications, f, indent=2)
            
            logger.info(f"Saved {len(classifications)} classifications to storage")
            return True
            
        except Exception as e:
            logger.error(f"Error saving classifications: {e}")
            return False
    
    def load_classifications(self) -> Dict[str, Any]:
        """Load data classifications from storage."""
        try:
            file_path = os.path.join(self.storage_path, "data_classifications.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    classifications = json.load(f)
                self._classifications_cache = classifications
                logger.info(f"Loaded {len(classifications)} classifications from storage")
                return classifications
        except Exception as e:
            logger.error(f"Error loading classifications: {e}")
        
        return {}
    
    def save_insights(self, insights: Dict[str, Any]) -> bool:
        """Save agent insights to storage."""
        try:
            self._insights_cache = insights.copy()
            
            # Convert insights to serializable format
            serializable_insights = {}
            for insight_id, insight in insights.items():
                if hasattr(insight, '__dict__'):
                    # Convert dataclass to dict
                    insight_dict = insight.__dict__.copy()
                    # Convert datetime objects to ISO strings
                    if insight_dict.get('created_at'):
                        insight_dict['created_at'] = insight_dict['created_at'].isoformat()
                    # Convert enums to strings
                    if hasattr(insight_dict.get('confidence'), 'value'):
                        insight_dict['confidence'] = insight_dict['confidence'].value
                    serializable_insights[insight_id] = insight_dict
                else:
                    serializable_insights[insight_id] = insight
            
            file_path = os.path.join(self.storage_path, "agent_insights.json")
            with open(file_path, 'w') as f:
                json.dump(serializable_insights, f, indent=2)
            
            logger.info(f"Saved {len(insights)} insights to storage")
            return True
            
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
            return False
    
    def load_insights(self) -> Dict[str, Any]:
        """Load agent insights from storage."""
        try:
            file_path = os.path.join(self.storage_path, "agent_insights.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    insights = json.load(f)
                self._insights_cache = insights
                logger.info(f"Loaded {len(insights)} insights from storage")
                return insights
        except Exception as e:
            logger.error(f"Error loading insights: {e}")
        
        return {}
    
    def save_context(self, context_data: Dict[str, Any]) -> bool:
        """Save cross-page context and agent states."""
        try:
            self._context_cache = context_data.copy()
            
            file_path = os.path.join(self.storage_path, "agent_context.json")
            with open(file_path, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            logger.info("Saved agent context to storage")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            return False
    
    def load_context(self) -> Dict[str, Any]:
        """Load cross-page context and agent states."""
        try:
            file_path = os.path.join(self.storage_path, "agent_context.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    context_data = json.load(f)
                self._context_cache = context_data
                logger.info("Loaded agent context from storage")
                return context_data
        except Exception as e:
            logger.error(f"Error loading context: {e}")
        
        return {
            "cross_page_context": {},
            "agent_states": {},
            "learning_experiences": []
        }
    
    def store_learning_experience(self, experience: Dict[str, Any]) -> bool:
        """Store a learning experience."""
        try:
            experience["stored_at"] = datetime.utcnow().isoformat()
            self._learning_experiences.append(experience)
            
            # Keep only recent experiences (last 1000)
            if len(self._learning_experiences) > 1000:
                self._learning_experiences = self._learning_experiences[-1000:]
            
            # Save to file periodically (every 10 experiences)
            if len(self._learning_experiences) % 10 == 0:
                self._save_learning_experiences()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing learning experience: {e}")
            return False
    
    def _save_learning_experiences(self) -> bool:
        """Save learning experiences to file."""
        try:
            file_path = os.path.join(self.storage_path, "learning_experiences.json")
            with open(file_path, 'w') as f:
                json.dump(self._learning_experiences, f, indent=2)
            
            logger.info(f"Saved {len(self._learning_experiences)} learning experiences")
            return True
            
        except Exception as e:
            logger.error(f"Error saving learning experiences: {e}")
            return False
    
    def load_learning_experiences(self) -> List[Dict[str, Any]]:
        """Load learning experiences from storage."""
        try:
            file_path = os.path.join(self.storage_path, "learning_experiences.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    experiences = json.load(f)
                self._learning_experiences = experiences
                logger.info(f"Loaded {len(experiences)} learning experiences from storage")
                return experiences
        except Exception as e:
            logger.error(f"Error loading learning experiences: {e}")
        
        return []
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        return {
            "questions_count": len(self._questions_cache),
            "classifications_count": len(self._classifications_cache),
            "insights_count": len(self._insights_cache),
            "context_items": len(self._context_cache.get("cross_page_context", {})),
            "agent_states": len(self._context_cache.get("agent_states", {})),
            "learning_experiences": len(self._learning_experiences),
            "storage_path": self.storage_path
        }
    
    def clear_all_data(self) -> bool:
        """Clear all stored data."""
        try:
            self._questions_cache.clear()
            self._classifications_cache.clear()
            self._insights_cache.clear()
            self._context_cache.clear()
            self._learning_experiences.clear()
            
            # Remove files
            files_to_remove = [
                "agent_questions.json",
                "data_classifications.json", 
                "agent_insights.json",
                "agent_context.json",
                "learning_experiences.json"
            ]
            
            for filename in files_to_remove:
                file_path = os.path.join(self.storage_path, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info("Cleared all agent UI bridge data")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for backup or transfer."""
        return {
            "questions": self._questions_cache,
            "classifications": self._classifications_cache,
            "insights": self._insights_cache,
            "context": self._context_cache,
            "learning_experiences": self._learning_experiences,
            "export_timestamp": datetime.utcnow().isoformat()
        }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup or transfer."""
        try:
            if "questions" in data:
                self._questions_cache = data["questions"]
                self.save_questions(self._questions_cache)
            
            if "classifications" in data:
                self._classifications_cache = data["classifications"]
                self.save_classifications(self._classifications_cache)
            
            if "insights" in data:
                self._insights_cache = data["insights"]
                self.save_insights(self._insights_cache)
            
            if "context" in data:
                self._context_cache = data["context"]
                self.save_context(self._context_cache)
            
            if "learning_experiences" in data:
                self._learning_experiences = data["learning_experiences"]
                self._save_learning_experiences()
            
            logger.info("Successfully imported agent UI bridge data")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False

# Instantiate storage managers for different data types
classification_storage = StorageManager(storage_path="/tmp/agent_ui_bridge/classifications")
question_storage = StorageManager(storage_path="/tmp/agent_ui_bridge/questions")
insight_storage = StorageManager(storage_path="/tmp/agent_ui_bridge/insights")
context_storage = StorageManager(storage_path="/tmp/agent_ui_bridge/context")

# Default storage manager
storage_manager = StorageManager() 