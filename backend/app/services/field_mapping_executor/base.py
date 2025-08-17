"""
Field Mapping Executor - Core Orchestrator

The main FieldMappingExecutor class that coordinates all field mapping operations
by orchestrating the modular components: parsers, validators, mapping engine,
transformation, rules engine, and formatters.

This class maintains the same public interface as the original monolithic
implementation while leveraging the modular architecture for better
maintainability and reduced complexity.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.services.crewai_flows.handlers.base_executor import BasePhaseExecutor
from app.services.storage_manager import StorageManager
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# from app.models.discovery_flows import DiscoveryFlow  # Currently unused
# from app.db.session import get_db  # Currently unused

from .exceptions import (
    FieldMappingExecutorError,
    MappingParseError,
    ValidationError,
    CrewExecutionError,
    TransformationError,
)
from .parsers import CompositeMappingParser
from .validation import CompositeValidator
from .mapping_engine import IntelligentMappingEngine
from .transformation import MappingTransformer
from .rules_engine import MappingRulesEngine
from .formatters import MappingResponseFormatter


logger = logging.getLogger(__name__)


class FieldMappingExecutor(BasePhaseExecutor):
    """
    Core executor for field mapping phase operations.

    Orchestrates field mapping by coordinating modular components:
    - Parsing: Extract mappings from CrewAI agent responses
    - Validation: Validate field mappings and confidence scores
    - Mapping Engine: Generate intelligent field mappings
    - Transformation: Transform and persist mapping data
    - Rules Engine: Apply business rules and generate clarifications
    - Formatting: Format responses and validation results
    """

    def __init__(
        self,
        storage_manager: StorageManager,
        agent_pool: TenantScopedAgentPool,
        client_account_id: str,
        engagement_id: str,
    ):
        """Initialize the field mapping executor with modular components."""
        super().__init__(storage_manager, agent_pool, client_account_id, engagement_id)

        # Initialize modular components
        self.parser = CompositeMappingParser()
        self.validator = CompositeValidator()
        self.mapping_engine = IntelligentMappingEngine()
        self.transformer = MappingTransformer(
            storage_manager, client_account_id, engagement_id
        )
        self.rules_engine = MappingRulesEngine()
        self.formatter = MappingResponseFormatter()

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
            self._validate_execution_state(state)

            # Get field mapping agent and execute mapping
            agent_response = await self._execute_field_mapping_agent(state)

            # Parse the agent response to extract mappings
            parsed_mappings = await self._parse_agent_response(agent_response, state)

            # Validate the parsed mappings
            validation_results = await self._validate_mappings(parsed_mappings, state)

            # Apply business rules and check for clarifications needed
            rules_results = await self._apply_business_rules(parsed_mappings, state)

            # Transform and persist the mappings
            transformation_results = await self._transform_and_persist(
                parsed_mappings, validation_results, state, db_session
            )

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

    def _validate_execution_state(self, state: UnifiedDiscoveryFlowState) -> None:
        """Validate that the state has required data for field mapping."""
        if not state.discovery_data:
            raise ValidationError("No discovery data available for field mapping")

        if not state.discovery_data.get("sample_data"):
            raise ValidationError("No sample data available for field mapping")

        if not state.discovery_data.get("detected_columns"):
            raise ValidationError("No detected columns available for field mapping")

        logger.debug(f"State validation passed for flow {state.flow_id}")

    async def _execute_field_mapping_agent(
        self, state: UnifiedDiscoveryFlowState
    ) -> str:
        """Execute the field mapping CrewAI agent."""
        try:
            # Get field mapping agent from the pool
            agent = await self.agent_pool.get_agent(
                agent_type="field_mapping",
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )

            if not agent:
                raise CrewExecutionError("Field mapping agent not available")

            # Prepare agent input from state
            agent_input = self._prepare_agent_input(state)

            # Execute the agent with retry logic
            response = await self._execute_with_retry(agent, agent_input)

            logger.info(
                f"Field mapping agent executed successfully for flow {state.flow_id}"
            )
            return response

        except Exception as e:
            logger.error(f"Field mapping agent execution failed: {str(e)}")
            raise CrewExecutionError(f"Agent execution failed: {str(e)}") from e

    def _prepare_agent_input(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Prepare input data for the field mapping agent."""
        discovery_data = state.discovery_data

        agent_input = {
            "sample_data": discovery_data.get("sample_data", []),
            "detected_columns": discovery_data.get("detected_columns", []),
            "data_source_info": discovery_data.get("data_source_info", {}),
            "previous_mappings": state.field_mappings or [],
            "mapping_context": {
                "flow_id": state.flow_id,
                "engagement_id": self.engagement_id,
                "client_account_id": self.client_account_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        logger.debug(
            f"Agent input prepared with {len(agent_input['detected_columns'])} columns"
        )
        return agent_input

    async def _execute_with_retry(self, agent: Any, agent_input: Dict[str, Any]) -> str:
        """Execute agent with retry logic for robustness."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await agent.execute(agent_input)
                if response and response.strip():
                    return response
                else:
                    raise CrewExecutionError("Agent returned empty response")

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise CrewExecutionError(
                        f"Agent execution failed after {max_retries} retries: {str(e)}"
                    )

                logger.warning(
                    f"Agent execution attempt {retry_count} failed, retrying: {str(e)}"
                )
                await asyncio.sleep(1 * retry_count)  # Exponential backoff

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
                "detected_columns": state.discovery_data.get("detected_columns", []),
                "sample_data": state.discovery_data.get("sample_data", []),
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
                "engagement_requirements": await self._get_engagement_requirements(),
                "client_preferences": await self._get_client_preferences(),
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
            response["next_phase"] = self._determine_next_phase(
                validation_results, rules_results, transformation_results
            )

            logger.info(f"Response formatted, next phase: {response['next_phase']}")
            return response

        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            raise FieldMappingExecutorError(
                f"Response formatting failed: {str(e)}"
            ) from e

    def _determine_next_phase(
        self,
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
    ) -> str:
        """Determine the next phase based on execution results."""
        # Check if clarifications are needed
        if rules_results.get("clarifications"):
            return "clarification_needed"

        # Check if validation failed critically
        if validation_results.get("critical_errors"):
            return "validation_failed"

        # Check if transformation failed
        if not transformation_results.get("success", False):
            return "transformation_failed"

        # Otherwise proceed to next phase
        return "data_transformation"

    async def _get_engagement_requirements(self) -> Dict[str, Any]:
        """Get engagement-specific requirements for field mapping."""
        try:
            # Get from storage manager
            requirements = await self.storage_manager.get_engagement_metadata(
                self.client_account_id, self.engagement_id
            )
            return requirements.get("field_mapping_requirements", {})
        except Exception as e:
            logger.warning(f"Could not retrieve engagement requirements: {str(e)}")
            return {}

    async def _get_client_preferences(self) -> Dict[str, Any]:
        """Get client-specific preferences for field mapping."""
        try:
            # Get from storage manager
            preferences = await self.storage_manager.get_client_preferences(
                self.client_account_id
            )
            return preferences.get("field_mapping_preferences", {})
        except Exception as e:
            logger.warning(f"Could not retrieve client preferences: {str(e)}")
            return {}

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
