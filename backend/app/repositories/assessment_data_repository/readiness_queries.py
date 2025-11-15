"""
Assessment Data Repository - Readiness Queries

Mixin for readiness assessment data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, func

from app.core.logging import get_logger
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.assessment_flow import AssessmentFlow
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.discovery_flow import DiscoveryFlow
from app.models.asset import Asset

logger = get_logger(__name__)


class ReadinessQueriesMixin:
    """Mixin for readiness assessment data queries"""

    async def get_readiness_data(self, flow_id: str) -> Dict[str, Any]:
        """
        Fetch data for readiness assessment phase.

        Retrieves application metadata, technology stack information, and
        discovery flow results if available.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - applications: List of application details
                - discovery_results: Discovery flow data if available
                - collected_inventory: Collected data from platforms
                - infrastructure_count: Number of servers/infrastructure
        """
        try:
            # Get assessment flow to find associated applications
            flow = await self._get_assessment_flow(flow_id)
            if not flow:
                logger.warning(f"Assessment flow not found: {flow_id}")
                return self._empty_readiness_data()

            # Fetch applications in this engagement
            applications = await self._get_applications()

            # Fetch discovery flow results if available
            discovery_data = await self._get_discovery_data()

            # Fetch collected inventory data
            inventory_data = await self._get_collected_inventory()

            # Get infrastructure count
            infrastructure_count = await self._get_infrastructure_count()

            return {
                "applications": [
                    self._serialize_application(app) for app in applications
                ],
                "discovery_results": discovery_data,
                "collected_inventory": inventory_data,
                "infrastructure_count": infrastructure_count,
                "engagement_id": str(self.engagement_id),
                "client_account_id": str(self.client_account_id),
            }

        except Exception as e:
            logger.error(f"Error fetching readiness data: {e}")
            return self._empty_readiness_data()

    # === PRIVATE HELPER METHODS ===

    async def _get_assessment_flow(self, flow_id: str) -> Optional[AssessmentFlow]:
        """Get assessment flow by ID with tenant scoping."""
        try:
            query = select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id
                    == UUID(
                        flow_id
                    ),  # Fixed: AssessmentFlow uses 'id' not 'flow_id' (ISSUE-999)
                    AssessmentFlow.client_account_id == self.client_account_id,
                    AssessmentFlow.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Error fetching assessment flow: {e}")
            return None

    async def _get_applications(self) -> List[CanonicalApplication]:
        """Get all applications for this engagement with tenant scoping."""
        try:
            query = select(CanonicalApplication).where(
                and_(
                    CanonicalApplication.client_account_id == self.client_account_id,
                    CanonicalApplication.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.warning(f"Error fetching applications: {e}")
            return []

    async def _get_selected_applications(
        self, application_ids: List[Any]
    ) -> List[CanonicalApplication]:
        """
        Get specific applications by IDs with tenant scoping.

        ISSUE-999: Added for per-application 6R strategy generation.

        Args:
            application_ids: List of canonical application UUIDs

        Returns:
            List of CanonicalApplication models matching the IDs
        """
        try:
            from uuid import UUID

            # Convert string IDs to UUID objects if needed
            uuid_ids = []
            for app_id in application_ids:
                if isinstance(app_id, str):
                    uuid_ids.append(UUID(app_id))
                elif isinstance(app_id, UUID):
                    uuid_ids.append(app_id)
                else:
                    logger.warning(
                        f"[ISSUE-999] Skipping invalid application ID type: {type(app_id)}"
                    )

            if not uuid_ids:
                logger.warning(
                    "[ISSUE-999] No valid application IDs provided, returning empty list"
                )
                return []

            query = select(CanonicalApplication).where(
                and_(
                    CanonicalApplication.client_account_id == self.client_account_id,
                    CanonicalApplication.engagement_id == self.engagement_id,
                    CanonicalApplication.id.in_(uuid_ids),
                )
            )
            result = await self.db.execute(query)
            apps = list(result.scalars().all())

            logger.info(
                f"[ISSUE-999] Retrieved {len(apps)} applications "
                f"from {len(uuid_ids)} requested IDs"
            )

            return apps
        except Exception as e:
            logger.error(
                f"[ISSUE-999] Error fetching selected applications: {e}", exc_info=True
            )
            return []

    async def _get_applications_with_assets(
        self, application_ids: List[Any]
    ) -> Dict[str, List[Asset]]:
        """
        Get comprehensive asset data for selected applications.

        Queries collection_flow_applications to link canonical applications with their assets,
        then fetches full asset details for comprehensive data serialization.

        Args:
            application_ids: List of canonical application UUIDs

        Returns:
            Dictionary mapping canonical_application_id -> List[Asset]
        """
        try:
            from uuid import UUID

            # Convert string IDs to UUID objects if needed
            uuid_ids = []
            for app_id in application_ids:
                if isinstance(app_id, str):
                    uuid_ids.append(UUID(app_id))
                elif isinstance(app_id, UUID):
                    uuid_ids.append(app_id)
                else:
                    logger.warning(
                        f"Skipping invalid application ID type: {type(app_id)}"
                    )

            if not uuid_ids:
                logger.warning("No valid application IDs provided for asset query")
                return {}

            # Query collection_flow_applications to get asset IDs for each app
            cfa_query = select(CollectionFlowApplication).where(
                and_(
                    CollectionFlowApplication.client_account_id
                    == self.client_account_id,
                    CollectionFlowApplication.engagement_id == self.engagement_id,
                    CollectionFlowApplication.canonical_application_id.in_(uuid_ids),
                    CollectionFlowApplication.asset_id.isnot(None),
                )
            )
            cfa_result = await self.db.execute(cfa_query)
            cfa_records = list(cfa_result.scalars().all())

            logger.info(
                f"Found {len(cfa_records)} collection_flow_application records "
                f"for {len(uuid_ids)} applications"
            )

            # Build mapping: canonical_app_id -> [asset_ids]
            app_asset_map: Dict[UUID, List[UUID]] = {}
            all_asset_ids = []
            for cfa in cfa_records:
                app_id = cfa.canonical_application_id
                asset_id = cfa.asset_id
                if app_id and asset_id:
                    if app_id not in app_asset_map:
                        app_asset_map[app_id] = []
                    app_asset_map[app_id].append(asset_id)
                    all_asset_ids.append(asset_id)

            # Fetch all assets in single query
            if all_asset_ids:
                asset_query = select(Asset).where(
                    and_(
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                        Asset.id.in_(all_asset_ids),
                    )
                )
                asset_result = await self.db.execute(asset_query)
                assets_list = list(asset_result.scalars().all())

                # Build asset lookup
                asset_lookup = {asset.id: asset for asset in assets_list}

                # Build final mapping: canonical_app_id -> [Asset objects]
                result_map: Dict[str, List[Asset]] = {}
                for app_id, asset_ids in app_asset_map.items():
                    assets = [
                        asset_lookup[aid] for aid in asset_ids if aid in asset_lookup
                    ]
                    result_map[str(app_id)] = assets

                logger.info(
                    f"Retrieved {len(assets_list)} assets for {len(result_map)} applications"
                )

                return result_map
            else:
                logger.warning("No assets found for selected applications")
                return {}

        except Exception as e:
            logger.error(f"Error fetching applications with assets: {e}", exc_info=True)
            return {}

    async def _get_servers(self) -> List[Asset]:
        """Get all server assets for this engagement with tenant scoping.

        Queries the assets table for asset_type IN ('server', 'Server').
        This provides infrastructure data for dependency analysis in assessment flow.
        """
        try:
            query = select(Asset).where(
                and_(
                    Asset.client_account_id == self.client_account_id,
                    Asset.engagement_id == self.engagement_id,
                    Asset.asset_type.in_(
                        ["server", "Server"]
                    ),  # Case variations in data
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            # Rollback transaction on error
            await self.db.rollback()
            logger.warning(f"Error fetching server assets: {type(e).__name__}: {e}")
            return []

    async def _get_discovery_data(self) -> Dict[str, Any]:
        """Get discovery flow data if available."""
        try:
            query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.status == "completed",
                )
            )
            result = await self.db.execute(query)
            discovery_flows = list(result.scalars().all())

            if not discovery_flows:
                return {}

            # Return summary of discovery results
            return {
                "total_flows": len(discovery_flows),
                "flows": [
                    {
                        "flow_id": str(df.flow_id),
                        "progress": df.progress_percentage,
                        "assessment_ready": df.assessment_ready,
                    }
                    for df in discovery_flows
                ],
            }
        except Exception as e:
            logger.warning(f"Error fetching discovery data: {e}")
            return {}

    async def _get_collected_inventory(self) -> Dict[str, Any]:
        """Get collected inventory data summary with tenant scoping."""
        try:
            # Import CollectionFlow for tenant scoping join
            from app.models.collection_flow.collection_flow_model import CollectionFlow

            query = (
                select(
                    CollectedDataInventory.data_type,
                    func.count(CollectedDataInventory.id).label("count"),
                    func.avg(CollectedDataInventory.quality_score).label("avg_quality"),
                )
                .join(
                    CollectionFlow,
                    CollectedDataInventory.collection_flow_id == CollectionFlow.id,
                )
                .where(
                    # Apply proper tenant scoping via CollectionFlow
                    CollectionFlow.client_account_id == self.client_account_id,
                    CollectionFlow.engagement_id == self.engagement_id,
                )
                .group_by(CollectedDataInventory.data_type)
            )

            result = await self.db.execute(query)
            rows = result.all()

            return {
                "by_type": [
                    {
                        "data_type": row.data_type,
                        "count": row.count,
                        "avg_quality": (
                            float(row.avg_quality) if row.avg_quality else 0.0
                        ),
                    }
                    for row in rows
                ],
                "total_items": sum(row.count for row in rows),
            }
        except Exception as e:
            # Rollback transaction to prevent "transaction aborted" errors
            await self.db.rollback()
            logger.warning(f"Error fetching collected inventory: {e}")
            return {"by_type": [], "total_items": 0}

    async def _get_infrastructure_count(self) -> int:
        """Get count of server infrastructure assets.

        Counts assets with asset_type IN ('server', 'Server') for this engagement.
        """
        try:
            query = select(func.count(Asset.id)).where(
                and_(
                    Asset.client_account_id == self.client_account_id,
                    Asset.engagement_id == self.engagement_id,
                    Asset.asset_type.in_(["server", "Server"]),
                )
            )
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            # Rollback transaction on error
            await self.db.rollback()
            logger.warning(f"Error counting server assets: {type(e).__name__}: {e}")
            return 0
