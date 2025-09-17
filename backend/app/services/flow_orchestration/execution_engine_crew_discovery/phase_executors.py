"""
Specific phase execution methods for Discovery Flow Execution Engine.
Contains field mapping, data cleansing, asset inventory, and generic phase executors.
"""

from typing import Any, Dict

from sqlalchemy import func, select, update

from app.core.logging import get_logger

logger = get_logger(__name__)


class PhaseExecutorsMixin:
    """Mixin class containing specific phase execution methods for discovery flows."""

    async def _execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase - delegated to specialized handler"""
        return await self.field_mapping_logic.execute_discovery_field_mapping(
            agent_pool, phase_input, self.db_session
        )

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
        """Execute asset inventory phase using persistent agent"""
        logger.info("📦 Executing discovery asset inventory using persistent agent")

        data_import_id = phase_input.get("data_import_id")
        if not data_import_id:
            raise ValueError("No data_import_id provided")

        # CORRECT IMPORTS
        from app.models.data_import.core import RawImportRecord  # CORRECT PATH

        # Query for cleansed data WITH TENANT SCOPING using self.db_session
        result = await self.db_session.execute(  # USE db_session
            select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.cleansed_data.isnot(None),
                RawImportRecord.client_account_id
                == self.context.client_account_id,  # TENANT
                RawImportRecord.engagement_id == self.context.engagement_id,  # TENANT
            )
        )
        records = result.scalars().all()

        cleansed_count = len(records)

        # Count raw records for comparison
        raw_result = await self.db_session.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.client_account_id == self.context.client_account_id,
                RawImportRecord.engagement_id == self.context.engagement_id,
            )
        )
        raw_count = raw_result.scalar()

        logger.info(
            f"📊 Found {cleansed_count} cleansed records, {raw_count} total records"
        )

        # REQUIRE cleansed data - no raw fallbacks allowed
        if cleansed_count == 0:
            return {
                "status": "error",
                "error_code": "CLEANSING_REQUIRED",  # Unified error code
                "message": "No cleansed data available for asset inventory. "
                "Data cleansing phase must be completed first.",
                "details": {
                    "cleansed_count": 0,
                    "raw_count": raw_count,
                    "data_import_id": str(data_import_id),
                },
            }

        # Extract cleansed data only
        cleansed_data = [r.cleansed_data for r in records]

        # Get field mappings
        field_mappings = await self._get_approved_field_mappings(phase_input)
        logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")

        # Get flow IDs
        master_flow_id = phase_input.get("master_flow_id") or phase_input.get("flow_id")
        discovery_flow_id = await self._get_discovery_flow_id(master_flow_id)

        # Normalize using cleansed data
        normalized_assets = await self._normalize_assets_for_creation(
            cleansed_data,  # USE CLEANSED DATA
            field_mappings,
            master_flow_id,
            discovery_flow_id,
        )

        logger.info(f"✅ Normalized {len(normalized_assets)}/{cleansed_count} records")

        # Get persistent agent for asset creation (use same pattern as cleansing)
        # Build context from self.context (ExecutionEngineDiscoveryCrews has it)
        request_context = self.context  # Already a RequestContext

        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        inventory_agent = await TenantScopedAgentPool.get_agent(
            context=request_context,
            agent_type="asset_inventory",
            service_registry=self.service_registry,  # Pass existing service_registry
        )

        logger.info("🔧 Retrieved agent: asset_inventory")
        logger.info("Agent tools: ['asset_creator','bulk_asset_creator']")

        # Continue with asset creation using the inventory agent
        try:
            # Use the persistent agent to create assets from normalized data
            # Prepare task description for the agent
            task_description = "Create database asset records from cleaned CMDB data"

            # Execute asset creation with the persistent agent
            # AssetCreationToolsExecutor already imported at module level
            from ..asset_creation_tools import AssetCreationToolsExecutor

            result = await AssetCreationToolsExecutor.execute_asset_creation_with_tools(
                inventory_agent, {"raw_data": normalized_assets}, task_description
            )

            # Extract actual counts from result
            assets_created = 0
            assets_failed = 0

            if isinstance(result, dict):
                assets_created = result.get("assets_created", 0)
                # Calculate failed count: total normalized - created
                total_normalized = len(normalized_assets)
                assets_failed = max(0, total_normalized - assets_created)

            # 5. Log asset creation results as specified
            logger.info(
                f"🔨 Asset creation result: created={assets_created}, failed={assets_failed}"
            )

            # Maintain backward compatibility with asset_inventory field
            asset_inventory = (
                result.get(
                    "asset_inventory",
                    {"total_assets": assets_created, "classification_complete": True},
                )
                if isinstance(result, dict)
                else {"total_assets": 0, "classification_complete": False}
            )

            return {
                "phase": "asset_inventory",
                "status": "completed",
                "crew_results": result,
                "asset_inventory": asset_inventory,  # Backward compatibility
                "agent": "asset_inventory_agent",
                "method": "persistent_agent_execution",
                "assets_created": assets_created,  # Return actual counts
                "assets_failed": assets_failed,
            }
        except Exception as e:
            logger.error(f"Asset inventory failed: {str(e)}")
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
