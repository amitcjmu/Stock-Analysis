"""
Database Asset Model
Used for tracking databases in the collection flow bulk import system.
"""

import uuid

from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Database(Base, TimestampMixin):
    """Database asset model for bulk import system."""

    __tablename__ = "databases"
    __table_args__ = {"schema": "migration"}

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    database_type = Column(String(100))
    version = Column(String(50))
    size_gb = Column(Integer, default=0)
    criticality = Column(String(50), default="Medium")

    # Multi-tenant scoping fields
    client_account_id = Column(String(50), nullable=False, index=True)
    engagement_id = Column(String(50), nullable=False, index=True)

    def __repr__(self):
        return f"<Database(id={self.id}, name={self.name})>"
