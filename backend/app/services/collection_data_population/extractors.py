"""
Collection Data Population Service - Data Extractors Module

This module contains data extraction and aggregation methods for collection
flows. It handles extracting data from collection results and phase results
to populate child data tables.

Key Features:
- Application collection data extraction
- Gaps data extraction from results
- Inventory data aggregation
- Data transformation utilities
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


class CollectionDataExtractors:
    """Data extraction utilities for collection flows"""

    @staticmethod
    def extract_application_collection_data(
        collection_flow: CollectionFlow, asset_id: UUID
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

    @staticmethod
    def extract_gaps_data(collection_flow: CollectionFlow) -> List[Dict[str, Any]]:
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

    @staticmethod
    def aggregate_inventory_data(collection_flow: CollectionFlow) -> Dict[str, Any]:
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
