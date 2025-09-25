"""
Server Asset Model
Used for tracking servers in the collection flow bulk import system.
"""

import uuid

from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Server(Base, TimestampMixin):
    """Server asset model for bulk import system."""

    __tablename__ = "servers"
    __table_args__ = {"schema": "migration"}

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    hostname = Column(String(255))
    ip_address = Column(String(45))  # Supports IPv6
    operating_system = Column(String(100))
    cpu_cores = Column(Integer, default=0)
    memory_gb = Column(Integer, default=0)
    storage_gb = Column(Integer, default=0)
    environment = Column(String(50), default="Production")

    # Multi-tenant scoping fields
    client_account_id = Column(String(50), nullable=False, index=True)
    engagement_id = Column(String(50), nullable=False, index=True)

    def __repr__(self):
        return f"<Server(id={self.id}, name={self.name})>"
