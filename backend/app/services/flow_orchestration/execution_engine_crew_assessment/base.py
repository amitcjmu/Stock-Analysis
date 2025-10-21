"""
Flow Execution Engine Assessment Crew - Base Class

Core execution engine with agent pool management.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled (memory=False).
"""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

from .readiness_executor import ReadinessExecutorMixin
from .complexity_executor import ComplexityExecutorMixin
from .dependency_executor import DependencyExecutorMixin
from .tech_debt_executor import TechDebtExecutorMixin
from .risk_executor import RiskExecutorMixin
from .recommendation_executor import RecommendationExecutorMixin

logger = get_logger(__name__)


class ExecutionEngineAssessmentCrews(
    ReadinessExecutorMixin,
    ComplexityExecutorMixin,
    DependencyExecutorMixin,
    TechDebtExecutorMixin,
    RiskExecutorMixin,
    RecommendationExecutorMixin,
):
    """
    Assessment flow CrewAI execution handlers using persistent agents.

    Per ADR-015: Uses TenantScopedAgentPool for singleton agents per tenant.
    Per ADR-024: CrewAI memory is DISABLED (memory=False), use TenantMemoryManager.
    """

    def __init__(self, crew_utils):
        self.crew_utils = crew_utils
        self._agent_pool = None  # Lazy initialization per tenant

    async def _initialize_assessment_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Any:
        """
        Initialize persistent agent pool for assessment tasks.

        Per ADR-015: TenantScopedAgentPool pattern for singleton agents.
        Per ADR-024: CrewAI memory disabled, use TenantMemoryManager.

        Args:
            master_flow: Master flow state with tenant identifiers

        Returns:
            TenantScopedAgentPool class for agent access

        Raises:
            ValueError: If required identifiers are missing
            RuntimeError: If pool initialization fails
        """
        try:
            # Import here to avoid circular dependencies
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            # Validate required identifiers before pool init
            client_id = master_flow.client_account_id
            engagement_id = master_flow.engagement_id

            # Ensure identifiers are non-empty strings
            if not client_id or not engagement_id:
                logger.error(
                    "Missing required identifiers for agent pool initialization"
                )
                raise ValueError(
                    "client_id and engagement_id are required for agent pool initialization"
                )

            # Convert to safe string representations
            safe_client = str(client_id)
            safe_eng = str(engagement_id)

            # Initialize the tenant pool (returns None but sets up the pool)
            try:
                await TenantScopedAgentPool.initialize_tenant_pool(
                    client_id=safe_client,
                    engagement_id=safe_eng,
                )
            except Exception as e:
                msg = "Failed to initialize TenantScopedAgentPool for assessment flow"
                logger.exception("%s", msg)
                raise RuntimeError(msg) from e

            logger.info(
                "Initialized agent pool for assessment flow - client_id=%s engagement_id=%s",
                str(client_id),
                str(engagement_id),
            )

            # Return the TenantScopedAgentPool class itself for agent access
            return TenantScopedAgentPool

        except Exception as e:
            logger.error(f"Failed to initialize assessment agent pool: {e}")
            raise

    async def get_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Optional[Any]:
        """
        Get or initialize agent pool (lazy loading pattern).

        Args:
            master_flow: Master flow state with tenant identifiers

        Returns:
            TenantScopedAgentPool class or None if initialization fails
        """
        if self._agent_pool is None:
            self._agent_pool = await self._initialize_assessment_agent_pool(master_flow)
        return self._agent_pool

    async def _get_agent_for_phase(
        self, phase_name: str, agent_pool: Any, master_flow: CrewAIFlowStateExtensions
    ) -> Any:
        """
        Get the appropriate agent for the phase from pool.

        Per ADR-015: Uses TenantScopedAgentPool for persistent agents.
        Per ADR-024: CrewAI memory disabled, use TenantMemoryManager.

        Args:
            phase_name: Name of the assessment phase
            agent_pool: TenantScopedAgentPool class
            master_flow: Master flow state with tenant identifiers

        Returns:
            Agent instance from pool

        Raises:
            ValueError: If no agent configured for phase
            RuntimeError: If agent retrieval fails
        """
        from app.services.persistent_agents.agent_pool_constants import (
            ASSESSMENT_PHASE_AGENT_MAPPING,
        )

        # Get agent type from mapping
        agent_type = ASSESSMENT_PHASE_AGENT_MAPPING.get(phase_name)
        if not agent_type:
            raise ValueError(f"No agent configured for phase: {phase_name}")

        # Build context for agent retrieval
        context = {
            "client_account_id": str(master_flow.client_account_id),
            "engagement_id": str(master_flow.engagement_id),
            "flow_id": str(master_flow.flow_id),
        }

        # Get persistent agent from pool
        try:
            agent = await agent_pool.get_agent(
                context=context,
                agent_type=agent_type,
                force_recreate=False,  # Use cached agent
            )

            logger.info(f"✅ Retrieved agent '{agent_type}' for phase '{phase_name}'")
            return agent

        except Exception as e:
            logger.error(f"Failed to get agent for phase {phase_name}: {e}")
            raise

    async def execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute assessment flow phase using persistent agents and persist results.

        Per ADR-015: Uses TenantScopedAgentPool for persistent agents.
        Per ADR-024: CrewAI memory disabled, use TenantMemoryManager.

        Args:
            master_flow: Master flow state
            phase_config: Phase configuration from flow config
            phase_input: Input data for the phase

        Returns:
            Dictionary with execution results and metadata
        """
        logger.info(
            f"🔄 Executing assessment phase '{phase_config.name}' with persistent agents"
        )

        try:
            # Initialize persistent agent pool for this tenant
            agent_pool = await self.get_agent_pool(master_flow)

            # Create data repository and input builders ONCE (per Qodo Bot optimization)
            from app.repositories.assessment_data_repository import (
                AssessmentDataRepository,
            )
            from app.services.flow_orchestration.assessment_input_builders import (
                AssessmentInputBuilders,
            )

            data_repo = AssessmentDataRepository(
                self.crew_utils.db,
                master_flow.client_account_id,
                master_flow.engagement_id,
            )
            input_builders = AssessmentInputBuilders(data_repo)

            # Map phase names to execution methods
            mapped_phase = self._map_assessment_phase_name(phase_config.name)

            # Execute the phase with persistent agents, passing shared instances
            result = await self._execute_assessment_mapped_phase(
                mapped_phase,
                agent_pool,
                master_flow,
                phase_input,
                data_repo,
                input_builders,
            )

            # Save results to database
            from app.repositories.assessment_flow_repository.commands.flow_commands.phase_results import (
                PhaseResultsPersistence,
            )

            persistence = PhaseResultsPersistence(
                self.crew_utils.db,
                master_flow.client_account_id,
                master_flow.engagement_id,
            )

            await persistence.save_phase_results(
                str(master_flow.flow_id), phase_config.name, result
            )

            # Add metadata about persistent agent usage and result persistence
            result["agent_pool_info"] = {
                "agent_pool_type": "TenantScopedAgentPool" if agent_pool else "none",
                "client_account_id": str(master_flow.client_account_id),
                "engagement_id": str(master_flow.engagement_id),
                "memory_strategy": "TenantMemoryManager",  # Per ADR-024
                "results_persisted": True,
            }

            logger.info(
                f"✅ Assessment phase '{phase_config.name}' completed with persistent agents"
            )
            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Assessment phase failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

    def _map_assessment_phase_name(self, phase_name: str) -> str:
        """
        Map assessment flow phase names to execution methods.

        Args:
            phase_name: Original phase name from config

        Returns:
            Mapped phase name for execution routing
        """
        phase_mapping = {
            "readiness_assessment": "readiness_assessment",
            "complexity_analysis": "complexity_analysis",
            "dependency_analysis": "dependency_analysis",
            "tech_debt_assessment": "tech_debt_assessment",
            "risk_assessment": "risk_assessment",
            "recommendation_generation": "recommendation_generation",
        }
        return phase_mapping.get(phase_name, phase_name)

    async def _execute_assessment_mapped_phase(
        self,
        mapped_phase: str,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute mapped assessment phase with appropriate agents.

        Args:
            mapped_phase: Mapped phase name
            agent_pool: TenantScopedAgentPool class
            master_flow: Master flow state
            phase_input: Phase input data
            data_repo: Shared AssessmentDataRepository instance
            input_builders: Shared AssessmentInputBuilders instance

        Returns:
            Phase execution results
        """
        phase_methods = {
            "readiness_assessment": self._execute_readiness_assessment,
            "complexity_analysis": self._execute_complexity_analysis,
            "dependency_analysis": self._execute_dependency_analysis,
            "tech_debt_assessment": self._execute_tech_debt_assessment,
            "risk_assessment": self._execute_risk_assessment,
            "recommendation_generation": self._execute_recommendation_generation,
        }

        method = phase_methods.get(mapped_phase, self._execute_generic_assessment_phase)
        return await method(
            agent_pool, master_flow, phase_input, data_repo, input_builders
        )

    async def _execute_generic_assessment_phase(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """Generic assessment phase execution for unmapped phases"""
        logger.info("Executing generic assessment phase with persistent agents")

        return {
            "phase": "generic",
            "status": "completed",
            "agent_pool_available": agent_pool is not None,
            "agent_pool_type": agent_pool.__name__ if agent_pool else "none",
            "message": "Generic phase executed with persistent agent pool",
        }
