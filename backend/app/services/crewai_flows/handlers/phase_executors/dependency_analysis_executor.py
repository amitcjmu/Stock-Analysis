"""
Dependency Analysis Executor
Handles dependency analysis phase execution for the Unified Discovery Flow.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class DependencyAnalysisExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "dependencies"  # FIX: Map to correct DB phase name

    def get_progress_percentage(self) -> float:
        return 66.7  # 4/6 phases

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for dependencies crew
        asset_inventory = getattr(self.state, "asset_inventory", {})

        # CRITICAL FIX: Load assets from database if asset_inventory is empty
        if not asset_inventory or asset_inventory.get("total_assets", 0) == 0:
            logger.warning("Asset inventory is empty, loading assets from database")
            assets_from_db = await self._load_assets_from_database()
            if assets_from_db:
                # Format assets for the crew
                asset_inventory = {
                    "assets": assets_from_db,
                    "total_assets": len(assets_from_db),
                    "asset_types": self._categorize_asset_types(assets_from_db),
                }
                logger.info(f"Loaded {len(assets_from_db)} assets from database")

                # CRITICAL: Update crew_input with the loaded asset inventory
                crew_input["asset_inventory"] = asset_inventory
            else:
                logger.warning("No assets found in database")

        crew = self.crew_manager.create_crew_on_demand(
            "dependencies", asset_inventory=asset_inventory, **self._get_crew_context()
        )
        # Run crew in thread to avoid blocking async execution
        import asyncio

        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)
        return self._process_crew_result(crew_result)

    async def execute_fallback(self) -> Dict[str, Any]:
        # 🚀 DATA VALIDATION: Check if we have data to process
        asset_inventory = getattr(self.state, "asset_inventory", {})
        if not asset_inventory or asset_inventory.get("total_assets", 0) == 0:
            return {
                "app_server_mapping": [],
                "cross_application_mapping": [],
                "total_applications": 0,
                "mapped_dependencies": 0,
                "dependency_relationships": [],
                "dependency_matrix": {},
                "critical_dependencies": [],
                "orphaned_assets": [],
                "complexity_score": 0.0,
                "recommendations": [
                    "No asset inventory data available for dependency analysis"
                ],
                "success": False,
                "reason": "no_data",
            }

        # Basic dependency analysis based on asset inventory
        total_assets = asset_inventory.get("total_assets", 0)
        return {
            "app_server_mapping": [],
            "cross_application_mapping": [],
            "total_applications": total_assets,
            "mapped_dependencies": 0,
            "dependency_relationships": [],
            "dependency_matrix": {},
            "critical_dependencies": [],
            "orphaned_assets": [],
            "complexity_score": 0.0,
            "recommendations": [
                f"Fallback dependency analysis for {total_assets} assets",
                "Run full dependency analysis to discover actual relationships",
            ],
            "fallback_used": True,
            "assets_analyzed": total_assets,
            "success": True,
        }

    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, "asset_inventory", {})}

    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Transform crew results into format expected by Dependencies page"""
        try:
            # Handle the crew result format from DependencyAnalysisCrew
            if isinstance(crew_result, dict) and crew_result.get("success"):
                # Get the structured dependencies directly
                dependencies = crew_result.get("dependencies", [])
                summary = crew_result.get("summary", {})

                # Transform dependencies into app-server and app-app mappings
                app_server_mapping = []
                cross_application_mapping = []
                all_dependencies = []

                for dep in dependencies:
                    if isinstance(dep, dict):
                        source_id = dep.get("source_id")
                        source_name = dep.get("source_name", "Unknown")
                        target_id = dep.get("target_id")
                        target_name = dep.get("target_name", "Unknown")
                        dep_type = dep.get("dependency_type", "unknown")
                        confidence = float(dep.get("confidence_score", 0.5))
                        is_app_to_app = dep.get("is_app_to_app", False)

                        # Add to all dependencies list
                        all_dependencies.append(
                            {
                                "source_id": source_id,
                                "source_name": source_name,
                                "target_id": target_id,
                                "target_name": target_name,
                                "dependency_type": dep_type,
                                "confidence": confidence,
                                "description": dep.get("description", ""),
                            }
                        )

                        # Categorize dependencies
                        if is_app_to_app:
                            # App-to-app dependency
                            cross_application_mapping.append(
                                {
                                    "source_application_id": source_id,
                                    "source_application": source_name,
                                    "target_application_id": target_id,
                                    "target_application": target_name,
                                    "dependency_type": dep_type,
                                    "confidence": confidence,
                                }
                            )
                        elif dep_type in ["hosting", "server", "infrastructure"]:
                            # App-server dependency
                            app_server_mapping.append(
                                {
                                    "application_id": source_id,
                                    "application_name": source_name,
                                    "server_id": target_id,
                                    "server_name": target_name,
                                    "dependency_type": dep_type,
                                    "confidence": confidence,
                                }
                            )
                        elif dep_type in ["database", "storage"]:
                            # App-database dependency (can be treated as app-server)
                            app_server_mapping.append(
                                {
                                    "application_id": source_id,
                                    "application_name": source_name,
                                    "server_id": target_id,
                                    "server_name": target_name,
                                    "dependency_type": dep_type,
                                    "confidence": confidence,
                                }
                            )
                        else:
                            # Other dependencies - check if both are applications
                            if (
                                "app" in source_name.lower()
                                and "app" in target_name.lower()
                            ):
                                cross_application_mapping.append(
                                    {
                                        "source_application_id": source_id,
                                        "source_application": source_name,
                                        "target_application_id": target_id,
                                        "target_application": target_name,
                                        "dependency_type": dep_type,
                                        "confidence": confidence,
                                    }
                                )
                            else:
                                # Default to app-server
                                app_server_mapping.append(
                                    {
                                        "application_id": source_id,
                                        "application_name": source_name,
                                        "server_id": target_id,
                                        "server_name": target_name,
                                        "dependency_type": dep_type,
                                        "confidence": confidence,
                                    }
                                )

                # Calculate metrics
                total_assets = summary.get("total_assets", 0)
                total_dependencies = len(all_dependencies)
                avg_confidence = (
                    sum(d["confidence"] for d in all_dependencies)
                    / len(all_dependencies)
                    if all_dependencies
                    else 0.0
                )

                # Return in format expected by Dependencies page
                return {
                    "app_server_mapping": app_server_mapping,
                    "cross_application_mapping": cross_application_mapping,
                    "total_applications": total_assets,
                    "mapped_dependencies": total_dependencies,
                    "dependency_relationships": all_dependencies,
                    "dependency_matrix": self._build_dependency_matrix(
                        all_dependencies
                    ),
                    "critical_dependencies": self._identify_critical_dependencies(
                        all_dependencies
                    ),
                    "orphaned_assets": [],  # Could be calculated from assets without dependencies
                    "complexity_score": avg_confidence,
                    "recommendations": [
                        f"Discovered {total_dependencies} dependencies across {total_assets} assets",
                        f"Average dependency confidence: {avg_confidence:.1%}",
                        f"Found {len(app_server_mapping)} app-server and "
                        f"{len(cross_application_mapping)} app-app dependencies",
                    ]
                    + summary.get("recommendations", []),
                    "analysis_timestamp": crew_result.get("metadata", {}).get(
                        "analysis_timestamp"
                    ),
                    "success": True,
                }
            else:
                # Use fallback format if crew result is not successful
                return {
                    "app_server_mapping": [],
                    "cross_application_mapping": [],
                    "total_applications": 0,
                    "mapped_dependencies": 0,
                    "dependency_relationships": [],
                    "dependency_matrix": {},
                    "critical_dependencies": [],
                    "orphaned_assets": [],
                    "complexity_score": 0.0,
                    "recommendations": [
                        "Dependency analysis failed - using fallback data"
                    ],
                    "success": False,
                    "error": (
                        crew_result.get("error", "Unknown error")
                        if isinstance(crew_result, dict)
                        else "Invalid crew result format"
                    ),
                }
        except Exception as e:
            # Fallback processing
            return {
                "app_server_mapping": [],
                "cross_application_mapping": [],
                "total_applications": 0,
                "mapped_dependencies": 0,
                "dependency_relationships": [],
                "dependency_matrix": {},
                "critical_dependencies": [],
                "orphaned_assets": [],
                "complexity_score": 0.0,
                "recommendations": [f"Error processing dependency analysis: {str(e)}"],
                "success": False,
                "error": str(e),
            }

    def _store_results(self, results: Dict[str, Any]):
        self.state.dependencies = results

        # CRITICAL: Persist dependencies to database
        import asyncio

        try:
            # Run async persistence in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._persist_dependencies_to_db(results))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to persist dependencies to database: {e}")

    async def _load_assets_from_database(self) -> List[Dict[str, Any]]:
        """Load assets from database using the flow bridge"""
        try:
            # Get database session directly
            from app.core.database import get_db
            from app.repositories.asset_repository import AssetRepository

            # Get context from state
            client_account_id = getattr(self.state, "client_account_id", None)
            engagement_id = getattr(self.state, "engagement_id", None)

            if not client_account_id or not engagement_id:
                logger.error("Missing client_account_id or engagement_id in state")
                return []

            # Get database session
            async for db in get_db():
                # Create asset repository
                asset_repo = AssetRepository(db, client_account_id, engagement_id)

                # Get all assets
                assets = await asset_repo.get_all()

                # Convert to dict format for crew
                asset_dicts = []
                for asset in assets:
                    asset_dict = {
                        "id": str(asset.id),
                        "name": asset.name or asset.asset_name or "Unknown",
                        "type": asset.asset_type or "unknown",
                        "hostname": asset.hostname,
                        "environment": asset.environment,
                        "status": asset.status,
                        "description": asset.description,
                        "department": asset.department,  # Use department instead of business_unit
                        "criticality": asset.criticality,
                        "six_r_strategy": asset.six_r_strategy,
                        "dependencies": asset.dependencies,
                        "related_assets": asset.related_assets,  # Use related_assets field
                        "ip_address": asset.ip_address,
                        "application_name": asset.application_name,
                        "technology_stack": asset.technology_stack,
                    }
                    asset_dicts.append(asset_dict)

                logger.info(
                    f"✅ Loaded {len(asset_dicts)} assets from database for dependency analysis"
                )
                return asset_dicts
        except Exception as e:
            logger.error(f"Error loading assets from database: {e}")
            return []

    def _categorize_asset_types(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize assets by type"""
        asset_types = {}
        for asset in assets:
            asset_type = asset.get("type", "unknown")
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        return asset_types

    async def _persist_dependencies_to_db(self, results: Dict[str, Any]):
        """Persist discovered dependencies to the database"""
        from app.services.dependency_analysis_service import DependencyAnalysisService
        from app.core.database import get_db

        # Get context from state
        client_account_id = getattr(self.state, "client_account_id", None)
        engagement_id = getattr(self.state, "engagement_id", None)
        flow_id = getattr(self.state, "flow_id", None)

        if not client_account_id or not engagement_id:
            logger.error("Missing context for dependency persistence")
            return

        async for db in get_db():
            try:
                # Create dependency service
                dep_service = DependencyAnalysisService(
                    db, client_account_id, engagement_id, flow_id
                )

                # Persist app-server dependencies
                app_server_deps = results.get("app_server_mapping", [])
                for dep in app_server_deps:
                    try:
                        await dep_service.create_dependency(
                            source_id=dep.get("application_id"),
                            target_id=dep.get("server_id"),
                            dependency_type=dep.get("dependency_type", "hosting"),
                            is_app_to_app=False,
                            description=f"{dep.get('application_name')} depends on {dep.get('server_name')}",
                        )
                        logger.info(
                            f"✅ Persisted app-server dependency: "
                            f"{dep.get('application_name')} -> {dep.get('server_name')}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to persist app-server dependency: {e}")

                # Persist app-app dependencies
                cross_app_deps = results.get("cross_application_mapping", [])
                for dep in cross_app_deps:
                    try:
                        await dep_service.create_dependency(
                            source_id=dep.get("source_application_id"),
                            target_id=dep.get("target_application_id"),
                            dependency_type=dep.get("dependency_type", "api"),
                            is_app_to_app=True,
                            description=f"{dep.get('source_application')} depends on {dep.get('target_application')}",
                        )
                        logger.info(
                            f"✅ Persisted app-app dependency: "
                            f"{dep.get('source_application')} -> {dep.get('target_application')}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to persist app-app dependency: {e}")

                # Also persist the raw dependency list if present
                all_deps = results.get("dependency_relationships", [])
                for dep in all_deps:
                    try:
                        if (
                            isinstance(dep, dict)
                            and dep.get("source_id")
                            and dep.get("target_id")
                        ):
                            await dep_service.create_dependency(
                                source_id=dep.get("source_id"),
                                target_id=dep.get("target_id"),
                                dependency_type=dep.get("dependency_type", "unknown"),
                                is_app_to_app=dep.get("source_name", "")
                                .lower()
                                .endswith("app")
                                and dep.get("target_name", "").lower().endswith("app"),
                                description=dep.get("description", ""),
                            )
                            logger.info(
                                f"✅ Persisted dependency: {dep.get('source_name')} -> {dep.get('target_name')}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to persist dependency: {e}")

                # Commit the transaction
                await db.commit()
                logger.info(
                    f"✅ Successfully persisted "
                    f"{len(app_server_deps) + len(cross_app_deps) + len(all_deps)} "
                    f"dependencies to database"
                )

            except Exception as e:
                logger.error(f"Error persisting dependencies: {e}")
                await db.rollback()
                raise

    def _get_phase_timeout(self) -> Optional[int]:
        """No timeout for dependency analysis - it's a complex agentic task"""
        return None  # No timeout for dependency analysis

    def _build_dependency_matrix(
        self, dependencies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a dependency matrix from the list of dependencies"""
        matrix = {}

        for dep in dependencies:
            source = dep.get("source_id")
            target = dep.get("target_id")

            if source not in matrix:
                matrix[source] = {}

            matrix[source][target] = {
                "type": dep.get("dependency_type"),
                "confidence": dep.get("confidence", 0.5),
            }

        return matrix

    def _identify_critical_dependencies(
        self, dependencies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify critical dependencies based on confidence and type"""
        critical = []

        # Count how many times each asset appears as a target (dependency)
        dependency_counts = {}
        for dep in dependencies:
            target = dep.get("target_id")
            if target:
                dependency_counts[target] = dependency_counts.get(target, 0) + 1

        # Dependencies are critical if:
        # 1. High confidence (>= 0.8)
        # 2. Target is depended on by multiple sources (>= 2)
        # 3. Type is database or infrastructure
        for dep in dependencies:
            is_critical = False
            reasons = []

            if dep.get("confidence", 0) >= 0.8:
                is_critical = True
                reasons.append("high confidence")

            target_id = dep.get("target_id")
            if dependency_counts.get(target_id, 0) >= 2:
                is_critical = True
                reasons.append("multiple dependents")

            if dep.get("dependency_type") in ["database", "infrastructure", "hosting"]:
                is_critical = True
                reasons.append(f"critical type: {dep.get('dependency_type')}")

            if is_critical:
                critical.append(
                    {
                        "source": dep.get("source_name"),
                        "target": dep.get("target_name"),
                        "type": dep.get("dependency_type"),
                        "confidence": dep.get("confidence"),
                        "reasons": reasons,
                    }
                )

        return critical
