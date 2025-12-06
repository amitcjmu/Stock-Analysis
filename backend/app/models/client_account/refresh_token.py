"""
Refresh Token model definition.
"""

from datetime import datetime, timezone

from ._common import (
    Base,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    PostgresUUID,
    String,
    func,
    relationship,
    uuid,
)


class RefreshToken(Base):
    """
    Represents a refresh token for JWT token rotation.
    Refresh tokens are long-lived tokens used to obtain new access tokens.
    """

    __tablename__ = "refresh_tokens"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the refresh token.",
    )
    token = Column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        comment="The actual refresh token string (hashed).",
    )
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user this refresh token belongs to.",
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this refresh token expires.",
    )
    is_revoked = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this token has been revoked (for token rotation).",
    )
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this token was revoked.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this token was created.",
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this token was last used to refresh access token.",
    )
    user_agent = Column(
        String(500),
        nullable=True,
        comment="User agent of the client that created this token (for security tracking).",
    )
    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address of the client that created this token (for security tracking).",
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="refresh_tokens")

    def __repr__(self):
        return (
            f"<RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, is_revoked={self.is_revoked})>"
        )

    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not expired and not revoked)."""
        return not self.is_revoked and datetime.now(timezone.utc) < self.expires_at

    def revoke(self):
        """Revoke this refresh token."""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
