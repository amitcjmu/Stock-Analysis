"""
6R Analysis core models - SixRAnalysis and SixRIteration.
"""

from typing import TYPE_CHECKING

from app.models.sixr_analysis.base import (
    Any,
    AnalysisStatus,
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
    JSONB,
    Optional,
    PostgresUUID,
    SixRStrategy,
    String,
    Text,
    datetime,
    func,
    relationship,
    uuid,
)

if TYPE_CHECKING:
    from app.models.sixr_analysis.parameters import SixRAnalysisParameters
    from app.models.sixr_analysis.recommendations import SixRRecommendation


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

    # Two-Tier Inline Gap-Filling (PR #816, October 2025)
    tier1_gaps_by_asset = Column(
        JSONB, nullable=True
    )  # Tier 1 (blocking) gaps by asset UUID when status=requires_input
    retry_after_inline = Column(
        Boolean, default=False
    )  # If True, analysis blocked pending inline answers

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


__all__ = ["SixRAnalysis", "SixRIteration"]
