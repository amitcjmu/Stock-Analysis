"""
Collection Data Population Service - Handlers Module

This module contains all data processing and population handlers for
collection flows. It handles the creation and population of child data
tables including applications, gaps, inventory, and analysis summaries.

Key Features:
- Collection applications population
- Collection gaps data handling
- Inventory data aggregation
- Gap analysis summary creation
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionGapAnalysis
from app.models.collection_data_gap import CollectionDataGap
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)
from app.models.asset import Asset

from .extractors import CollectionDataExtractors

logger = logging.getLogger(__name__)


class CollectionDataHandlers:
    """Handlers for data processing and population operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.extractors = CollectionDataExtractors()

    async def populate_collection_applications(
        self, collection_flow: CollectionFlow, force_repopulate: bool
    ) -> Dict[str, Any]:
        """Populate collection_flow_applications table"""

        result = {"applications_populated": 0, "applications_errors": []}

        # Check if applications already exist
        if not force_repopulate:
            existing_apps = await self.db.execute(
                select(CollectionFlowApplication).where(
                    CollectionFlowApplication.collection_flow_id == collection_flow.id
                )
            )
            if existing_apps.scalars().first():
                logger.info("Collection applications already exist, skipping")
                return result

        # Get selected application IDs from collection config
        selected_app_ids = []
        if collection_flow.collection_config:
            selected_app_ids = collection_flow.collection_config.get(
                "selected_application_ids", []
            )

        if not selected_app_ids:
            logger.warning(
                f"No selected applications found in flow {collection_flow.flow_id}"
            )
            return result

        # Get assets for these application IDs
        assets_result = await self.db.execute(
            select(Asset).where(
                and_(
                    Asset.id.in_(selected_app_ids),
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                )
            )
        )
        assets = assets_result.scalars().all()

        # Create CollectionFlowApplication records
        for asset in assets:
            try:
                # Extract data from collection results or phase results
                collection_data = self.extractors.extract_application_collection_data(
                    collection_flow, asset.id
                )

                app_record = CollectionFlowApplication(
                    id=uuid4(),
                    collection_flow_id=collection_flow.id,
                    asset_id=asset.id,
                    application_name=asset.application_name or asset.name,
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    # Data completeness metrics
                    data_completeness_score=collection_data.get(
                        "completeness_score", 0.0
                    ),
                    fields_collected=collection_data.get("fields_collected", 0),
                    fields_missing=collection_data.get("fields_missing", 0),
                    # Technical data
                    technology_stack=collection_data.get("technology_stack"),
                    dependencies_data=collection_data.get("dependencies"),
                    infrastructure_details=collection_data.get("infrastructure"),
                    # Assessment readiness
                    migration_complexity=collection_data.get("migration_complexity"),
                    business_criticality=collection_data.get("business_criticality"),
                    compliance_requirements=collection_data.get("compliance"),
                    # Collection status
                    collection_status=(
                        "completed"
                        if collection_flow.status == "completed"
                        else "in_progress"
                    ),
                    last_updated=datetime.utcnow(),
                    # Additional metadata
                    collection_notes=collection_data.get("notes"),
                    validation_status=collection_data.get(
                        "validation_status", "pending"
                    ),
                )

                self.db.add(app_record)
                result["applications_populated"] += 1

            except Exception as e:
                error_msg = (
                    f"Failed to create application record for asset {asset.id}: {e}"
                )
                logger.error(error_msg)
                result["applications_errors"].append(error_msg)

        return result

    async def populate_collection_gaps(
        self, collection_flow: CollectionFlow, force_repopulate: bool
    ) -> Dict[str, Any]:
        """Populate collection_data_gaps table"""

        result = {"gaps_populated": 0, "gaps_errors": []}

        # Check if gaps already exist
        if not force_repopulate:
            existing_gaps = await self.db.execute(
                select(CollectionDataGap).where(
                    CollectionDataGap.collection_flow_id == collection_flow.id
                )
            )
            if existing_gaps.scalars().first():
                logger.info("Collection gaps already exist, skipping")
                return result

        # Extract gaps from gap_analysis_results or phase_results
        gaps_data = self.extractors.extract_gaps_data(collection_flow)

        for gap_info in gaps_data:
            try:
                gap_record = CollectionDataGap(
                    id=uuid4(),
                    collection_flow_id=collection_flow.id,
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    # Gap identification
                    field_name=gap_info.get("field_name", "unknown_field"),
                    gap_type=gap_info.get("gap_type", "missing_data"),
                    severity=gap_info.get("severity", "medium"),
                    # Gap details
                    description=gap_info.get("description", ""),
                    category=gap_info.get("category", "uncategorized"),
                    impact_score=gap_info.get("impact_score", 0.5),
                    # Resolution
                    suggested_solution=gap_info.get("suggested_solution"),
                    resolution_effort=gap_info.get("resolution_effort", "medium"),
                    is_critical=gap_info.get("severity") in ["critical", "high"],
                    # Status
                    status="identified",
                    identified_at=datetime.utcnow(),
                    # Asset linkage
                    asset_id=gap_info.get("asset_id"),
                )

                self.db.add(gap_record)
                result["gaps_populated"] += 1

            except Exception as e:
                error_msg = f"Failed to create gap record: {e}"
                logger.error(error_msg)
                result["gaps_errors"].append(error_msg)

        return result

    async def populate_inventory_data(
        self, collection_flow: CollectionFlow, force_repopulate: bool
    ) -> Dict[str, Any]:
        """Populate inventory data from collection results"""

        result = {"inventory_populated": 0, "inventory_errors": []}

        # For now, this updates the collection_flow.collection_results
        # In the future, this could populate a separate inventory table

        try:
            # Aggregate inventory data from all sources
            inventory_data = self.extractors.aggregate_inventory_data(collection_flow)

            # Update collection_results with aggregated inventory
            current_results = collection_flow.collection_results or {}
            current_results["inventory"] = inventory_data
            current_results["last_inventory_update"] = datetime.utcnow().isoformat()

            collection_flow.collection_results = current_results
            result["inventory_populated"] = len(inventory_data.get("applications", []))

        except Exception as e:
            error_msg = f"Failed to populate inventory data: {e}"
            logger.error(error_msg)
            result["inventory_errors"].append(error_msg)

        return result

    async def create_gap_analysis_summary(
        self, collection_flow: CollectionFlow, force_repopulate: bool
    ) -> Dict[str, Any]:
        """Create or update gap analysis summary record"""

        result = {"gap_analysis_created": False, "gap_analysis_errors": []}

        try:
            # Check if gap analysis already exists
            existing_analysis = await self.db.execute(
                select(CollectionGapAnalysis).where(
                    CollectionGapAnalysis.collection_flow_id == collection_flow.id
                )
            )
            gap_analysis = existing_analysis.scalar_one_or_none()

            # Import validators here to avoid circular import
            from .validators import CollectionDataValidators

            validators = CollectionDataValidators(self.db, self.context)

            # Calculate summary metrics
            summary_metrics = await validators.calculate_gap_summary_metrics(
                collection_flow
            )

            if gap_analysis and not force_repopulate:
                # Update existing record
                for key, value in summary_metrics.items():
                    setattr(gap_analysis, key, value)
                gap_analysis.updated_at = datetime.utcnow()
            else:
                # Create new record
                gap_analysis = CollectionGapAnalysis(
                    id=uuid4(),
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    collection_flow_id=collection_flow.id,
                    analyzed_at=datetime.utcnow(),
                    **summary_metrics,
                )
                self.db.add(gap_analysis)

            result["gap_analysis_created"] = True

        except Exception as e:
            error_msg = f"Failed to create gap analysis summary: {e}"
            logger.error(error_msg)
            result["gap_analysis_errors"].append(error_msg)

        return result
