"""
Asset analysis operations for dependency and technical debt analysis.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import and_, select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class AssetAnalysis:
    """Handles asset analysis operations."""

    def __init__(self, context: RequestContext):
        self.context = context

    async def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get asset dependencies for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "dependencies": {},
                    }

                # Get dependencies data from flow
                dependencies_data = getattr(flow, "dependencies_data", {}) or {}

                # Get assets for context
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.engagement_id == self.context.engagement_id,
                    )
                )
                result = await db.execute(asset_query)
                assets = result.scalars().all()

                # Build dependency map
                dependency_map = {}
                orphaned_assets = []
                highly_connected_assets = []

                for asset in assets:
                    asset_id = str(asset.id)
                    asset_dependencies = dependencies_data.get(asset_id, {})

                    dependency_info = {
                        "asset_id": asset_id,
                        "asset_name": asset.name,
                        "asset_type": asset.asset_type,
                        "depends_on": asset_dependencies.get("depends_on", []),
                        "depended_by": asset_dependencies.get("depended_by", []),
                        "dependency_count": len(
                            asset_dependencies.get("depends_on", [])
                        ),
                        "dependent_count": len(
                            asset_dependencies.get("depended_by", [])
                        ),
                    }

                    total_connections = (
                        dependency_info["dependency_count"]
                        + dependency_info["dependent_count"]
                    )

                    if total_connections == 0:
                        orphaned_assets.append(dependency_info)
                    elif total_connections > 5:
                        highly_connected_assets.append(dependency_info)

                    dependency_map[asset_id] = dependency_info

                # Generate dependency analysis
                total_assets = len(assets)
                total_dependencies = sum(
                    len(dep_info.get("depends_on", []))
                    for dep_info in dependency_map.values()
                )

                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "dependencies": dependency_map,
                    "analysis": {
                        "total_assets": total_assets,
                        "total_dependencies": total_dependencies,
                        "orphaned_assets": len(orphaned_assets),
                        "highly_connected_assets": len(highly_connected_assets),
                        "dependency_density": (
                            (total_dependencies / total_assets)
                            if total_assets > 0
                            else 0
                        ),
                    },
                    "insights": {
                        "orphaned_assets": orphaned_assets[:5],  # Top 5
                        "highly_connected_assets": highly_connected_assets[:5],  # Top 5
                    },
                    "metadata": {
                        "dependency_analysis_completed": flow.dependency_analysis_completed,
                        "analysis_timestamp": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    },
                }

            except Exception as e:
                logger.error(f"Database error in get_asset_dependencies: {e}")
                raise

    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "analysis": {},
                    }

                # Get tech debt data from flow
                tech_debt_data = getattr(flow, "tech_debt_data", {}) or {}

                # Get assets for analysis
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.engagement_id == self.context.engagement_id,
                    )
                )
                result = await db.execute(asset_query)
                assets = result.scalars().all()

                # Analyze tech debt by asset
                tech_debt_by_asset = tech_debt_data.get("by_asset", {})
                high_debt_assets = []
                medium_debt_assets = []
                low_debt_assets = []

                debt_categories = {
                    "security": 0,
                    "performance": 0,
                    "maintainability": 0,
                    "compatibility": 0,
                    "compliance": 0,
                }

                for asset in assets:
                    asset_id = str(asset.id)
                    asset_debt = tech_debt_by_asset.get(asset_id, {})

                    debt_score = asset_debt.get("debt_score", 0)
                    debt_items = asset_debt.get("debt_items", [])

                    asset_debt_info = {
                        "asset_id": asset_id,
                        "asset_name": asset.name,
                        "asset_type": asset.asset_type,
                        "debt_score": debt_score,
                        "debt_level": self._categorize_debt_level(debt_score),
                        "debt_items": debt_items,
                        "debt_count": len(debt_items),
                    }

                    # Categorize by debt level
                    if debt_score >= 7:
                        high_debt_assets.append(asset_debt_info)
                    elif debt_score >= 4:
                        medium_debt_assets.append(asset_debt_info)
                    else:
                        low_debt_assets.append(asset_debt_info)

                    # Count debt by category
                    for item in debt_items:
                        category = item.get("category", "other")
                        if category in debt_categories:
                            debt_categories[category] += 1

                # Calculate overall statistics
                total_debt_items = sum(
                    len(tech_debt_by_asset.get(str(a.id), {}).get("debt_items", []))
                    for a in assets
                )
                avg_debt_score = (
                    sum(
                        tech_debt_by_asset.get(str(a.id), {}).get("debt_score", 0)
                        for a in assets
                    )
                    / len(assets)
                    if assets
                    else 0
                )

                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "analysis": {
                        "summary": {
                            "total_assets": len(assets),
                            "total_debt_items": total_debt_items,
                            "average_debt_score": round(avg_debt_score, 2),
                            "high_debt_assets": len(high_debt_assets),
                            "medium_debt_assets": len(medium_debt_assets),
                            "low_debt_assets": len(low_debt_assets),
                        },
                        "debt_by_category": debt_categories,
                        "assets_by_debt_level": {
                            "high": high_debt_assets,
                            "medium": medium_debt_assets,
                            "low": low_debt_assets,
                        },
                        "top_issues": self._get_top_debt_issues(tech_debt_data),
                        "recommendations": self._generate_debt_recommendations(
                            debt_categories, avg_debt_score
                        ),
                    },
                    "metadata": {
                        "tech_debt_assessment_completed": flow.tech_debt_assessment_completed,
                        "analysis_timestamp": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    },
                }

            except Exception as e:
                logger.error(f"Database error in get_tech_debt_analysis: {e}")
                raise

    def _categorize_debt_level(self, debt_score: float) -> str:
        """Categorize debt level based on score"""
        if debt_score >= 7:
            return "high"
        elif debt_score >= 4:
            return "medium"
        else:
            return "low"

    def _get_top_debt_issues(
        self, tech_debt_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get top technical debt issues"""
        all_issues = tech_debt_data.get("top_issues", [])
        return sorted(all_issues, key=lambda x: x.get("severity", 0), reverse=True)[:10]

    def _generate_debt_recommendations(
        self, debt_categories: Dict[str, int], avg_debt_score: float
    ) -> List[str]:
        """Generate recommendations based on debt analysis"""
        recommendations = []

        if avg_debt_score >= 7:
            recommendations.append(
                "High technical debt detected - prioritize debt reduction before migration"
            )
        elif avg_debt_score >= 4:
            recommendations.append(
                "Moderate technical debt - plan debt reduction during migration"
            )

        # Category-specific recommendations
        if debt_categories.get("security", 0) > 0:
            recommendations.append("Address security vulnerabilities before migration")
        if debt_categories.get("performance", 0) > 0:
            recommendations.append(
                "Consider performance optimizations during migration"
            )
        if debt_categories.get("compliance", 0) > 0:
            recommendations.append(
                "Ensure compliance requirements are met in target environment"
            )

        return recommendations
