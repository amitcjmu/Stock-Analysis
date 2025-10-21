"""
Assessment Data Repository - Readiness Queries

Mixin for readiness assessment data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, func

from app.core.logging import get_logger
from app.models.application import Application
from app.models.assessment_flow import AssessmentFlow
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.discovery_flow import DiscoveryFlow
from app.models.server import Server

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
                    AssessmentFlow.flow_id == UUID(flow_id),
                    AssessmentFlow.client_account_id == self.client_account_id,
                    AssessmentFlow.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Error fetching assessment flow: {e}")
            return None

    async def _get_applications(self) -> List[Application]:
        """Get all applications for this engagement with tenant scoping."""
        try:
            query = select(Application).where(
                and_(
                    Application.client_account_id == self.client_account_id,
                    Application.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.warning(f"Error fetching applications: {e}")
            return []

    async def _get_servers(self) -> List[Server]:
        """Get all servers for this engagement with tenant scoping."""
        try:
            query = select(Server).where(
                and_(
                    Server.client_account_id == self.client_account_id,
                    Server.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.warning(f"Error fetching servers: {e}")
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
            logger.warning(f"Error fetching collected inventory: {e}")
            return {"by_type": [], "total_items": 0}

    async def _get_infrastructure_count(self) -> int:
        """Get count of infrastructure items."""
        try:
            query = select(func.count(Server.id)).where(
                and_(
                    Server.client_account_id == self.client_account_id,
                    Server.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.warning(f"Error counting infrastructure: {e}")
            return 0
