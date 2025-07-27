"""
Core assessment manager for discovery flow completion operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset as DiscoveryAsset
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from ..assessors.complexity_assessor import ComplexityAssessor
from ..assessors.readiness_assessor import ReadinessAssessor
from ..assessors.risk_assessor import RiskAssessor

logger = logging.getLogger(__name__)


class AssessmentManager:
    """Main assessment manager for discovery flow completion and assessment handoff."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.discovery_repo = DiscoveryFlowRepository(
            db, str(context.client_account_id), str(context.engagement_id)
        )
        self.asset_repo = AssetRepository(db, str(context.client_account_id))

        # Initialize assessors
        self.readiness_assessor = ReadinessAssessor(db, context)
        self.risk_assessor = RiskAssessor(db, context)
        self.complexity_assessor = ComplexityAssessor(db, context)

    async def validate_flow_completion_readiness(
        self, discovery_flow_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Validate if a discovery flow is ready for completion and assessment handoff.

        Args:
            discovery_flow_id: UUID of the discovery flow

        Returns:
            Dict containing validation results and readiness status
        """
        try:
            logger.info(
                f"🔍 Validating completion readiness for flow: {discovery_flow_id}"
            )

            # Get discovery flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")

            # Get discovery assets
            discovery_assets = await self.db.execute(
                select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
            )
            assets = discovery_assets.scalars().all()

            # Perform readiness assessment
            readiness_result = await self.readiness_assessor.assess_flow_readiness(
                flow, assets
            )

            logger.info(
                f"✅ Flow readiness validation completed for {discovery_flow_id}"
            )
            return readiness_result

        except Exception as e:
            logger.error(f"❌ Error validating flow completion readiness: {e}")
            raise

    async def get_assessment_ready_assets(
        self, discovery_flow_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get assets that are ready for migration assessment.

        Args:
            discovery_flow_id: UUID of the discovery flow

        Returns:
            Dict containing assessment-ready assets and metadata
        """
        try:
            logger.info(
                f"📋 Getting assessment-ready assets for flow: {discovery_flow_id}"
            )

            # Get discovery flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")

            # Get all discovery assets
            discovery_assets = await self.db.execute(
                select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
            )
            assets = discovery_assets.scalars().all()

            # Filter and categorize assets
            assessment_ready = []
            needs_review = []
            insufficient_data = []

            for asset in assets:
                # Assess asset readiness
                asset_assessment = await self._assess_asset_readiness(asset)

                if asset_assessment["is_ready"]:
                    assessment_ready.append(asset_assessment)
                elif asset_assessment["needs_review"]:
                    needs_review.append(asset_assessment)
                else:
                    insufficient_data.append(asset_assessment)

            result = {
                "flow_id": str(discovery_flow_id),
                "total_assets": len(assets),
                "assessment_ready": {
                    "count": len(assessment_ready),
                    "assets": assessment_ready,
                },
                "needs_review": {"count": len(needs_review), "assets": needs_review},
                "insufficient_data": {
                    "count": len(insufficient_data),
                    "assets": insufficient_data,
                },
                "readiness_percentage": (
                    (len(assessment_ready) / len(assets) * 100) if assets else 0
                ),
            }

            logger.info(f"✅ Found {len(assessment_ready)} assessment-ready assets")
            return result

        except Exception as e:
            logger.error(f"❌ Error getting assessment-ready assets: {e}")
            raise

    async def generate_assessment_package(
        self, discovery_flow_id: uuid.UUID, include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive assessment package for migration planning.

        Args:
            discovery_flow_id: UUID of the discovery flow
            include_recommendations: Whether to include AI-generated recommendations

        Returns:
            Dict containing complete assessment package
        """
        try:
            logger.info(
                f"📦 Generating assessment package for flow: {discovery_flow_id}"
            )

            # Get flow and assets
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")

            # Get assessment-ready assets
            assets_result = await self.get_assessment_ready_assets(discovery_flow_id)
            ready_assets = assets_result["assessment_ready"]["assets"]

            # Generate risk assessment
            risk_assessment = await self.risk_assessor.assess_migration_risks(
                ready_assets
            )

            # Generate complexity assessment
            complexity_assessment = (
                await self.complexity_assessor.assess_migration_complexity(ready_assets)
            )

            # Create assessment package
            assessment_package = {
                "flow_id": str(discovery_flow_id),
                "generated_at": datetime.utcnow().isoformat(),
                "package_version": "1.0",
                "metadata": {
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id,
                    "flow_name": flow.flow_name,
                    "discovery_completed_at": (
                        flow.completed_at.isoformat() if flow.completed_at else None
                    ),
                },
                "asset_inventory": assets_result,
                "risk_assessment": risk_assessment,
                "complexity_assessment": complexity_assessment,
                "summary": {
                    "total_assets": assets_result["total_assets"],
                    "ready_for_migration": assets_result["assessment_ready"]["count"],
                    "overall_risk_score": risk_assessment.get(
                        "overall_risk_score", 0.0
                    ),
                    "overall_complexity_score": complexity_assessment.get(
                        "overall_complexity_score", 0.0
                    ),
                    "estimated_effort": complexity_assessment.get(
                        "estimated_effort", "Unknown"
                    ),
                },
            }

            # Add recommendations if requested
            if include_recommendations:
                assessment_package["recommendations"] = (
                    await self._generate_recommendations(
                        risk_assessment, complexity_assessment, assets_result
                    )
                )

            logger.info(f"✅ Assessment package generated for {discovery_flow_id}")
            return assessment_package

        except Exception as e:
            logger.error(f"❌ Error generating assessment package: {e}")
            raise

    async def complete_discovery_flow(
        self, discovery_flow_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Complete discovery flow and transition to assessment phase.

        Args:
            discovery_flow_id: UUID of the discovery flow to complete
            user_id: Optional user ID for audit trail

        Returns:
            Dict containing completion results and next steps
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {discovery_flow_id}")

            # Validate readiness
            readiness_result = await self.validate_flow_completion_readiness(
                discovery_flow_id
            )
            if not readiness_result["is_ready"]:
                raise ValueError(
                    f"Flow not ready for completion: {readiness_result['errors']}"
                )

            # Generate assessment package
            assessment_package = await self.generate_assessment_package(
                discovery_flow_id
            )

            # Update flow status
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            flow.completed_at = datetime.utcnow()
            flow.completion_status = "completed"
            flow.assessment_package_generated = True
            flow.assessment_package_data = assessment_package

            await self.db.commit()

            completion_result = {
                "flow_id": str(discovery_flow_id),
                "status": "completed",
                "completed_at": flow.completed_at.isoformat(),
                "assessment_package": assessment_package,
                "next_steps": {
                    "phase": "migration_assessment",
                    "ready_assets": assessment_package["asset_inventory"][
                        "assessment_ready"
                    ]["count"],
                    "estimated_duration": self._estimate_assessment_duration(
                        assessment_package
                    ),
                    "recommended_actions": [
                        "Review asset inventory and dependencies",
                        "Validate migration complexity assessments",
                        "Plan migration waves based on risk analysis",
                        "Prepare detailed migration runbooks",
                    ],
                },
            }

            logger.info(f"✅ Discovery flow completed: {discovery_flow_id}")
            return completion_result

        except Exception as e:
            logger.error(f"❌ Error completing discovery flow: {e}")
            await self.db.rollback()
            raise

    async def _assess_asset_readiness(self, asset: DiscoveryAsset) -> Dict[str, Any]:
        """Assess individual asset readiness for migration assessment."""

        # Basic readiness criteria
        has_required_data = bool(asset.asset_name and asset.asset_type)
        confidence_threshold = 0.7
        is_validated = asset.validation_status == "approved"

        # Determine readiness status
        is_ready = (
            has_required_data
            and (asset.confidence_score or 0) >= confidence_threshold
            and is_validated
        )

        needs_review = has_required_data and (
            (asset.confidence_score or 0) < confidence_threshold or not is_validated
        )

        return {
            "asset_id": str(asset.id),
            "asset_name": asset.asset_name,
            "asset_type": asset.asset_type,
            "is_ready": is_ready,
            "needs_review": needs_review,
            "confidence_score": asset.confidence_score,
            "validation_status": asset.validation_status,
            "migration_ready": asset.migration_ready,
            "readiness_factors": {
                "has_required_data": has_required_data,
                "meets_confidence_threshold": (asset.confidence_score or 0)
                >= confidence_threshold,
                "is_validated": is_validated,
            },
        }

    async def _generate_recommendations(
        self,
        risk_assessment: Dict[str, Any],
        complexity_assessment: Dict[str, Any],
        assets_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations based on assessments."""

        recommendations = []

        # Risk-based recommendations
        overall_risk = risk_assessment.get("overall_risk_score", 0.0)
        if overall_risk > 0.7:
            recommendations.append(
                {
                    "category": "risk_mitigation",
                    "priority": "high",
                    "title": "High Risk Migration Detected",
                    "description": "Consider phased migration approach and additional risk mitigation strategies",
                    "actions": [
                        "Implement comprehensive backup strategy",
                        "Plan detailed rollback procedures",
                        "Consider pilot migration with low-risk assets first",
                    ],
                }
            )

        # Complexity-based recommendations
        overall_complexity = complexity_assessment.get("overall_complexity_score", 0.0)
        if overall_complexity > 0.8:
            recommendations.append(
                {
                    "category": "complexity_management",
                    "priority": "medium",
                    "title": "High Complexity Migration",
                    "description": "Additional planning and specialized expertise may be required",
                    "actions": [
                        "Engage migration specialists for complex assets",
                        "Allocate additional time for migration activities",
                        "Consider modernization opportunities during migration",
                    ],
                }
            )

        # Asset readiness recommendations
        ready_percentage = assets_result.get("readiness_percentage", 0)
        if ready_percentage < 80:
            recommendations.append(
                {
                    "category": "asset_preparation",
                    "priority": "high",
                    "title": "Asset Readiness Improvement Needed",
                    "description": f"Only {ready_percentage:.1f}% of assets are ready for migration",
                    "actions": [
                        "Complete data validation for remaining assets",
                        "Resolve asset classification issues",
                        "Gather missing technical specifications",
                    ],
                }
            )

        return recommendations

    def _estimate_assessment_duration(self, assessment_package: Dict[str, Any]) -> str:
        """Estimate duration for migration assessment phase."""

        ready_assets = assessment_package["asset_inventory"]["assessment_ready"][
            "count"
        ]
        complexity_score = assessment_package["complexity_assessment"].get(
            "overall_complexity_score", 0.5
        )

        # Base duration calculation
        base_days = max(5, ready_assets * 0.5)  # Minimum 5 days, 0.5 days per asset

        # Adjust for complexity
        complexity_multiplier = 1 + (
            complexity_score * 0.5
        )  # Up to 50% increase for high complexity

        estimated_days = int(base_days * complexity_multiplier)

        if estimated_days <= 7:
            return f"{estimated_days} days"
        elif estimated_days <= 30:
            weeks = estimated_days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = estimated_days // 30
            return f"{months} month{'s' if months > 1 else ''}"
