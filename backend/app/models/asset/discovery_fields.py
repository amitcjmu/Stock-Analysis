"""Discovery metadata field definitions for the Asset model."""

from sqlalchemy import Column, DateTime, String, JSON
from .base import SMALL_STRING_LENGTH, MEDIUM_STRING_LENGTH


class DiscoveryFieldsMixin:
    """Mixin providing discovery and relationship fields for the Asset model."""

    # Dependencies and relationships
    dependencies = Column(
        JSON,
        comment="A JSON array of assets that this asset depends on.",
        info={
            "display_name": "Dependencies",
            "short_hint": "Assets this depends on",
            "category": "technical",
        },
    )
    dependents = Column(
        JSON,
        comment="A JSON array of assets that depend on this asset (Issue #962).",
        info={
            "display_name": "Dependents",
            "short_hint": "Assets depending on this",
            "category": "technical",
        },
    )
    related_assets = Column(
        JSON,
        comment="A JSON array of other related assets or CIs.",
        info={
            "display_name": "Related Assets",
            "short_hint": "Related configuration items",
            "category": "technical",
        },
    )

    # Discovery metadata
    discovery_method = Column(
        String(SMALL_STRING_LENGTH),
        comment="How the asset was discovered (e.g., 'network_scan', 'agent', 'import').",
        info={
            "display_name": "Discovery Method",
            "short_hint": "Network Scan / Agent / Import",
            "category": "identification",
        },
    )
    discovery_source = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The specific tool or system that discovered the asset (e.g., 'ServiceNow', 'Azure Migrate').",
        info={
            "display_name": "Discovery Source",
            "short_hint": "ServiceNow / Azure Migrate / Manual",
            "category": "identification",
        },
    )
    discovery_timestamp = Column(
        DateTime(timezone=True),
        comment="Timestamp of when the asset was last discovered or updated.",
        info={
            "display_name": "Discovery Timestamp",
            "short_hint": "Last discovery update",
            "category": "identification",
        },
    )
