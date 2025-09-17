"""
Main asset model classes.

This module contains the primary Asset model and its core properties and methods.
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
    MEDIUM_STRING_LENGTH,
    LARGE_STRING_LENGTH,
    IP_ADDRESS_LENGTH,
    MAC_ADDRESS_LENGTH,
    DEFAULT_MIGRATION_PRIORITY,
    DEFAULT_STATUS,
    DEFAULT_MIGRATION_STATUS,
    DEFAULT_ASSESSMENT_READINESS,
    DEFAULT_CURRENT_PHASE,
    DEFAULT_SOURCE_PHASE,
)
from .mixins import AssetPropertiesMixin, AssetBusinessLogicMixin


class Asset(Base, AssetPropertiesMixin, AssetBusinessLogicMixin):
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
        comment="FK to client account.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to engagement.",
    )

    # Flow-based tracking (migrated from session_id)
    flow_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("discovery_flows.flow_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Legacy field. Use master_flow_id.",
    )
    migration_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migrations.id"),
        nullable=True,
        comment="Migration activity ID.",
    )

    # Master Flow Coordination (Phase 2)
    master_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Master flow ID processing this asset.",
    )
    discovery_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Discovery flow that created/updated this.",
    )
    assessment_flow_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Assessment flow that analyzed this.",
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
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_SOURCE_PHASE,
        index=True,
        comment="The phase in which the asset was originally created (e.g., 'discovery').",
    )
    current_phase = Column(
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_CURRENT_PHASE,
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
        String(LARGE_STRING_LENGTH),
        nullable=False,
        index=True,
        comment="The primary name of the asset.",
    )
    asset_name = Column(
        String(LARGE_STRING_LENGTH),
        nullable=True,
        comment="Alternative or display name for the asset.",
    )
    hostname = Column(
        String(LARGE_STRING_LENGTH),
        index=True,
        comment="The hostname of the asset, if applicable.",
    )
    asset_type = Column(
        String(SMALL_STRING_LENGTH),
        nullable=False,
        index=True,
        comment="The type of the asset, from the AssetType enum (e.g., 'server', 'database').",
    )
    description = Column(
        Text, comment="A detailed description of the asset and its function."
    )

    # Network information
    ip_address = Column(
        String(IP_ADDRESS_LENGTH),
        comment="The primary IP address of the asset (supports IPv6).",
    )
    fqdn = Column(
        String(LARGE_STRING_LENGTH),
        comment="The fully qualified domain name of the asset.",
    )
    mac_address = Column(
        String(MAC_ADDRESS_LENGTH),
        comment="The MAC address of the asset's primary network interface.",
    )

    # Location and environment
    environment = Column(
        String(SMALL_STRING_LENGTH),
        index=True,
        comment="The operational environment (e.g., 'Production', 'Development', 'Test').",
    )
    location = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The geographical location or region of the asset.",
    )
    datacenter = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The datacenter where the asset is hosted.",
    )
    rack_location = Column(
        String(SMALL_STRING_LENGTH),
        comment="The specific rack location within the datacenter.",
    )
    availability_zone = Column(
        String(SMALL_STRING_LENGTH),
        comment="The cloud availability zone, if applicable.",
    )

    # Technical specifications (from Azure Migrate)
    operating_system = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The operating system running on the asset.",
    )
    os_version = Column(
        String(SMALL_STRING_LENGTH), comment="The version of the operating system."
    )
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
        String(LARGE_STRING_LENGTH),
        comment="The name of the business owner or department responsible for the asset.",
    )
    technical_owner = Column(
        String(LARGE_STRING_LENGTH),
        comment="The name of the technical owner or team responsible for the asset.",
    )
    department = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The business department or unit that uses this asset.",
    )
    application_name = Column(
        String(LARGE_STRING_LENGTH),
        comment="The primary application or service this asset supports.",
    )
    technology_stack = Column(
        String(LARGE_STRING_LENGTH),
        comment="A summary of the technology stack running on the asset.",
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
    technical_details = Column(
        JSON,
        comment="A JSON blob containing technical details and enrichments for the asset.",
    )

    # Migration assessment
    six_r_strategy = Column(
        String(SMALL_STRING_LENGTH),
        comment="The recommended 6R migration strategy (e.g., 'Rehost', 'Refactor').",
    )
    mapping_status = Column(
        String(20),
        index=True,
        comment="The status of the asset's field mapping during import.",
    )
    migration_priority = Column(
        Integer,
        default=DEFAULT_MIGRATION_PRIORITY,
        comment="A priority score (1-10) for migrating this asset.",
    )
    migration_complexity = Column(
        String(20),
        comment="The assessed complexity of migrating this asset (e.g., 'Low', 'Medium', 'High').",
    )
    migration_wave = Column(
        Integer, comment="The migration wave this asset is assigned to."
    )
    sixr_ready = Column(
        String(SMALL_STRING_LENGTH),
        comment="Indicates if the asset is ready for 6R analysis (e.g., 'Ready', 'Needs Analysis').",
    )

    # Status and ownership
    status = Column(
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_STATUS,
        index=True,
        comment="The operational status of the asset (e.g., 'active', 'decommissioned', 'maintenance').",
    )
    migration_status = Column(
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_MIGRATION_STATUS,
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
        String(SMALL_STRING_LENGTH),
        comment="How the asset was discovered (e.g., 'network_scan', 'agent', 'import').",
    )
    discovery_source = Column(
        String(MEDIUM_STRING_LENGTH),
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
    confidence_score = Column(
        Float,
        comment="A confidence score (0.0-1.0) indicating reliability of asset data.",
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
        String(LARGE_STRING_LENGTH),
        comment="The original filename from which this asset was imported.",
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

    # Discovery/Assessment readiness fields (bridge between flows)
    discovery_status = Column(
        String(SMALL_STRING_LENGTH),
        index=True,
        comment="Discovery lifecycle status for this asset (e.g., 'completed').",
    )
    discovery_completed_at = Column(
        DateTime(timezone=True),
        comment="Timestamp when discovery completed for this asset.",
    )

    # Import local SQL text function to avoid affecting global namespace
    from sqlalchemy import text as _sql_text

    assessment_readiness = Column(
        String(SMALL_STRING_LENGTH),
        index=True,
        default=DEFAULT_ASSESSMENT_READINESS,
        server_default=_sql_text(f"'{DEFAULT_ASSESSMENT_READINESS}'"),
        comment="Assessment readiness status for this asset (e.g., 'ready', 'not_ready').",
    )
    assessment_readiness_score = Column(
        Float,
        comment="Optional readiness score (0-100 or 0-1 depending on configuration).",
    )
    assessment_blockers = Column(
        JSON, comment="List of identified blockers preventing assessment readiness."
    )
    assessment_recommendations = Column(
        JSON, comment="List of recommendations to achieve assessment readiness."
    )

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
    questionnaire_responses = relationship(
        "CollectionQuestionnaireResponse", back_populates="asset"
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
