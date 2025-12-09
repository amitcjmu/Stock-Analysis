"""
Discovery Flow Completion Service - Validation Module
Handles flow completion readiness validation and checks.
"""

import logging
import uuid
from typing import Any, Dict

from sqlalchemy import and_, select

from app.models.asset import Asset as DiscoveryAsset
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class FlowCompletionValidator:
    """Validator for discovery flow completion readiness"""

    def __init__(self, service):
        """
        Initialize validator with parent service reference.

        Args:
            service: Parent DiscoveryFlowCompletionService instance
        """
        self.service = service
        self.db = service.db
        self.context = service.context
        self.discovery_repo = service.discovery_repo

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

            # Validation checks
            validation_results = {
                "flow_id": str(discovery_flow_id),
                "is_ready": True,
                "validation_checks": {},
                "warnings": [],
                "errors": [],
                "asset_summary": {},
                "readiness_score": 0.0,
            }

            # Run all validation checks
            self._validate_phases(flow, validation_results)
            self._validate_asset_count(assets, validation_results)
            self._validate_asset_quality(assets, validation_results)
            self._validate_data_completeness(assets, validation_results)

            # Generate asset summary
            self._generate_asset_summary(assets, validation_results)

            # Calculate overall readiness score
            self._calculate_readiness_score(flow, assets, validation_results)

            logger.info(
                f"✅ Flow validation completed: {discovery_flow_id} - Ready: {validation_results['is_ready']}"
            )
            return validation_results

        except Exception as e:
            logger.error(f"❌ Error validating flow completion: {e}")
            raise

    def _validate_phases(self, flow: DiscoveryFlow, results: Dict[str, Any]) -> None:
        """Validate all required phases are completed"""
        required_phases = [
            "data_import_completed",
            "field_mapping_completed",
            "data_cleansing_completed",
            "asset_inventory_completed",
        ]

        completed_phases = []
        for phase in required_phases:
            if getattr(flow, phase, False):
                completed_phases.append(phase)

        results["validation_checks"]["phases_completed"] = {
            "required": len(required_phases),
            "completed": len(completed_phases),
            "missing": [p for p in required_phases if not getattr(flow, p, False)],
            "passed": len(completed_phases) == len(required_phases),
        }

        if len(completed_phases) < len(required_phases):
            results["errors"].append(
                f"Missing required phases: {results['validation_checks']['phases_completed']['missing']}"
            )
            results["is_ready"] = False

    def _validate_asset_count(self, assets: list, results: Dict[str, Any]) -> None:
        """Validate minimum asset count requirement"""
        min_assets = 1
        asset_count = len(assets)

        results["validation_checks"]["asset_count"] = {
            "minimum_required": min_assets,
            "actual_count": asset_count,
            "passed": asset_count >= min_assets,
        }

        if asset_count < min_assets:
            results["errors"].append(
                f"Insufficient assets: {asset_count} found, minimum {min_assets} required"
            )
            results["is_ready"] = False

    def _validate_asset_quality(self, assets: list, results: Dict[str, Any]) -> None:
        """Validate asset quality thresholds"""
        asset_count = len(assets)
        if asset_count == 0:
            return

        migration_ready_count = sum(1 for a in assets if a.migration_ready)
        high_confidence_count = sum(
            1 for a in assets if (a.confidence_score or 0) >= 0.8
        )
        validated_count = sum(1 for a in assets if a.validation_status == "approved")

        results["validation_checks"]["asset_quality"] = {
            "migration_ready": {
                "count": migration_ready_count,
                "percentage": (migration_ready_count / asset_count * 100),
                "minimum_percentage": 50,
                "passed": (migration_ready_count / asset_count * 100) >= 50,
            },
            "high_confidence": {
                "count": high_confidence_count,
                "percentage": (high_confidence_count / asset_count * 100),
                "minimum_percentage": 70,
                "passed": (high_confidence_count / asset_count * 100) >= 70,
            },
            "validated": {
                "count": validated_count,
                "percentage": (validated_count / asset_count * 100),
                "minimum_percentage": 80,
                "passed": (validated_count / asset_count * 100) >= 80,
            },
        }

        # Add warnings for quality thresholds
        if not results["validation_checks"]["asset_quality"]["migration_ready"][
            "passed"
        ]:
            results["warnings"].append(
                f"Low migration readiness: {migration_ready_count}/{asset_count} assets ready"
            )

        if not results["validation_checks"]["asset_quality"]["high_confidence"][
            "passed"
        ]:
            results["warnings"].append(
                f"Low confidence scores: {high_confidence_count}/{asset_count} assets with >80% confidence"
            )

        if not results["validation_checks"]["asset_quality"]["validated"]["passed"]:
            results["warnings"].append(
                f"Low validation rate: {validated_count}/{asset_count} assets validated"
            )

    def _validate_data_completeness(
        self, assets: list, results: Dict[str, Any]
    ) -> None:
        """Validate critical data completeness"""
        asset_count = len(assets)
        if asset_count == 0:
            return

        assets_with_names = sum(
            1 for a in assets if a.asset_name and a.asset_name.strip()
        )
        assets_with_types = sum(
            1 for a in assets if a.asset_type and a.asset_type.strip()
        )

        results["validation_checks"]["data_completeness"] = {
            "assets_with_names": {
                "count": assets_with_names,
                "percentage": (assets_with_names / asset_count * 100),
                "passed": assets_with_names == asset_count,
            },
            "assets_with_types": {
                "count": assets_with_types,
                "percentage": (assets_with_types / asset_count * 100),
                "passed": assets_with_types == asset_count,
            },
        }

        if assets_with_names < asset_count:
            results["errors"].append(
                f"Missing asset names: {asset_count - assets_with_names} assets without names"
            )
            results["is_ready"] = False

        if assets_with_types < asset_count:
            results["warnings"].append(
                f"Missing asset types: {asset_count - assets_with_types} assets without types"
            )

    def _generate_asset_summary(self, assets: list, results: Dict[str, Any]) -> None:
        """Generate summary statistics for assets"""
        asset_count = len(assets)
        migration_ready_count = sum(1 for a in assets if a.migration_ready)

        asset_types = {}
        migration_complexities = {}
        for asset in assets:
            # Count by type
            asset_type = asset.asset_type or "unknown"
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1

            # Count by complexity
            complexity = asset.migration_complexity or "unknown"
            migration_complexities[complexity] = (
                migration_complexities.get(complexity, 0) + 1
            )

        results["asset_summary"] = {
            "total_assets": asset_count,
            "migration_ready": migration_ready_count,
            "by_type": asset_types,
            "by_complexity": migration_complexities,
            "average_confidence": (
                sum(a.confidence_score or 0 for a in assets) / asset_count
                if asset_count > 0
                else 0
            ),
        }

    def _calculate_readiness_score(
        self, flow: DiscoveryFlow, assets: list, results: Dict[str, Any]
    ) -> None:
        """Calculate overall readiness score"""
        required_phases = [
            "data_import_completed",
            "field_mapping_completed",
            "data_cleansing_completed",
            "asset_inventory_completed",
        ]
        completed_phases = [p for p in required_phases if getattr(flow, p, False)]

        asset_count = len(assets)
        min_assets = 1
        migration_ready_count = sum(1 for a in assets if a.migration_ready)
        high_confidence_count = sum(
            1 for a in assets if (a.confidence_score or 0) >= 0.8
        )
        validated_count = sum(1 for a in assets if a.validation_status == "approved")

        phase_score = (len(completed_phases) / len(required_phases)) * 30
        asset_count_score = min(asset_count / min_assets, 1.0) * 20
        migration_ready_score = (
            (migration_ready_count / asset_count) * 25 if asset_count > 0 else 0
        )
        confidence_score = (
            (high_confidence_count / asset_count) * 15 if asset_count > 0 else 0
        )
        validation_score = (
            (validated_count / asset_count) * 10 if asset_count > 0 else 0
        )

        results["readiness_score"] = (
            phase_score
            + asset_count_score
            + migration_ready_score
            + confidence_score
            + validation_score
        )
