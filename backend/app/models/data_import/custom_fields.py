import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class CustomTargetField(Base):
    __tablename__ = "custom_target_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False
    )
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)
    description = Column(Text)
    is_required = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validation_schema = Column(JSON)
    default_value = Column(String)
    allowed_values = Column(JSON)

    client_account = relationship("ClientAccount")
    creator = relationship("User")
