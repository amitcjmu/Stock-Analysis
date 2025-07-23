"""
Assessment models for 6R analysis and migration planning.
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

try:
    from app.core.database import Base
except ImportError:
    Base = object


class AssessmentType(str, enum.Enum):
    """Assessment type enumeration."""

    SIX_R_ANALYSIS = "six_r_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    COST_ANALYSIS = "cost_analysis"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    BUSINESS_IMPACT = "business_impact"
    SECURITY_ASSESSMENT = "security_assessment"
    COMPLIANCE_REVIEW = "compliance_review"


class AssessmentStatus(str, enum.Enum):
    """Assessment status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, enum.Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Assessment(Base):
    """Migration assessment model."""

    __tablename__ = "assessments"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
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
    migration_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("migrations.id"), nullable=False
    )
    asset_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("assets.id"), nullable=True
    )  # Null for migration-wide assessments

    # Assessment metadata
    assessment_type = Column(Enum(AssessmentType), nullable=False)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.PENDING)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Assessment results
    overall_score = Column(Float)  # 0-100 overall assessment score
    risk_level = Column(Enum(RiskLevel))
    confidence_level = Column(Float)  # 0-1 confidence in assessment

    # 6R Strategy Analysis
    recommended_strategy = Column(String(50))  # Primary 6R recommendation
    alternative_strategies = Column(JSON)  # Alternative 6R options with scores
    strategy_rationale = Column(Text)  # Explanation for recommendation

    # Cost Analysis
    current_cost = Column(Float)
    estimated_migration_cost = Column(Float)
    estimated_target_cost = Column(Float)
    cost_savings_potential = Column(Float)
    roi_months = Column(Integer)  # Return on investment timeline

    # Risk Analysis
    identified_risks = Column(JSON)  # List of identified risks
    risk_mitigation = Column(JSON)  # Risk mitigation strategies
    blockers = Column(JSON)  # Migration blockers
    dependencies_impact = Column(JSON)  # Impact of dependencies

    # Technical Assessment
    technical_complexity = Column(String(20))  # "low", "medium", "high"
    compatibility_score = Column(Float)  # Cloud compatibility (0-100)
    modernization_opportunities = Column(JSON)  # Modernization recommendations
    performance_impact = Column(JSON)  # Expected performance changes

    # Business Impact
    business_criticality = Column(String(20))  # "low", "medium", "high", "critical"
    downtime_requirements = Column(JSON)  # Acceptable downtime windows
    user_impact = Column(Text)  # Impact on end users
    compliance_considerations = Column(JSON)  # Regulatory requirements

    # AI Analysis
    ai_insights = Column(JSON)  # AI-generated insights
    ai_confidence = Column(Float)  # AI confidence score (0-1)
    ai_model_version = Column(String(50))  # AI model used for analysis

    # Timeline and effort
    estimated_effort_hours = Column(Integer)
    estimated_duration_days = Column(Integer)
    recommended_wave = Column(Integer)  # Migration wave assignment
    prerequisites = Column(JSON)  # Prerequisites for migration

    # Assessment metadata
    assessor = Column(String(100))  # Who performed the assessment
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    review_date = Column(DateTime(timezone=True))
    approval_date = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    migration = relationship("Migration", back_populates="assessments")
    asset = relationship("Asset")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return f"<Assessment(id={self.id}, type='{self.assessment_type}', status='{self.status}')>"

    @property
    def is_completed(self) -> bool:
        """Check if assessment is completed."""
        return self.status in [
            AssessmentStatus.COMPLETED,
            AssessmentStatus.REVIEWED,
            AssessmentStatus.APPROVED,
        ]

    @property
    def is_high_risk(self) -> bool:
        """Check if assessment indicates high risk."""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def get_readiness_score(self) -> float:
        """Calculate migration readiness score based on assessment."""
        if not self.overall_score:
            return 0.0

        score = self.overall_score

        # Adjust based on risk level
        risk_penalties = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 10,
            RiskLevel.HIGH: 25,
            RiskLevel.CRITICAL: 50,
        }

        if self.risk_level in risk_penalties:
            score -= risk_penalties[self.risk_level]

        # Adjust based on technical complexity
        complexity_penalties = {"high": 20, "medium": 10, "low": 0}
        if self.technical_complexity in complexity_penalties:
            score -= complexity_penalties[self.technical_complexity]

        return max(0.0, min(100.0, score))


class WavePlan(Base):
    """Migration wave planning model."""

    __tablename__ = "wave_plans"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
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
    migration_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("migrations.id"), nullable=False
    )

    # Wave details
    wave_number = Column(Integer, nullable=False)
    wave_name = Column(String(255))
    description = Column(Text)

    # Timeline
    planned_start_date = Column(DateTime(timezone=True))
    planned_end_date = Column(DateTime(timezone=True))
    actual_start_date = Column(DateTime(timezone=True))
    actual_end_date = Column(DateTime(timezone=True))

    # Wave characteristics
    total_assets = Column(Integer, default=0)
    completed_assets = Column(Integer, default=0)
    estimated_effort_hours = Column(Integer)
    estimated_cost = Column(Float)

    # Dependencies and constraints
    prerequisites = Column(JSON)  # Prerequisites for this wave
    dependencies = Column(JSON)  # Dependencies on other waves
    constraints = Column(JSON)  # Resource or timing constraints

    # Risk and complexity
    overall_risk_level = Column(Enum(RiskLevel))
    complexity_score = Column(Float)  # 0-100 complexity score
    success_criteria = Column(JSON)  # Success criteria for the wave

    # Status tracking
    status = Column(
        String(50), default="planned"
    )  # planned, in_progress, completed, delayed
    progress_percentage = Column(Float, default=0.0)

    # AI recommendations
    ai_recommendations = Column(JSON)  # AI-generated wave optimization suggestions
    optimization_score = Column(Float)  # Wave optimization score (0-100)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    migration = relationship("Migration")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return f"<WavePlan(id={self.id}, wave={self.wave_number}, migration_id={self.migration_id})>"

    @property
    def is_completed(self) -> bool:
        """Check if wave is completed."""
        return self.status == "completed"

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_assets == 0:
            return 0.0
        return (self.completed_assets / self.total_assets) * 100

    def update_progress(self):
        """Update wave progress based on asset completion."""
        self.progress_percentage = self.completion_percentage
        if self.progress_percentage >= 100:
            self.status = "completed"
