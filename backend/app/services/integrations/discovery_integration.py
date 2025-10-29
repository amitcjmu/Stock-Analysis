"""
Discovery Flow Integration Service for Assessment Flow.
Handles integration points with Discovery Flow for application metadata and readiness management.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class DiscoveryFlowIntegration:
    """Integration service for Discovery Flow data access and coordination."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_applications_ready_for_assessment(
        self, db: AsyncSession, client_account_id: int, engagement_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get applications marked ready for assessment from Discovery Flow.

        Args:
            db: Database session
            client_account_id: Client account ID for multi-tenant filtering
            engagement_id: Engagement ID for scope filtering

        Returns:
            List of applications ready for assessment with metadata
        """
        try:
            # Query assets that are discovery-complete and ready for assessment
            stmt = (
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                select(Asset)
                .where(
                    and_(
                        Asset.client_account_id == client_account_id,
                        Asset.engagement_id == engagement_id,
                        Asset.discovery_status == "completed",
                        Asset.assessment_readiness == "ready",
                    )
                )
                .order_by(Asset.created_at.desc())
            )

            result = await db.execute(stmt)
            assets = result.scalars().all()

            applications = []
            for asset in assets:
                application_data = {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type,
                    "environment": asset.environment,
                    "discovery_completed_at": (
                        asset.discovery_completed_at.isoformat()
                        if asset.discovery_completed_at
                        else None
                    ),
                    "metadata": {
                        "technology_stack": asset.technology_stack or [],
                        "dependencies_count": len(asset.dependencies or []),
                        "criticality": asset.business_criticality,
                        "complexity_score": asset.complexity_score,
                        "data_classification": asset.data_classification,
                    },
                    "readiness_score": asset.assessment_readiness_score or 0.0,
                    "readiness_blockers": asset.assessment_blockers or [],
                }
                applications.append(application_data)

            self.logger.info(
                f"Found {len(applications)} applications ready for assessment in engagement {engagement_id}"
            )
            return applications

        except Exception as e:
            self.logger.error(
                f"Failed to get applications ready for assessment: {str(e)}"
            )
            raise

    async def verify_applications_ready_for_assessment(
        self, db: AsyncSession, application_ids: List[str], client_account_id: int
    ) -> bool:
        """
        Verify that specified applications are ready for assessment.

        Args:
            db: Database session
            application_ids: List of application IDs to verify
            client_account_id: Client account ID for multi-tenant filtering

        Returns:
            True if all applications are ready, raises exception otherwise
        """
        try:
            # Query assets to verify readiness
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.id.in_(application_ids),
                    Asset.client_account_id == client_account_id,
                )
            )

            result = await db.execute(stmt)
            assets = result.scalars().all()

            found_ids = {str(asset.id) for asset in assets}
            missing_ids = set(application_ids) - found_ids

            if missing_ids:
                raise ValueError(f"Applications not found: {', '.join(missing_ids)}")

            # Check readiness status
            not_ready = []
            for asset in assets:
                if asset.discovery_status != "completed":
                    not_ready.append(f"{asset.name} (discovery not completed)")
                elif asset.assessment_readiness != "ready":
                    not_ready.append(f"{asset.name} (not ready for assessment)")

            if not_ready:
                raise ValueError(
                    f"Applications not ready for assessment: {'; '.join(not_ready)}"
                )

            self.logger.info(
                f"Verified {len(application_ids)} applications are ready for assessment"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to verify application readiness: {str(e)}")
            raise

    async def get_application_metadata(
        self, db: AsyncSession, application_id: str, client_account_id: int
    ) -> Dict[str, Any]:
        """
        Get complete application metadata from Discovery Flow.

        Args:
            db: Database session
            application_id: Application ID
            client_account_id: Client account ID for multi-tenant filtering

        Returns:
            Complete application metadata
        """
        try:
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            # Query asset with full metadata
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.id == application_id,
                    Asset.client_account_id == client_account_id,
                )
            )

            result = await db.execute(stmt)
            asset = result.scalar_one_or_none()

            if not asset:
                raise ValueError(f"Application {application_id} not found")

            # Build comprehensive metadata
            metadata = {
                "basic_info": {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type,
                    "environment": asset.environment,
                    "description": asset.description,
                    "business_criticality": asset.business_criticality,
                },
                "discovery_info": {
                    "status": asset.discovery_status,
                    "completed_at": (
                        asset.discovery_completed_at.isoformat()
                        if asset.discovery_completed_at
                        else None
                    ),
                    "discovery_flow_id": asset.discovery_flow_id,
                    "confidence_score": asset.confidence_score,
                },
                "technical_info": {
                    "technology_stack": asset.technology_stack or [],
                    "operating_system": asset.operating_system,
                    "database_technologies": asset.database_technologies or [],
                    "network_ports": asset.network_ports or [],
                    "file_paths": asset.file_paths or [],
                },
                "architecture_info": {
                    "components": asset.components or [],
                    "dependencies": asset.dependencies or [],
                    "interfaces": asset.interfaces or [],
                    "data_flows": asset.data_flows or [],
                },
                "assessment_readiness": {
                    "status": asset.assessment_readiness,
                    "score": asset.assessment_readiness_score or 0.0,
                    "blockers": asset.assessment_blockers or [],
                    "recommendations": asset.assessment_recommendations or [],
                },
                "data_classification": {
                    "classification": asset.data_classification,
                    "sensitive_data_types": asset.sensitive_data_types or [],
                    "compliance_requirements": asset.compliance_requirements or [],
                },
                "performance_metrics": {
                    "complexity_score": asset.complexity_score,
                    "size_metrics": asset.size_metrics or {},
                    "performance_characteristics": asset.performance_characteristics
                    or {},
                },
                "raw_discovery_data": asset.raw_discovery_data or {},
            }

            self.logger.info(f"Retrieved metadata for application {application_id}")
            return metadata

        except Exception as e:
            self.logger.error(f"Failed to get application metadata: {str(e)}")
            raise

    async def update_application_assessment_status(
        self,
        db: AsyncSession,
        application_id: str,
        status: str,
        client_account_id: int,
        assessment_flow_id: Optional[str] = None,
        assessment_results: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update application assessment status and results.

        Args:
            db: Database session
            application_id: Application ID
            status: New assessment status ("in_progress", "completed", "failed")
            client_account_id: Client account ID for multi-tenant filtering
            assessment_flow_id: Optional assessment flow ID
            assessment_results: Optional assessment results to store

        Returns:
            True if updated successfully
        """
        try:
            update_data = {"assessment_status": status, "updated_at": "now()"}

            if assessment_flow_id:
                update_data["assessment_flow_id"] = assessment_flow_id

            if assessment_results:
                update_data["assessment_results"] = assessment_results

            if status == "completed":
                update_data["assessment_completed_at"] = "now()"
                # Mark as ready for planning
                update_data["planning_readiness"] = "ready"

            stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.id == application_id,
                        Asset.client_account_id == client_account_id,
                    )
                )
                .values(**update_data)
            )

            result = await db.execute(stmt)
            await db.commit()

            success = result.rowcount > 0
            if success:
                self.logger.info(
                    f"Updated assessment status for application {application_id} to {status}"
                )
            else:
                self.logger.warning(f"No rows updated for application {application_id}")

            return success

        except Exception as e:
            await db.rollback()
            self.logger.error(
                f"Failed to update application assessment status: {str(e)}"
            )
            raise

    async def update_application_readiness_status(
        self,
        db: AsyncSession,
        application_ids: List[str],
        status: str,
        client_account_id: int,
        readiness_notes: Optional[str] = None,
    ) -> bool:
        """
        Update application readiness for next flow phase.

        Args:
            db: Database session
            application_ids: List of application IDs to update
            status: New readiness status ("ready", "blocked", "in_progress")
            client_account_id: Client account ID for multi-tenant filtering
            readiness_notes: Optional notes about readiness status

        Returns:
            True if updated successfully
        """
        try:
            update_data = {"planning_readiness": status, "updated_at": "now()"}

            if readiness_notes:
                update_data["planning_readiness_notes"] = readiness_notes

            stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.id.in_(application_ids),
                        Asset.client_account_id == client_account_id,
                    )
                )
                .values(**update_data)
            )

            result = await db.execute(stmt)
            await db.commit()

            success = result.rowcount > 0
            if success:
                self.logger.info(
                    f"Updated readiness status for {result.rowcount} applications to {status}"
                )

            return success

        except Exception as e:
            await db.rollback()
            self.logger.error(
                f"Failed to update application readiness status: {str(e)}"
            )
            raise

    async def get_discovery_flow_summary(
        self, db: AsyncSession, engagement_id: int, client_account_id: int
    ) -> Dict[str, Any]:
        """
        Get summary of Discovery Flow completion for an engagement.

        Args:
            db: Database session
            engagement_id: Engagement ID
            client_account_id: Client account ID for multi-tenant filtering

        Returns:
            Discovery flow summary with statistics
        """
        try:
            # Query discovery flows for engagement
            discovery_stmt = (
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                select(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.engagement_id == engagement_id,
                        DiscoveryFlow.client_account_id == client_account_id,
                    )
                )
                .order_by(DiscoveryFlow.created_at.desc())
            )

            discovery_result = await db.execute(discovery_stmt)
            discovery_flows = discovery_result.scalars().all()

            # Query assets for engagement
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            assets_stmt = select(Asset).where(
                and_(
                    Asset.engagement_id == engagement_id,
                    Asset.client_account_id == client_account_id,
                )
            )

            assets_result = await db.execute(assets_stmt)
            assets = assets_result.scalars().all()

            # Calculate statistics
            total_assets = len(assets)
            discovery_completed = sum(
                1 for asset in assets if asset.discovery_status == "completed"
            )
            ready_for_assessment = sum(
                1 for asset in assets if asset.assessment_readiness == "ready"
            )
            assessment_completed = sum(
                1 for asset in assets if asset.assessment_status == "completed"
            )
            ready_for_planning = sum(
                1 for asset in assets if asset.planning_readiness == "ready"
            )

            summary = {
                "engagement_id": engagement_id,
                "discovery_flows": {
                    "total_flows": len(discovery_flows),
                    "active_flows": sum(
                        1 for flow in discovery_flows if flow.status == "active"
                    ),
                    "completed_flows": sum(
                        1 for flow in discovery_flows if flow.status == "completed"
                    ),
                },
                "assets": {
                    "total_assets": total_assets,
                    "discovery_completed": discovery_completed,
                    "ready_for_assessment": ready_for_assessment,
                    "assessment_completed": assessment_completed,
                    "ready_for_planning": ready_for_planning,
                },
                "readiness_percentages": {
                    "discovery_completion": (
                        (discovery_completed / total_assets * 100)
                        if total_assets > 0
                        else 0
                    ),
                    "assessment_readiness": (
                        (ready_for_assessment / total_assets * 100)
                        if total_assets > 0
                        else 0
                    ),
                    "assessment_completion": (
                        (assessment_completed / total_assets * 100)
                        if total_assets > 0
                        else 0
                    ),
                    "planning_readiness": (
                        (ready_for_planning / total_assets * 100)
                        if total_assets > 0
                        else 0
                    ),
                },
            }

            self.logger.info(
                f"Generated discovery flow summary for engagement {engagement_id}"
            )
            return summary

        except Exception as e:
            self.logger.error(f"Failed to get discovery flow summary: {str(e)}")
            raise

    async def validate_assessment_prerequisites(
        self, db: AsyncSession, application_ids: List[str], client_account_id: int
    ) -> Dict[str, Any]:
        """
        Validate that all prerequisites are met for assessment.

        Args:
            db: Database session
            application_ids: List of application IDs to validate
            client_account_id: Client account ID for multi-tenant filtering

        Returns:
            Validation results with any issues found
        """
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        try:
            # Query assets to validate prerequisites
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.id.in_(application_ids),
                    Asset.client_account_id == client_account_id,
                )
            )

            result = await db.execute(stmt)
            assets = result.scalars().all()

            validation_results = {
                "valid": True,
                "issues": [],
                "warnings": [],
                "application_status": {},
            }

            for asset in assets:
                app_issues = []
                app_warnings = []

                # Check discovery completion
                if asset.discovery_status != "completed":
                    app_issues.append("Discovery not completed")

                # Check for minimum required data
                if not asset.technology_stack:
                    app_warnings.append("Technology stack not identified")

                if not asset.components:
                    app_warnings.append("Components not identified")

                # Check assessment readiness
                if asset.assessment_readiness != "ready":
                    app_issues.append(
                        f"Assessment readiness: {asset.assessment_readiness}"
                    )

                # Check for blockers
                if asset.assessment_blockers:
                    for blocker in asset.assessment_blockers:
                        app_issues.append(f"Blocker: {blocker}")

                validation_results["application_status"][str(asset.id)] = {
                    "name": asset.name,
                    "valid": len(app_issues) == 0,
                    "issues": app_issues,
                    "warnings": app_warnings,
                }

                # Add to overall results
                validation_results["issues"].extend(
                    [f"{asset.name}: {issue}" for issue in app_issues]
                )
                validation_results["warnings"].extend(
                    [f"{asset.name}: {warning}" for warning in app_warnings]
                )

            validation_results["valid"] = len(validation_results["issues"]) == 0

            self.logger.info(
                f"Validated prerequisites for {len(application_ids)} applications"
            )
            return validation_results

        except Exception as e:
            self.logger.error(f"Failed to validate assessment prerequisites: {str(e)}")
            raise
