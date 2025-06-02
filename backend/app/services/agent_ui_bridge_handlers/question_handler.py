"""
Question Handler for Agent-UI Communication
Manages agent questions and user responses.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from ..models.agent_communication import AgentQuestion, QuestionType, ConfidenceLevel

logger = logging.getLogger(__name__)

class QuestionHandler:
    """Handles agent questions and user responses."""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.agent_questions: Dict[str, AgentQuestion] = {}
    
    def add_agent_question(self, agent_id: str, agent_name: str, 
                          question_type: QuestionType, page: str,
                          title: str, question: str, context: Dict[str, Any],
                          options: Optional[List[str]] = None,
                          confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                          priority: str = "medium") -> str:
        """Add a new question from an agent (with duplicate filtering)."""
        question_id = str(uuid.uuid4())
        
        # Enhanced duplicate checking - check both pending and recently resolved questions
        existing_questions = [
            existing for existing in self.agent_questions.values()
            if (existing.page == page and existing.agent_id == agent_id and 
                (existing.title == title or existing.question == question) and
                # Don't re-add if recently resolved (within last hour)
                (not existing.is_resolved or 
                 (existing.answered_at and 
                  (datetime.utcnow() - existing.answered_at).total_seconds() < 3600)))
        ]
        
        if existing_questions:
            logger.info(f"Duplicate question detected and filtered out: {title} from {agent_name}")
            return existing_questions[0].id  # Return existing question ID
        
        # Create new question
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
        
        self.agent_questions[question_id] = agent_question
        self.storage_manager.save_questions(self.agent_questions)
        
        logger.info(f"Agent {agent_name} added question: {title} (page: {page})")
        return question_id
    
    def answer_agent_question(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Process user response to an agent question."""
        if question_id not in self.agent_questions:
            return {"success": False, "error": "Question not found"}
        
        question = self.agent_questions[question_id]
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
        
        self.storage_manager.store_learning_experience(learning_context)
        self.storage_manager.save_questions(self.agent_questions)
        
        logger.info(f"User answered question {question_id} from {question.agent_name}")
        
        return {
            "success": True,
            "question": asdict(question),
            "learning_stored": True
        }
    
    def get_questions_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all pending questions for a specific page."""
        page_questions = [
            asdict(q) for q in self.agent_questions.values()
            if q.page == page and not q.is_resolved
        ]
        
        # Sort by priority and creation time
        priority_order = {"high": 3, "medium": 2, "low": 1}
        page_questions.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['created_at']),
            reverse=True
        )
        
        return page_questions
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Get all questions across all pages."""
        return [asdict(q) for q in self.agent_questions.values()]
    
    def clear_resolved_questions(self, page: str = None) -> int:
        """Clear resolved questions for a page or all pages."""
        initial_count = len(self.agent_questions)
        
        if page:
            # Clear resolved questions for specific page
            self.agent_questions = {
                qid: q for qid, q in self.agent_questions.items()
                if not (q.is_resolved and q.page == page)
            }
        else:
            # Clear all resolved questions
            self.agent_questions = {
                qid: q for qid, q in self.agent_questions.items()
                if not q.is_resolved
            }
        
        cleared_count = initial_count - len(self.agent_questions)
        
        if cleared_count > 0:
            self.storage_manager.save_questions(self.agent_questions)
            logger.info(f"Cleared {cleared_count} resolved questions")
        
        return cleared_count
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get statistics about questions."""
        total_questions = len(self.agent_questions)
        resolved_questions = sum(1 for q in self.agent_questions.values() if q.is_resolved)
        
        # Group by page
        by_page = {}
        for q in self.agent_questions.values():
            if q.page not in by_page:
                by_page[q.page] = {"total": 0, "resolved": 0, "pending": 0}
            by_page[q.page]["total"] += 1
            if q.is_resolved:
                by_page[q.page]["resolved"] += 1
            else:
                by_page[q.page]["pending"] += 1
        
        # Group by priority
        by_priority = {"high": 0, "medium": 0, "low": 0}
        for q in self.agent_questions.values():
            if not q.is_resolved:
                by_priority[q.priority] = by_priority.get(q.priority, 0) + 1
        
        return {
            "total_questions": total_questions,
            "resolved_questions": resolved_questions,
            "pending_questions": total_questions - resolved_questions,
            "by_page": by_page,
            "pending_by_priority": by_priority,
            "resolution_rate": resolved_questions / total_questions if total_questions > 0 else 0
        }
    
    def load_questions(self, questions_data: Dict[str, Any]) -> None:
        """Load questions from storage."""
        self.agent_questions.clear()
        for qid, q_data in questions_data.items():
            # Convert dict back to AgentQuestion
            question = AgentQuestion(
                id=q_data['id'],
                agent_id=q_data['agent_id'],
                agent_name=q_data['agent_name'],
                question_type=QuestionType(q_data['question_type']),
                page=q_data['page'],
                title=q_data['title'],
                question=q_data['question'],
                context=q_data['context'],
                options=q_data.get('options'),
                confidence=ConfidenceLevel(q_data['confidence']) if q_data.get('confidence') else None,
                priority=q_data.get('priority', 'medium'),
                created_at=datetime.fromisoformat(q_data['created_at']),
                answered_at=datetime.fromisoformat(q_data['answered_at']) if q_data.get('answered_at') else None,
                user_response=q_data.get('user_response'),
                is_resolved=q_data.get('is_resolved', False)
            )
            self.agent_questions[qid] = question 