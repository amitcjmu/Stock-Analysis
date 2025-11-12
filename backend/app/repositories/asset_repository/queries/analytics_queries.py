"""
Analytics query operations for assets.

Handles data quality and workflow analytics queries:
- Data quality summary metrics
- Workflow progress summary
- Cross-phase analytics
"""

from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.future import select

from app.models.asset import Asset
from app.repositories.asset_repository.queries.base import BaseAssetQueries


class AssetAnalyticsQueries(BaseAssetQueries):
    """Analytics query operations for assets."""

    async def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        query = select(
            func.avg(Asset.completeness_score).label("avg_completeness"),
            func.avg(Asset.quality_score).label("avg_quality"),
            func.count(Asset.id).label("total_assets"),
            func.count(Asset.missing_critical_fields).label(
                "assets_with_missing_fields"
            ),
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        row = result.first()

        return {
            "average_completeness": float(row.avg_completeness or 0),
            "average_quality": float(row.avg_quality or 0),
            "total_assets": row.total_assets,
            "assets_with_missing_fields": row.assets_with_missing_fields,
        }

    async def get_workflow_summary(self) -> Dict[str, Dict[str, int]]:
        """Get workflow progress summary across all phases."""
        phases = ["discovery", "mapping", "cleanup", "assessment"]
        statuses = ["pending", "in_progress", "completed", "failed"]

        summary = {}
        for phase in phases:
            summary[phase] = {}
            for status in statuses:
                field_name = f"{phase}_status"
                if not hasattr(Asset, field_name):
                    summary[phase][status] = 0
                    continue

                query = select(func.count(Asset.id)).where(
                    getattr(Asset, field_name) == status
                )
                query = self._apply_context_filter(query)
                result = await self.db.execute(query)
                count = result.scalar() or 0
                summary[phase][status] = count

        return summary

    async def get_master_flow_summary(self, master_flow_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a master flow."""
        # Get assets for this flow
        query = select(Asset).where(
            Asset.master_flow_id == master_flow_id
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        assets = result.scalars().all()

        summary = {
            "master_flow_id": master_flow_id,
            "total_assets": len(assets),
            "phases": {},
            "asset_types": {},
            "strategies": {},
            "status_distribution": {},
        }

        for asset in assets:
            phase = asset.current_phase or "unknown"
            summary["phases"][phase] = summary["phases"].get(phase, 0) + 1

            asset_type = asset.asset_type or "unknown"
            summary["asset_types"][asset_type] = (
                summary["asset_types"].get(asset_type, 0) + 1
            )

            strategy = asset.six_r_strategy or "unknown"
            summary["strategies"][strategy] = summary["strategies"].get(strategy, 0) + 1

            status = asset.status or "unknown"
            summary["status_distribution"][status] = (
                summary["status_distribution"].get(status, 0) + 1
            )

        return summary

    async def get_cross_phase_analytics(self) -> Dict[str, Any]:
        """Get analytics across all phases and master flows."""
        query = select(
            Asset.master_flow_id,
            Asset.source_phase,
            Asset.current_phase,
            func.count(Asset.id).label("asset_count"),
            func.avg(Asset.quality_score).label("avg_quality"),
            func.avg(Asset.completeness_score).label("avg_completeness"),
        ).group_by(Asset.master_flow_id, Asset.source_phase, Asset.current_phase)

        query = self._apply_context_filter(query)
        result = await self.db.execute(query)

        analytics = {
            "master_flows": {},
            "phase_transitions": {},
            "quality_by_phase": {},
        }

        for row in result:
            if row.master_flow_id not in analytics["master_flows"]:
                analytics["master_flows"][row.master_flow_id] = {
                    "total_assets": 0,
                    "phases": {},
                }

            analytics["master_flows"][row.master_flow_id][
                "total_assets"
            ] += row.asset_count
            analytics["master_flows"][row.master_flow_id]["phases"][
                row.current_phase
            ] = row.asset_count

            transition = f"{row.source_phase} → {row.current_phase}"
            analytics["phase_transitions"][transition] = (
                analytics["phase_transitions"].get(transition, 0) + row.asset_count
            )

            if row.current_phase not in analytics["quality_by_phase"]:
                analytics["quality_by_phase"][row.current_phase] = {
                    "avg_quality": 0,
                    "avg_completeness": 0,
                    "asset_count": 0,
                }

            analytics["quality_by_phase"][row.current_phase]["avg_quality"] = float(
                row.avg_quality or 0
            )
            analytics["quality_by_phase"][row.current_phase]["avg_completeness"] = (
                float(row.avg_completeness or 0)
            )
            analytics["quality_by_phase"][row.current_phase][
                "asset_count"
            ] += row.asset_count

        return analytics
