"""
Flow Execution Engine - Modularized Version

Main orchestrator that delegates to specialized execution modules.
This modularized version splits the monolithic execution engine into:
- Core execution logic (execution_engine_core.py)
- CrewAI flow handling (execution_engine_crew.py) 
- Flow initialization (execution_engine_initialization.py)
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.crewai_flows.agents.decision import (
    AgentDecision,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry

# Import modular components
from .execution_engine_core import FlowExecutionCore
from .execution_engine_crew import FlowCrewExecutor
from .execution_engine_initialization import FlowInitializer

logger = get_logger(__name__)


class FlowExecutionEngine:
    """
    Main Flow Execution Engine that orchestrates flow phases and delegates to specialized modules.
    
    This modularized version maintains the same interface while organizing complex logic
    into focused, maintainable modules:
    - FlowExecutionCore: Core phase execution and orchestration
    - FlowCrewExecutor: CrewAI-specific execution logic
    - FlowInitializer: Flow initialization for different types
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry,
                 handler_registry: HandlerRegistry,
                 validator_registry: ValidatorRegistry):
        """
        Initialize the Flow Execution Engine
        
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
        
        # Initialize modular components
        self._core_executor = FlowExecutionCore(
            db, context, master_repo, flow_registry, handler_registry, validator_registry
        )
        
        self._crew_executor = FlowCrewExecutor(
            db, context, master_repo, flow_registry, handler_registry, validator_registry
        )
        
        self._initializer = FlowInitializer(
            db, context, master_repo, flow_registry, handler_registry, validator_registry
        )
        
        logger.info(f"✅ Flow Execution Engine initialized with modular components for client {context.client_account_id}")
    
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
        # Delegate to core executor
        return await self._core_executor.execute_phase(
            flow_id, phase_name, phase_input, validation_overrides
        )
    
    async def initialize_flow_execution(
        self,
        flow_id: str,
        flow_type: str,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize flow execution for specific flow types
        
        Args:
            flow_id: Flow identifier
            flow_type: Type of flow to initialize
            configuration: Flow configuration
            initial_state: Initial state data
            
        Returns:
            Initialization result
        """
        # Delegate to initializer
        return await self._initializer.initialize_flow_execution(
            flow_id, flow_type, configuration, initial_state
        )
    
    # Expose core executor properties and methods for backward compatibility
    @property
    def phase_transition_agent(self):
        """Access to phase transition agent"""
        return self._core_executor.phase_transition_agent
    
    @property
    def field_mapping_agent(self):
        """Access to field mapping agent"""
        return self._core_executor.field_mapping_agent
    
    def _get_default_next_phase(self, current_phase: str) -> str:
        """Get default next phase - delegate to core executor"""
        return self._core_executor._get_default_next_phase(current_phase)
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """Check if error is recoverable - delegate to core executor"""
        return self._core_executor._is_recoverable_error(error)
    
    def _ensure_json_serializable(self, obj: Any) -> Any:
        """Ensure JSON serializable - delegate to core executor"""
        return self._core_executor._ensure_json_serializable(obj)
    
    # Legacy method aliases for backward compatibility
    async def _run_phase_validators(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_data: Dict[str, Any],
        validation_type: str
    ) -> Dict[str, Any]:
        """Run phase validators - delegate to core executor"""
        return await self._core_executor._run_phase_validators(
            master_flow, phase_config, phase_data, validation_type
        )
    
    async def _execute_crew_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute crew phase - delegate to crew executor"""
        return await self._crew_executor.execute_crew_phase(
            master_flow, phase_config, phase_input
        )
    
    async def _execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute discovery phase - delegate to crew executor"""
        return await self._crew_executor._execute_discovery_phase(
            master_flow, phase_config, phase_input
        )
    
    async def _execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute assessment phase - delegate to crew executor"""
        return await self._crew_executor._execute_assessment_phase(
            master_flow, phase_config, phase_input
        )
    
    async def _initialize_discovery_flow(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize discovery flow - delegate to initializer"""
        return await self._initializer._initialize_discovery_flow(flow_id, initial_state)
    
    async def _initialize_assessment_flow(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize assessment flow - delegate to initializer"""
        return await self._initializer._initialize_assessment_flow(flow_id, initial_state)
    
    async def _get_agent_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_input: Dict[str, Any]
    ) -> AgentDecision:
        """Get agent decision - delegate to core executor"""
        return await self._core_executor._get_agent_decision(
            master_flow, phase_name, phase_input
        )
    
    async def _log_agent_decision(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ):
        """Log agent decision - delegate to core executor"""
        return await self._core_executor._log_agent_decision(
            flow_id, phase_name, decision
        )
    
    async def _handle_agent_pause(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ) -> Dict[str, Any]:
        """Handle agent pause - delegate to core executor"""
        return await self._core_executor._handle_agent_pause(
            flow_id, phase_name, decision
        )
    
    async def _skip_to_next_phase(
        self,
        flow_id: str,
        phase_name: str,
        decision: AgentDecision
    ) -> Dict[str, Any]:
        """Skip to next phase - delegate to core executor"""
        return await self._core_executor._skip_to_next_phase(
            flow_id, phase_name, decision
        )
    
    async def _get_flow_state(
        self,
        flow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get flow state - delegate to core executor"""
        return await self._core_executor._get_flow_state(flow_id)
    
    async def _get_post_execution_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_result: Dict[str, Any]
    ) -> AgentDecision:
        """Get post-execution decision - delegate to core executor"""
        return await self._core_executor._get_post_execution_decision(
            master_flow, phase_name, phase_result
        )