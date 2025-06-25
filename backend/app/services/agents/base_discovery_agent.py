"""
Base Discovery Agent - Foundation for all Discovery Flow agents
Provides common functionality, confidence scoring, and agent-UI integration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class AgentClarificationRequest(BaseModel):
    """Request for user clarification through Agent-UI-monitor panel"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    options: List[Dict[str, str]]  # [{"value": "option1", "label": "Display Text"}]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium")  # low, medium, high, critical
    clarification_type: str = Field(default="mapping")  # mapping, validation, bulk_operation

class AgentInsight(BaseModel):
    """Agent insight for display in Agent-UI-monitor panel"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=100.0)
    category: str  # mapping, quality, anomaly, recommendation
    actionable: bool = False
    action_items: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    """Standard result format for all Discovery agents"""
    agent_name: str
    execution_time: float
    confidence_score: float = Field(ge=0.0, le=100.0)
    status: str  # success, partial, failed
    data: Dict[str, Any] = Field(default_factory=dict)
    clarifications_requested: List[AgentClarificationRequest] = Field(default_factory=list)
    insights_generated: List[AgentInsight] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseDiscoveryAgent(ABC):
    """
    Base class for all Discovery Flow agents
    Provides common functionality for confidence scoring, clarifications, and insights
    """
    
    def __init__(self, agent_name: str, agent_id: str = None):
        self.agent_name = agent_name
        self.agent_id = agent_id or f"{agent_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"agents.{self.agent_name.lower().replace(' ', '_')}")
        self.clarifications_pending: List[AgentClarificationRequest] = []
        self.insights_generated: List[AgentInsight] = []
        self.confidence_factors: Dict[str, float] = {}
        
    @abstractmethod
    def get_role(self) -> str:
        """Return the agent's role description"""
        pass
    
    @abstractmethod
    def get_goal(self) -> str:
        """Return the agent's goal description"""
        pass
    
    @abstractmethod
    def get_backstory(self) -> str:
        """Return the agent's backstory"""
        pass
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute the agent's main functionality
        
        Args:
            data: Input data for processing
            context: Additional context (flow_id, session_id, etc.)
            
        Returns:
            AgentResult with processing results, confidence, clarifications, and insights
        """
        pass
    
    def calculate_confidence_score(self, factors: Dict[str, float] = None) -> float:
        """
        Calculate overall confidence score based on various factors
        
        Args:
            factors: Dict of confidence factors with weights
            
        Returns:
            Confidence score between 0-100
        """
        if factors:
            self.confidence_factors.update(factors)
            
        if not self.confidence_factors:
            return 50.0  # Default neutral confidence
            
        # Weighted average of confidence factors
        total_weight = sum(self.confidence_factors.values())
        if total_weight == 0:
            return 50.0
            
        weighted_score = sum(score * weight for score, weight in self.confidence_factors.items())
        return min(100.0, max(0.0, weighted_score / total_weight))
    
    def add_clarification_request(self, 
                                question_text: str, 
                                options: List[Dict[str, str]], 
                                context: Dict[str, Any] = None,
                                priority: str = "medium",
                                clarification_type: str = "mapping") -> str:
        """
        Add a clarification request for the Agent-UI-monitor panel
        
        Args:
            question_text: The question to ask the user
            options: List of answer options
            context: Additional context for the question
            priority: Question priority level
            clarification_type: Type of clarification needed
            
        Returns:
            question_id for tracking
        """
        clarification = AgentClarificationRequest(
            question_text=question_text,
            options=options,
            context=context or {},
            priority=priority,
            clarification_type=clarification_type
        )
        
        self.clarifications_pending.append(clarification)
        self.logger.info(f"📝 Clarification requested: {question_text[:50]}...")
        return clarification.question_id
    
    def add_insight(self, 
                   title: str, 
                   description: str, 
                   confidence_score: float,
                   category: str = "recommendation",
                   actionable: bool = False,
                   action_items: List[str] = None) -> str:
        """
        Add an insight for the Agent-UI-monitor panel
        
        Args:
            title: Insight title
            description: Detailed description
            confidence_score: Confidence in this insight (0-100)
            category: Insight category
            actionable: Whether this insight requires action
            action_items: List of actionable items
            
        Returns:
            insight_id for tracking
        """
        insight = AgentInsight(
            title=title,
            description=description,
            confidence_score=confidence_score,
            category=category,
            actionable=actionable,
            action_items=action_items or []
        )
        
        self.insights_generated.append(insight)
        self.logger.info(f"💡 Insight generated: {title}")
        return insight.insight_id
    
    def process_clarification_response(self, question_id: str, response: Dict[str, Any]) -> bool:
        """
        Process user response to clarification request
        
        Args:
            question_id: ID of the question being answered
            response: User's response data
            
        Returns:
            True if response was processed successfully
        """
        for clarification in self.clarifications_pending:
            if clarification.question_id == question_id:
                self.logger.info(f"✅ Clarification response received for: {clarification.question_text[:50]}...")
                # Remove from pending list
                self.clarifications_pending.remove(clarification)
                return True
                
        self.logger.warning(f"⚠️ No pending clarification found for question_id: {question_id}")
        return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current agent status for monitoring
        
        Returns:
            Status dictionary with agent information
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "role": self.get_role(),
            "pending_clarifications": len(self.clarifications_pending),
            "insights_generated": len(self.insights_generated),
            "current_confidence": self.calculate_confidence_score(),
            "confidence_factors": self.confidence_factors,
            "status": "active"
        }
    
    def reset_agent_state(self):
        """Reset agent state for new execution"""
        self.clarifications_pending.clear()
        self.insights_generated.clear()
        self.confidence_factors.clear()
        self.logger.info(f"🔄 Agent state reset: {self.agent_name}")
    
    def _create_result(self, 
                      execution_time: float,
                      confidence_score: float,
                      status: str,
                      data: Dict[str, Any],
                      errors: List[str] = None,
                      warnings: List[str] = None,
                      metadata: Dict[str, Any] = None) -> AgentResult:
        """
        Create standardized agent result
        
        Args:
            execution_time: Time taken for execution
            confidence_score: Overall confidence score
            status: Execution status
            data: Result data
            errors: List of errors encountered
            warnings: List of warnings
            metadata: Additional metadata
            
        Returns:
            AgentResult object
        """
        return AgentResult(
            agent_name=self.agent_name,
            execution_time=execution_time,
            confidence_score=confidence_score,
            status=status,
            data=data,
            clarifications_requested=self.clarifications_pending.copy(),
            insights_generated=self.insights_generated.copy(),
            errors=errors or [],
            warnings=warnings or [],
            metadata=metadata or {}
        ) 