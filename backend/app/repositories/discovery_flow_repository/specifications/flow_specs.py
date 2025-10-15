"""
Flow Specifications

Reusable query specifications for discovery flows.
"""

from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.sql import ColumnElement

from app.models.discovery_flow import DiscoveryFlow


class FlowSpecifications:
    """Reusable specifications for flow queries"""

    @staticmethod
    def active_flow_spec() -> ColumnElement:
        """
        Specification for active flows.

        CC FIX: Per ADR-012, only use Master Flow lifecycle statuses.
        Phase-based statuses (assessment_ready, data_gathering, planning, discovery)
        have been removed from the codebase. Phase tracking uses current_phase field.
        """
        valid_active_statuses = [
            "initialized",
            "active",
            "running",
            "paused",
        ]

        return DiscoveryFlow.status.in_(valid_active_statuses)

    @staticmethod
    def completed_flow_spec() -> ColumnElement:
        """Specification for completed flows"""
        return DiscoveryFlow.status == "completed"

    @staticmethod
    def incomplete_phases_spec() -> ColumnElement:
        """
        Specification for flows with incomplete phases.

        Per ADR-027: Discovery v3.0.0 has only 5 phases.
        Legacy dependency_analysis and tech_debt_assessment columns
        retained for backward compatibility but not checked for completion.
        """
        return ~and_(
            DiscoveryFlow.data_import_completed is True,
            DiscoveryFlow.field_mapping_completed is True,
            DiscoveryFlow.data_cleansing_completed is True,
            DiscoveryFlow.asset_inventory_completed is True,
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
            "attribute_mapping": DiscoveryFlow.field_mapping_completed,
            "field_mapping": DiscoveryFlow.field_mapping_completed,
            "data_cleansing": DiscoveryFlow.data_cleansing_completed,
            "inventory": DiscoveryFlow.asset_inventory_completed,
            "dependencies": DiscoveryFlow.dependency_analysis_completed,
            "tech_debt": DiscoveryFlow.tech_debt_assessment_completed,
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
