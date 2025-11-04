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
    DEFAULT_CURRENT_PHASE,
    DEFAULT_SOURCE_PHASE,
)
from .mixins import AssetPropertiesMixin, AssetBusinessLogicMixin
from .assessment_fields import AssessmentFieldsMixin
from .import_fields import ImportFieldsMixin
from .cmdb_fields import CMDBFieldsMixin
from .location_fields import LocationFieldsMixin
from .performance_fields import PerformanceFieldsMixin
from .discovery_fields import DiscoveryFieldsMixin
from .business_fields import BusinessFieldsMixin
from .migration_fields import MigrationFieldsMixin


class Asset(
    Base,
    AssetPropertiesMixin,
    AssetBusinessLogicMixin,
    AssessmentFieldsMixin,
    ImportFieldsMixin,
    CMDBFieldsMixin,
    LocationFieldsMixin,
    PerformanceFieldsMixin,
    DiscoveryFieldsMixin,
    BusinessFieldsMixin,
    MigrationFieldsMixin,
):
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
        info={
            "display_name": "Asset Name",
            "short_hint": "Primary asset identifier",
            "category": "identification",
        },
    )
    asset_name = Column(
        String(LARGE_STRING_LENGTH),
        nullable=True,
        comment="Alternative or display name for the asset.",
        info={
            "display_name": "Display Name",
            "short_hint": "Friendly display name",
            "category": "identification",
        },
    )
    hostname = Column(
        String(LARGE_STRING_LENGTH),
        index=True,
        comment="The hostname of the asset, if applicable.",
        info={
            "display_name": "Hostname",
            "short_hint": "System hostname",
            "category": "identification",
        },
    )
    asset_type = Column(
        String(SMALL_STRING_LENGTH),
        nullable=False,
        index=True,
        comment="The type of the asset, from the AssetType enum (e.g., 'server', 'database').",
        info={
            "display_name": "Asset Type",
            "short_hint": "Server / Database / Application / Network Device",
            "category": "identification",
        },
    )
    description = Column(
        Text,
        comment="A detailed description of the asset and its function.",
        info={
            "display_name": "Description",
            "short_hint": "Asset description",
            "category": "identification",
        },
    )

    # Network information
    ip_address = Column(
        String(IP_ADDRESS_LENGTH),
        comment="The primary IP address of the asset (supports IPv6).",
        info={
            "display_name": "IP Address",
            "short_hint": "Primary IP address",
            "category": "identification",
        },
    )
    fqdn = Column(
        String(LARGE_STRING_LENGTH),
        comment="The fully qualified domain name of the asset.",
        info={
            "display_name": "FQDN",
            "short_hint": "Fully qualified domain name",
            "category": "identification",
        },
    )
    mac_address = Column(
        String(MAC_ADDRESS_LENGTH),
        comment="The MAC address of the asset's primary network interface.",
        info={
            "display_name": "MAC Address",
            "short_hint": "Network MAC address",
            "category": "identification",
        },
    )
    # Technical specifications (from Azure Migrate)
    operating_system = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The operating system running on the asset.",
        info={
            "display_name": "Operating System",
            "short_hint": "Windows / Linux / Unix / AIX",
            "category": "technical",
        },
    )
    os_version = Column(
        String(SMALL_STRING_LENGTH),
        comment="The version of the operating system.",
        info={
            "display_name": "OS Version",
            "short_hint": "Operating system version",
            "category": "technical",
        },
    )
    cpu_cores = Column(
        Integer,
        comment="The number of CPU cores allocated to the asset.",
        info={
            "display_name": "CPU Cores",
            "short_hint": "Number of cores",
            "category": "technical",
        },
    )
    memory_gb = Column(
        Float,
        comment="The amount of RAM in gigabytes allocated to the asset.",
        info={
            "display_name": "Memory (GB)",
            "short_hint": "RAM in gigabytes",
            "category": "technical",
        },
    )
    storage_gb = Column(
        Float,
        comment="The total storage in gigabytes allocated to the asset.",
        info={
            "display_name": "Storage (GB)",
            "short_hint": "Total storage in gigabytes",
            "category": "technical",
        },
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
    # field_conflicts = relationship("AssetFieldConflict", back_populates="asset")
    # Removed - causing circular dependency

    # Enrichment relationships (1:1) - PHASE 2 Bug #679
    # Eager loading with selectinload for intelligent gap detection
    resilience = relationship(
        "AssetResilience",
        uselist=False,
        back_populates="asset",
        lazy="selectin",
    )
    compliance_flags = relationship(
        "AssetComplianceFlags",
        uselist=False,
        back_populates="asset",
        lazy="selectin",
    )
    vulnerabilities = relationship(
        "AssetVulnerabilities",
        back_populates="asset",
        lazy="selectin",
    )
    licenses = relationship(
        "AssetLicenses",
        back_populates="asset",
        lazy="selectin",
    )
    eol_assessments = relationship(
        "AssetEOLAssessment",
        back_populates="asset",
        lazy="selectin",
    )
    contacts = relationship(
        "AssetContact",
        back_populates="asset",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
