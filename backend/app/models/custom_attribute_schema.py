"""
CustomAttributeSchema SQLAlchemy Model

Stores client-specific JSON schemas for validating the custom_attributes
JSONB column in the assets table. Uses JSON Schema draft-07 format.

Part of Issue #1240 - JSONB Schema Validation
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import Base


class CustomAttributeSchema(Base):
    """
    Client-specific JSON schema for custom_attributes validation.

    Each client can define one or more schemas to validate the custom_attributes
    JSONB column in the assets table. Schemas use JSON Schema draft-07 format.

    Features:
    - Version support for schema evolution
    - Active/inactive toggle for schema lifecycle
    - Strict mode toggle (reject vs warn on validation failure)
    """

    __tablename__ = "custom_attribute_schemas"
    __table_args__ = (
        UniqueConstraint(
            "client_account_id",
            "schema_name",
            "schema_version",
            name="uq_custom_attr_schema_client_name_version",
        ),
        {"schema": "migration"},
    )

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the schema",
    )

    # Client association
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Client account this schema belongs to",
    )

    # Schema identification
    schema_name = Column(
        String(100),
        nullable=False,
        comment="Human-readable name for the schema (e.g., 'cmdb_fields')",
    )
    schema_version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Schema version number for evolution tracking",
    )

    # Schema definition (JSON Schema draft-07)
    json_schema = Column(
        JSONB,
        nullable=False,
        comment="JSON Schema draft-07 definition for validation",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of what this schema validates",
    )

    # Schema state
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this schema is currently active for validation",
    )
    strict_mode = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="When true, validation failures reject data. When false, log warnings only.",
    )

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        comment="When this schema was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When this schema was last updated",
    )
    created_by = Column(
        String(255),
        nullable=True,
        comment="User who created this schema",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomAttributeSchema("
            f"name='{self.schema_name}', "
            f"version={self.schema_version}, "
            f"active={self.is_active})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "json_schema": self.json_schema,
            "description": self.description,
            "is_active": self.is_active,
            "strict_mode": self.strict_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
