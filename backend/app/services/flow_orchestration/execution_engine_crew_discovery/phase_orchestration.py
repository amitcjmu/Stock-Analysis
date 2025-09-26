"""
Phase orchestration logic for Discovery Flow Execution Engine.
Contains phase routing, execution, and state management methods.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class PhaseOrchestrationMixin:
    """Mixin class containing phase orchestration methods for discovery flows."""

    async def execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Main entry point for discovery phase execution.

        Routes to appropriate phase method based on phase name.
        """
        phase_name = phase_config.name
        logger.info(f"🎯 Executing discovery phase: {phase_name}")

        # Define phase-to-method mapping
        phase_methods = {
            "data_cleansing": self._execute_discovery_data_cleansing,  # Data cleansing phase
            "asset_creation": self._execute_discovery_asset_inventory,  # Asset creation is part of inventory (ADR-022)
            "asset_inventory": self._execute_discovery_asset_inventory,
            "dependency_analysis": self._execute_discovery_dependency_analysis,  # Dependency analysis phase
            "dependencies": self._execute_discovery_dependency_analysis,  # Alternative phase name
            # Add other phases as needed
        }

        # Map phase to execution method
        execution_method = phase_methods.get(phase_name)

        if execution_method:
            logger.info(
                f"📍 Mapped phase '{phase_name}' to method: {execution_method.__name__}"
            )
            return await execution_method(
                None, phase_input
            )  # agent_pool not used in persistent agent pattern
        else:
            # Use generic phase handler for unmapped phases
            logger.warning(f"⚠️ Phase '{phase_name}' not mapped, using generic handler")
            return await self._execute_discovery_generic_phase(None, phase_input)

    async def execute_discovery_phase_with_persistent_agents(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute discovery flow phase using persistent agents (ADR-015)"""

        # ADR-015: Use ONLY persistent agents - no fallback to service pattern
        logger.info(f"🔄 Executing phase '{phase_config.name}' with persistent agents")

        # Prepare phase input with flow context
        await self._prepare_phase_input(master_flow, phase_input)

        # Load raw data from persistence if available
        self._load_raw_data_from_persistence(master_flow, phase_input)

        try:
            # Initialize persistent agent pool
            agent_pool = await self._initialize_discovery_agent_pool(master_flow)
        except ValueError as e:
            return self._handle_pydantic_validation_error(e, phase_config, master_flow)
        except Exception as e:
            return self._handle_general_agent_error(e, phase_config, master_flow)

        try:
            # Execute the phase
            return await self._execute_phase_with_agent_pool(
                phase_config, agent_pool, phase_input
            )
        except Exception as e:
            logger.error(f"❌ Discovery phase failed: {e}")
            return self.crew_utils.build_error_response(phase_config.name, str(e))

    async def _prepare_phase_input(
        self, master_flow: CrewAIFlowStateExtensions, phase_input: Dict[str, Any]
    ) -> None:
        """Prepare phase input with flow context data"""
        # Ensure flow_id is set (may already be set by execution_engine_core)
        if "flow_id" not in phase_input:
            phase_input["flow_id"] = master_flow.id
        if "master_flow_id" not in phase_input:
            phase_input["master_flow_id"] = master_flow.flow_id
        if "client_account_id" not in phase_input:
            phase_input["client_account_id"] = master_flow.client_account_id
        if "engagement_id" not in phase_input:
            phase_input["engagement_id"] = master_flow.engagement_id

        # Get data_import_id and discovery_flow_id from discovery_flows table
        if (
            "data_import_id" not in phase_input
            or "discovery_flow_id" not in phase_input
        ):
            # First check flow_metadata for data_import_id
            if "data_import_id" not in phase_input:
                if hasattr(master_flow, "flow_metadata") and master_flow.flow_metadata:
                    if isinstance(master_flow.flow_metadata, dict):
                        phase_input["data_import_id"] = master_flow.flow_metadata.get(
                            "data_import_id"
                        )

            # Get both data_import_id and discovery_flow_id from discovery_flows table
            if (
                not phase_input.get("data_import_id")
                or "discovery_flow_id" not in phase_input
            ):
                try:
                    from sqlalchemy import select
                    from app.models.discovery_flow import DiscoveryFlow

                    result = await self.db_session.execute(
                        select(
                            DiscoveryFlow.data_import_id, DiscoveryFlow.flow_id
                        ).where(
                            DiscoveryFlow.master_flow_id == master_flow.flow_id,
                            DiscoveryFlow.client_account_id
                            == master_flow.client_account_id,
                            DiscoveryFlow.engagement_id == master_flow.engagement_id,
                        )
                    )
                    discovery_flow = result.first()
                    if discovery_flow:
                        if not phase_input.get("data_import_id"):
                            phase_input["data_import_id"] = str(
                                discovery_flow.data_import_id
                            )
                            logger.info(
                                f"✅ Retrieved data_import_id from discovery_flows: {discovery_flow.data_import_id}"
                            )
                        phase_input["discovery_flow_id"] = str(discovery_flow.flow_id)
                        logger.info(
                            f"✅ Retrieved discovery_flow_id from discovery_flows: {discovery_flow.flow_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to retrieve flow IDs from discovery_flows: {e}"
                    )

    def _load_raw_data_from_persistence(
        self, master_flow: CrewAIFlowStateExtensions, phase_input: Dict[str, Any]
    ) -> None:
        """Load raw data from flow persistence data"""
        logger.info(
            f"🔍 Flow persistence data exists: {master_flow.flow_persistence_data is not None}"
        )

        if not master_flow.flow_persistence_data:
            logger.warning("⚠️ No flow_persistence_data available on master_flow")
            return

        logger.info(
            f"🔍 Flow persistence keys: {list(master_flow.flow_persistence_data.keys())}"
        )

        # Type check to ensure we have a dict before calling extract
        if isinstance(master_flow.flow_persistence_data, dict):
            raw_data = self._extract_raw_data(master_flow.flow_persistence_data)
        else:
            raw_data = None

        if raw_data is not None:
            phase_input["raw_data"] = raw_data
            record_count = self._get_safe_record_count(raw_data)
            logger.info(
                f"📊 Retrieved {record_count} records from flow persistence for phase execution"
            )
        else:
            logger.warning("⚠️ No raw_data found in flow_persistence_data structure")

    def _extract_raw_data(self, flow_persistence_data: Dict[str, Any]) -> Any:
        """Extract raw data from flow persistence data"""
        if "raw_data" in flow_persistence_data:
            logger.info("✅ Found raw_data in flow_persistence_data")
            return flow_persistence_data["raw_data"]

        if "initial_state" in flow_persistence_data:
            initial_state = flow_persistence_data["initial_state"]
            if isinstance(initial_state, dict) and "raw_data" in initial_state:
                logger.info("✅ Found raw_data in flow_persistence_data.initial_state")
                return initial_state["raw_data"]

        return None

    def _get_safe_record_count(self, raw_data: Any) -> int:
        """Safely get count of records from raw data"""
        try:
            return len(raw_data) if raw_data is not None else 0
        except (TypeError, AttributeError):
            return 1 if raw_data is not None else 0

    def _map_discovery_phase_name(self, phase_name: str) -> str:
        """Map flow phase names to discovery service methods"""
        phase_mapping = {
            "data_import": "data_import_validation",
            "field_mapping": "field_mapping",
            "data_cleansing": "data_cleansing",
            "asset_creation": "asset_creation",
            "asset_inventory": "asset_inventory",
            "dependency_analysis": "dependency_analysis",
            "dependencies": "dependency_analysis",  # Map dependencies to dependency_analysis
            "analysis": "analysis",
        }
        return phase_mapping.get(phase_name, phase_name)

    async def _execute_discovery_mapped_phase(
        self, mapped_phase: str, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mapped discovery phase"""
        phase_methods = {
            "data_import_validation": self.phase_handlers.execute_data_import_validation,
            "field_mapping": self._execute_discovery_field_mapping,
            "data_cleansing": self._execute_discovery_data_cleansing,
            "asset_creation": self._execute_discovery_asset_inventory,  # Asset creation is part of inventory (ADR-022)
            "asset_inventory": self._execute_discovery_asset_inventory,
            "dependency_analysis": self._execute_discovery_dependency_analysis,  # Dependency analysis phase
            "dependencies": self._execute_discovery_dependency_analysis,  # Alternative phase name
            "analysis": self.phase_handlers.execute_analysis,
        }

        method = phase_methods.get(mapped_phase, self._execute_discovery_generic_phase)
        return await method(agent_pool, phase_input)
