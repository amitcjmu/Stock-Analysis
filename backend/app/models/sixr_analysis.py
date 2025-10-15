"""
6R Analysis models for migration strategy analysis and recommendations.
"""

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        Enum,
        Float,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = (
        Float
    ) = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from app.core.database import Base
    from app.models.asset import SixRStrategy
    from app.schemas.sixr_analysis import AnalysisStatus, ApplicationType, QuestionType
except ImportError:
    Base = object

    # Define enums locally if schemas not available

    class AnalysisStatus(str, enum.Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
        REQUIRES_INPUT = "requires_input"

    class QuestionType(str, enum.Enum):
        TEXT = "text"
        SELECT = "select"
        MULTISELECT = "multiselect"
        FILE_UPLOAD = "file_upload"
        BOOLEAN = "boolean"
        NUMERIC = "numeric"

    class ApplicationType(str, enum.Enum):
        CUSTOM = "custom"
        COTS = "cots"
        HYBRID = "hybrid"


class SixRAnalysis(Base):
    """Main 6R analysis model."""

    __tablename__ = "sixr_analyses"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    migration_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("migrations.id"), nullable=True
    )

    # Multi-tenant isolation
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Analysis metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(
        Enum(
            AnalysisStatus,
            name="analysis_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    priority = Column(Integer, default=3)  # 1-5 scale

    # Application data
    application_ids = Column(JSON)  # List of application IDs being analyzed
    application_data = Column(JSON)  # Cached application data for analysis

    # Analysis progress
    current_iteration = Column(Integer, default=1)
    progress_percentage = Column(Float, default=0.0)
    estimated_completion = Column(DateTime(timezone=True))

    # Results
    final_recommendation = Column(
        Enum(
            SixRStrategy,
            name="sixr_strategy",
            values_callable=lambda x: [e.value for e in x],
        )
    )
    confidence_score = Column(Float)  # 0-1 confidence in final recommendation

    # Metadata
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Analysis configuration
    analysis_config = Column(JSON)  # Configuration options for analysis

    # Relationships
    migration = relationship("Migration", back_populates="sixr_analyses")
    parameters = relationship(
        "SixRAnalysisParameters",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    iterations = relationship(
        "SixRIteration", back_populates="analysis", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "SixRRecommendation", back_populates="analysis", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<SixRAnalysis(id={self.id}, name='{self.name}', status='{self.status}')>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status == AnalysisStatus.COMPLETED

    @property
    def current_parameters(self) -> Optional["SixRAnalysisParameters"]:
        """Get current iteration parameters."""
        if self.parameters:
            return max(self.parameters, key=lambda p: p.iteration_number)
        return None

    @property
    def latest_recommendation(self) -> Optional["SixRRecommendation"]:
        """Get latest recommendation."""
        if self.recommendations:
            return max(self.recommendations, key=lambda r: r.iteration_number)
        return None

    def get_iteration_count(self) -> int:
        """Get total number of iterations."""
        return len(self.iterations) if self.iterations else 0

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get analysis progress summary."""
        return {
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "current_iteration": self.current_iteration,
            "total_iterations": self.get_iteration_count(),
            "estimated_completion": self.estimated_completion,
            "confidence_score": self.confidence_score,
        }


class SixRIteration(Base):
    """6R analysis iteration model for tracking refinement cycles."""

    __tablename__ = "sixr_iterations"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("sixr_analyses.id"), nullable=False
    )
    iteration_number = Column(Integer, nullable=False)

    # Iteration metadata
    iteration_name = Column(String(255))
    iteration_reason = Column(Text)  # Why this iteration was created
    stakeholder_feedback = Column(Text)  # Feedback that triggered iteration

    # Parameter changes
    parameter_changes = Column(JSON)  # Changes from previous iteration

    # Question responses
    question_responses = Column(JSON)  # Responses to qualifying questions

    # Iteration results
    recommendation_data = Column(JSON)  # Recommendation for this iteration
    confidence_score = Column(Float)  # Confidence in this iteration's recommendation

    # Analysis metadata
    analysis_duration = Column(Float)  # Time taken for analysis (seconds)
    agent_insights = Column(JSON)  # Insights from AI agents

    # Status tracking
    status = Column(
        String(20), default="pending"
    )  # pending, in_progress, completed, failed
    error_details = Column(JSON)  # Error information if iteration failed

    # Audit fields
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    analysis = relationship("SixRAnalysis", back_populates="iterations")

    def __repr__(self):
        return f"<SixRIteration(id={self.id}, analysis_id={self.analysis_id}, iteration={self.iteration_number})>"

    @property
    def is_completed(self) -> bool:
        """Check if iteration is completed."""
        return self.status == "completed"

    def get_changes_summary(self) -> Dict[str, Any]:
        """Get summary of changes in this iteration."""
        if not self.parameter_changes:
            return {}

        return {
            "total_changes": len(self.parameter_changes),
            "parameter_changes": self.parameter_changes,
            "iteration_reason": self.iteration_reason,
            "confidence_impact": self.confidence_score,
        }

    def mark_completed(self, recommendation_data: Dict[str, Any], confidence: float):
        """Mark iteration as completed with results."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.recommendation_data = recommendation_data
        self.confidence_score = confidence

    def mark_failed(self, error_details: Dict[str, Any]):
        """Mark iteration as failed with error details."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_details = error_details


class SixRRecommendation(Base):
    """6R analysis recommendation results."""

    __tablename__ = "sixr_recommendations"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("sixr_analyses.id"), nullable=False
    )
    iteration_number = Column(Integer, default=1)

    # Core recommendation
    recommended_strategy = Column(
        Enum(
            SixRStrategy,
            name="sixr_strategy",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    confidence_score = Column(Float, nullable=False)

    # Strategy scores (JSON)
    strategy_scores = Column(JSON)

    # Analysis insights
    key_factors = Column(JSON)  # List of key decision factors
    assumptions = Column(JSON)  # List of assumptions made
    next_steps = Column(JSON)  # List of recommended next steps

    # Estimates
    estimated_effort = Column(String(50))  # low, medium, high, very_high
    estimated_timeline = Column(String(100))  # e.g., "3-6 months"
    estimated_cost_impact = Column(String(50))  # low, moderate, high, very_high

    # Additional details
    risk_factors = Column(JSON)
    business_benefits = Column(JSON)
    technical_benefits = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    # Relationships
    analysis = relationship("SixRAnalysis", back_populates="recommendations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "iteration_number": self.iteration_number,
            "recommended_strategy": self.recommended_strategy,
            "confidence_score": self.confidence_score,
            "strategy_scores": self.strategy_scores or [],
            "key_factors": self.key_factors or [],
            "assumptions": self.assumptions or [],
            "next_steps": self.next_steps or [],
            "estimated_effort": self.estimated_effort,
            "estimated_timeline": self.estimated_timeline,
            "estimated_cost_impact": self.estimated_cost_impact,
            "risk_factors": self.risk_factors or [],
            "business_benefits": self.business_benefits or [],
            "technical_benefits": self.technical_benefits or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    def get_strategy_score(self, strategy: SixRStrategy) -> Optional[Dict[str, Any]]:
        """Get score for specific strategy."""
        if not self.strategy_scores:
            return None

        for score_data in self.strategy_scores:
            if score_data.get("strategy") == strategy:
                return score_data
        return None

    def get_top_strategies(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get top N strategies by score."""
        if not self.strategy_scores:
            return []

        sorted_strategies = sorted(
            self.strategy_scores, key=lambda x: x.get("score", 0), reverse=True
        )
        return sorted_strategies[:limit]

    def validate_recommendation(self, validated_by: str, notes: Optional[str] = None):
        """Validate the recommendation."""
        self.validation_status = "validated"
        self.validated_by = validated_by
        self.validated_at = datetime.utcnow()
        if notes:
            self.validation_notes = notes

    def reject_recommendation(self, rejected_by: str, notes: str):
        """Reject the recommendation."""
        self.validation_status = "rejected"
        self.validated_by = rejected_by
        self.validated_at = datetime.utcnow()
        self.validation_notes = notes


class SixRQuestion(Base):
    """6R qualifying questions model."""

    __tablename__ = "sixr_questions"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # Question definition
    question_id = Column(String(100), unique=True, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(
        Enum(
            QuestionType,
            name="question_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    category = Column(String(100), nullable=False)

    # Question metadata
    priority = Column(Integer, default=1)  # 1-5 priority
    required = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

    # Question configuration
    options = Column(JSON)  # Options for select/multiselect questions
    validation_rules = Column(JSON)  # Validation rules
    help_text = Column(Text)  # Help text for question
    depends_on = Column(String(100))  # Question dependency

    # Conditional logic
    show_conditions = Column(JSON)  # Conditions for showing question
    skip_conditions = Column(JSON)  # Conditions for skipping question

    # Audit fields
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Version control
    version = Column(String(20), default="1.0")
    parent_question_id = Column(String(100))  # For question versioning

    def __repr__(self):
        return f"<SixRQuestion(id='{self.question_id}', type='{self.question_type}', category='{self.category}')>"

    @property
    def is_active(self) -> bool:
        """Check if question is active."""
        return self.active

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules for question."""
        return self.validation_rules or {}

    def get_options(self) -> List[Dict[str, Any]]:
        """Get question options."""
        return self.options or []


class SixRAnalysisParameters(Base):
    """6R analysis parameters model for a specific analysis run."""

    __tablename__ = "sixr_analysis_parameters"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("sixr_analyses.id"), nullable=False
    )
    iteration_number = Column(Integer, nullable=False)  # Tracks parameter set version

    # Dynamic parameters based on analysis needs
    business_value = Column(Float, nullable=False, default=3)
    technical_complexity = Column(Float, nullable=False, default=3)
    migration_urgency = Column(Float, nullable=False, default=3)
    compliance_requirements = Column(Float, nullable=False, default=3)
    cost_sensitivity = Column(Float, nullable=False, default=3)
    risk_tolerance = Column(Float, nullable=False, default=3)
    innovation_priority = Column(Float, nullable=False, default=3)

    # Contextual parameters
    application_type = Column(String(20), default="custom")
    parameter_source = Column(
        String(50), default="initial"
    )  # initial, user_adjusted, ai_suggested
    confidence_level = Column(Float, default=1.0)

    # Metadata
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    parameter_notes = Column(Text)
    validation_status = Column(String(20), default="valid")

    # Relationships
    analysis = relationship("SixRAnalysis", back_populates="parameters")

    def __repr__(self):
        return f"<SixRAnalysisParameters(analysis_id={self.analysis_id}, iteration={self.iteration_number})>"


class SixRParameter(Base):
    """Global 6R configuration parameters (key-value store)."""

    __tablename__ = "sixr_parameters"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parameter_key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SixRParameter(key='{self.parameter_key}', value='{self.value}')>"


class SixRQuestionResponse(Base):
    """6R question responses model."""

    __tablename__ = "sixr_question_responses"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("sixr_analyses.id"), nullable=False
    )
    iteration_number = Column(Integer, nullable=False)
    question_id = Column(
        String(100), ForeignKey("sixr_questions.question_id"), nullable=False
    )

    # Response data
    response_value = Column(JSON)  # The actual response (can be various types)
    response_text = Column(Text)  # Text representation of response
    confidence = Column(Float, default=1.0)  # 0-1 confidence in response
    source = Column(String(50), default="user")  # user, ai_suggested, imported

    # Response metadata
    response_time = Column(Float)  # Time taken to respond (seconds)
    validation_status = Column(String(20), default="pending")  # pending, valid, invalid
    validation_errors = Column(JSON)  # Validation error details

    # Audit fields
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    analysis = relationship("SixRAnalysis")
    question = relationship("SixRQuestion")

    def __repr__(self):
        return f"<SixRQuestionResponse(id={self.id}, question_id='{self.question_id}', analysis_id={self.analysis_id})>"

    @property
    def is_valid(self) -> bool:
        """Check if response is valid."""
        return self.validation_status == "valid"

    def validate_response(self) -> List[str]:
        """Validate response against question rules."""
        if not self.question:
            return ["Question not found"]

        self.question.get_validation_rules()
        errors = []

        # Add validation logic based on question type and rules
        if self.question.required and not self.response_value:
            errors.append("Response is required")

        # Type-specific validation
        if self.question.question_type == QuestionType.NUMERIC:
            try:
                float(self.response_value)
            except (ValueError, TypeError):
                errors.append("Response must be a number")

        return errors

    def mark_valid(self):
        """Mark response as valid."""
        self.validation_status = "valid"
        self.validation_errors = None

    def mark_invalid(self, errors: List[str]):
        """Mark response as invalid with errors."""
        self.validation_status = "invalid"
        self.validation_errors = errors


# Update the Migration model to include 6R analyses relationship
# This would be added to the existing Migration model in migration.py
"""
Add this to the Migration model in backend/app/models/migration.py:

# Relationships (add this line)
sixr_analyses = relationship("SixRAnalysis", back_populates="migration")
"""
