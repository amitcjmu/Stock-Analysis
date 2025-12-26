"""
Specific phase execution methods for Discovery Flow Execution Engine.
Contains field mapping, data cleansing, asset inventory, and generic phase executors.
"""

from typing import Any, Dict

from sqlalchemy import update

from app.core.logging import get_logger

logger = get_logger(__name__)


class PhaseExecutorsMixin:
    """Mixin class containing specific phase execution methods for discovery flows."""

    async def _execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase - REMOVED: field mapping functionality was removed"""
        # REMOVED: Field mapping logic - field mapping functionality was removed
        # return await self.field_mapping_logic.execute_discovery_field_mapping(
        #     agent_pool, phase_input, self.db_session
        # )
        return {
            "status": "skipped",
            "message": "Field mapping phase is no longer available - functionality was removed",
            "phase": "field_mapping",
        }

    async def _execute_discovery_data_cleansing(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data cleansing phase using DataCleansingExecutor"""
        logger.info("🧹 Executing discovery data cleansing using DataCleansingExecutor")

        try:
            # Import the DataCleansingExecutor
            from app.services.crewai_flows.handlers.phase_executors.data_cleansing_executor import (
                DataCleansingExecutor,
            )
            from app.models.unified_discovery_flow_state import (
                UnifiedDiscoveryFlowState,
            )

            # Create state object from phase_input
            state = UnifiedDiscoveryFlowState()

            # Set required state attributes from phase_input
            # Debug logging to understand what's in phase_input
            logger.info(f"📋 phase_input keys: {list(phase_input.keys())}")
            logger.info(f"📋 flow_id from phase_input: {phase_input.get('flow_id')}")
            logger.info(
                f"📋 master_flow_id from phase_input: {phase_input.get('master_flow_id')}"
            )

            state.flow_id = phase_input.get("flow_id") or phase_input.get(
                "master_flow_id"
            )

            # If flow_id is still None, log error but continue
            if not state.flow_id:
                logger.error("❌ CRITICAL: flow_id is None in phase_input!")
                logger.error(f"❌ phase_input contents: {phase_input}")
                # Try to get flow_id from context or other sources
                if hasattr(self, "context") and hasattr(self.context, "flow_id"):
                    state.flow_id = self.context.flow_id
                    logger.info(f"✅ Retrieved flow_id from context: {state.flow_id}")
            else:
                logger.info(f"✅ flow_id set to: {state.flow_id}")

            # Ensure data_import_id is available - add it as an attribute dynamically
            if not hasattr(state, "data_import_id"):
                setattr(state, "data_import_id", phase_input.get("data_import_id"))
            else:
                state.data_import_id = phase_input.get("data_import_id")
            state.client_account_id = self.context.client_account_id
            state.engagement_id = self.context.engagement_id
            state.raw_data = phase_input.get("raw_data", [])

            # Initialize the executor with state and session - providing required crew_manager parameter
            # DataCleansingExecutor expects (state, crew_manager, flow_bridge=None)
            executor = DataCleansingExecutor(state, crew_manager=None, flow_bridge=None)
            # Set additional attributes that the executor uses
            if hasattr(executor, "db_session"):
                executor.db_session = self.db_session
            else:
                setattr(executor, "db_session", self.db_session)
            if hasattr(executor, "service_registry"):
                executor.service_registry = self.service_registry
            else:
                setattr(executor, "service_registry", self.service_registry)

            # Execute with crew
            result = await executor.execute_with_crew(phase_input)

            # Check if cleansing was successful
            if result.get("status") == "error":
                logger.error(f"❌ Data cleansing failed: {result.get('message')}")
                return result  # Return error result without marking complete

            # Only persist phase completion if successful
            try:
                from app.models.discovery_flow import DiscoveryFlow

                master_flow_id = phase_input.get("master_flow_id") or phase_input.get(
                    "flow_id"
                )
                if (
                    master_flow_id
                    and self.db_session
                    and result.get("status") == "success"
                ):
                    await self.db_session.execute(
                        update(DiscoveryFlow)
                        .where(DiscoveryFlow.master_flow_id == master_flow_id)
                        .values(data_cleansing_completed=True)
                    )
                    await self.db_session.commit()
                    logger.info(
                        "✅ Persisted data_cleansing_completed=True on discovery flow"
                    )
            except Exception as persist_err:
                logger.warning(
                    f"⚠️ Failed to persist data_cleansing_completed flag: {persist_err}"
                )

            logger.info("✅ Data cleansing completed using DataCleansingExecutor")

            return {
                "phase": "data_cleansing",
                "status": "completed",
                "crew_results": result,
                "cleansed_data": result.get("cleaned_data", []),
                "agent": "data_cleansing_agent",
                "method": "data_cleansing_executor",
                "quality_metrics": result.get("quality_metrics", {}),
            }

        except Exception as e:
            logger.error(f"❌ Data cleansing failed with DataCleansingExecutor: {e}")
            return {
                "phase": "data_cleansing",
                "status": "error",
                "error": str(e),
                "cleansed_data": [],
                "agent": "data_cleansing_agent",
                "method": "data_cleansing_executor",
            }

    async def _execute_discovery_asset_inventory(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute asset inventory phase using NEW AssetInventoryExecutor with direct execution (no crews)"""
        logger.info(
            "📦 Executing discovery asset inventory using AssetInventoryExecutor (direct execution)"
        )

        # CC: FIX for issues #520/#521/#522 - Use NEW AssetInventoryExecutor.execute_asset_creation()
        # AssetInventoryExecutor uses DIRECT EXECUTION via AssetService, NOT crews
        # It applies field mappings and has intelligent classification logic

        from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor import (
            AssetInventoryExecutor,
        )
        from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

        # Create minimal state object for executor initialization (required by BasePhaseExecutor)
        state = UnifiedDiscoveryFlowState()
        state.flow_id = phase_input.get("flow_id") or phase_input.get("master_flow_id")
        state.client_account_id = self.context.client_account_id
        state.engagement_id = self.context.engagement_id

        # Create executor instance (state not used by execute_asset_creation but required by __init__)
        executor = AssetInventoryExecutor(state, crew_manager=None, flow_bridge=None)

        # Build flow_context for AssetInventoryExecutor.execute_asset_creation()
        # CC: Convert data_import_id UUID to string (Pydantic validation requirement)
        data_import_id = phase_input.get("data_import_id")
        flow_context = {
            "flow_id": phase_input.get("flow_id"),
            "master_flow_id": phase_input.get("master_flow_id")
            or phase_input.get("flow_id"),
            "discovery_flow_id": phase_input.get("flow_id"),
            "data_import_id": str(data_import_id) if data_import_id else None,
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id,
            "user_id": self.context.user_id,
            "db_session": self.db_session,
        }

        logger.info("✅ Initialized AssetInventoryExecutor for direct execution")

        # Execute asset inventory with direct execution (no crews needed)
        try:
            # Call execute_asset_creation() on the executor instance
            result = await executor.execute_asset_creation(flow_context)

            # CC: AssetInventoryExecutor returns standardized result format
            logger.info(f"✅ AssetInventoryExecutor result: {result.get('status')}")

            # Extract actual counts from result
            assets_created = result.get("assets_created", 0)
            assets_failed = result.get("assets_failed", 0)

            logger.info(
                f"🔨 Asset creation result: created={assets_created}, failed={assets_failed}"
            )

            # Maintain backward compatibility with asset_inventory field
            asset_inventory = result.get(
                "asset_inventory",
                {"total_assets": assets_created, "classification_complete": True},
            )

            # CC: Commit transaction after asset creation completes
            # This persists all changes: assets, conflict flags, and flow completion
            # Matches pattern from data_cleansing phase executor (lines 109-114)
            await self.db_session.commit()
            logger.info("✅ Committed asset inventory transaction")

            return {
                "phase": "asset_inventory",
                "status": result.get("status", "completed"),
                "crew_results": result,
                "asset_inventory": asset_inventory,  # Backward compatibility
                "agent": "asset_inventory_agent",
                "method": "asset_inventory_executor_direct",  # Direct execution, no crews
                "assets_created": assets_created,
                "assets_failed": assets_failed,
            }
        except Exception as e:
            # CC: Rollback transaction on error to prevent partial commits
            await self.db_session.rollback()
            logger.error(
                f"❌ Asset inventory failed with AssetInventoryExecutor: {str(e)}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "phase": "asset_inventory",
                "status": "error",
                "error": str(e),
                "asset_inventory": {
                    "total_assets": 0,
                    "classification_complete": False,
                },
                "agent": "asset_inventory_agent",
                "assets_created": 0,
                "assets_failed": 0,
            }

    async def _execute_discovery_dependency_analysis(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute dependency analysis phase using DependencyAnalysisExecutor"""
        logger.info(
            "🔍 Executing discovery dependency analysis using DependencyAnalysisExecutor"
        )

        try:
            # Import the DependencyAnalysisExecutor
            from app.services.crewai_flows.handlers.phase_executors.dependency_analysis_executor import (
                DependencyAnalysisExecutor,
            )
            from app.models.unified_discovery_flow_state import (
                UnifiedDiscoveryFlowState,
            )

            # Create state object from phase_input
            state = UnifiedDiscoveryFlowState()

            # Set required state attributes from phase_input
            logger.info(f"📋 phase_input keys: {list(phase_input.keys())}")
            logger.info(f"📋 flow_id from phase_input: {phase_input.get('flow_id')}")
            logger.info(
                f"📋 master_flow_id from phase_input: {phase_input.get('master_flow_id')}"
            )

            state.flow_id = phase_input.get("flow_id") or phase_input.get(
                "master_flow_id"
            )

            # If flow_id is still None, log error but continue
            if not state.flow_id:
                logger.error("❌ CRITICAL: flow_id is None in phase_input!")
                logger.error(f"❌ phase_input contents: {phase_input}")
                # Try to get flow_id from context or other sources
                if hasattr(self, "context") and hasattr(self.context, "flow_id"):
                    state.flow_id = self.context.flow_id
                    logger.info(f"✅ Retrieved flow_id from context: {state.flow_id}")
            else:
                logger.info(f"✅ flow_id set to: {state.flow_id}")

            # Set required context attributes
            state.client_account_id = self.context.client_account_id
            state.engagement_id = self.context.engagement_id

            # Set asset inventory from phase_input if available
            state.asset_inventory = phase_input.get("asset_inventory", {})

            # Initialize the executor with state and crew_manager
            # DependencyAnalysisExecutor expects (state, crew_manager, flow_bridge=None)
            executor = DependencyAnalysisExecutor(
                state, crew_manager=None, flow_bridge=None
            )
            # Set additional attributes that the executor uses
            if hasattr(executor, "db_session"):
                executor.db_session = self.db_session
            else:
                setattr(executor, "db_session", self.db_session)
            if hasattr(executor, "service_registry"):
                executor.service_registry = self.service_registry
            else:
                setattr(executor, "service_registry", self.service_registry)

            # Execute with crew
            result = await executor.execute_with_crew(phase_input)

            # Check if dependency analysis was successful
            if result.get("status") == "error":
                logger.error(f"❌ Dependency analysis failed: {result.get('message')}")
                return result  # Return error result without marking complete

            # Only persist phase completion if successful
            try:
                from app.models.discovery_flow import DiscoveryFlow

                master_flow_id = phase_input.get("master_flow_id") or phase_input.get(
                    "flow_id"
                )
                if master_flow_id and self.db_session and result.get("success"):
                    await self.db_session.execute(
                        update(DiscoveryFlow)
                        .where(DiscoveryFlow.master_flow_id == master_flow_id)
                        .values(dependency_analysis_completed=True)
                    )
                    await self.db_session.commit()
                    logger.info(
                        "✅ Persisted dependency_analysis_completed=True on discovery flow"
                    )
            except Exception as persist_err:
                logger.warning(
                    f"⚠️ Failed to persist dependency_analysis_completed flag: {persist_err}"
                )

            logger.info(
                "✅ Dependency analysis completed using DependencyAnalysisExecutor"
            )

            return {
                "phase": "dependency_analysis",
                "status": "completed",
                "crew_results": result,
                "dependency_analysis": result,  # Make available as dependency_analysis for backward compatibility
                "agent": "dependency_analysis_agent",
                "method": "dependency_analysis_executor",
                "total_dependencies": result.get("mapped_dependencies", 0),
                "complexity_score": result.get("complexity_score", 0.0),
            }

        except Exception as e:
            logger.error(
                f"❌ Dependency analysis failed with DependencyAnalysisExecutor: {e}"
            )
            return {
                "phase": "dependency_analysis",
                "status": "error",
                "error": str(e),
                "dependency_analysis": {},
                "agent": "dependency_analysis_agent",
                "method": "dependency_analysis_executor",
            }

    async def _execute_discovery_generic_phase(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute generic discovery phase"""
        logger.info("⚡ Executing generic discovery phase")

        # Generic phase execution
        return {
            "phase": "generic",
            "status": "completed",
            "result": "Generic phase execution completed",
            "agent": "generic_agent",
        }
