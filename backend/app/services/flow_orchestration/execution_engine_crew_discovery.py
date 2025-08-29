"""
Flow Execution Engine Discovery Crew
Discovery-specific CrewAI execution methods and phase handlers.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from .field_mapping_logic import FieldMappingLogic

logger = get_logger(__name__)


class ExecutionEngineDiscoveryCrews:
    """Discovery flow CrewAI execution handlers."""

    def __init__(self, crew_utils):
        self.crew_utils = crew_utils
        self.field_mapping_logic = FieldMappingLogic()

    async def execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute discovery flow phase using persistent agents (ADR-015)"""

        # ADR-015: Use ONLY persistent agents - no fallback to service pattern
        logger.info(f"🔄 Executing phase '{phase_config.name}' with persistent agents")

        # Add flow context to phase_input for proper persistence
        phase_input["flow_id"] = master_flow.id
        phase_input["client_account_id"] = master_flow.client_account_id
        phase_input["engagement_id"] = master_flow.engagement_id

        # Get data_import_id from flow_metadata if available
        if hasattr(master_flow, "flow_metadata") and master_flow.flow_metadata:
            # flow_metadata is a JSONB column, accessed directly
            if isinstance(master_flow.flow_metadata, dict):
                phase_input["data_import_id"] = master_flow.flow_metadata.get(
                    "data_import_id"
                )

        # Retrieve flow data from persistence to ensure raw_data is available
        if master_flow.flow_persistence_data:
            # Add raw_data from flow persistence if not already in phase_input
            if (
                "raw_data" not in phase_input
                and "raw_data" in master_flow.flow_persistence_data
            ):
                raw_data = master_flow.flow_persistence_data["raw_data"]
                phase_input["raw_data"] = raw_data

                # Safely get the count of records
                try:
                    record_count = len(raw_data) if raw_data is not None else 0
                except (TypeError, AttributeError):
                    # Handle cases where raw_data is not a sized iterable
                    record_count = 1 if raw_data is not None else 0

                logger.info(
                    f"📊 Retrieved {record_count} records from flow persistence for phase execution"
                )

        try:
            # Initialize persistent agent pool
            agent_pool = await self._initialize_discovery_agent_pool(master_flow)

        except Exception as e:
            logger.error(f"❌ Discovery phase '{phase_config.name}' failed: {e}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

        try:
            # Map and execute phase
            mapped_phase = self._map_discovery_phase_name(phase_config.name)
            logger.info(
                f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for agent execution"
            )

            # Execute the specific phase
            result = await self._execute_discovery_mapped_phase(
                mapped_phase, agent_pool, phase_input
            )

            logger.info(
                f"✅ Discovery phase '{mapped_phase}' completed using persistent agents"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Discovery phase failed: {e}")
            return self.crew_utils.build_error_response(phase_config.name, str(e))

    async def _initialize_discovery_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Dict[str, Any]:
        """Initialize persistent agent pool for the tenant with ServiceRegistry support"""
        try:
            # Import here to avoid circular dependencies
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                client_id=master_flow.client_account_id,
                engagement_id=master_flow.engagement_id,
            )

            logger.info(
                f"🏊 Initialized agent pool for tenant {master_flow.client_account_id}"
            )
            return agent_pool

        except Exception as e:
            logger.error(f"❌ Failed to initialize agent pool: {e}")
            raise

    def _map_discovery_phase_name(self, phase_name: str) -> str:
        """Map flow phase names to discovery service methods"""
        phase_mapping = {
            "data_import": "data_import_validation",
            "field_mapping": "field_mapping",
            "data_cleansing": "data_cleansing",
            "asset_creation": "asset_creation",
            "analysis": "analysis",
        }
        return phase_mapping.get(phase_name, phase_name)

    async def _execute_discovery_mapped_phase(
        self, mapped_phase: str, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mapped discovery phase"""
        phase_methods = {
            "data_import_validation": self._execute_discovery_data_import_validation,
            "field_mapping": self._execute_discovery_field_mapping,
            "data_cleansing": self._execute_discovery_data_cleansing,
            "asset_creation": self._execute_discovery_asset_creation,
            "analysis": self._execute_discovery_analysis,
        }

        method = phase_methods.get(mapped_phase, self._execute_discovery_generic_phase)
        return await method(agent_pool, phase_input)

    async def _execute_discovery_data_import_validation(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data import validation phase"""
        logger.info("🔍 Executing discovery data import validation")

        # Placeholder implementation for data import validation
        return {
            "phase": "data_import_validation",
            "status": "completed",
            "validation_results": {"valid": True, "issues": []},
            "agent": "data_validation_agent",
        }

    async def _execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase - delegated to specialized handler"""
        return await self.field_mapping_logic.execute_discovery_field_mapping(
            agent_pool, phase_input
        )

    async def _execute_discovery_data_cleansing(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data cleansing phase"""
        logger.info("🧹 Executing discovery data cleansing")

        # Placeholder implementation for data cleansing
        return {
            "phase": "data_cleansing",
            "status": "completed",
            "cleansed_data": [],
            "agent": "data_cleansing_agent",
        }

    async def _execute_discovery_asset_creation(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute asset creation phase"""
        logger.info("🏗️ Executing discovery asset creation")

        # Placeholder implementation for asset creation
        return {
            "phase": "asset_creation",
            "status": "completed",
            "assets_created": 0,
            "agent": "asset_creation_agent",
        }

    async def _execute_discovery_analysis(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute analysis phase"""
        logger.info("📊 Executing discovery analysis")

        # Placeholder implementation for analysis
        return {
            "phase": "analysis",
            "status": "completed",
            "analysis_results": {},
            "agent": "analysis_agent",
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
