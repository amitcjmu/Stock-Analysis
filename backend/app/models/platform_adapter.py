"""
Platform Adapter Model

This model represents platform adapters for data collection.
"""

import uuid
from enum import Enum

from app.models.base import Base, TimestampMixin
from sqlalchemy import UUID, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


class AdapterStatus(str, Enum):
    """Adapter status values"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class PlatformAdapter(Base, TimestampMixin):
    """
    Model for platform adapters used in data collection.
    """

    __tablename__ = "platform_adapters"
    __table_args__ = (
        UniqueConstraint("adapter_name", "version", name="_adapter_name_version_uc"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Adapter identification
    adapter_name = Column(String(100), nullable=False, index=True)
    adapter_type = Column(String(50), nullable=False, index=True)
    version = Column(String(20), nullable=False)

    # Status
    status = Column(
        SQLEnum(
            AdapterStatus,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
        default=AdapterStatus.ACTIVE,
        server_default="active",
        index=True,
    )

    # Configuration
    capabilities = Column(JSONB, nullable=False, default=[], server_default="[]")
    configuration_schema = Column(
        JSONB, nullable=False, default={}, server_default="{}"
    )
    supported_platforms = Column(JSONB, nullable=False, default=[], server_default="[]")
    required_credentials = Column(
        JSONB, nullable=False, default=[], server_default="[]"
    )

    # Metadata
    adapter_metadata = Column(
        "metadata", JSONB, nullable=False, default={}, server_default="{}"
    )

    # Relationships
    collected_data = relationship("CollectedDataInventory", back_populates="adapter")

    def __repr__(self):
        return f"<PlatformAdapter(id={self.id}, name='{self.adapter_name}', version='{self.version}')>"
