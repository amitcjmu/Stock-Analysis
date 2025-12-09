"""
Discovery Flow Completion Service - Package Generation Module
Handles assessment package generation and flow completion.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update

from app.models.asset import Asset as DiscoveryAsset
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery_flow_completion_service.helpers import (
    assess_asset_risk,
    determine_six_r_strategy,
    assess_modernization_potential,
    generate_migration_waves,
    generate_risk_assessment,
    generate_recommendations,
)

logger = logging.getLogger(__name__)


class AssessmentPackageGenerator:
    """Generator for assessment packages and flow completion"""

    def __init__(self, service):
        """
        Initialize package generator with parent service reference.

        Args:
            service: Parent DiscoveryFlowCompletionService instance
        """
        self.service = service
        self.db = service.db
        self.context = service.context
        self.discovery_repo = service.discovery_repo

    async def generate_assessment_package(
        self,
        discovery_flow_id: uuid.UUID,
        selected_asset_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive assessment package for handoff to assessment phase.

        Args:
            discovery_flow_id: UUID of the discovery flow
            selected_asset_ids: Optional list of specific asset IDs to include

        Returns:
            Dict containing complete assessment package
        """
        try:
            logger.info(
                f"🎯 Generating assessment package for flow: {discovery_flow_id}"
            )

            # Validate flow readiness
            validation_results = await self.service.validate_flow_completion_readiness(
                discovery_flow_id
            )
            if not validation_results["is_ready"]:
                raise ValueError(
                    f"Flow not ready for assessment: {validation_results['errors']}"
                )

            # Get flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))

            # Get assets based on selection
            discovery_assets = await self._get_assets_for_package(
                flow.id, selected_asset_ids
            )

            # Build assessment package structure
            assessment_package = self._build_package_structure(flow)

            # Process assets and populate package
            self._process_assets(discovery_assets, assessment_package)

            # Generate additional analysis
            assessment_package["migration_waves"] = generate_migration_waves(
                discovery_assets
            )
            assessment_package["risk_assessment"] = generate_risk_assessment(
                discovery_assets
            )
            assessment_package["recommendations"] = generate_recommendations(
                discovery_assets
            )

            logger.info(
                f"✅ Assessment package generated for {len(discovery_assets)} assets"
            )
            return assessment_package

        except Exception as e:
            logger.error(f"❌ Error generating assessment package: {e}")
            raise

    async def complete_discovery_flow(
        self, discovery_flow_id: uuid.UUID, assessment_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark discovery flow as complete and prepare for assessment handoff.

        Args:
            discovery_flow_id: UUID of the discovery flow
            assessment_package: Generated assessment package

        Returns:
            Dict containing completion results
        """
        try:
            logger.info(f"🎯 Completing discovery flow: {discovery_flow_id}")

            # Update flow status
            await self.db.execute(
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.flow_id == discovery_flow_id,
                        DiscoveryFlow.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .values(
                    status="completed",
                    progress_percentage=100.0,
                    assessment_ready=True,
                    completed_at=datetime.utcnow(),
                    assessment_package=assessment_package,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.commit()

            completion_result = {
                "flow_id": str(discovery_flow_id),
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "assessment_ready": True,
                "assessment_package": assessment_package,
                "next_steps": {
                    "assessment_initialization": f"/assess/initialize/{discovery_flow_id}",
                    "asset_selection": f"/assess/assets/{discovery_flow_id}",
                    "migration_planning": f"/plan/waves/{discovery_flow_id}",
                },
            }

            logger.info(
                f"✅ Discovery flow completed successfully: {discovery_flow_id}"
            )
            return completion_result

        except Exception as e:
            logger.error(f"❌ Error completing discovery flow: {e}")
            raise

    async def _get_assets_for_package(
        self, flow_internal_id: uuid.UUID, selected_asset_ids: Optional[List[str]]
    ) -> list:
        """Get assets for assessment package based on selection"""
        if selected_asset_ids:
            # Get specific selected assets
            asset_query = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow_internal_id,
                    DiscoveryAsset.id.in_(
                        [uuid.UUID(aid) for aid in selected_asset_ids]
                    ),
                    DiscoveryAsset.client_account_id == self.context.client_account_id,
                )
            )
        else:
            # Get all migration-ready assets
            asset_query = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow_internal_id,
                    DiscoveryAsset.migration_ready == True,  # noqa: E712
                    DiscoveryAsset.client_account_id == self.context.client_account_id,
                )
            )

        result = await self.db.execute(asset_query)
        return result.scalars().all()

    def _build_package_structure(self, flow: DiscoveryFlow) -> Dict[str, Any]:
        """Build the basic structure of the assessment package"""
        return {
            "package_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "discovery_flow": {
                "id": str(flow.id),
                "flow_id": str(flow.flow_id),
                "flow_name": flow.flow_name,
                "completed_at": datetime.utcnow().isoformat(),
                "progress_percentage": flow.progress_percentage,
                "migration_readiness_score": flow.migration_readiness_score,
            },
            "assets": [],
            "summary": {
                "total_assets": 0,
                "migration_ready_assets": 0,
                "by_type": {},
                "by_complexity": {},
                "by_priority": {},
                "average_confidence": 0.0,
                "total_estimated_effort": 0,
            },
            "migration_waves": [],
            "risk_assessment": {
                "overall_risk": "medium",
                "risk_factors": [],
                "mitigation_recommendations": [],
            },
            "recommendations": {
                "six_r_distribution": {},
                "modernization_opportunities": [],
                "quick_wins": [],
                "complex_migrations": [],
            },
        }

    def _process_assets(
        self, discovery_assets: list, assessment_package: Dict[str, Any]
    ) -> None:
        """Process assets and populate package data"""
        complexity_weights = {"low": 1, "medium": 3, "high": 8, "unknown": 5}
        total_confidence = 0

        for asset in discovery_assets:
            asset_data = {
                "id": str(asset.id),
                "name": asset.asset_name,
                "type": asset.asset_type,
                "subtype": asset.asset_subtype,
                "migration_ready": asset.migration_ready,
                "migration_complexity": asset.migration_complexity,
                "migration_priority": asset.migration_priority or 3,
                "confidence_score": asset.confidence_score or 0.0,
                "validation_status": asset.validation_status,
                "discovered_in_phase": asset.discovered_in_phase,
                "normalized_data": asset.normalized_data or {},
                "raw_data": asset.raw_data or {},
                "estimated_effort_weeks": complexity_weights.get(
                    asset.migration_complexity or "unknown", 5
                ),
                "six_r_recommendation": determine_six_r_strategy(asset),
                "risk_level": assess_asset_risk(asset),
                "modernization_potential": assess_modernization_potential(asset),
            }

            assessment_package["assets"].append(asset_data)

            # Update summary statistics
            self._update_summary_stats(asset, asset_data, assessment_package)
            total_confidence += asset.confidence_score or 0.0

        # Calculate averages
        if len(discovery_assets) > 0:
            assessment_package["summary"]["average_confidence"] = (
                total_confidence / len(discovery_assets)
            )
            assessment_package["summary"]["total_assets"] = len(discovery_assets)
            assessment_package["summary"]["migration_ready_assets"] = sum(
                1 for a in discovery_assets if a.migration_ready
            )

    def _update_summary_stats(
        self, asset: DiscoveryAsset, asset_data: Dict[str, Any], package: Dict[str, Any]
    ) -> None:
        """Update summary statistics for an asset"""
        asset_type = asset.asset_type or "unknown"
        package["summary"]["by_type"][asset_type] = (
            package["summary"]["by_type"].get(asset_type, 0) + 1
        )

        complexity = asset.migration_complexity or "unknown"
        package["summary"]["by_complexity"][complexity] = (
            package["summary"]["by_complexity"].get(complexity, 0) + 1
        )

        priority = asset.migration_priority or 3
        package["summary"]["by_priority"][str(priority)] = (
            package["summary"]["by_priority"].get(str(priority), 0) + 1
        )

        package["summary"]["total_estimated_effort"] += asset_data[
            "estimated_effort_weeks"
        ]
