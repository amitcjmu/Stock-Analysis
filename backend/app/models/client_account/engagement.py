"""
Engagement model definition.
"""

from ._common import (
    Base,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    JSON,
    PostgresUUID,
    String,
    Text,
    func,
    relationship,
    uuid,
)


class Engagement(Base):
    """
    Represents a specific project or migration initiative for a client account.
    All work, such as data imports and analyses, is scoped to an engagement.
    """

    __tablename__ = "engagements"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the engagement.",
    )
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key linking this engagement to its parent client account.",
    )

    name = Column(
        String(255),
        nullable=False,
        comment="The official name of the engagement (e.g., 'US-East Datacenter Migration').",
    )
    slug = Column(
        String(100), nullable=False, comment="A URL-friendly slug for the engagement."
    )
    description = Column(
        Text, comment="A detailed description of the engagement's goals and scope."
    )

    # Engagement Details
    engagement_type = Column(
        String(50),
        default="migration",
        comment="The type of engagement (e.g., 'migration', 'discovery', 'assessment').",
    )
    status = Column(
        String(50),
        default="active",
        index=True,
        comment="The current status of the engagement (e.g., 'planning', 'active', 'completed', 'on-hold').",
    )
    priority = Column(
        String(20),
        default="medium",
        comment="The priority of the engagement (e.g., 'low', 'medium', 'high').",
    )

    # Timeline
    start_date = Column(
        DateTime(timezone=True), comment="The official start date of the engagement."
    )
    target_completion_date = Column(
        DateTime(timezone=True),
        comment="The planned completion date for the engagement.",
    )
    actual_completion_date = Column(
        DateTime(timezone=True), comment="The actual date the engagement was completed."
    )

    # Team & Contacts
    engagement_lead_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.users.id"),
        nullable=True,
        comment="The user ID of the person leading the engagement.",
    )
    client_contact_name = Column(
        String(255),
        comment="The name of the primary contact on the client's side for this engagement.",
    )
    client_contact_email = Column(
        String(255),
        comment="The email of the primary client contact for this engagement. Considered PII.",
    )

    # Settings
    settings = Column(
        JSON,
        default=lambda: {},
        comment="A JSON blob for any engagement-specific settings.",
    )

    # Enhanced Engagement Context
    migration_scope = Column(
        JSON,
        default=lambda: {
            "target_clouds": [],
            "migration_strategies": [],
            "excluded_systems": [],
            "included_environments": [],
            "business_units": [],
            "geographic_scope": [],
            "timeline_constraints": {},
        },
        comment="Defines the scope of the migration, including targets, strategies, and exclusions.",
    )

    team_preferences = Column(
        JSON,
        default=lambda: {
            "stakeholders": [],
            "decision_makers": [],
            "technical_leads": [],
            "communication_style": "formal",
            "reporting_frequency": "weekly",
            "preferred_meeting_times": [],
            "escalation_contacts": [],
            "project_methodology": "agile",
        },
        comment="Stores preferences for team collaboration and communication styles for this engagement.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the engagement was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to the engagement record.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.users.id"),
        nullable=True,
        comment="The user ID of the person who created the engagement.",
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="A soft-delete flag. If false, the engagement is considered inactive.",
    )

    # Core relationships only
    client_account = relationship("ClientAccount", back_populates="engagements")
    engagement_lead = relationship("User", foreign_keys=[engagement_lead_id])
    created_by_user = relationship("User", foreign_keys=[created_by])

    # Asset relationships (string reference to avoid circular imports)
    assets = relationship(
        "Asset",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Data import relationships (string reference to avoid circular imports)
    data_imports = relationship(
        "DataImport",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Feedback relationships (string reference to avoid circular imports)
    feedback = relationship(
        "Feedback",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # LLM usage relationships (string reference to avoid circular imports)
    llm_usage_logs = relationship(
        "LLMUsageLog",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )
    llm_usage_summaries = relationship(
        "LLMUsageSummary",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # User active flows relationships
    user_active_flows = relationship(
        "UserActiveFlow",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Collection flow relationships (string reference to avoid circular imports)
    collection_flows = relationship(
        "CollectionFlow",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Canonical application relationships (string reference to avoid circular imports)
    canonical_applications = relationship(
        "CanonicalApplication",
        back_populates="engagement",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Engagement(id={self.id}, name='{self.name}', client_account_id={self.client_account_id})>"
