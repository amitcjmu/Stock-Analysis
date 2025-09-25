"""
Application Asset Model
Used for tracking applications in the collection flow bulk import system.
"""

import uuid

from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Application(Base, TimestampMixin):
    """Application asset model for bulk import system."""

    __tablename__ = "applications"
    __table_args__ = {"schema": "migration"}

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    business_criticality = Column(String(50), default="Medium")
    description = Column(Text)
    technology_stack = Column(JSON, default=dict)

    # Multi-tenant scoping fields
    client_account_id = Column(String(50), nullable=False, index=True)
    engagement_id = Column(String(50), nullable=False, index=True)

    def __repr__(self):
        return f"<Application(id={self.id}, name={self.name})>"
