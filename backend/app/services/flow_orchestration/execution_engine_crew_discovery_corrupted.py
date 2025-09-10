"""
Flow Execution Engine Discovery Crew
Discovery-specific CrewAI execution methods and phase handlers.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.crewai_flows.handlers.unified_flow_crew_manager import (
    UnifiedFlowCrewManager,
)
from .asset_creation_tools import AssetCreationToolsExecutor
from .discovery_phase_handlers import DiscoveryPhaseHandlers
from .field_mapping_logic import FieldMappingLogic

logger = get_logger(__name__)


class DictStateAdapter:
    """Adapter to make a dict work as a state object for UnifiedFlowCrewManager."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize adapter with dict data as attributes."""
        self._errors: List[Dict[str, str]] = []
        # Prevent overwriting internal attributes
        for k, v in data.items():
            if k.startswith("_"):
                continue
            setattr(self, k, v)

    def add_error(self, key: str, message: str):
        """Add an error to the state."""
        self._errors.append({"key": key, "message": message})


class ExecutionEngineDiscoveryCrews:
    """Discovery flow CrewAI execution handlers."""

    def __init__(self, crew_utils, context=None, db_session=None):
        self.crew_utils = crew_utils
        self.field_mapping_logic = FieldMappingLogic()
        self.phase_handlers = DiscoveryPhaseHandlers(context)
        self.context = context
        self.service_registry = None
        self.db_session = db_session

    def set_service_registry(self, service_registry):
        """Set the ServiceRegistry for this discovery crews instance."""
        self.service_registry = service_registry

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
            "asset_inventory": "asset_inventory",
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
            "data_cleansing": self.phase_handlers.execute_data_cleansing,
            "asset_creation": self._execute_discovery_asset_creation,
            "asset_inventory": self._execute_discovery_asset_inventory,
            "analysis": self.phase_handlers.execute_analysis,
        }

        method = phase_methods.get(mapped_phase, self._execute_discovery_generic_phase)
        return await method(agent_pool, phase_input)

                }

            # Check if crew has async kickoff method
            if hasattr(crew, "kickoff_async"):
                result = await crew.kickoff_async(inputs=phase_input)
            else:
                # Use synchronous kickoff
                result = crew.kickoff(inputs=phase_input)

            # Maintain backward compatibility with validation_results field
            validation_results = (
                result.get("validation_results", {"valid": True, "issues": []})
                if isinstance(result, dict)
                else {"valid": True, "issues": []}
            )

            return {
                "phase": "data_import_validation",
                "status": "completed",
                "crew_results": result,
                "validation_results": validation_results,  # Backward compatibility
                "agent": "data_validation_agent",
            }
        except Exception as e:
            logger.error(f"Data import validation failed: {str(e)}")
            return {
                "phase": "data_import_validation",
                "status": "error",
                "error": str(e),
                "validation_results": {"valid": False, "issues": [str(e)]},
                "agent": "data_validation_agent",
            }

    async def _execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase - delegated to specialized handler"""
        return await self.field_mapping_logic.execute_discovery_field_mapping(
            agent_pool, phase_input, self.db_session
        )

                }

            # Check if crew has async kickoff method
            if hasattr(crew, "kickoff_async"):
                result = await crew.kickoff_async(inputs=phase_input)
            else:
                # Use synchronous kickoff
                result = crew.kickoff(inputs=phase_input)

            # Maintain backward compatibility with cleansed_data field
            cleansed_data = (
                result.get("cleansed_data", []) if isinstance(result, dict) else []
            )

            return {
                "phase": "data_cleansing",
                "status": "completed",
                "crew_results": result,
                "cleansed_data": cleansed_data,  # Backward compatibility
                "agent": "data_cleansing_agent",
            }
        except Exception as e:
            logger.error(f"Data cleansing failed: {str(e)}")
            return {
                "phase": "data_cleansing",
                "status": "error",
                "error": str(e),
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

    async def _execute_discovery_asset_inventory(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute asset inventory phase using persistent agent"""
        logger.info("📦 Executing discovery asset inventory using persistent agent")

        try:
            # Ensure all inputs are JSON-serializable (convert UUIDs to strings)
            serializable_input = {}
            for key, value in phase_input.items():
                if hasattr(value, "__str__") and hasattr(
                    value, "hex"
                ):  # UUID-like object
                    serializable_input[key] = str(value)
                elif (
                    isinstance(value, (str, int, float, bool, list, dict))
                    or value is None
                ):
                    serializable_input[key] = value
                else:
                    serializable_input[key] = str(
                        value
                    )  # Convert unknown types to string

            # Use persistent agent pattern instead of crew pattern
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            # Ensure context has required attributes from phase_input
            context_for_agent = self.context
            if (
                not hasattr(context_for_agent, "client_account_id")
                or context_for_agent.client_account_id is None
            ):
                # Create a context object with the required attributes from phase_input
                from app.core.context import RequestContext

                context_for_agent = RequestContext(
                    client_account_id=phase_input.get("client_account_id"),
                    engagement_id=phase_input.get("engagement_id"),
                    request_id=(
                        getattr(self.context, "request_id", None)
                        if self.context
                        else None
                    ),
                )
                logger.info(
                    f"Created context for agent: client_id={context_for_agent.client_account_id}, "
                    f"engagement_id={context_for_agent.engagement_id}"
                )

            # Get the persistent agent
            agent = await TenantScopedAgentPool.get_agent(
                context=context_for_agent,
                agent_type="asset_inventory_agent",
                service_registry=self.service_registry,
            )

            # Prepare task description for the agent
            task_description = "Create database asset records from cleaned CMDB data"

            # Execute asset creation using agent's tools (extracted to separate class)
            result = await AssetCreationToolsExecutor.execute_asset_creation_with_tools(
                agent, serializable_input, task_description
            )

            # Maintain backward compatibility with asset_inventory field
            asset_inventory = (
                result.get(
                    "asset_inventory",
                    {"total_assets": 0, "classification_complete": False},
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

