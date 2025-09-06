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

# Use late import pattern to avoid circular dependencies
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from .agent_executor import AgentExecutor
from .exceptions import (
    FieldMappingExecutorError,
    MappingParseError,
    TransformationError,
    ValidationError,
)
from .formatters import MappingResponseFormatter
from .mapping_engine import IntelligentMappingEngine
from .parsers import CompositeMappingParser
from .rules_engine import MappingRulesEngine
from .state_utils import PhaseUtils, StateValidator, StorageUtils
from .transformation import MappingTransformer
from .validation import CompositeValidator

if TYPE_CHECKING:
    pass

# Initialize logger first to avoid F821 error
logger = logging.getLogger(__name__)

# from app.models.discovery_flows import DiscoveryFlow  # Currently unused
# from app.db.session import get_db  # Currently unused


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

        # Initialize utility components
        self.agent_executor = AgentExecutor(
            client_account_id, engagement_id, agent_pool
        )
        self.storage_utils = StorageUtils(
            storage_manager, client_account_id, engagement_id
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
            StateValidator.validate_execution_state(state)

            # Get field mapping agent and execute mapping
            agent_response = await self.agent_executor.execute_field_mapping_agent(
                state
            )

            # Parse the agent response to extract mappings
            parsed_mappings = await self._parse_agent_response(agent_response, state)

            # Validate the parsed mappings
            validation_results = await self._validate_mappings(parsed_mappings, state)

            # Apply business rules and check for clarifications needed
            rules_results = await self._apply_business_rules(parsed_mappings, state)

            # Transform and persist the mappings if transformer is available
            if self.transformer:
                transformation_results = await self._transform_and_persist(
                    parsed_mappings, validation_results, state, db_session
                )
            else:
                transformation_results = {
                    "success": True,
                    "mappings_persisted": len(parsed_mappings.get("mappings", [])),
                    "message": "Transformation skipped - no storage manager",
                }

            # Format the final response
            response = await self._format_response(
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

    async def _parse_agent_response(
        self, agent_response: str, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Parse the agent response to extract field mappings."""
        try:
            parsed_data = await self.parser.parse_response(agent_response)

            # Enhance with state context
            parsed_data["flow_context"] = {
                "flow_id": state.flow_id,
                "engagement_id": self.engagement_id,
                "client_account_id": self.client_account_id,
            }

            logger.info(f"Parsed {len(parsed_data.get('mappings', []))} field mappings")
            return parsed_data

        except Exception as e:
            logger.error(f"Failed to parse agent response: {str(e)}")
            raise MappingParseError(f"Response parsing failed: {str(e)}") from e

    async def _validate_mappings(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Validate the parsed field mappings."""
        try:
            validation_context = {
                "detected_columns": state.metadata.get("detected_columns", []),
                "sample_data": state.raw_data,
                "flow_id": state.flow_id,
            }

            validation_results = await self.validator.validate_mappings(
                parsed_mappings, validation_context
            )

            logger.info(
                f"Validation completed with {validation_results.get('error_count', 0)} errors"
            )
            return validation_results

        except Exception as e:
            logger.error(f"Mapping validation failed: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}") from e

    async def _apply_business_rules(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Apply business rules and check for clarifications needed."""
        try:
            rules_context = {
                "flow_state": state,
                "engagement_requirements": await self.storage_utils.get_engagement_requirements(),
                "client_preferences": await self.storage_utils.get_client_preferences(),
            }

            rules_results = await self.rules_engine.apply_rules(
                parsed_mappings, rules_context
            )

            logger.info(
                f"Business rules applied, {len(rules_results.get('clarifications', []))} clarifications generated"
            )
            return rules_results

        except Exception as e:
            logger.error(f"Business rules application failed: {str(e)}")
            raise ValidationError(f"Rules validation failed: {str(e)}") from e

    async def _transform_and_persist(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
        db_session: Any,
    ) -> Dict[str, Any]:
        """Transform and persist the field mappings."""
        try:
            transformation_results = await self.transformer.transform_and_persist(
                parsed_mappings, validation_results, state, db_session
            )

            logger.info(
                f"Transformation completed, {transformation_results.get('mappings_persisted', 0)} mappings persisted"
            )
            return transformation_results

        except Exception as e:
            logger.error(f"Transformation and persistence failed: {str(e)}")
            raise TransformationError(f"Transformation failed: {str(e)}") from e

    async def _format_response(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
    ) -> Dict[str, Any]:
        """Format the final response for the field mapping phase."""
        try:
            response = await self.formatter.format_response(
                parsed_mappings=parsed_mappings,
                validation_results=validation_results,
                rules_results=rules_results,
                transformation_results=transformation_results,
                flow_context={
                    "flow_id": state.flow_id,
                    "engagement_id": self.engagement_id,
                    "client_account_id": self.client_account_id,
                    "current_phase": "field_mapping",
                },
            )

            # Determine next phase based on results
            response["next_phase"] = PhaseUtils.determine_next_phase(
                validation_results, rules_results, transformation_results
            )

            logger.info(f"Response formatted, next phase: {response['next_phase']}")
            return response

        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            raise FieldMappingExecutorError(
                f"Response formatting failed: {str(e)}"
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
        return ["unified_discovery", "field_mapping", "data_mapping"]
