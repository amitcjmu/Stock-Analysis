"""
Collection Data Population Service - Core Module

This module contains the main service class and orchestration logic for
collection data population. It coordinates between handlers and validators
to ensure proper data population for collection flows.

Key Features:
- Main service class with public API
- Flow metadata management
- Data integrity orchestration
- Atomic transaction coordination
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionGapAnalysis
from app.models.collection_data_gap import CollectionDataGap
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)

from .handlers import CollectionDataHandlers
from .validators import CollectionDataValidators

logger = logging.getLogger(__name__)


class CollectionDataPopulationService:
    """Service to ensure proper data population for collection flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        # Initialize helper modules
        self.handlers = CollectionDataHandlers(db, context)
        self.validators = CollectionDataValidators(db, context)

    async def populate_collection_data(
        self, collection_flow: CollectionFlow, force_repopulate: bool = False
    ) -> Dict[str, Any]:
        """
        Populate all child data tables for a collection flow.

        This method ensures that when a collection flow is marked as completed,
        it has proper data in all related child tables.

        Args:
            collection_flow: The collection flow to populate data for
            force_repopulate: If True, recreate data even if it exists

        Returns:
            Dictionary with population results
        """
        logger.info(
            f"Starting data population for collection flow {collection_flow.flow_id}"
        )

        results = {
            "flow_id": str(collection_flow.flow_id),
            "applications_populated": 0,
            "gaps_populated": 0,
            "inventory_populated": 0,
            "gap_analysis_created": False,
            "errors": [],
        }

        try:
            async with self.db.begin():
                # 1. Populate collection_flow_applications
                apps_result = await self.handlers.populate_collection_applications(
                    collection_flow, force_repopulate
                )
                results.update(apps_result)

                # 2. Populate collection gaps
                gaps_result = await self.handlers.populate_collection_gaps(
                    collection_flow, force_repopulate
                )
                results.update(gaps_result)

                # 3. Populate inventory data (from phase_results or collection_results)
                inventory_result = await self.handlers.populate_inventory_data(
                    collection_flow, force_repopulate
                )
                results.update(inventory_result)

                # 4. Create/update gap analysis summary
                gap_analysis_result = await self.handlers.create_gap_analysis_summary(
                    collection_flow, force_repopulate
                )
                results.update(gap_analysis_result)

                # 5. Update collection flow metadata
                await self._update_flow_metadata(collection_flow, results)

                await self.db.flush()

        except Exception as e:
            logger.error(f"Error populating collection data: {e}")
            results["errors"].append(str(e))
            raise

        logger.info(
            f"Data population completed for flow {collection_flow.flow_id}: "
            f"{results['applications_populated']} apps, {results['gaps_populated']} gaps"
        )

        return results

    async def ensure_data_integrity(self, collection_flow_id: UUID) -> Dict[str, Any]:
        """Ensure data integrity for a collection flow"""

        # Get the collection flow
        result = await self.db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == collection_flow_id,
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                )
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise ValueError(f"Collection flow {collection_flow_id} not found")

        # Check for missing child data
        issues = []
        fixes = []

        # Check applications
        apps_count = await self.db.scalar(
            select(func.count(CollectionFlowApplication.id)).where(
                CollectionFlowApplication.collection_flow_id == collection_flow.id
            )
        )

        if apps_count == 0 and collection_flow.collection_config:
            selected_apps = collection_flow.collection_config.get(
                "selected_application_ids", []
            )
            if selected_apps:
                issues.append(f"Missing {len(selected_apps)} application records")
                # Fix by populating applications
                await self.handlers.populate_collection_applications(
                    collection_flow, force_repopulate=True
                )
                fixes.append(f"Populated {len(selected_apps)} application records")

        # Check gaps
        gaps_count = await self.db.scalar(
            select(func.count(CollectionDataGap.id)).where(
                CollectionDataGap.collection_flow_id == collection_flow.id
            )
        )

        if gaps_count == 0 and collection_flow.gap_analysis_results:
            await self.handlers.populate_collection_gaps(collection_flow, force_repopulate=True)
            fixes.append("Populated gap analysis records")

        # Check gap analysis summary
        gap_analysis_count = await self.db.scalar(
            select(func.count(CollectionGapAnalysis.id)).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )

        if gap_analysis_count == 0:
            await self.handlers.create_gap_analysis_summary(
                collection_flow, force_repopulate=True
            )
            fixes.append("Created gap analysis summary")

        await self.db.commit()

        return {
            "flow_id": str(collection_flow_id),
            "issues_found": len(issues),
            "issues": issues,
            "fixes_applied": len(fixes),
            "fixes": fixes,
            "integrity_check_completed": datetime.utcnow().isoformat(),
        }

    async def _update_flow_metadata(
        self, collection_flow: CollectionFlow, population_results: Dict[str, Any]
    ) -> None:
        """Update collection flow metadata with population results"""

        current_metadata = collection_flow.flow_metadata or {}

        current_metadata["data_population"] = {
            "last_populated": datetime.utcnow().isoformat(),
            "population_results": population_results,
            "data_integrity_check": datetime.utcnow().isoformat(),
        }

        collection_flow.flow_metadata = current_metadata

        # Update progress if applications were populated
        if population_results["applications_populated"] > 0:
            collection_flow.apps_ready_for_assessment = population_results[
                "applications_populated"
            ]

        # Update assessment readiness if data is complete
        if (
            population_results["applications_populated"] > 0
            and population_results["gaps_populated"] >= 0
            and population_results["gap_analysis_created"]
        ):
            collection_flow.assessment_ready = True