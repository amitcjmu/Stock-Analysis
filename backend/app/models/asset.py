"""
CMDB Asset models for multi-tenant asset management.
"""

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        Enum,
        Float,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = (
        Float
    ) = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


import enum
import uuid

try:
    from app.core.database import Base
except ImportError:
    Base = object


class AssetType(str, enum.Enum):
    """Asset type enumeration based on Azure Migrate metadata."""

    # Core Infrastructure
    SERVER = "server"
    DATABASE = "database"
    APPLICATION = "application"

    # Network Devices
    NETWORK = "network"
    LOAD_BALANCER = "load_balancer"

    # Storage Devices
    STORAGE = "storage"

    # Security Devices
    SECURITY_GROUP = "security_group"

    # Virtualization
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"

    # Other/Unknown
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    """Asset discovery and migration status."""

    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategy(str, enum.Enum):
    """5R cloud migration strategy framework."""

    # Migration Lift and Shift
    REHOST = "rehost"  # Like to Like Migration: Lift and Shift (P2V/V2V), Reconfigure using IAAS

    # Legacy Modernization Treatments
    REPLATFORM = "replatform"  # Reconfigure as PaaS/IAAS treatment, framework upgrades, containerize
    REFACTOR = "refactor"  # Modify/extend code base for cloud VM/container deployment
    REARCHITECT = "rearchitect"  # Modify/extend for native container/cloud native services, microservices

    # Cloud Native
    REPLACE = "replace"  # Applications identified to be retired/modernized, replace with COTS/SaaS
    REWRITE = "rewrite"  # Re-write application in cloud native code


class Asset(Base):
    """
    Represents a single Configuration Item (CI) or asset within the CMDB.
    This is the central table for all discovered and managed assets, enriched
    with data across discovery, assessment, and planning phases.
    """

    __tablename__ = "assets"

    # Primary Key
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the asset.",
    )

    # Multi-tenant isolation
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the client account this asset belongs to.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the engagement this asset is part of.",
    )

    # Flow-based tracking (migrated from session_id)
    flow_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("discovery_flows.flow_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Legacy field linking to a discovery flow. Use master_flow_id for new logic.",
    )
    migration_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migrations.id"),
        nullable=True,
        comment="Identifier for a specific migration activity this asset is involved in.",
    )

    # Master Flow Coordination (Phase 2)
    master_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="The master flow ID that is currently processing this asset.",
    )
    discovery_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="The specific discovery flow that created or updated this asset.",
    )
    assessment_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="The assessment flow that analyzed this asset.",
    )
    planning_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="The planning flow that has included this asset.",
    )
    execution_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="The execution flow that is migrating this asset.",
    )

    # Multi-Phase Tracking (Phase 2)
    source_phase = Column(
        String(50),
        default="discovery",
        index=True,
        comment="The phase in which the asset was originally created (e.g., 'discovery').",
    )
    current_phase = Column(
        String(50),
        default="discovery",
        index=True,
        comment="The current workflow phase this asset is in (e.g., 'assessment', 'planning').",
    )
    phase_context = Column(
        JSON,
        default=dict,
        comment="A JSON blob for storing phase-specific data or state about the asset.",
    )

    # Basic asset information (based on Azure Migrate metadata)
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="The primary name of the asset.",
    )
    asset_name = Column(
        String(255), nullable=True, comment="Alternative or display name for the asset."
    )
    hostname = Column(
        String(255), index=True, comment="The hostname of the asset, if applicable."
    )
    asset_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="The type of the asset, from the AssetType enum (e.g., 'server', 'database').",
    )
    description = Column(
        Text, comment="A detailed description of the asset and its function."
    )

    # Network information
    ip_address = Column(
        String(45), comment="The primary IP address of the asset (supports IPv6)."
    )
    fqdn = Column(String(255), comment="The fully qualified domain name of the asset.")
    mac_address = Column(
        String(17), comment="The MAC address of the asset's primary network interface."
    )

    # Location and environment
    environment = Column(
        String(50),
        index=True,
        comment="The operational environment (e.g., 'Production', 'Development', 'Test').",
    )
    location = Column(
        String(100), comment="The geographical location or region of the asset."
    )
    datacenter = Column(
        String(100), comment="The datacenter where the asset is hosted."
    )
    rack_location = Column(
        String(50), comment="The specific rack location within the datacenter."
    )
    availability_zone = Column(
        String(50), comment="The cloud availability zone, if applicable."
    )

    # Technical specifications (from Azure Migrate)
    operating_system = Column(
        String(100), comment="The operating system running on the asset."
    )
    os_version = Column(String(50), comment="The version of the operating system.")
    cpu_cores = Column(
        Integer, comment="The number of CPU cores allocated to the asset."
    )
    memory_gb = Column(
        Float, comment="The amount of RAM in gigabytes allocated to the asset."
    )
    storage_gb = Column(
        Float, comment="The total storage in gigabytes allocated to the asset."
    )

    # Business information
    business_owner = Column(
        String(255),
        comment="The name of the business owner or department responsible for the asset.",
    )
    technical_owner = Column(
        String(255),
        comment="The name of the technical owner or team responsible for the asset.",
    )
    department = Column(
        String(100), comment="The business department or unit that uses this asset."
    )
    application_name = Column(
        String(255), comment="The primary application or service this asset supports."
    )
    technology_stack = Column(
        String(255), comment="A summary of the technology stack running on the asset."
    )
    criticality = Column(
        String(20),
        comment="The technical criticality of the asset (e.g., 'Low', 'Medium', 'High').",
    )
    business_criticality = Column(
        String(20), comment="The business impact or criticality of the asset."
    )
    custom_attributes = Column(
        JSON,
        comment="A JSON blob for storing any custom fields or attributes not in the standard schema.",
    )

    # Migration assessment
    six_r_strategy = Column(
        String(50),
        comment="The recommended 6R migration strategy (e.g., 'Rehost', 'Refactor').",
    )
    mapping_status = Column(
        String(20),
        index=True,
        comment="The status of the asset's field mapping during import.",
    )
    migration_priority = Column(
        Integer, default=5, comment="A priority score (1-10) for migrating this asset."
    )
    migration_complexity = Column(
        String(20),
        comment="The assessed complexity of migrating this asset (e.g., 'Low', 'Medium', 'High').",
    )
    migration_wave = Column(
        Integer, comment="The migration wave this asset is assigned to."
    )
    sixr_ready = Column(
        String(50),
        comment="Indicates if the asset is ready for 6R analysis (e.g., 'Ready', 'Needs Analysis').",
    )

    # Status and ownership
    status = Column(
        String(50),
        default="active",
        index=True,
        comment="The operational status of the asset (e.g., 'active', 'decommissioned', 'maintenance').",
    )
    migration_status = Column(
        String(50),
        default="discovered",
        index=True,
        comment="The status of the asset within the migration lifecycle (e.g., 'discovered', 'assessed', 'migrated').",
    )

    # Dependencies and relationships
    dependencies = Column(
        JSON, comment="A JSON array of assets that this asset depends on."
    )
    related_assets = Column(
        JSON, comment="A JSON array of other related assets or CIs."
    )

    # Discovery metadata
    discovery_method = Column(
        String(50),
        comment="How the asset was discovered (e.g., 'network_scan', 'agent', 'import').",
    )
    discovery_source = Column(
        String(100),
        comment="The specific tool or system that discovered the asset (e.g., 'ServiceNow', 'Azure Migrate').",
    )
    discovery_timestamp = Column(
        DateTime(timezone=True),
        comment="Timestamp of when the asset was last discovered or updated.",
    )

    # Performance and utilization (from Azure Migrate)
    cpu_utilization_percent = Column(
        Float, comment="The average CPU utilization percentage."
    )
    memory_utilization_percent = Column(
        Float, comment="The average memory utilization percentage."
    )
    disk_iops = Column(
        Float, comment="The average disk Input/Output Operations Per Second."
    )
    network_throughput_mbps = Column(
        Float, comment="The average network throughput in megabits per second."
    )

    # Data quality metrics
    completeness_score = Column(
        Float, comment="A score indicating how complete the asset's data is."
    )
    quality_score = Column(
        Float, comment="An overall data quality score for the asset record."
    )

    # Cost information
    current_monthly_cost = Column(
        Float,
        comment="The estimated current monthly cost of running the asset on-premises.",
    )
    estimated_cloud_cost = Column(
        Float, comment="The estimated monthly cost of running the asset in the cloud."
    )

    # Import and processing metadata
    imported_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user who imported the data that created this asset.",
    )
    imported_at = Column(
        DateTime(timezone=True), comment="Timestamp of when the asset was imported."
    )
    source_filename = Column(
        String(255), comment="The original filename from which this asset was imported."
    )
    raw_data = Column(
        JSON,
        comment="A JSON blob of the original, raw data for this asset from the import source.",
    )
    field_mappings_used = Column(
        JSON,
        comment="The specific field mappings that were applied to create this asset record.",
    )
    raw_import_records_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("raw_import_records.id"),
        nullable=True,
        comment="The raw import record this asset was created from.",
    )

    # is_mock removed - use multi-tenant isolation instead

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the asset record was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to the asset record.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user who originally created this asset record.",
    )
    updated_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user who last updated this asset record.",
    )

    # Relationships
    client_account = relationship("ClientAccount")
    migration = relationship("Migration", back_populates="assets")
    engagement = relationship("Engagement", back_populates="assets")
    discovery_flow = relationship(
        "DiscoveryFlow",
        foreign_keys=[flow_id],
        primaryjoin="Asset.flow_id == DiscoveryFlow.flow_id",
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"

    @property
    def is_migrated(self) -> bool:
        """Check if asset has been successfully migrated."""
        return self.status == AssetStatus.MIGRATED

    @property
    def has_dependencies(self) -> bool:
        """Check if asset has dependencies."""
        return bool(self.dependencies and len(self.dependencies) > 0)

    def get_migration_readiness_score(self) -> float:
        """Calculate migration readiness score based on various factors."""
        score = 100.0

        # Reduce score based on complexity
        complexity_penalties = {"high": 30, "medium": 15, "low": 5}
        if (
            self.migration_complexity
            and self.migration_complexity.lower() in complexity_penalties
        ):
            score -= complexity_penalties[self.migration_complexity.lower()]

        # Reduce score based on dependencies
        if self.has_dependencies:
            score -= 10

        # Reduce score if no 6R strategy assigned
        if not self.six_r_strategy:
            score -= 20

        # Reduce score for unknown asset types
        if self.asset_type == AssetType.OTHER:
            score -= 25

        return max(0.0, min(100.0, score))


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
        String(50),
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
        String(50),
        nullable=False,
        comment="The workflow stage being tracked (e.g., 'Discovery', 'Assessment', 'Migration').",
    )
    status = Column(
        String(50),
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
        String(255), nullable=False, comment="A user-defined name for the analysis."
    )
    description = Column(Text, comment="A description of the analysis goals or scope.")
    status = Column(
        String(50),
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
        String(255),
        nullable=False,
        comment="A user-defined name for the migration wave.",
    )
    description = Column(
        Text, comment="A description of the wave's goals, scope, and included assets."
    )
    status = Column(
        String(50),
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
