"""
User model definition.
"""

from ._common import (
    Base,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    PostgresUUID,
    String,
    association_proxy,
    func,
    relationship,
    uuid,
)


class User(Base):
    """
    Represents a user of the platform. Users can be associated with multiple client accounts.
    """

    __tablename__ = "users"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the user.",
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="The user's email address, used for login. This is PII.",
    )
    username = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Optional username for the user.",
    )
    password_hash = Column(
        String(255),
        nullable=True,
        comment="Stores the salted and hashed password for the user.",
    )
    first_name = Column(String(100), comment="The user's first name. This is PII.")
    last_name = Column(String(100), comment="The user's last name. This is PII.")

    # User Status
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="A soft-delete flag. If false, the user cannot log in.",
    )
    is_verified = Column(
        Boolean,
        default=False,
        comment="Indicates if the user has verified their email address.",
    )
    is_admin = Column(
        Boolean,
        default=False,
        comment="Indicates if the user is a platform administrator.",
    )

    # Password Reset
    password_reset_token = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Hashed token for password reset. Expires after 15 minutes.",
    )
    password_reset_token_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration timestamp for the password reset token.",
    )

    # Default Context (for faster context establishment)
    default_client_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id"),
        nullable=True,
        comment="The default client account to use for the user upon login.",
    )
    default_engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.engagements.id"),
        nullable=True,
        comment="The default engagement to use for the user upon login.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the user account was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to the user record.",
    )
    last_login = Column(
        DateTime(timezone=True), comment="Timestamp of the user's last login."
    )

    # Relationships
    user_associations = relationship(
        "UserAccountAssociation",
        foreign_keys="[UserAccountAssociation.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # CC: Add roles relationship for RBAC checks
    roles = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
        lazy="select",
    )
    default_client = relationship("ClientAccount", foreign_keys=[default_client_id])
    default_engagement = relationship(
        "Engagement", foreign_keys=[default_engagement_id]
    )
    active_flows = relationship(
        "UserActiveFlow", back_populates="user", cascade="all, delete-orphan"
    )
    collection_flows = relationship(
        "CollectionFlow",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    questionnaire_responses = relationship(
        "CollectionQuestionnaireResponse",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    # Define association proxy with deferred import to avoid circular imports

    def _create_association(self, client_account):
        from .associations import UserAccountAssociation

        return UserAccountAssociation(client_account=client_account)

    client_accounts = association_proxy(
        "user_associations",
        "client_account",
        creator=_create_association,
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
