"""Flow Deletion Audit Model

Comprehensive audit trail for discovery flow deletions.
"""

from app.core.database import Base
from sqlalchemy import TIMESTAMP, UUID, Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func


class FlowDeletionAudit(Base):
    """Audit trail for flow deletion operations."""

    __tablename__ = "flow_deletion_audit"

    # Primary identification
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    flow_id = Column(
        UUID(as_uuid=True), nullable=False, index=True
    )  # Primary flow identifier
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False)

    # Deletion metadata
    deletion_type = Column(
        String, nullable=False, index=True
    )  # user_requested, auto_cleanup, admin_action, batch_operation
    deletion_reason = Column(Text, nullable=True)
    deletion_method = Column(String, nullable=False)  # manual, api, batch, scheduled

    # Comprehensive data deletion summary
    data_deleted = Column(
        JSONB, nullable=False, default={}
    )  # Summary of what was deleted
    deletion_impact = Column(JSONB, nullable=False, default={})  # Impact analysis
    cleanup_summary = Column(
        JSONB, nullable=False, default={}
    )  # Cleanup operation results

    # CrewAI specific cleanup
    shared_memory_cleaned = Column(Boolean, nullable=False, default=False)
    knowledge_base_refs_cleaned = Column(JSONB, nullable=False, default=[])
    agent_memory_cleaned = Column(Boolean, nullable=False, default=False)

    # Audit trail
    deleted_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    deleted_by = Column(String, nullable=False)
    deletion_duration_ms = Column(Integer, nullable=True)  # How long the deletion took

    # Recovery information (if applicable)
    recovery_possible = Column(Boolean, nullable=False, default=False)
    recovery_data = Column(JSONB, nullable=False, default={})

    def __repr__(self):
        return f"<FlowDeletionAudit(id={self.id}, flow_id={self.flow_id}, type={self.deletion_type})>"

    @property
    def deletion_summary(self) -> dict:
        """Get a summary of the deletion operation."""
        return {
            "flow_id": str(self.flow_id),
            "deletion_type": self.deletion_type,
            "deletion_method": self.deletion_method,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": self.deleted_by,
            "duration_ms": self.deletion_duration_ms,
            "data_deleted": self.data_deleted,
            "cleanup_complete": {
                "shared_memory": self.shared_memory_cleaned,
                "agent_memory": self.agent_memory_cleaned,
                "knowledge_bases": (
                    len(self.knowledge_base_refs_cleaned)
                    if self.knowledge_base_refs_cleaned
                    else 0
                ),
            },
            "recovery_possible": self.recovery_possible,
        }

    @classmethod
    def create_audit_record(
        cls,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        user_id: str,
        deletion_type: str,
        deletion_method: str,
        deleted_by: str,
        deletion_reason: str = None,
        data_deleted: dict = None,
        deletion_impact: dict = None,
        cleanup_summary: dict = None,
        deletion_duration_ms: int = None,
    ) -> "FlowDeletionAudit":
        """Create a new audit record for flow deletion."""
        return cls(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            deletion_type=deletion_type,
            deletion_method=deletion_method,
            deletion_reason=deletion_reason,
            deleted_by=deleted_by,
            data_deleted=data_deleted or {},
            deletion_impact=deletion_impact or {},
            cleanup_summary=cleanup_summary or {},
            deletion_duration_ms=deletion_duration_ms,
        )
