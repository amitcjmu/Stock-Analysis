"""
Asset relationship and dependency models.

This module contains models that define relationships between assets
and track workflow progress and analysis results.
"""

from .base import (
    Base,
    Column,
    PostgresUUID,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    relationship,
    func,
    uuid,
    SMALL_STRING_LENGTH,
    LARGE_STRING_LENGTH,
)


class AssetDependency(Base):
    """
    An association table defining a directed dependency between two assets.
    For example, an application asset might depend on a database asset.
    """

    __tablename__ = "asset_dependencies"
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the dependency relationship.",
    )
    asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="The asset that has the dependency.",
    )
    depends_on_asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="The asset that is being depended upon.",
    )
    dependency_type = Column(
        String(SMALL_STRING_LENGTH),
        nullable=False,
        comment="The type of dependency (e.g., 'database', 'application', 'storage').",
    )
    description = Column(Text, comment="A description of the dependency relationship.")
    # is_mock removed - use multi-tenant isolation instead
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the dependency was recorded.",
    )

    asset = relationship("Asset", foreign_keys=[asset_id])
    depends_on = relationship("Asset", foreign_keys=[depends_on_asset_id])


class WorkflowProgress(Base):
    """
    Tracks the progress of a single asset through various workflow stages,
    providing a detailed audit trail of its lifecycle.
    """

    __tablename__ = "workflow_progress"
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the progress record.",
    )
    asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the asset this progress record belongs to.",
    )
    stage = Column(
        String(SMALL_STRING_LENGTH),
        nullable=False,
        comment="The workflow stage being tracked (e.g., 'Discovery', 'Assessment', 'Migration').",
    )
    status = Column(
        String(SMALL_STRING_LENGTH),
        nullable=False,
        comment="The status within that stage (e.g., 'Not Started', 'In Progress', 'Completed').",
    )
    notes = Column(
        Text, comment="Any notes or logs related to this specific progress step."
    )
    # is_mock removed - use multi-tenant isolation instead
    started_at = Column(
        DateTime(timezone=True), comment="Timestamp when this stage was started."
    )
    completed_at = Column(
        DateTime(timezone=True), comment="Timestamp when this stage was completed."
    )

    asset = relationship("Asset")


class CMDBSixRAnalysis(Base):
    """
    Stores the results of a 6R (Rehost, Replatform, etc.) analysis run
    across a set of assets for a given engagement.
    """

    __tablename__ = "cmdb_sixr_analyses"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the 6R analysis run.",
    )

    # Multi-tenant isolation
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The client account this analysis belongs to.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The engagement this analysis is for.",
    )

    # Analysis metadata
    analysis_name = Column(
        String(LARGE_STRING_LENGTH),
        nullable=False,
        comment="A user-defined name for the analysis.",
    )
    description = Column(Text, comment="A description of the analysis goals or scope.")
    status = Column(
        String(SMALL_STRING_LENGTH),
        default="in_progress",
        index=True,
        comment="The status of the analysis run (e.g., 'in_progress', 'completed', 'failed').",
    )

    # Analysis results
    total_assets = Column(
        Integer,
        default=0,
        comment="The total number of assets included in this analysis.",
    )
    rehost_count = Column(
        Integer, default=0, comment="The number of assets recommended for Rehosting."
    )
    replatform_count = Column(
        Integer,
        default=0,
        comment="The number of assets recommended for Replatforming.",
    )
    refactor_count = Column(
        Integer, default=0, comment="The number of assets recommended for Refactoring."
    )
    rearchitect_count = Column(
        Integer,
        default=0,
        comment="The number of assets recommended for Rearchitecting.",
    )
    retire_count = Column(
        Integer, default=0, comment="The number of assets recommended for Retiring."
    )
    retain_count = Column(
        Integer, default=0, comment="The number of assets recommended for Retaining."
    )

    # Cost estimates
    total_current_cost = Column(
        Float,
        comment="The total estimated current monthly cost of all analyzed assets.",
    )
    total_estimated_cost = Column(
        Float,
        comment="The total estimated future monthly cost after applying the recommendations.",
    )
    potential_savings = Column(
        Float, comment="The estimated potential monthly savings."
    )

    # Analysis details
    analysis_results = Column(
        JSON,
        comment="A JSON blob containing the detailed analysis results for each individual asset.",
    )
    recommendations = Column(
        JSON,
        comment="A JSON blob containing the high-level summary and overall recommendations from the analysis.",
    )

    # is_mock removed - use multi-tenant isolation instead

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the analysis was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to the analysis.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user who initiated the analysis.",
    )

    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return f"<CMDBSixRAnalysis(id={self.id}, name='{self.analysis_name}')>"


class MigrationWave(Base):
    """
    Defines a migration wave, which is a logical grouping of assets
    to be migrated together in a phased approach.
    """

    __tablename__ = "migration_waves"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the migration wave.",
    )

    # Multi-tenant isolation
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The client account this wave belongs to.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The engagement this wave is part of.",
    )

    # Wave information
    wave_number = Column(
        Integer,
        nullable=False,
        index=True,
        comment="The sequential number of the wave (e.g., 1, 2, 3).",
    )
    name = Column(
        String(LARGE_STRING_LENGTH),
        nullable=False,
        comment="A user-defined name for the migration wave.",
    )
    description = Column(
        Text, comment="A description of the wave's goals, scope, and included assets."
    )
    status = Column(
        String(SMALL_STRING_LENGTH),
        default="planned",
        index=True,
        comment="The current status of the wave (e.g., 'planned', 'in_progress', 'completed').",
    )

    # Timeline
    planned_start_date = Column(
        DateTime(timezone=True),
        comment="The planned start date for the migration wave.",
    )
    planned_end_date = Column(
        DateTime(timezone=True), comment="The planned end date for the migration wave."
    )
    actual_start_date = Column(
        DateTime(timezone=True), comment="The actual start date of the wave."
    )
    actual_end_date = Column(
        DateTime(timezone=True), comment="The actual end date of the wave."
    )

    # Wave details
    total_assets = Column(
        Integer, default=0, comment="The total number of assets included in this wave."
    )
    completed_assets = Column(
        Integer,
        default=0,
        comment="The number of assets successfully migrated in this wave.",
    )
    failed_assets = Column(
        Integer,
        default=0,
        comment="The number of assets that failed to migrate in this wave.",
    )

    # Cost and effort
    estimated_cost = Column(
        Float, comment="The total estimated cost for this migration wave."
    )
    actual_cost = Column(
        Float, comment="The total actual cost incurred for this migration wave."
    )
    estimated_effort_hours = Column(
        Float, comment="The total estimated effort in hours for this wave."
    )
    actual_effort_hours = Column(
        Float, comment="The total actual effort in hours spent on this wave."
    )

    # is_mock removed - use multi-tenant isolation instead

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the wave was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to the wave.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user who planned or created this wave.",
    )

    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return f"<MigrationWave(id={self.id}, name='{self.name}', wave_number={self.wave_number})>"
