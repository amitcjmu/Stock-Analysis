"""Discovery metadata field definitions for the Asset model."""

from sqlalchemy import Column, DateTime, String, JSON
from .base import SMALL_STRING_LENGTH, MEDIUM_STRING_LENGTH


class DiscoveryFieldsMixin:
    """Mixin providing discovery and relationship fields for the Asset model."""

    # Dependencies and relationships
    dependencies = Column(
        JSON, comment="A JSON array of assets that this asset depends on."
    )
    dependents = Column(
        JSON, comment="A JSON array of assets that depend on this asset (Issue #962)."
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
