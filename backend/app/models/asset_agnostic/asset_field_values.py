"""
Asset Field Values Model - EAV Pattern for Dynamic Asset Fields

This model implements the Entity-Attribute-Value pattern to store dynamic
asset fields with comprehensive data provenance and conflict tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

# pgvector import with fallback
try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.models.base import Base


class FieldType(str, Enum):
    """Supported field data types"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    JSON = "json"
    VECTOR = "vector"


class ValidationStatus(str, Enum):
    """Field validation status"""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    INVALID = "invalid"


class ConflictResolutionStatus(str, Enum):
    """Conflict resolution status"""

    NONE = "none"
    DETECTED = "detected"
    RESOLVED = "resolved"
    MANUAL_REVIEW = "manual_review"


class ResolutionStrategy(str, Enum):
    """Conflict resolution strategies"""

    LATEST_WINS = "latest_wins"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MANUAL_CHOICE = "manual_choice"
    MERGE = "merge"
    CUSTOM_RULE = "custom_rule"


class AssetFieldValue(Base):
    """
    Stores individual field values for assets with comprehensive data provenance.

    Uses Entity-Attribute-Value (EAV) pattern to support dynamic asset schemas.
    Each row represents one field value for one asset from one data source.
    """

    __tablename__ = "asset_field_values"
    __table_args__ = (
        # Ensure only one value type is populated
        CheckConstraint(
            text(
                """
            (
                (value_text IS NOT NULL AND value_number IS NULL AND value_boolean IS NULL
                 AND value_date IS NULL AND value_json IS NULL AND value_vector IS NULL) OR
                (value_text IS NULL AND value_number IS NOT NULL AND value_boolean IS NULL
                 AND value_date IS NULL AND value_json IS NULL AND value_vector IS NULL) OR
                (value_text IS NULL AND value_number IS NULL AND value_boolean IS NOT NULL
                 AND value_date IS NULL AND value_json IS NULL AND value_vector IS NULL) OR
                (value_text IS NULL AND value_number IS NULL AND value_boolean IS NULL
                 AND value_date IS NOT NULL AND value_json IS NULL AND value_vector IS NULL) OR
                (value_text IS NULL AND value_number IS NULL AND value_boolean IS NULL
                 AND value_date IS NULL AND value_json IS NOT NULL AND value_vector IS NULL) OR
                (value_text IS NULL AND value_number IS NULL AND value_boolean IS NULL
                 AND value_date IS NULL AND value_json IS NULL AND value_vector IS NOT NULL)
            )
            """
            ),
            name="ck_asset_field_values_single_value",
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_asset_field_values_confidence_range",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 1.0",
            name="ck_asset_field_values_quality_range",
        ),
        {"schema": "migration"},
    )

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for this field value record",
    )

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the asset this field belongs to",
    )

    # Multi-tenant isolation
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Client account for multi-tenant isolation",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Engagement for data scoping",
    )

    # Field definition
    field_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Name of the field (e.g., hostname, cpu_cores, operating_system)",
    )
    field_type = Column(
        String(50),
        nullable=False,
        comment="Data type: string, number, boolean, date, json, vector",
    )

    # Polymorphic value storage (only one should be populated)
    value_text = Column(Text, nullable=True)
    value_number = Column(Numeric, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_date = Column(DateTime(timezone=True), nullable=True)
    value_json = Column(JSONB, nullable=True)
    value_vector = Column(
        Vector(1536) if PGVECTOR_AVAILABLE else Text,
        nullable=True,
        comment="Embedding vector for similarity matching",
    )

    # Data provenance
    source_system = Column(
        String(100),
        nullable=False,
        index=True,
        comment="System that provided this data (ServiceNow, Azure, CSV, etc.)",
    )
    source_record_id = Column(
        String(255), nullable=True, comment="Original record ID in source system"
    )
    data_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_imports.id", ondelete="SET NULL"),
        nullable=True,
        comment="Data import job that created this field value",
    )
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.collection_flows.id", ondelete="SET NULL"),
        nullable=True,
        comment="Collection flow that created this field value",
    )

    # Quality and confidence metrics
    confidence_score = Column(
        Float, nullable=True, comment="Confidence score 0.0-1.0 for this field value"
    )
    quality_score = Column(
        Float, nullable=True, comment="Data quality score 0.0-1.0 based on validation"
    )
    validation_status = Column(
        String(20),
        nullable=False,
        default=ValidationStatus.VALID.value,
        server_default=ValidationStatus.VALID.value,
        comment="Validation status: valid, warning, error, invalid",
    )
    validation_errors = Column(
        JSONB, nullable=True, comment="Array of validation error messages"
    )

    # Conflict tracking
    has_conflicts = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="True if this field has conflicting values from other sources",
    )
    conflict_resolution_status = Column(
        String(20),
        nullable=False,
        default=ConflictResolutionStatus.NONE.value,
        server_default=ConflictResolutionStatus.NONE.value,
        comment="none, detected, resolved, manual_review",
    )
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who resolved the conflict",
    )
    resolved_at = Column(
        DateTime(timezone=True), nullable=True, comment="When the conflict was resolved"
    )
    resolution_strategy = Column(
        String(50),
        nullable=True,
        comment="latest_wins, highest_confidence, manual_choice, merge",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this field value was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="When this field value was last updated",
    )

    # Relationships
    asset = relationship("Asset", back_populates="field_values")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    data_import = relationship("DataImport")
    collection_flow = relationship("CollectionFlow")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])

    @hybrid_property
    def value(self) -> Any:
        """Get the actual value regardless of type"""
        if self.field_type == FieldType.STRING.value:
            return self.value_text
        elif self.field_type == FieldType.NUMBER.value:
            return self.value_number
        elif self.field_type == FieldType.BOOLEAN.value:
            return self.value_boolean
        elif self.field_type == FieldType.DATE.value:
            return self.value_date
        elif self.field_type == FieldType.JSON.value:
            return self.value_json
        elif self.field_type == FieldType.VECTOR.value:
            return self.value_vector
        return None

    def set_value(self, value: Any, field_type: str = None) -> None:
        """Set the value with automatic type detection if not specified"""
        if field_type:
            self.field_type = field_type

        # Clear all value fields first
        self.value_text = None
        self.value_number = None
        self.value_boolean = None
        self.value_date = None
        self.value_json = None
        self.value_vector = None

        # Set the appropriate field based on type
        if self.field_type == FieldType.STRING.value:
            self.value_text = str(value) if value is not None else None
        elif self.field_type == FieldType.NUMBER.value:
            self.value_number = float(value) if value is not None else None
        elif self.field_type == FieldType.BOOLEAN.value:
            self.value_boolean = bool(value) if value is not None else None
        elif self.field_type == FieldType.DATE.value:
            self.value_date = value if isinstance(value, datetime) else None
        elif self.field_type == FieldType.JSON.value:
            self.value_json = value
        elif self.field_type == FieldType.VECTOR.value:
            self.value_vector = value

    def calculate_weighted_confidence(
        self,
        source_reliability: float = 1.0,
        freshness_penalty: float = 1.0,
        priority_weight: float = 1.0,
    ) -> float:
        """
        Calculate weighted confidence score considering multiple factors

        Args:
            source_reliability: Reliability score of the data source (0.0-1.0)
            freshness_penalty: Penalty for data age (0.0-1.0, 1.0 = no penalty)
            priority_weight: Manual priority weight for the source (>0.0)

        Returns:
            Weighted confidence score (0.0-1.0)
        """
        base_confidence = self.confidence_score or 0.5

        # Validation status penalty
        validation_multiplier = {
            ValidationStatus.VALID.value: 1.0,
            ValidationStatus.WARNING.value: 0.8,
            ValidationStatus.ERROR.value: 0.3,
            ValidationStatus.INVALID.value: 0.1,
        }.get(self.validation_status, 0.5)

        # Combined weighted confidence
        weighted_confidence = (
            base_confidence
            * source_reliability
            * freshness_penalty
            * priority_weight
            * validation_multiplier
        )

        # Ensure bounds
        return max(0.0, min(1.0, weighted_confidence))

    def get_display_value(self) -> str:
        """Get a string representation of the value for display purposes"""
        value = self.value
        if value is None:
            return ""

        if self.field_type == FieldType.BOOLEAN.value:
            return "Yes" if value else "No"
        elif self.field_type == FieldType.DATE.value:
            return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""
        elif self.field_type == FieldType.JSON.value:
            return str(value) if value else "{}"
        elif self.field_type == FieldType.VECTOR.value:
            return f"Vector({len(value)} dims)" if value else "Vector(empty)"
        else:
            return str(value)

    def to_dict(self, include_value: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "field_name": self.field_name,
            "field_type": self.field_type,
            "source_system": self.source_system,
            "source_record_id": self.source_record_id,
            "confidence_score": self.confidence_score,
            "quality_score": self.quality_score,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors,
            "has_conflicts": self.has_conflicts,
            "conflict_resolution_status": self.conflict_resolution_status,
            "resolution_strategy": self.resolution_strategy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

        if include_value:
            data["value"] = self.value
            data["display_value"] = self.get_display_value()

        return data

    def __repr__(self):
        return (
            f"<AssetFieldValue(id={self.id}, field='{self.field_name}', "
            f"value='{self.get_display_value()[:50]}', source='{self.source_system}')>"
        )
