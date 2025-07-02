"""
Agent Communication Models
Data models for agent-UI communication.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

class QuestionType(Enum):
    """Types of questions agents can ask users."""
    FIELD_MAPPING = "field_mapping"
    DATA_CLASSIFICATION = "data_classification"
    APPLICATION_BOUNDARY = "application_boundary"
    DEPENDENCY_CLARIFICATION = "dependency_clarification"
    DEPENDENCY_VALIDATION = "dependency_validation"
    BUSINESS_CONTEXT = "business_context"
    QUALITY_VALIDATION = "quality_validation"
    STAKEHOLDER_PREFERENCE = "stakeholder_preference"
    RISK_ASSESSMENT = "risk_assessment"

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
    # Client context fields for multi-tenancy
    client_account_id: str = None
    engagement_id: str = None
    flow_id: str = None
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
    # Client context fields for multi-tenancy
    client_account_id: str = None
    engagement_id: str = None
    flow_id: str = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow() 