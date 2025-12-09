"""Migration assessment field definitions for the Asset model."""

from sqlalchemy import Column, Integer, String

from .base import (
    SMALL_STRING_LENGTH,
    DEFAULT_MIGRATION_PRIORITY,
    DEFAULT_STATUS,
    DEFAULT_MIGRATION_STATUS,
)


class MigrationFieldsMixin:
    """Mixin providing migration assessment fields for the Asset model."""

    # Migration assessment
    six_r_strategy = Column(
        String(SMALL_STRING_LENGTH),
        comment="The recommended 6R migration strategy (e.g., 'Rehost', 'Refactor').",
        info={
            "display_name": "6R Strategy",
            "short_hint": "Rehost / Replatform / Refactor / Repurchase / Retire / Retain",
            "category": "migration",
        },
    )
    mapping_status = Column(
        String(20),
        index=True,
        comment="The status of the asset's field mapping during import.",
        info={
            "display_name": "Mapping Status",
            "short_hint": "Pending / Mapped / Validated",
            "category": "migration",
        },
    )
    migration_priority = Column(
        Integer,
        default=DEFAULT_MIGRATION_PRIORITY,
        comment="A priority score (1-10) for migrating this asset.",
        info={
            "display_name": "Migration Priority",
            "short_hint": "1-10 scale (10=Highest)",
            "category": "migration",
        },
    )
    migration_complexity = Column(
        String(20),
        comment="The assessed complexity of migrating this asset (e.g., 'Low', 'Medium', 'High').",
        info={
            "display_name": "Migration Complexity",
            "short_hint": "Low / Medium / High",
            "category": "migration",
        },
    )
    migration_wave = Column(
        Integer,
        comment="The migration wave this asset is assigned to.",
        info={
            "display_name": "Migration Wave",
            "short_hint": "Wave number or phase",
            "category": "migration",
        },
    )
    sixr_ready = Column(
        String(SMALL_STRING_LENGTH),
        comment="Indicates if the asset is ready for 6R analysis (e.g., 'Ready', 'Needs Analysis').",
        info={
            "display_name": "6R Readiness",
            "short_hint": "Ready / Needs Analysis",
            "category": "migration",
        },
    )

    # Status and ownership
    status = Column(
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_STATUS,
        index=True,
        comment="The operational status of the asset (e.g., 'active', 'decommissioned', 'maintenance').",
        info={
            "display_name": "Status",
            "short_hint": "Active / Decommissioned / Maintenance",
            "category": "migration",
        },
    )
    migration_status = Column(
        String(SMALL_STRING_LENGTH),
        default=DEFAULT_MIGRATION_STATUS,
        index=True,
        comment="The status of the asset within the migration lifecycle (e.g., 'discovered', 'assessed', 'migrated').",
        info={
            "display_name": "Migration Status",
            "short_hint": "Discovered / Assessed / Migrated",
            "category": "migration",
        },
    )
