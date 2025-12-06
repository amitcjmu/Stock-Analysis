"""
Agent Discovered Patterns Model
Patterns discovered by agents during task execution for learning and optimization
Part of the Agent Observability Enhancement
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    literal,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import text

from app.core.database import Base


class PatternType(str, Enum):
    """Types of patterns that agents can discover"""

    TECHNOLOGY_CORRELATION = "TECHNOLOGY_CORRELATION"
    BUSINESS_VALUE_INDICATOR = "BUSINESS_VALUE_INDICATOR"
    RISK_FACTOR = "RISK_FACTOR"
    MODERNIZATION_OPPORTUNITY = "MODERNIZATION_OPPORTUNITY"
    DEPENDENCY_PATTERN = "DEPENDENCY_PATTERN"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"
    PERFORMANCE_BOTTLENECK = "PERFORMANCE_BOTTLENECK"
    COMPLIANCE_REQUIREMENT = "COMPLIANCE_REQUIREMENT"
    FIELD_MAPPING_APPROVAL = "FIELD_MAPPING_APPROVAL"
    FIELD_MAPPING_REJECTION = "FIELD_MAPPING_REJECTION"
    FIELD_MAPPING_SUGGESTION = "FIELD_MAPPING_SUGGESTION"
    PRODUCT_MATCHING = "PRODUCT_MATCHING"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    LICENSING_ANALYSIS = "LICENSING_ANALYSIS"
    VULNERABILITY_ANALYSIS = "VULNERABILITY_ANALYSIS"
    RESILIENCE_ANALYSIS = "RESILIENCE_ANALYSIS"
    DEPENDENCY_ANALYSIS = "DEPENDENCY_ANALYSIS"
    WAVE_PLANNING_OPTIMIZATION = "WAVE_PLANNING_OPTIMIZATION"


class AgentDiscoveredPatterns(Base):
    """
    Patterns discovered by agents during task execution for learning and optimization.
    This table captures insights and patterns that agents identify, which can be used
    to improve future task execution and system optimization.
    """

    __tablename__ = "agent_discovered_patterns"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the discovered pattern",
    )

    # Pattern identification
    pattern_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Unique identifier for the pattern",
    )
    pattern_type = Column(
        SQLEnum(PatternType),
        nullable=False,
        index=True,
        comment="Type of pattern discovered",
    )
    pattern_name = Column(
        String(255), nullable=False, comment="Human-readable name of the pattern"
    )
    pattern_description = Column(
        Text, nullable=True, comment="Detailed description of the pattern"
    )

    # Discovery information
    discovered_by_agent = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Agent that discovered this pattern",
    )
    task_id = Column(
        String(255), nullable=True, comment="Task ID where pattern was discovered"
    )

    # Pattern quality metrics
    confidence_score = Column(
        DECIMAL(3, 2), nullable=False, comment="Confidence score of the pattern (0-1)"
    )
    evidence_count = Column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Number of instances supporting this pattern",
    )
    times_referenced = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Number of times this pattern has been referenced",
    )
    pattern_effectiveness_score = Column(
        DECIMAL(3, 2),
        nullable=True,
        comment="Effectiveness score based on usage and feedback (0-1)",
    )

    # Vector search capabilities (thenlper/gte-large model - 1024 dimensions)
    embedding = Column(
        Vector(1024),
        nullable=True,
        comment="Vector embedding for similarity search (thenlper/gte-large 1024-dim)",
    )
    insight_type = Column(
        String(50),
        nullable=True,
        comment="Structured classification of the pattern type",
    )

    # Pattern data and context
    pattern_data = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Detailed pattern data and parameters",
    )
    execution_context = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Context in which pattern was discovered",
    )

    # Usage and feedback tracking
    user_feedback_given = Column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether user has provided feedback on this pattern",
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this pattern was used",
    )

    # Multi-tenant fields
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id"),
        nullable=False,
        index=True,
        comment="Client account this pattern belongs to",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id"),
        nullable=False,
        index=True,
        comment="Engagement this pattern is part of",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this pattern was discovered",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="When this record was last updated",
    )

    # Foreign key relationships - removed to avoid circular dependencies
    # Relationships can be accessed via foreign key queries if needed

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "pattern_id",
            "client_account_id",
            "engagement_id",
            name="uq_agent_discovered_patterns_pattern_client_engagement",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="chk_agent_discovered_patterns_confidence_score",
        ),
        CheckConstraint(
            "pattern_effectiveness_score >= 0 AND pattern_effectiveness_score <= 1",
            name="chk_agent_discovered_patterns_effectiveness_score",
        ),
        CheckConstraint(
            """insight_type IS NULL OR insight_type IN (
                'field_mapping_suggestion',
                'risk_pattern',
                'optimization_opportunity',
                'anomaly_detection',
                'workflow_improvement',
                'dependency_pattern',
                'performance_pattern',
                'error_pattern'
            )""",
            name="chk_agent_patterns_insight_type",
        ),
        {"extend_existing": True, "schema": "migration"},
    )

    def __repr__(self):
        return (
            f"<AgentDiscoveredPatterns(id={self.id}, pattern={self.pattern_name}, "
            f"agent={self.discovered_by_agent}, confidence={self.confidence_score})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "pattern_name": self.pattern_name,
            "pattern_description": self.pattern_description,
            "discovered_by_agent": self.discovered_by_agent,
            "task_id": self.task_id,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "evidence_count": self.evidence_count,
            "times_referenced": self.times_referenced,
            "pattern_effectiveness_score": (
                float(self.pattern_effectiveness_score)
                if self.pattern_effectiveness_score
                else None
            ),
            "embedding": list(self.embedding) if self.embedding else None,
            "insight_type": self.insight_type,
            "pattern_data": self.pattern_data or {},
            "execution_context": self.execution_context or {},
            "user_feedback_given": self.user_feedback_given,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def increment_reference_count(self):
        """Increment the times this pattern has been referenced"""
        self.times_referenced += 1
        self.last_used_at = datetime.utcnow()

    def update_effectiveness_score(self, new_score: float):
        """Update the pattern effectiveness score based on usage and feedback"""
        if 0 <= new_score <= 1:
            self.pattern_effectiveness_score = round(new_score, 2)

    def add_evidence(self, evidence_data: Dict[str, Any]):
        """Add new evidence supporting this pattern"""
        self.evidence_count += 1

        if not self.pattern_data:
            self.pattern_data = {}

        if "evidence" not in self.pattern_data:
            self.pattern_data["evidence"] = []

        self.pattern_data["evidence"].append(
            {"timestamp": datetime.utcnow().isoformat(), "data": evidence_data}
        )

        # Keep only last 50 evidence entries to prevent unbounded growth
        if len(self.pattern_data["evidence"]) > 50:
            self.pattern_data["evidence"] = self.pattern_data["evidence"][-50:]

    def apply_user_feedback(self, feedback_type: str, feedback_value: Any):
        """Apply user feedback to the pattern"""
        self.user_feedback_given = True

        if not self.pattern_data:
            self.pattern_data = {}

        if "user_feedback" not in self.pattern_data:
            self.pattern_data["user_feedback"] = []

        self.pattern_data["user_feedback"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": feedback_type,
                "value": feedback_value,
            }
        )

        # Adjust effectiveness score based on feedback
        if feedback_type == "rating" and isinstance(feedback_value, (int, float)):
            # Simple averaging of ratings for effectiveness score
            ratings = [
                f["value"]
                for f in self.pattern_data["user_feedback"]
                if f["type"] == "rating" and isinstance(f["value"], (int, float))
            ]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                # Normalize to 0-1 scale (assuming ratings are 1-5)
                self.pattern_effectiveness_score = round(avg_rating / 5.0, 2)

    def set_embedding(self, embedding_vector: List[float]):
        """Set the vector embedding for similarity search"""
        if len(embedding_vector) != 1024:
            raise ValueError(
                "Embedding vector must be exactly 1024 dimensions "
                "for thenlper/gte-large model compatibility"
            )
        self.embedding = embedding_vector

    def set_insight_type(self, insight_type: str):
        """Set the structured insight type with validation"""
        valid_types = {
            "field_mapping_suggestion",
            "risk_pattern",
            "optimization_opportunity",
            "anomaly_detection",
            "workflow_improvement",
            "dependency_pattern",
            "performance_pattern",
            "error_pattern",
        }
        if insight_type not in valid_types:
            raise ValueError(
                f"Invalid insight_type: {insight_type}. "
                f"Must be one of {valid_types}"
            )
        self.insight_type = insight_type

    @classmethod
    def find_similar_patterns(
        cls,
        session,
        query_embedding: List[float],
        client_account_id: uuid.UUID,
        insight_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[tuple["AgentDiscoveredPatterns", float]]:
        """
        Find similar patterns using vector similarity search with PostgreSQL filtering.

        Issue #984 Fix: Moved similarity threshold filtering from Python to PostgreSQL
        for 5-10x performance improvement on large datasets.

        Args:
            session: SQLAlchemy session
            query_embedding: Vector to search against (1024 dimensions for thenlper/gte-large)
            client_account_id: Client account for tenant isolation
            insight_type: Optional filter by insight type
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0-1), default 0.7

        Returns:
            List of tuples (pattern, similarity_score) ordered by similarity descending.
            Similarity score is 1.0 for identical, 0.0 for orthogonal vectors.
        """
        if len(query_embedding) != 1024:
            raise ValueError(
                "Query embedding must be exactly 1024 dimensions for thenlper/gte-large model"
            )

        # Use pgvector's native cosine_distance method (secure, no SQL injection risk)
        # Cosine distance: 0 = identical, 2 = opposite
        # Cosine similarity = 1 - cosine_distance (for unit vectors)
        distance_expr = cls.embedding.cosine_distance(query_embedding)
        similarity_expr = literal(1.0) - distance_expr

        # Convert similarity threshold to distance threshold
        # similarity >= threshold means distance <= (1 - threshold)
        max_distance = 1.0 - similarity_threshold

        # Build query with PostgreSQL-level filtering (Issue #984 fix)
        query = (
            session.query(cls, similarity_expr.label("similarity"))
            .filter(
                cls.client_account_id == client_account_id,
                cls.embedding.isnot(None),
                # Filter by threshold IN DATABASE - key performance fix
                distance_expr <= max_distance,
            )
            .order_by(distance_expr)  # Order by distance ascending = similarity desc
            .limit(limit)
        )

        # Add insight type filter if specified
        if insight_type:
            query = query.filter(cls.insight_type == insight_type)

        # Execute and return results with similarity scores
        return [(pattern, float(sim)) for pattern, sim in query.all()]

    def calculate_similarity(self, other_embedding: List[float]) -> float:
        """
        Calculate cosine similarity between this pattern's embedding and another

        Args:
            other_embedding: Vector to compare against (1024 dimensions for thenlper/gte-large)

        Returns:
            Cosine similarity score (0-1, where 1 is identical)
        """
        if not self.embedding or len(other_embedding) != 1024:
            return 0.0

        # Simple dot product implementation for similarity
        # In production, this should use optimized vector operations
        dot_product = sum(a * b for a, b in zip(self.embedding, other_embedding))
        magnitude_a = sum(a * a for a in self.embedding) ** 0.5
        magnitude_b = sum(b * b for b in other_embedding) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
