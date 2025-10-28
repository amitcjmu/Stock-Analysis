"""
6R Analysis question and response models.
"""

from app.models.sixr_analysis.base import (
    Any,
    Base,
    Boolean,
    Column,
    DateTime,
    Dict,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    List,
    PostgresUUID,
    QuestionType,
    String,
    Text,
    func,
    relationship,
    uuid,
)


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


__all__ = ["SixRQuestion", "SixRQuestionResponse"]
