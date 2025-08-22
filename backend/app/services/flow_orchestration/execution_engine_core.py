"""
Flow Execution Engine Core Module - Main Implementation
Core execution logic using modularized components for phase orchestration.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowNotFoundError
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.crewai_flows.agents.decision.base import PhaseAction
from app.services.crewai_flows.agents.decision.field_mapping import (
    FieldMappingDecisionAgent,
)
from app.services.crewai_flows.agents.decision.phase_transition import (
    PhaseTransitionAgent,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry

# Import modularized components
from app.services.flow_orchestration.execution_engine_agents import (
    ExecutionEngineAgentHandlers,
)
from app.services.flow_orchestration.execution_engine_phase_utils import (
    ExecutionEnginePhaseUtils,
)
from app.services.flow_orchestration.execution_engine_state_utils import (
    ExecutionEngineStateUtils,
)
from app.services.flow_orchestration.execution_engine_validators import (
    ExecutionEngineValidators,
)

logger = get_logger(__name__)


class FlowExecutionCore:
    """
    Core execution logic for flow phases and orchestration.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry: FlowTypeRegistry,
        handler_registry: HandlerRegistry,
        validator_registry: ValidatorRegistry,
    ):
        """
        Initialize the Flow Execution Core
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry

        # Initialize decision agents
        self.field_mapping_agent = FieldMappingDecisionAgent()
        # Make the phase transition agent flow-aware by providing the registry
        # Flow type will be determined at runtime from context
        self.phase_transition_agent = PhaseTransitionAgent(
            flow_registry=self.flow_registry
        )

        # Initialize modular components
        self.agents = ExecutionEngineAgentHandlers(
            master_repo, self.phase_transition_agent
        )
        self.phase_utils = ExecutionEnginePhaseUtils(master_repo, self.flow_registry)
        self.state_utils = ExecutionEngineStateUtils(master_repo, context)
        self.validators = ExecutionEngineValidators(validator_registry, context)

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a specific phase of a flow

        Args:
            flow_id: Flow identifier
            phase_name: Name of the phase to execute
            phase_input: Input data for the phase
            validation_overrides: Optional validation overrides

        Returns:
            Phase execution results

        Raises:
            ValueError: If flow or phase not found
            RuntimeError: If phase execution fails
        """
        start_time = datetime.utcnow()

        try:
            # Get flow and validate
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise FlowNotFoundError(flow_id)

            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            if not flow_config:
                raise ValueError(
                    f"Flow type '{master_flow.flow_type}' not found in registry"
                )

            # Get phase configuration
            phase_config = flow_config.get_phase_config(phase_name)
            if not phase_config:
                raise ValueError(
                    f"Phase '{phase_name}' not found in flow type '{master_flow.flow_type}'"
                )

            logger.info(f"🎯 Executing phase '{phase_name}' for flow {flow_id}")

            # Prepare phase input
            if phase_input is None:
                phase_input = {}

            # Run pre-phase validations (if not overridden)
            if not validation_overrides or validation_overrides.get(
                "run_pre_validations", True
            ):
                validation_result = await self.validators.run_phase_validators(
                    master_flow, phase_config, phase_input, "pre"
                )
                if not validation_result["valid"]:
                    logger.error(
                        f"❌ Pre-phase validation failed for {phase_name}: {validation_result['errors']}"
                    )
                    return {
                        "phase": phase_name,
                        "status": "failed",
                        "validation_errors": validation_result["errors"],
                        "execution_time": (
                            datetime.utcnow() - start_time
                        ).total_seconds(),
                    }

            # Get current flow state for agent context
            flow_state = await self.state_utils.get_flow_state(flow_id)

            # Get agent decision for phase execution (if enabled)
            agent_decision = await self.agents.get_agent_decision(
                master_flow,
                phase_name,
                phase_input,
                flow_state,
                self.phase_utils.get_default_next_phase,
            )

            # Log agent decision
            await self.agents.log_agent_decision(flow_id, phase_name, agent_decision)

            # Handle agent pause if requested
            if agent_decision.action == PhaseAction.PAUSE:
                return await self.agents.handle_agent_pause(
                    flow_id, phase_name, agent_decision
                )

            # Handle agent skip if requested
            if agent_decision.action == PhaseAction.SKIP:
                return await self.phase_utils.skip_to_next_phase(
                    flow_id, phase_name, agent_decision
                )

            # Execute the phase based on executor type
            phase_result = {}
            # Determine executor type based on phase configuration
            has_crew_config = bool(
                phase_config.crew_config and len(phase_config.crew_config) > 0
            )

            if has_crew_config:
                # Import crew execution handler
                try:
                    from app.services.flow_orchestration.execution_engine_crew import (
                        FlowExecutionCrew,
                    )

                    crew_executor = FlowExecutionCrew(
                        self.db, self.context, self.master_repo
                    )
                    phase_result = await crew_executor.execute_crew_phase(
                        master_flow, phase_config, phase_input
                    )
                except ImportError as e:
                    logger.warning(f"CrewAI execution not available: {e}")
                    # Fallback to handler-based execution
                    phase_result = await self._execute_handler_phase(
                        master_flow, phase_config, phase_input
                    )
            else:
                # Handler-based execution
                phase_result = await self._execute_handler_phase(
                    master_flow, phase_config, phase_input
                )

            # Get post-execution decision with flow-type aware fallback
            post_decision = await self.agents.get_post_execution_decision(
                master_flow,
                phase_name,
                phase_result,
                flow_state,
                lambda name: self.phase_utils.get_default_next_phase(
                    name, flow_type=master_flow.flow_type
                ),
            )

            # Apply post-execution decision to result
            phase_result["next_phase"] = post_decision.next_phase
            phase_result["agent_decision"] = {
                "action": post_decision.action.value,
                "confidence": post_decision.confidence,
                "reasoning": post_decision.reasoning,
            }

            # Ensure result is JSON serializable
            phase_result = self.state_utils.ensure_json_serializable(phase_result)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            phase_result["execution_time"] = execution_time

            logger.info(
                f"✅ Phase '{phase_name}' completed successfully in {execution_time:.2f}s"
            )

            return phase_result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Phase '{phase_name}' failed: {str(e)}")

            # Check if error is recoverable
            is_recoverable = self.phase_utils.is_recoverable_error(e)

            return {
                "phase": phase_name,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "recoverable": is_recoverable,
                "execution_time": execution_time,
            }

    async def _execute_handler_phase(
        self, master_flow, phase_config, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute phase using handler-based approach"""
        try:
            # Get phase handler
            handler = self.handler_registry.get_handler(phase_config.handler)
            if not handler:
                raise ValueError(f"Handler '{phase_config.handler}' not found")

            # Execute phase through handler
            result = await handler.execute(
                flow_id=master_flow.flow_id,
                phase_input=phase_input,
                context=self.context,
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "result": result,
                "next_phase": self.phase_utils.get_default_next_phase(
                    phase_config.name
                ),
            }

        except Exception as e:
            logger.error(f"Handler execution failed: {e}")
            raise
