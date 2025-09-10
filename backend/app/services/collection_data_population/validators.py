"""
Collection Data Population Service - Validators Module

This module contains validation and verification methods for collection
data. It handles gap analysis calculations, metrics generation, and
recommendation creation based on collection flow data.

Key Features:
- Gap summary metrics calculation
- Data quality assessment
- Gap categorization and analysis
- Recommendation generation
- Questionnaire requirements assessment
"""

import logging
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.collection_data_gap import CollectionDataGap
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)

logger = logging.getLogger(__name__)


class CollectionDataValidators:
    """Validators for data quality and gap analysis operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def calculate_gap_summary_metrics(
        self, collection_flow: CollectionFlow
    ) -> Dict[str, Any]:
        """Calculate gap analysis summary metrics"""

        # Count gaps from database
        gaps_result = await self.db.execute(
            select(CollectionDataGap).where(
                CollectionDataGap.collection_flow_id == collection_flow.id
            )
        )
        gaps = gaps_result.scalars().all()

        critical_gaps = [gap for gap in gaps if gap.is_critical]
        optional_gaps = [gap for gap in gaps if not gap.is_critical]

        # Calculate completeness from applications
        apps_result = await self.db.execute(
            select(CollectionFlowApplication).where(
                CollectionFlowApplication.collection_flow_id == collection_flow.id
            )
        )
        apps = apps_result.scalars().all()

        if apps:
            total_fields = sum(
                app.fields_collected + app.fields_missing
                for app in apps
                if app.fields_collected is not None
            )
            collected_fields = sum(
                app.fields_collected for app in apps if app.fields_collected is not None
            )
            completeness = (
                (collected_fields / total_fields * 100) if total_fields > 0 else 0
            )
            avg_data_quality = sum(
                app.data_completeness_score
                for app in apps
                if app.data_completeness_score is not None
            ) / len(apps)
        else:
            # Fallback to flow-level data
            total_fields = 100  # Default assumption
            completeness = collection_flow.progress_percentage or 0
            collected_fields = int(completeness)
            avg_data_quality = completeness / 100.0

        return {
            "total_fields_required": total_fields,
            "fields_collected": collected_fields,
            "fields_missing": total_fields - collected_fields,
            "completeness_percentage": completeness,
            "data_quality_score": avg_data_quality,
            "confidence_level": min(
                avg_data_quality + 0.1, 1.0
            ),  # Slightly higher than data quality
            "automation_coverage": 0.7,  # Default assumption
            "critical_gaps": [
                (
                    gap.to_dict()
                    if hasattr(gap, "to_dict")
                    else {
                        "field_name": gap.field_name,
                        "severity": gap.severity,
                        "description": gap.description,
                    }
                )
                for gap in critical_gaps[:10]
            ],  # Limit to 10 for performance
            "optional_gaps": [
                (
                    gap.to_dict()
                    if hasattr(gap, "to_dict")
                    else {
                        "field_name": gap.field_name,
                        "severity": gap.severity,
                        "description": gap.description,
                    }
                )
                for gap in optional_gaps[:10]
            ],
            "gap_categories": self._categorize_gaps(gaps),
            "recommended_actions": self._generate_recommendations(
                critical_gaps, optional_gaps
            ),
            "questionnaire_requirements": self._generate_questionnaire_requirements(
                gaps
            ),
        }

    def _categorize_gaps(self, gaps: List[CollectionDataGap]) -> Dict[str, int]:
        """Categorize gaps by type"""
        categories = {}
        for gap in gaps:
            category = gap.category or "uncategorized"
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _generate_recommendations(
        self,
        critical_gaps: List[CollectionDataGap],
        optional_gaps: List[CollectionDataGap],
    ) -> List[str]:
        """Generate recommendations based on gaps"""
        recommendations = []

        if critical_gaps:
            recommendations.append(
                f"Address {len(critical_gaps)} critical data gaps through manual collection"
            )

        if len(optional_gaps) > 10:
            recommendations.append(
                "Consider automated data collection for optional gaps"
            )

        # Category-specific recommendations
        gap_categories = [
            gap.category for gap in critical_gaps + optional_gaps if gap.category
        ]
        if "infrastructure" in gap_categories:
            recommendations.append(
                "Complete infrastructure discovery and documentation"
            )

        if "security" in gap_categories:
            recommendations.append("Review and document security configurations")

        return recommendations

    def _generate_questionnaire_requirements(
        self, gaps: List[CollectionDataGap]
    ) -> Dict[str, Any]:
        """Generate questionnaire requirements based on gaps"""

        requirements = {
            "technical_questionnaire": len(
                [g for g in gaps if g.category in ["infrastructure", "technical"]]
            )
            > 0,
            "business_questionnaire": len(
                [g for g in gaps if g.category in ["business", "compliance"]]
            )
            > 0,
            "security_questionnaire": len([g for g in gaps if g.category == "security"])
            > 0,
            "estimated_time": min(
                30, max(5, len(gaps) * 2)
            ),  # 2 minutes per gap, 5-30 min range
            "priority_gaps": [gap.field_name for gap in gaps if gap.is_critical][:5],
        }

        return requirements