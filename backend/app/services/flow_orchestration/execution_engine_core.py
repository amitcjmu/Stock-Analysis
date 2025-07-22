"""
Flow Execution Engine Core Module

Core execution logic and phase orchestration for flow operations.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowNotFoundError
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.crewai_flows.agents.decision import (
    AgentDecision,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry
from app.services.crewai_flows.agents.decision.base import PhaseAction
from app.services.crewai_flows.agents.decision.field_mapping import FieldMappingDecisionAgent
from app.services.crewai_flows.agents.decision.phase_transition import PhaseTransitionAgent

logger = get_logger(__name__)


class FlowExecutionCore:
    """
    Core execution logic for flow phases and orchestration.
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry,
                 handler_registry: HandlerRegistry,
                 validator_registry: ValidatorRegistry):
        """
        Initialize the Flow Execution Core
        
        Args:
            db: Database session
            context: Request context
            master_repo: Repository for master flow operations
            flow_registry: Registry for flow type configurations
            handler_registry: Registry for flow handlers
            validator_registry: Registry for flow validators
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        
        # Initialize decision agents
        self.phase_transition_agent = PhaseTransitionAgent()
        self.field_mapping_agent = FieldMappingDecisionAgent()
        
        logger.info(f"✅ Flow Execution Core initialized with decision agents for client {context.client_account_id}")
    
    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None
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
                raise ValueError(f"Flow type '{master_flow.flow_type}' not found in registry")
            
            # Get phase configuration
            phase_config = flow_config.get_phase_config(phase_name)
            if not phase_config:
                raise ValueError(f"Phase '{phase_name}' not found in flow type '{master_flow.flow_type}'")
            
            logger.info(f"🎯 Executing phase '{phase_name}' for flow {flow_id}")
            
            # Prepare phase input
            if phase_input is None:
                phase_input = {}
            
            # Run pre-phase validations (if not overridden)
            if not validation_overrides or validation_overrides.get("run_pre_validations", True):
                validation_result = await self._run_phase_validators(
                    master_flow, phase_config, phase_input, "pre"
                )
                if not validation_result["valid"]:
                    logger.error(f"❌ Pre-phase validation failed for {phase_name}: {validation_result['errors']}")
                    return {
                        "phase": phase_name,
                        "status": "failed",
                        "validation_errors": validation_result["errors"],
                        "execution_time": (datetime.utcnow() - start_time).total_seconds()
                    }
            
            # Get agent decision for phase execution (if enabled)
            agent_decision = await self._get_agent_decision(
                master_flow, phase_name, phase_input
            )
            
            # Log agent decision
            await self._log_agent_decision(flow_id, phase_name, agent_decision)
            
            # Handle agent pause if requested
            if agent_decision.action == PhaseAction.PAUSE:
                return await self._handle_agent_pause(flow_id, phase_name, agent_decision)
            
            # Handle agent skip if requested
            if agent_decision.action == PhaseAction.SKIP:
                return await self._skip_to_next_phase(flow_id, phase_name, agent_decision)
            
            # Execute the phase based on executor type
            phase_result = {}
            # Determine executor type based on phase configuration
            has_crew_config = bool(phase_config.crew_config and len(phase_config.crew_config) > 0)
            
            if has_crew_config:
                # Import crew execution handler
                from .execution_engine_crew import FlowCrewExecutor
                crew_executor = FlowCrewExecutor(
                    self.db, self.context, self.master_repo, self.flow_registry, 
                    self.handler_registry, self.validator_registry
                )
                phase_result = await crew_executor.execute_crew_phase(master_flow, phase_config, phase_input)
            elif not has_crew_config:
                # Execute through registered handler
                handler_name = phase_config.completion_handler or f"{phase_name}_handler"
                handler = self.handler_registry.get_handler(handler_name)
                if not handler:
                    # If no specific handler found, create a simple successful result
                    logger.warning(f"⚠️ No handler found for {handler_name}, attempting generic execution")
                    phase_result = {
                        "phase": phase_name,
                        "status": "completed",
                        "message": f"Phase {phase_name} completed (no specific handler configured)",
                        "timestamp": datetime.utcnow().isoformat(),
                        "inputs_processed": phase_input or {},
                        "outputs": {}
                    }
                else:
                    phase_result = await handler(
                        flow_id=flow_id,
                        phase_name=phase_name,
                        phase_input=phase_input,
                        context=self.context
                    )
            # No longer needed - covered by the has_crew_config logic
            
            # Run post-phase validations
            if not validation_overrides or validation_overrides.get("run_post_validations", True):
                validation_result = await self._run_phase_validators(
                    master_flow, phase_config, phase_result, "post"
                )
                if validation_result["warnings"]:
                    phase_result["validation_warnings"] = validation_result["warnings"]
            
            # Get post-execution decision from agent (if needed)
            post_execution_decision = await self._get_post_execution_decision(
                master_flow, phase_name, phase_result
            )
            
            # Apply agent's post-execution decision if it differs from default
            if post_execution_decision.next_phase != self._get_default_next_phase(phase_name):
                logger.info(f"🤖 Agent override: Proceeding to {post_execution_decision.next_phase} instead of default")
                phase_result["agent_override"] = {
                    "suggested_next_phase": post_execution_decision.next_phase,
                    "reasoning": post_execution_decision.reasoning
                }
            
            # Update flow status based on phase result
            if phase_result.get("status") == "completed":
                flow_status = "running"
                if post_execution_decision.next_phase == "completed":
                    flow_status = "completed"
                await self.master_repo.update_flow_status(
                    flow_id=flow_id,
                    status=flow_status,
                    phase_data={"last_completed_phase": phase_name, "last_phase_result": phase_result}
                )
            
            # Add execution metadata
            phase_result.update({
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "executed_at": datetime.utcnow().isoformat(),
                "agent_decision": {
                    "action": agent_decision.action.value,
                    "reasoning": agent_decision.reasoning,
                    "next_phase": agent_decision.next_phase
                }
            })
            
            logger.info(f"✅ Phase '{phase_name}' executed successfully for flow {flow_id}")
            return phase_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Phase execution failed for {phase_name} in flow {flow_id}: {e}")
            
            # Update flow status to failed
            error_details = {
                "phase": phase_name,
                "error": str(e),
                "execution_time": execution_time,
                "failed_at": datetime.utcnow().isoformat()
            }
            
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data=error_details
            )
            
            raise RuntimeError(f"Phase execution failed: {str(e)}")
    
    async def _run_phase_validators(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_data: Dict[str, Any],
        validation_type: str
    ) -> Dict[str, Any]:
        """Run validators for a specific phase"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Get validators for this phase and type
        validators = getattr(phase_config, f"{validation_type}_validators", [])
        
        for validator_name in validators:
            validator = self.validator_registry.get_validator(validator_name)
            if validator:
                try:
                    result = await validator(
                        flow_id=master_flow.flow_id,
                        phase_data=phase_data,
                        context=self.context
                    )
                    
                    # Handle ValidationResult dataclass or dict response
                    if hasattr(result, 'valid'):
                        # ValidationResult dataclass - use attribute access
                        if not result.valid:
                            validation_results["valid"] = False
                            validation_results["errors"].extend(result.errors or [])
                        
                        validation_results["warnings"].extend(result.warnings or [])
                    else:
                        # Legacy dict response - use dictionary access
                        if not result.get("valid", True):
                            validation_results["valid"] = False
                            validation_results["errors"].extend(result.get("errors", []))
                        
                        validation_results["warnings"].extend(result.get("warnings", []))
                
                except Exception as e:
                    logger.warning(f"⚠️ Validator {validator_name} failed: {e}")
                    validation_results["warnings"].append(f"Validator {validator_name} failed: {str(e)}")
        
        return validation_results
    
    async def _get_agent_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_input: Dict[str, Any]
    ) -> AgentDecision:
        """Get agent decision for phase execution"""
        try:
            # Get flow state for agent context
            flow_state = await self._get_flow_state(master_flow.flow_id)
            
            # Create agent context
            agent_context = {
                "flow_id": master_flow.flow_id,
                "flow_type": master_flow.flow_type,
                "current_phase": phase_name,
                "phase_input": phase_input,
                "flow_state": flow_state,
                "flow_history": master_flow.flow_persistence_data or {}
            }
            
            # Get decision from phase transition agent
            decision = await self.phase_transition_agent.get_decision(agent_context)
            
            return decision
            
        except Exception as e:
            logger.warning(f"⚠️ Agent decision failed for phase {phase_name}: {e}")
            # Return default decision on agent failure
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=self._get_default_next_phase(phase_name),
                confidence=0.0,
                reasoning=f"Agent decision failed, proceeding with default: {str(e)}",
                metadata={}
            )
    
    async def _log_agent_decision(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ):
        """Log agent decision for audit purposes"""
        try:
            decision_log = {
                "flow_id": flow_id,
                "phase": phase_name,
                "action": decision.action.value,
                "next_phase": decision.next_phase,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "metadata": decision.metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in flow phase data
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="running",  # Keep current status
                phase_data={
                    "agent_decisions": [decision_log]
                }
            )
            
            logger.info(f"🤖 Agent Decision for {phase_name}: {decision.action.value} -> {decision.next_phase} (confidence: {decision.confidence:.2f})")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to log agent decision: {e}")
    
    async def _handle_agent_pause(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ) -> Dict[str, Any]:
        """Handle agent pause decision"""
        logger.info(f"⏸️ Agent requested pause for phase {phase_name}: {decision.reasoning}")
        
        # Update flow status to paused
        await self.master_repo.update_flow_status(
            flow_id=flow_id,
            status="paused",
            phase_data={
                "paused_phase": phase_name,
                "pause_reason": decision.reasoning,
                "agent_decision": decision.metadata
            }
        )
        
        return {
            "phase": phase_name,
            "status": "paused",
            "reason": decision.reasoning,
            "next_phase": decision.next_phase,
            "agent_action": decision.action.value
        }
    
    async def _skip_to_next_phase(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ) -> Dict[str, Any]:
        """Handle agent skip decision"""
        logger.info(f"⏭️ Agent requested skip for phase {phase_name}: {decision.reasoning}")
        
        # Update flow to mark phase as skipped
        await self.master_repo.update_flow_status(
            flow_id=flow_id,
            status="running",
            phase_data={
                "skipped_phase": phase_name,
                "skip_reason": decision.reasoning,
                "next_phase": decision.next_phase
            }
        )
        
        return {
            "phase": phase_name,
            "status": "skipped",
            "reason": decision.reasoning,
            "next_phase": decision.next_phase,
            "agent_action": decision.action.value
        }
    
    async def _get_flow_state(
        self,
        flow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current flow state for agent context"""
        try:
            # Try to get discovery flow state if this is a discovery flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if master_flow and master_flow.flow_type == "discovery":
                # Import discovery state utilities
                from app.services.crewai_flows.flow_state_bridge import FlowStateBridge
                
                # Create bridge and get state
                bridge = FlowStateBridge(self.context)
                discovery_state = await bridge.recover_flow_state(flow_id)
                
                if discovery_state:
                    # Convert to dict for agent processing
                    return {
                        "flow_id": discovery_state.flow_id,
                        "status": discovery_state.status,
                        "current_phase": discovery_state.current_phase,
                        "completed_phases": discovery_state.completed_phases or [],
                        "raw_data": discovery_state.raw_data or [],
                        "processed_data": discovery_state.processed_data or [],
                        "field_mappings": discovery_state.field_mappings or {},
                        "validation_results": discovery_state.validation_results or {},
                        "assets_created": discovery_state.assets_created or []
                    }
            
            # Fallback to master flow data
            return master_flow.flow_persistence_data if master_flow else {}
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get flow state: {e}")
            return {}
    
    def _get_default_next_phase(self, current_phase: str) -> str:
        """Get default next phase using FlowTypeRegistry"""
        # This would ideally come from flow configuration
        phase_transitions = {
            "initialization": "data_import",
            "data_import": "field_mapping", 
            "field_mapping": "data_cleansing",
            "data_cleansing": "asset_creation",
            "asset_creation": "analysis",
            "analysis": "completed"
        }
        
        return phase_transitions.get(current_phase, "completed")
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """
        Determine if an error is recoverable and phase should be retried
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if error is recoverable, False otherwise
        """
        recoverable_types = [
            "ConnectionError",
            "TimeoutError", 
            "TemporaryFailure",
            "RateLimitError"
        ]
        
        error_name = type(error).__name__
        return error_name in recoverable_types
    
    def _ensure_json_serializable(self, obj: Any) -> Any:
        """
        Ensure object is JSON serializable for database storage
        
        Args:
            obj: Object to make serializable
            
        Returns:
            JSON-serializable version of object
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._ensure_json_serializable(item) for item in obj]
        else:
            # Convert unknown types to string
            return str(obj)
    
    async def _get_post_execution_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_result: Dict[str, Any]
    ) -> AgentDecision:
        """Get agent decision after phase execution"""
        try:
            # Get updated flow state
            flow_state = await self._get_flow_state(master_flow.flow_id)
            
            # Create post-execution context
            agent_context = {
                "flow_id": master_flow.flow_id,
                "flow_type": master_flow.flow_type,
                "completed_phase": phase_name,
                "phase_result": phase_result,
                "flow_state": flow_state,
                "flow_history": master_flow.flow_persistence_data or {}
            }
            
            # Get decision from phase transition agent
            decision = await self.phase_transition_agent.get_post_execution_decision(agent_context)
            
            # Log decision if it differs from default
            if decision.next_phase != self._get_default_next_phase(phase_name):
                logger.info(f"🤖 Post-execution override: {phase_name} -> {decision.next_phase} (reasoning: {decision.reasoning})")
            
            return decision
            
        except Exception as e:
            logger.warning(f"⚠️ Post-execution agent decision failed: {e}")
            # Return default decision
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=self._get_default_next_phase(phase_name),
                confidence=0.0,
                reasoning=f"Post-execution decision failed, using default: {str(e)}",
                metadata={}
            )