"""
Field Mapping Executor - Core Orchestrator

The main FieldMappingExecutor class that coordinates all field mapping operations
by orchestrating the modular components: parsers, validators, mapping engine,
transformation, rules engine, and formatters.

This class maintains the same public interface as the original monolithic
implementation while leveraging the modular architecture for better
maintainability and reduced complexity.
"""

import logging
from typing import Any, Dict, List, Optional

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .agent_operations import AgentOperations
from .business_logic import BusinessLogicManager
from .exceptions import FieldMappingExecutorError
from .formatters import MappingResponseFormatter
from .mapping_engine import IntelligentMappingEngine
from .parsers import CompositeMappingParser
from .rules_engine import MappingRulesEngine
from .state_management import StateManager
from .transformation import MappingTransformer
from .validation import CompositeValidator

logger = logging.getLogger(__name__)


class FieldMappingExecutor:
    """
    Core executor for field mapping phase operations.

    Orchestrates field mapping by coordinating modular components:
    - Parsing: Extract mappings from CrewAI agent responses
    - Validation: Validate field mappings and confidence scores
    - Mapping Engine: Generate intelligent field mappings
    - Transformation: Transform and persist mapping data
    - Rules Engine: Apply business rules and generate clarifications
    - Formatting: Format responses and validation results

    This class can work independently without BasePhaseExecutor inheritance
    to avoid circular dependencies while maintaining full functionality.
    """

    def __init__(
        self,
        storage_manager: Optional[Any] = None,
        agent_pool: Optional[Any] = None,
        client_account_id: str = "unknown",
        engagement_id: str = "unknown",
    ):
        """Initialize the field mapping executor with modular components."""
        # Store attributes with optional types for flexibility
        self.storage_manager = storage_manager
        self.agent_pool = agent_pool
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize modular components
        self.parser = CompositeMappingParser()
        self.validator = CompositeValidator()
        self.mapping_engine = IntelligentMappingEngine()
        # Only initialize transformer if storage_manager is available
        self.transformer = (
            MappingTransformer(storage_manager, client_account_id, engagement_id)
            if storage_manager
            else None
        )
        self.rules_engine = MappingRulesEngine()
        self.formatter = MappingResponseFormatter()

        # Initialize modular managers
        self.agent_ops = AgentOperations(agent_pool, client_account_id, engagement_id)
        self.state_manager = StateManager(client_account_id, engagement_id)
        self.business_logic = BusinessLogicManager(
            self.parser,
            self.validator,
            self.rules_engine,
            self.formatter,
            self.transformer,
        )

        logger.info(
            f"FieldMappingExecutor initialized for client {client_account_id}, engagement {engagement_id}"
        )

    async def execute_phase(
        self, state: UnifiedDiscoveryFlowState, db_session: Any
    ) -> Dict[str, Any]:
        """
        Execute the field mapping phase.

        Args:
            state: Current unified discovery flow state
            db_session: Database session for persistence

        Returns:
            Dictionary containing execution results and next phase information

        Raises:
            FieldMappingExecutorError: If field mapping execution fails
        """
        try:
            logger.info(f"Starting field mapping execution for flow {state.flow_id}")

            # Validate state has required data
            self.state_manager.validate_execution_state(state)

            # Get field mapping agent and execute mapping
            agent_response = await self.agent_ops.execute_field_mapping_agent(state)

            # Parse the agent response to extract mappings
            parsed_mappings = await self.business_logic.parse_agent_response(
                agent_response, state
            )

            # Validate the parsed mappings
            validation_results = await self.business_logic.validate_mappings(
                parsed_mappings, state
            )

            # Apply business rules and check for clarifications needed
            rules_results = await self.business_logic.apply_business_rules(
                parsed_mappings, state
            )

            # Transform and persist the mappings if transformer is available
            if self.transformer:
                transformation_results = (
                    await self.business_logic.transform_and_persist(
                        parsed_mappings, validation_results, state, db_session
                    )
                )
            else:
                transformation_results = {
                    "success": True,
                    "mappings_persisted": len(parsed_mappings.get("mappings", [])),
                    "message": "Transformation skipped - no storage manager",
                }

            # Format the final response
            response = await self.business_logic.format_response(
                parsed_mappings,
                validation_results,
                rules_results,
                transformation_results,
                state,
            )

            logger.info(f"Field mapping execution completed for flow {state.flow_id}")
            return response

        except Exception as e:
            logger.error(
                f"Field mapping execution failed for flow {state.flow_id}: {str(e)}"
            )
            raise FieldMappingExecutorError(
                f"Field mapping execution failed: {str(e)}"
            ) from e

    # Backward compatibility methods
    async def execute_field_mapping(
        self, flow_state: UnifiedDiscoveryFlowState, db_session: Any
    ) -> Dict[str, Any]:
        """
        Backward compatibility method for execute_field_mapping.

        This method maintains the original interface while using the new
        modular implementation under the hood.
        """
        return await self.execute_phase(flow_state, db_session)

    def get_phase_name(self) -> str:
        """Return the phase name for this executor."""
        return "field_mapping"

    def get_supported_flow_types(self) -> List[str]:
        """Return the flow types supported by this executor."""
        return ["discovery"]

    # Delegate methods for backward compatibility
    def _validate_execution_state(self, state: UnifiedDiscoveryFlowState) -> None:
        """Delegate to state manager for backward compatibility."""
        return self.state_manager.validate_execution_state(state)

    async def _execute_field_mapping_agent(
        self, state: UnifiedDiscoveryFlowState
    ) -> str:
        """Delegate to agent operations for backward compatibility."""
        return await self.agent_ops.execute_field_mapping_agent(state)

    def _get_mock_agent_response(self, state: UnifiedDiscoveryFlowState) -> str:
        """Delegate to agent operations for backward compatibility."""
        return self.agent_ops._get_mock_agent_response(state)

    def _prepare_agent_input(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Delegate to agent operations for backward compatibility."""
        return self.agent_ops._prepare_agent_input(state)

    async def _execute_agent_with_crew(
        self, agent: Any, agent_input: Dict[str, Any]
    ) -> str:
        """Delegate to agent operations for backward compatibility."""
        return await self.agent_ops._execute_agent_with_crew(agent, agent_input)

    def _prepare_unified_state(self, agent_input: Dict[str, Any]) -> Any:
        """Delegate to agent operations for backward compatibility."""
        return self.agent_ops._prepare_unified_state(agent_input)

    async def _parse_agent_response(
        self, agent_response: str, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Delegate to business logic for backward compatibility."""
        return await self.business_logic.parse_agent_response(agent_response, state)

    async def _validate_mappings(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Delegate to business logic for backward compatibility."""
        return await self.business_logic.validate_mappings(parsed_mappings, state)

    async def _apply_business_rules(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Delegate to business logic for backward compatibility."""
        return await self.business_logic.apply_business_rules(parsed_mappings, state)

    async def _transform_and_persist(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
        db_session: Any,
    ) -> Dict[str, Any]:
        """Delegate to business logic for backward compatibility."""
        return await self.business_logic.transform_and_persist(
            parsed_mappings, validation_results, state, db_session
        )

    async def _format_response(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
    ) -> Dict[str, Any]:
        """Delegate to business logic for backward compatibility."""
        return await self.business_logic.format_response(
            parsed_mappings,
            validation_results,
            rules_results,
            transformation_results,
            state,
        )

    def _determine_next_phase(
        self,
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
    ) -> str:
        """Delegate to state manager for backward compatibility."""
        return self.state_manager.determine_next_phase(
            validation_results, rules_results, transformation_results
        )

    async def _get_engagement_requirements(self) -> Dict[str, Any]:
        """Delegate to state manager for backward compatibility."""
        return await self.state_manager.get_engagement_requirements()

    async def _get_client_preferences(self) -> Dict[str, Any]:
        """Delegate to state manager for backward compatibility."""
        return await self.state_manager.get_client_preferences()
