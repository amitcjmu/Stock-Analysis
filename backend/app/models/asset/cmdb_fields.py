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
    )

    vendor = Column(
        String(LARGE_STRING_LENGTH),
        nullable=True,
        index=True,
        comment="Vendor or manufacturer name",
    )

    application_type = Column(
        String(20),
        nullable=True,
        comment="Application type: cots, custom, custom_cots, other",
    )

    lifecycle = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Asset lifecycle status: retire, replace, retain, invest",
    )

    # Infrastructure Fields
    hosting_model = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Hosting model: on_prem, cloud, hybrid, colo",
    )

    server_role = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Server role: web, db, app, citrix, file, email, other",
    )

    security_zone = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Network security zone or segment",
    )

    # Database Fields
    database_type = Column(
        String(MEDIUM_STRING_LENGTH),
        nullable=True,
        comment="Primary database platform name",
    )

    database_version = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Database version string",
    )

    database_size_gb = Column(
        Float,
        nullable=True,
        comment="Database size in gigabytes",
    )

    # Performance/Capacity Fields
    cpu_utilization_percent_max = Column(
        Float,
        nullable=True,
        comment="Peak CPU utilization percentage",
    )

    memory_utilization_percent_max = Column(
        Float,
        nullable=True,
        comment="Peak memory utilization percentage",
    )

    storage_free_gb = Column(
        Float,
        nullable=True,
        comment="Available storage in gigabytes",
    )

    storage_used_gb = Column(
        Float,
        nullable=True,
        comment="Used storage space in GB (calculated or imported from CMDB)",
    )

    tech_debt_flags = Column(
        Text,
        nullable=True,
        comment="Technical debt indicators and flags from CMDB assessment",
    )

    # Compliance/Security Fields
    pii_flag = Column(
        Boolean,
        default=False,
        nullable=True,
        index=True,
        comment="Contains Personally Identifiable Information",
    )

    application_data_classification = Column(
        String(SMALL_STRING_LENGTH),
        nullable=True,
        comment="Data sensitivity classification level",
    )

    # Migration Planning Fields
    has_saas_replacement = Column(
        Boolean,
        nullable=True,
        comment="SaaS alternative available for this asset",
    )

    risk_level = Column(
        String(20),
        nullable=True,
        comment="Migration risk level: low, medium, high, critical",
    )

    tshirt_size = Column(
        String(10),
        nullable=True,
        comment="Complexity sizing: xs, s, m, l, xl, xxl",
    )

    proposed_treatmentplan_rationale = Column(
        Text,
        nullable=True,
        comment="Rationale for proposed migration treatment plan",
    )

    # Financial/Operational Fields
    annual_cost_estimate = Column(
        Float,
        nullable=True,
        comment="Estimated annual operational cost",
    )

    backup_policy = Column(
        Text,
        nullable=True,
        comment="Backup and recovery policy details",
    )

    # Metadata Fields
    asset_tags = Column(
        JSONB,
        default=list,
        nullable=True,
        comment="Asset tags and labels as JSONB array",
    )
