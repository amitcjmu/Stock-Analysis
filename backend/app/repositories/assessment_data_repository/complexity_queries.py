"""
Assessment Data Repository - Complexity Queries

Mixin for complexity analysis data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.canonical_applications import CanonicalApplication
from sqlalchemy import select

logger = get_logger(__name__)


class ComplexityQueriesMixin:
    """Mixin for complexity analysis data queries"""

    async def get_complexity_data(self, flow_id: str) -> Dict[str, Any]:
        """
        Fetch data for complexity analysis phase.

        Retrieves component inventory, integration points, customization levels,
        and technology stack complexity indicators.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - applications: Application details with tech stacks
                - collected_components: Components from collected inventory
                - integration_points: Integration data
                - customization_indicators: Customization level data
        """
        try:
            # ISSUE-6: Get assessment flow to access selected application IDs
            flow = await self._get_assessment_flow(flow_id)
            selected_app_ids = (
                flow.selected_canonical_application_ids or [] if flow else []
            )

            # Get applications filtered by selected IDs
            if selected_app_ids:
                applications = await self._get_selected_applications(selected_app_ids)
                logger.info(
                    f"[ISSUE-6] Filtered to {len(applications)} selected applications for complexity analysis"
                )
            else:
                logger.warning(
                    "[ISSUE-6] No selected IDs, using all applications for complexity analysis"
                )
                applications = await self._get_applications()

            # Get collected inventory grouped by type
            inventory_by_type = await self._get_inventory_by_type()

            # Calculate complexity indicators
            complexity_indicators = await self._calculate_complexity_indicators(
                applications, inventory_by_type
            )

            return {
                "applications": [
                    self._serialize_application(app) for app in applications
                ],
                "inventory_by_type": inventory_by_type,
                "complexity_indicators": complexity_indicators,
                "total_applications": len(applications),
                "engagement_id": str(self.engagement_id),
            }

        except Exception as e:
            logger.error(f"Error fetching complexity data: {e}")
            return self._empty_complexity_data()

    async def _get_inventory_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get collected inventory grouped by data type with tenant scoping."""
        try:
            # Import CollectionFlow for tenant scoping join
            from app.models.collection_flow.collection_flow_model import CollectionFlow

            # Apply tenant scoping via CollectionFlow join
            query = (
                select(CollectedDataInventory)
                .join(
                    CollectionFlow,
                    CollectedDataInventory.collection_flow_id == CollectionFlow.id,
                )
                .where(
                    CollectionFlow.client_account_id == self.client_account_id,
                    CollectionFlow.engagement_id == self.engagement_id,
                )
                .limit(100)
            )
            result = await self.db.execute(query)
            items = list(result.scalars().all())

            # Group by data_type
            by_type: Dict[str, List[Dict[str, Any]]] = {}
            for item in items:
                data_type = item.data_type
                if data_type not in by_type:
                    by_type[data_type] = []

                by_type[data_type].append(
                    {
                        "id": str(item.id),
                        "platform": item.platform,
                        "resource_count": item.resource_count,
                        "quality_score": item.quality_score,
                    }
                )

            return by_type
        except Exception as e:
            logger.warning(f"Error grouping inventory by type: {e}")
            return {}

    async def _calculate_complexity_indicators(
        self,
        applications: List[CanonicalApplication],
        inventory_by_type: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Calculate complexity indicators from application and inventory data."""
        return {
            "total_applications": len(applications),
            "total_inventory_types": len(inventory_by_type),
            "applications_with_tech_stack": sum(
                1 for app in applications if app.technology_stack
            ),
            "avg_tech_stack_size": sum(
                len(app.technology_stack) if app.technology_stack else 0
                for app in applications
            )
            / max(len(applications), 1),
        }
