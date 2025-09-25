"""
Device Asset Model
Used for tracking devices in the collection flow bulk import system.
"""

import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Device(Base, TimestampMixin):
    """Device asset model for bulk import system."""

    __tablename__ = "devices"
    __table_args__ = {"schema": "migration"}

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    device_type = Column(String(100))
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    location = Column(String(255))
    criticality = Column(String(50), default="Medium")

    # Multi-tenant scoping fields
    client_account_id = Column(String(50), nullable=False, index=True)
    engagement_id = Column(String(50), nullable=False, index=True)

    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name})>"
