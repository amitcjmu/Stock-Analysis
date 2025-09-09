"""
Collection Data Population Service

This service fixes the database population issues identified in validation:
- Collection flows marked "completed" have no child data
- Ensures data is properly saved when collection processes run
- Populates collection_flow_applications, collection_flow_gaps, collection_flow_inventory
- Maintains data integrity between master and child flows
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionGapAnalysis
from app.models.collection_data_gap import CollectionDataGap
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)
from app.models.asset import Asset

logger = logging.getLogger(__name__)


class CollectionDataPopulationService:
    """Service to ensure proper data population for collection flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

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
                apps_result = await self._populate_collection_applications(
                    collection_flow, force_repopulate
                )
                results.update(apps_result)

                # 2. Populate collection gaps
                gaps_result = await self._populate_collection_gaps(
                    collection_flow, force_repopulate
                )
                results.update(gaps_result)

                # 3. Populate inventory data (from phase_results or collection_results)
                inventory_result = await self._populate_inventory_data(
                    collection_flow, force_repopulate
                )
                results.update(inventory_result)

                # 4. Create/update gap analysis summary
                gap_analysis_result = await self._create_gap_analysis_summary(
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

    async def _populate_collection_applications(
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
                collection_data = self._extract_application_collection_data(
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

    async def _populate_collection_gaps(
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
        gaps_data = self._extract_gaps_data(collection_flow)

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

    async def _populate_inventory_data(
        self, collection_flow: CollectionFlow, force_repopulate: bool
    ) -> Dict[str, Any]:
        """Populate inventory data from collection results"""

        result = {"inventory_populated": 0, "inventory_errors": []}

        # For now, this updates the collection_flow.collection_results
        # In the future, this could populate a separate inventory table

        try:
            # Aggregate inventory data from all sources
            inventory_data = self._aggregate_inventory_data(collection_flow)

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

    async def _create_gap_analysis_summary(
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

            # Calculate summary metrics
            summary_metrics = await self._calculate_gap_summary_metrics(collection_flow)

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

    def _extract_application_collection_data(
        self, collection_flow: CollectionFlow, asset_id: UUID
    ) -> Dict[str, Any]:
        """Extract collection data for a specific application"""

        collection_data = {
            "completeness_score": 0.0,
            "fields_collected": 0,
            "fields_missing": 0,
            "technology_stack": {},
            "dependencies": {},
            "infrastructure": {},
            "migration_complexity": None,
            "business_criticality": None,
            "compliance": {},
            "notes": "",
            "validation_status": "pending",
        }

        # Extract from collection_results
        if collection_flow.collection_results:
            app_data = collection_flow.collection_results.get("applications", {}).get(
                str(asset_id)
            )
            if app_data:
                collection_data.update(app_data)

        # Extract from phase_results
        if collection_flow.phase_results:
            for phase, results in collection_flow.phase_results.items():
                if isinstance(results, dict) and "applications" in results:
                    app_data = results["applications"].get(str(asset_id))
                    if app_data:
                        # Merge data, preferring more recent/complete data
                        for key, value in app_data.items():
                            if value is not None and (
                                key not in collection_data
                                or collection_data[key] is None
                            ):
                                collection_data[key] = value

        # Calculate completeness score if not provided
        if collection_data["completeness_score"] == 0.0:
            total_fields = 20  # Example total expected fields
            collected_fields = sum(
                1
                for key in [
                    "technology_stack",
                    "dependencies",
                    "infrastructure",
                    "migration_complexity",
                    "business_criticality",
                    "compliance",
                ]
                if collection_data.get(key)
            )

            collection_data["completeness_score"] = collected_fields / total_fields
            collection_data["fields_collected"] = collected_fields
            collection_data["fields_missing"] = total_fields - collected_fields

        return collection_data

    def _extract_gaps_data(
        self, collection_flow: CollectionFlow
    ) -> List[Dict[str, Any]]:
        """Extract gaps data from collection flow results"""

        gaps_data = []

        # Extract from gap_analysis_results
        if collection_flow.gap_analysis_results:
            # Critical gaps
            critical_gaps = collection_flow.gap_analysis_results.get(
                "critical_gaps", []
            )
            for gap in critical_gaps:
                if isinstance(gap, dict):
                    gaps_data.append({**gap, "severity": "critical"})
                else:
                    gaps_data.append(
                        {
                            "field_name": str(gap),
                            "gap_type": "missing_data",
                            "severity": "critical",
                            "description": f"Critical gap: {gap}",
                        }
                    )

            # Optional gaps
            optional_gaps = collection_flow.gap_analysis_results.get(
                "optional_gaps", []
            )
            for gap in optional_gaps:
                if isinstance(gap, dict):
                    gaps_data.append({**gap, "severity": "low"})
                else:
                    gaps_data.append(
                        {
                            "field_name": str(gap),
                            "gap_type": "missing_data",
                            "severity": "low",
                            "description": f"Optional gap: {gap}",
                        }
                    )

        # Extract from phase_results
        if collection_flow.phase_results:
            for phase, results in collection_flow.phase_results.items():
                if isinstance(results, dict) and "gaps" in results:
                    phase_gaps = results["gaps"]
                    if isinstance(phase_gaps, list):
                        for gap in phase_gaps:
                            if isinstance(gap, dict):
                                gaps_data.append(gap)

        # If no gaps found, create default gaps based on missing data
        if not gaps_data and collection_flow.collection_config:
            selected_apps = collection_flow.collection_config.get(
                "selected_application_ids", []
            )
            for app_id in selected_apps:
                gaps_data.append(
                    {
                        "field_name": "application_inventory",
                        "gap_type": "incomplete_data",
                        "severity": "medium",
                        "description": f"Incomplete inventory data for application {app_id}",
                        "asset_id": app_id,
                        "category": "inventory",
                        "suggested_solution": "Manual data collection required",
                    }
                )

        return gaps_data

    def _aggregate_inventory_data(
        self, collection_flow: CollectionFlow
    ) -> Dict[str, Any]:
        """Aggregate inventory data from all collection sources"""

        inventory = {
            "applications": [],
            "infrastructure": [],
            "databases": [],
            "networks": [],
            "dependencies": [],
            "summary": {
                "total_applications": 0,
                "applications_complete": 0,
                "total_components": 0,
                "last_updated": datetime.utcnow().isoformat(),
            },
        }

        # Aggregate from collection_results
        if collection_flow.collection_results:
            results = collection_flow.collection_results

            # Applications
            if "applications" in results:
                apps = results["applications"]
                if isinstance(apps, dict):
                    for app_id, app_data in apps.items():
                        inventory["applications"].append(
                            {
                                "id": app_id,
                                "name": app_data.get("name", f"Application {app_id}"),
                                "technology_stack": app_data.get(
                                    "technology_stack", {}
                                ),
                                "completeness": app_data.get("completeness_score", 0.0),
                                "status": app_data.get("status", "discovered"),
                            }
                        )

            # Infrastructure
            if "infrastructure" in results:
                inventory["infrastructure"] = results["infrastructure"]

            # Dependencies
            if "dependencies" in results:
                inventory["dependencies"] = results["dependencies"]

        # Update summary
        inventory["summary"]["total_applications"] = len(inventory["applications"])
        inventory["summary"]["applications_complete"] = sum(
            1 for app in inventory["applications"] if app.get("completeness", 0) >= 0.8
        )
        inventory["summary"]["total_components"] = (
            len(inventory["applications"])
            + len(inventory["infrastructure"])
            + len(inventory["databases"])
        )

        return inventory

    async def _calculate_gap_summary_metrics(
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
                await self._populate_collection_applications(
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
            await self._populate_collection_gaps(collection_flow, force_repopulate=True)
            fixes.append("Populated gap analysis records")

        # Check gap analysis summary
        gap_analysis_count = await self.db.scalar(
            select(func.count(CollectionGapAnalysis.id)).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )

        if gap_analysis_count == 0:
            await self._create_gap_analysis_summary(
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
