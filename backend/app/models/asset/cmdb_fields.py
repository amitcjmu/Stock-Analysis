"""
CMDB-specific field definitions for the Asset model.

These fields support comprehensive migration planning with explicit columns
for high-query frequency fields.
"""

from sqlalchemy import Boolean, Column, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from .base import (
    SMALL_STRING_LENGTH,
    MEDIUM_STRING_LENGTH,
    LARGE_STRING_LENGTH,
)


class CMDBFieldsMixin:
    """Mixin providing CMDB-specific fields for the Asset model"""

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
            "short_hint": "COTS / Custom / Custom-COTS / SaaS",
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

    # Infrastructure Fields
    hosting_model = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Hosting model: on_prem, cloud, hybrid, colo",
        info={
            "display_name": "Hosting Model",
            "short_hint": "On-Prem / Cloud / Hybrid / Colo",
            "category": "infrastructure",
        },
    )

    server_role = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Server role: web, db, app, citrix, file, email, other",
        info={
            "display_name": "Server Role",
            "short_hint": "Web / DB / App / Citrix / File / Email",
            "category": "infrastructure",
        },
    )

    security_zone = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Network security zone or segment",
        info={
            "display_name": "Security Zone",
            "short_hint": "DMZ / Internal / External / Restricted",
            "category": "security",
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
            "category": "database",
        },
    )

    database_version = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Database version string",
        info={
            "display_name": "Database Version",
            "short_hint": "Version number",
            "category": "database",
        },
    )

    database_size_gb = Column(
        Float,
        nullable=True,
        comment="Database size in gigabytes",
        info={
            "display_name": "Database Size (GB)",
            "short_hint": "In gigabytes",
            "category": "database",
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
            "category": "quality",
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
            "category": "security",
        },
    )

    application_data_classification = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Data sensitivity classification level",
        info={
            "display_name": "Data Classification",
            "short_hint": "Public / Internal / Confidential / Restricted",
            "category": "security",
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
            "category": "financial",
        },
    )

    backup_policy = Column(
        Text,
        nullable=True,
        comment="Backup and recovery policy details",
        info={
            "display_name": "Backup Policy",
            "short_hint": "Backup and recovery details",
            "category": "operational",
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
            "category": "metadata",
        },
    )
