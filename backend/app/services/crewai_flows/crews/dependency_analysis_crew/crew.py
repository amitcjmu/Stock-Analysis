"""
Dependency Analysis Crew - Main Crew Class

This module contains the main DependencyAnalysisCrew class that orchestrates
network dependency analysis, application dependency mapping, and infrastructure
dependency analysis for migration planning.

The crew uses sequential processing to analyze dependencies across three layers:
network, application, and infrastructure.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from app.services.crewai_flows.crews.dependency_analysis_crew.agents import (
    create_dependency_analysis_agents,
)
from app.services.crewai_flows.crews.dependency_analysis_crew.tasks import (
    create_dependency_analysis_crew_instance,
    create_dependency_analysis_tasks,
)
from app.services.crewai_flows.crews.dependency_analysis_crew.tools import (
    DependencyAnalysisResult,
    NetworkTopologyTool,
)
from app.services.crewai_flows.crews.dependency_analysis_crew.utils import (
    determine_architecture_type_from_asset,
    generate_dependency_summary,
)

logger = logging.getLogger(__name__)
logger.info("✅ CrewAI imports successful for DependencyAnalysisCrew")


class DependencyAnalysisCrew:
    """
    Strategic crew for complex dependency analysis and network architecture assessment.
    Uses parallel analysis with synthesis pattern.
    """

    def __init__(
        self,
        crewai_service=None,
        asset_inventory=None,
        shared_memory=None,
        knowledge_base=None,
    ):
        self.crewai_service = crewai_service
        self.asset_inventory = asset_inventory or []
        self.shared_memory = shared_memory
        self.knowledge_base = knowledge_base
        self.network_topology_tool = NetworkTopologyTool()

        # Initialize agents - CrewAI is required
        agents = create_dependency_analysis_agents(self.network_topology_tool)
        self.network_architecture_specialist = agents[0]
        self.application_dependency_analyst = agents[1]
        self.infrastructure_dependency_mapper = agents[2]

        self.crew = None  # Will be created in kickoff method
        logger.info("🎯 Dependency Analysis Crew initialized with specialized agents")

    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the dependency analysis crew using standard CrewAI kickoff pattern.

        Args:
            inputs: Dictionary containing asset_inventory and other context

        Returns:
            Comprehensive dependency analysis results
        """
        try:
            # Extract asset inventory from inputs
            asset_inventory = inputs.get("asset_inventory", {}) if inputs else {}
            assets_data = asset_inventory.get("assets", [])

            if not assets_data:
                # Try to get assets directly from asset_inventory if it's a list
                if isinstance(asset_inventory, list):
                    assets_data = asset_inventory
                else:
                    logger.warning("No assets found in inventory")
                    assets_data = []

            # Validate that assets_data contains valid asset dictionaries
            if assets_data:
                valid_assets = []
                for asset in assets_data:
                    if isinstance(asset, dict) and asset.get("id"):
                        valid_assets.append(asset)
                    else:
                        logger.warning(f"Skipping invalid asset: {asset}")
                assets_data = valid_assets

            # CRITICAL: Ensure we have actual asset data
            if not assets_data:
                logger.error("❌ No assets data available for dependency analysis")
                return {
                    "success": False,
                    "error": "No assets data available",
                    "analysis_results": [],
                    "dependencies": [],
                    "crew_insights": [],
                    "summary": {},
                    "metadata": {
                        "total_assets_analyzed": 0,
                        "total_dependencies_found": 0,
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "crew_pattern": "sequential_analysis",
                        "agents_involved": [],
                    },
                }

            # Log asset details for debugging
            logger.info(f"📊 Asset inventory contains {len(assets_data)} assets:")
            asset_types = {}
            asset_names = []
            for asset in assets_data:
                if isinstance(asset, dict):
                    asset_type = asset.get("type", "unknown")
                    asset_name = asset.get("name", asset.get("asset_name", "Unknown"))
                    asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                    asset_names.append(f"{asset_name} ({asset_type})")

            for asset_type, count in asset_types.items():
                logger.info(f"  - {asset_type}: {count} assets")

            # Log sample asset names for verification
            if asset_names:
                logger.info(f"Sample assets: {', '.join(asset_names[:5])}...")

            logger.info(
                f"🚀 Starting Dependency Analysis Crew for {len(assets_data)} REAL assets"
            )

            # CrewAI is required - no fallback

            # Create tasks for the crew
            tasks = create_dependency_analysis_tasks(
                assets_data,
                self.network_architecture_specialist,
                self.application_dependency_analyst,
                self.infrastructure_dependency_mapper,
            )

            # Create and execute the crew
            self.crew = create_dependency_analysis_crew_instance(
                agents=[
                    self.network_architecture_specialist,
                    self.application_dependency_analyst,
                    self.infrastructure_dependency_mapper,
                ],
                tasks=tasks,
            )

            # Execute crew
            crew_result = self.crew.kickoff(inputs=inputs)

            # Process the results
            return self._process_crew_results(crew_result, assets_data)

        except Exception as e:
            logger.error(f"❌ Dependency Analysis Crew failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": [],
                "crew_insights": [],
                "dependencies": [],
                "summary": {},
                "metadata": {
                    "total_assets_analyzed": 0,
                    "total_dependencies_found": 0,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "crew_pattern": "sequential_analysis",
                    "agents_involved": [],
                },
            }

    def _process_crew_results(
        self, crew_result: Any, assets_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process crew execution results into structured format"""
        try:
            # Initialize empty results
            dependencies = []
            analysis_results = []

            # Try to extract structured JSON from crew result
            if isinstance(crew_result, str):
                # Try to parse JSON from string result
                # Look for JSON in the result
                json_match = re.search(r"\{[\s\S]*\}", crew_result)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group())
                        if "dependencies" in parsed_result:
                            dependencies = parsed_result["dependencies"]
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse JSON from crew result")
            elif isinstance(crew_result, dict):
                # Direct dict result
                dependencies = crew_result.get("dependencies", [])

            # Create asset lookup for validation
            asset_lookup = {}
            for asset in assets_data:
                if isinstance(asset, dict):
                    asset_id = asset.get("id")
                    if asset_id:
                        asset_lookup[asset_id] = asset

            # Process and validate dependencies
            validated_dependencies = []
            for dep in dependencies:
                if isinstance(dep, dict):
                    source_id = dep.get("source_id")
                    target_id = dep.get("target_id")

                    # Validate that both assets exist
                    if source_id in asset_lookup and target_id in asset_lookup:
                        validated_dep = {
                            "source_id": source_id,
                            "source_name": dep.get(
                                "source_name",
                                asset_lookup[source_id].get("name", "Unknown"),
                            ),
                            "target_id": target_id,
                            "target_name": dep.get(
                                "target_name",
                                asset_lookup[target_id].get("name", "Unknown"),
                            ),
                            "dependency_type": dep.get("dependency_type", "unknown"),
                            "confidence_score": float(dep.get("confidence_score", 0.5)),
                            "is_app_to_app": bool(dep.get("is_app_to_app", False)),
                            "description": dep.get("description", ""),
                        }
                        validated_dependencies.append(validated_dep)
                    else:
                        logger.warning(
                            f"Skipping invalid dependency: {source_id} -> {target_id}"
                        )

            # If no valid dependencies found, this is still a valid result
            if not validated_dependencies:
                logger.info(
                    "No dependencies extracted from crew - assets may be standalone"
                )
                # Return empty dependencies - this is a valid result
                validated_dependencies = []

            # Create analysis results for compatibility
            for asset_data in assets_data:
                asset_id = asset_data.get("id", "unknown")
                asset_name = asset_data.get(
                    "name", asset_data.get("asset_name", "Unknown")
                )

                # Find dependencies for this asset
                upstream = [
                    d for d in validated_dependencies if d["target_id"] == asset_id
                ]
                downstream = [
                    d for d in validated_dependencies if d["source_id"] == asset_id
                ]

                dependency_result = DependencyAnalysisResult(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    network_analysis={
                        "complexity_level": (
                            "low"
                            if len(upstream) + len(downstream) == 0
                            else (
                                "medium"
                                if len(upstream) + len(downstream) < 3
                                else "high"
                            )
                        ),
                        "architecture_type": determine_architecture_type_from_asset(
                            asset_data
                        ),
                        "network_indicators": {
                            "ports": [],
                            "protocols": [],
                        },
                    },
                    application_dependencies={
                        "dependency_strength": (
                            "low"
                            if not downstream
                            else "medium" if len(downstream) < 2 else "high"
                        ),
                        "integration_complexity": "low",
                        "integration_patterns": {},
                    },
                    infrastructure_dependencies={
                        "maturity_level": "medium",
                        "dependency_complexity": "low" if not upstream else "medium",
                        "critical_components": [],
                    },
                    critical_path_analysis={
                        "critical_dependencies": [d["source_name"] for d in upstream],
                        "migration_blockers": [],
                        "sequence_requirements": [],
                    },
                    dependency_map={
                        "upstream_dependencies": [d["source_id"] for d in upstream],
                        "downstream_dependencies": [d["target_id"] for d in downstream],
                        "peer_dependencies": [],
                    },
                    migration_sequence=[],
                    risk_assessment={
                        "overall_risk": "low" if not upstream else "medium",
                        "key_risks": [],
                        "mitigation_strategies": [],
                    },
                    confidence_score=0.8 if validated_dependencies else 0.5,
                )

                analysis_results.append(dependency_result)

            # Generate comprehensive summary
            summary = generate_dependency_summary(analysis_results)

            logger.info("✅ Dependency Analysis Crew completed successfully")

            return {
                "success": True,
                "analysis_results": analysis_results,
                "dependencies": validated_dependencies,
                "crew_insights": [],
                "summary": summary,
                "metadata": {
                    "total_assets_analyzed": len(assets_data),
                    "total_dependencies_found": len(validated_dependencies),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "crew_pattern": "sequential_analysis",
                    "agents_involved": [
                        "Network Architecture Specialist",
                        "Application Dependency Analyst",
                        "Infrastructure Dependency Mapper",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": [],
                "crew_insights": [],
                "dependencies": [],
                "summary": {},
                "metadata": {
                    "total_assets_analyzed": 0,
                    "total_dependencies_found": 0,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "crew_pattern": "sequential_analysis",
                    "agents_involved": [],
                },
            }


# Factory function for crew creation
def create_dependency_analysis_crew(
    crewai_service=None, asset_inventory=None, shared_memory=None, knowledge_base=None
) -> DependencyAnalysisCrew:
    """Create and return a Dependency Analysis Crew instance"""
    return DependencyAnalysisCrew(
        crewai_service, asset_inventory, shared_memory, knowledge_base
    )


# Export the crew class and factory function
__all__ = [
    "DependencyAnalysisCrew",
    "create_dependency_analysis_crew",
]
