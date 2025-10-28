"""
6R Analysis parameter models.
"""

from app.models.sixr_analysis.base import (
    Base,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    PostgresUUID,
    String,
    Text,
    func,
    relationship,
    uuid,
)


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


__all__ = ["SixRAnalysisParameters", "SixRParameter"]
