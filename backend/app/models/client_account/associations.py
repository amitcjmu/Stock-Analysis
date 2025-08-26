"""
User account association model definition.
"""

from ._common import (
    Base,
    Column,
    DateTime,
    ForeignKey,
    PostgresUUID,
    String,
    UniqueConstraint,
    func,
    relationship,
    uuid,
)


class UserAccountAssociation(Base):
    """
    Association table linking Users to ClientAccounts, defining their role within that account.
    This is the basis of the multi-tenancy authorization model.
    """

    __tablename__ = "user_account_associations"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the association record.",
    )
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the users table.",
    )
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the client_accounts table.",
    )

    # Role within the client account
    role = Column(
        String(50),
        nullable=False,
        default="member",
        comment="The user's role within this specific client account (e.g., 'admin', 'member', 'viewer').",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the association was created.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user ID of the user who created this association (typically an admin).",
    )

    # Relationships
    user = relationship(
        "User", back_populates="user_associations", foreign_keys=[user_id]
    )
    client_account = relationship("ClientAccount", back_populates="user_associations")
    created_by_user = relationship("User", foreign_keys=[created_by])

    def __init__(self, *args, **kwargs):
        # Import here to avoid circular import
        from .base import ClientAccount

        # Allow creating association with a ClientAccount object
        if "client_account" in kwargs and isinstance(
            kwargs["client_account"], ClientAccount
        ):
            super().__init__(*args, **kwargs)
        # Allow creating association with a dict that can be used to make a ClientAccount
        elif "client_account" in kwargs and isinstance(kwargs["client_account"], dict):
            account_data = kwargs.pop("client_account")
            # Ensure we don't pass unexpected arguments to ClientAccount
            allowed_keys = {c.name for c in ClientAccount.__table__.columns}
            filtered_data = {k: v for k, v in account_data.items() if k in allowed_keys}
            kwargs["client_account"] = ClientAccount(**filtered_data)
            super().__init__(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    # Unique constraint for user_id and client_account_id
    __table_args__ = (
        UniqueConstraint(
            "user_id", "client_account_id", name="_user_client_account_uc"
        ),
        {"extend_existing": True},
    )

    def __repr__(self):
        return (
            f"<UserAccountAssociation(user_id={self.user_id}, "
            f"client_account_id={self.client_account_id}, role='{self.role}')>"
        )
