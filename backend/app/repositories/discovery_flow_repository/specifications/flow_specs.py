"""
Flow Specifications

Reusable query specifications for discovery flows.
"""

from datetime import datetime

from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import and_
from sqlalchemy.sql import ColumnElement


class FlowSpecifications:
    """Reusable specifications for flow queries"""

    @staticmethod
    def active_flow_spec() -> ColumnElement:
        """Specification for active flows"""
        valid_active_statuses = [
            "initialized",
            "active",
            "running",
            "paused",
            # Phase names that might have been set as status
            "data_import",
            "attribute_mapping",
            "field_mapping",
            "data_cleansing",
            "inventory",
            "dependencies",
            "tech_debt",
        ]

        return DiscoveryFlow.status.in_(valid_active_statuses)

    @staticmethod
    def completed_flow_spec() -> ColumnElement:
        """Specification for completed flows"""
        return DiscoveryFlow.status == "completed"

    @staticmethod
    def incomplete_phases_spec() -> ColumnElement:
        """Specification for flows with incomplete phases"""
        return ~and_(
            DiscoveryFlow.data_import_completed is True,
            DiscoveryFlow.attribute_mapping_completed is True,
            DiscoveryFlow.data_cleansing_completed is True,
            DiscoveryFlow.inventory_completed is True,
            DiscoveryFlow.dependencies_completed is True,
            DiscoveryFlow.tech_debt_completed is True,
        )

    @staticmethod
    def assessment_ready_spec() -> ColumnElement:
        """Specification for assessment-ready flows"""
        return DiscoveryFlow.assessment_ready is True

    @staticmethod
    def by_flow_type_spec(flow_type: str) -> ColumnElement:
        """Specification for flows by type"""
        return DiscoveryFlow.flow_type == flow_type

    @staticmethod
    def has_master_flow_spec() -> ColumnElement:
        """Specification for flows with master flow reference"""
        return DiscoveryFlow.master_flow_id is not None

    @staticmethod
    def date_range_spec(start_date: datetime, end_date: datetime) -> ColumnElement:
        """Specification for flows within date range"""
        return and_(
            DiscoveryFlow.created_at >= start_date, DiscoveryFlow.created_at <= end_date
        )

    @staticmethod
    def progress_range_spec(min_progress: float, max_progress: float) -> ColumnElement:
        """Specification for flows within progress range"""
        return and_(
            DiscoveryFlow.progress_percentage >= min_progress,
            DiscoveryFlow.progress_percentage <= max_progress,
        )

    @staticmethod
    def phase_completed_spec(phase: str) -> ColumnElement:
        """Specification for flows with specific phase completed"""
        phase_map = {
            "data_import": DiscoveryFlow.data_import_completed,
            "attribute_mapping": DiscoveryFlow.attribute_mapping_completed,
            "field_mapping": DiscoveryFlow.attribute_mapping_completed,
            "data_cleansing": DiscoveryFlow.data_cleansing_completed,
            "inventory": DiscoveryFlow.inventory_completed,
            "dependencies": DiscoveryFlow.dependencies_completed,
            "tech_debt": DiscoveryFlow.tech_debt_completed,
        }

        if phase in phase_map:
            return phase_map[phase] is True

        raise ValueError(f"Unknown phase: {phase}")

    @staticmethod
    def stale_flows_spec(days: int = 7) -> ColumnElement:
        """Specification for flows not updated in X days"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return and_(
            DiscoveryFlow.status != "completed", DiscoveryFlow.updated_at < cutoff_date
        )
