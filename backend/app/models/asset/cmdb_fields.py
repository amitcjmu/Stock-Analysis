"""
CMDB-specific field definitions for the Asset model.

These fields support comprehensive migration planning with explicit columns
for high-query frequency fields.
"""

from sqlalchemy import Boolean, Column, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from .base import (
    SMALL_STRING_LENGTH,
    MEDIUM_STRING_LENGTH,
    LARGE_STRING_LENGTH,
)
from .enums import VirtualizationType


class CMDBFieldsMixin:
    """Mixin providing CMDB-specific fields for the Asset model"""

    # Identification Fields
    serial_number = Column(
        String(MEDIUM_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Serial number or unique identifier for the asset",
        info={
            "display_name": "Serial Number",
            "short_hint": "Unique serial identifier",
            "category": "identification",
        },
    )

    # Business/Organizational Fields
    business_unit = Column(
        String(MEDIUM_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Business unit owning the asset",
        info={
            "display_name": "Business Unit",
            "short_hint": None,
            "category": "business",
        },
    )

    vendor = Column(
        String(LARGE_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Vendor or manufacturer name",
        info={
            "display_name": "Vendor",
            "short_hint": "Software/hardware vendor name",
            "category": "business",
        },
    )

    application_type = Column(
        String(20),
        nullable=True,
        comment="Application type: cots, custom, custom_cots, other",
        info={
            "display_name": "Application Type",
            "short_hint": "COTS / Custom / Custom-COTS / SaaS / Other",
            "category": "business",
        },
    )

    lifecycle = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Asset lifecycle status: retire, replace, retain, invest",
        info={
            "display_name": "Lifecycle Stage",
            "short_hint": "Retire / Replace / Retain / Invest",
            "category": "business",
        },
    )

    asset_status = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Current operational status of the asset (e.g., 'active', 'inactive', 'maintenance', 'decommissioned')",
        info={
            "display_name": "Asset Status",
            "short_hint": "Active / Inactive / Maintenance / Decommissioned",
            "category": "business",
        },
    )

    # Infrastructure Fields
    hosting_model = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Hosting model: on_prem, cloud, hybrid, colo",
        info={
            "display_name": "Hosting Model",
            "short_hint": "On-Prem / Cloud / Hybrid / Colo",
            "category": "technical",
        },
    )

    architecture_type = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Application architecture type: monolithic, microservices, serverless, hybrid",
        info={
            "display_name": "Architecture Type",
            "short_hint": "Monolithic / Microservices / Serverless / Hybrid",
            "category": "technical",
        },
    )

    server_role = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Server role: web, db, app, citrix, file, email, other",
        info={
            "display_name": "Server Role",
            "short_hint": "Web server/ DB server/ App server/ Citrix / File / Email",
            "category": "technical",
        },
    )

    security_zone = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Network security zone or segment",
        info={
            "display_name": "Security Zone",
            "short_hint": "DMZ / Internal / External / Restricted",
            "category": "business",
        },
    )

    # Database Fields
    database_type = Column(
        String(MEDIUM_STRING_LENGTH),
        nullable=True,
        comment="Primary database platform name",
        info={
            "display_name": "Database Type",
            "short_hint": "PostgreSQL / MySQL / Oracle / SQL Server / MongoDB",
            "category": "technical",
        },
    )

    database_version = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Database version string",
        info={
            "display_name": "Database Version",
            "short_hint": "Version number",
            "category": "technical",
        },
    )

    database_size_gb = Column(
        Float,
        nullable=True,
        comment="Database size in gigabytes",
        info={
            "display_name": "Database Size (GB)",
            "short_hint": "In gigabytes",
            "category": "technical",
        },
    )

    # Performance/Capacity Fields
    cpu_utilization_percent_max = Column(
        Float,
        nullable=True,
        comment="Peak CPU utilization percentage",
        info={
            "display_name": "CPU Utilization (Max %)",
            "short_hint": "0-100%",
            "category": "performance",
        },
    )

    memory_utilization_percent_max = Column(
        Float,
        nullable=True,
        comment="Peak memory utilization percentage",
        info={
            "display_name": "Memory Utilization (Max %)",
            "short_hint": "0-100%",
            "category": "performance",
        },
    )

    storage_free_gb = Column(
        Float,
        nullable=True,
        comment="Available storage in gigabytes",
        info={
            "display_name": "Storage Free (GB)",
            "short_hint": "Available storage in GB",
            "category": "performance",
        },
    )

    storage_used_gb = Column(
        Float,
        nullable=True,
        comment="Used storage space in GB (calculated or imported from CMDB)",
        info={
            "display_name": "Storage Used (GB)",
            "short_hint": "Used storage in GB",
            "category": "performance",
        },
    )

    tech_debt_flags = Column(
        Text,
        nullable=True,
        comment="Technical debt indicators and flags from CMDB assessment",
        info={
            "display_name": "Tech Debt Flags",
            "short_hint": "Technical debt indicators",
            "category": "performance",
        },
    )

    # Compliance/Security Fields
    pii_flag = Column(
        Boolean,
        default=False,
        nullable=True,
        index=True,
        comment="Contains Personally Identifiable Information",
        info={
            "display_name": "Contains PII",
            "short_hint": "true / false",
            "category": "business",
        },
    )

    application_data_classification = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Data sensitivity classification level",
        info={
            "display_name": "Data Classification",
            "short_hint": "Public / Internal / Confidential / Restricted",
            "category": "business",
        },
    )

    # Migration Planning Fields
    has_saas_replacement = Column(
        Boolean,
        nullable=True,
        comment="SaaS alternative available for this asset",
        info={
            "display_name": "Has SaaS Replacement",
            "short_hint": "true / false",
            "category": "migration",
        },
    )

    risk_level = Column(
        String(20),
        nullable=True,
        comment="Migration risk level: low, medium, high, critical",
        info={
            "display_name": "Risk Level",
            "short_hint": "Low / Medium / High / Critical",
            "category": "migration",
        },
    )

    tshirt_size = Column(
        String(10),
        nullable=True,
        comment="Complexity sizing: xs, s, m, l, xl, xxl",
        info={
            "display_name": "T-Shirt Size",
            "short_hint": "XS / S / M / L / XL / XXL",
            "category": "migration",
        },
    )

    proposed_treatmentplan_rationale = Column(
        Text,
        nullable=True,
        comment="Rationale for proposed migration treatment plan",
        info={
            "display_name": "Treatment Plan Rationale",
            "short_hint": "Explanation for recommended approach",
            "category": "migration",
        },
    )

    # Financial/Operational Fields
    annual_cost_estimate = Column(
        Float,
        nullable=True,
        comment="Estimated annual operational cost",
        info={
            "display_name": "Annual Cost Estimate",
            "short_hint": "Estimated yearly cost in USD",
            "category": "business",
        },
    )

    backup_policy = Column(
        Text,
        nullable=True,
        comment="Backup and recovery policy details",
        info={
            "display_name": "Backup Policy",
            "short_hint": "Backup and recovery details",
            "category": "migration",
        },
    )

    # Critical Assessment Fields (Issue #798)
    virtualization_platform = Column(
        String(MEDIUM_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Virtualization platform: VMware, Hyper-V, KVM, etc.",
        info={
            "display_name": "Virtualization Platform",
            "short_hint": "VMware / Hyper-V / KVM / Physical",
            "category": "technical",
        },
    )

    virtualization_type = Column(
        Enum(
            VirtualizationType,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=True,
        index=True,
        comment="Virtualization type: virtual, physical, container, other",
        info={
            "display_name": "Virtualization Type",
            "short_hint": "Virtual / Physical / Container / Other",
            "category": "technical",
        },
    )

    data_volume_characteristics = Column(
        Text,
        nullable=True,
        comment="Data volume characteristics and patterns",
        info={
            "display_name": "Data Volume Characteristics",
            "short_hint": "Data volume patterns and characteristics",
            "category": "technical",
        },
    )

    user_load_patterns = Column(
        Text,
        nullable=True,
        comment="User load patterns and traffic characteristics",
        info={
            "display_name": "User Load Patterns",
            "short_hint": "User load and traffic patterns",
            "category": "technical",
        },
    )

    business_logic_complexity = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Business logic complexity: low, medium, high, critical",
        info={
            "display_name": "Business Logic Complexity",
            "short_hint": "Low / Medium / High / Critical",
            "category": "assessment",
        },
    )

    configuration_complexity = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Configuration complexity: low, medium, high, critical",
        info={
            "display_name": "Configuration Complexity",
            "short_hint": "Low / Medium / High / Critical",
            "category": "assessment",
        },
    )

    change_tolerance = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Change tolerance level: low, medium, high",
        info={
            "display_name": "Change Tolerance",
            "short_hint": "Low / Medium / High",
            "category": "business",
        },
    )

    eol_technology_assessment = Column(
        Text,
        nullable=True,
        comment="End-of-life technology assessment details",
        info={
            "display_name": "EOL Technology Assessment",
            "short_hint": "End-of-life technology assessment",
            "category": "assessment",
        },
    )

    # Metadata Fields
    asset_tags = Column(
        JSONB,
        default=list,
        nullable=True,
        comment="Asset tags and labels as JSONB array",
        info={
            "display_name": "Asset Tags",
            "short_hint": "Tags and labels",
            "category": "other",
        },
    )
