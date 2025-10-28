"""
6R Analysis recommendation models.
"""

from app.models.sixr_analysis.base import (
    Any,
    Base,
    Column,
    DateTime,
    Dict,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    List,
    Optional,
    PostgresUUID,
    SixRStrategy,
    String,
    datetime,
    relationship,
    uuid,
)


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


__all__ = ["SixRRecommendation"]
