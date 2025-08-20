"""
Flow Execution Engine Crew - Main Implementation
Main CrewAI execution engine using modularized flow-specific components.
"""

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)

# Import modularized components
from app.services.flow_orchestration.execution_engine_crew_utils import (
    ExecutionEngineCrewUtils,
)
from app.services.flow_orchestration.execution_engine_crew_discovery import (
    ExecutionEngineDiscoveryCrews,
)
from app.services.flow_orchestration.execution_engine_crew_assessment import (
    ExecutionEngineAssessmentCrews,
)
from app.services.flow_orchestration.execution_engine_crew_collection import (
    ExecutionEngineCollectionCrews,
)

logger = get_logger(__name__)


class FlowExecutionCrew:
    """
    CrewAI-based flow execution engine with modular flow type handlers.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
    ):
        """Initialize the FlowExecutionCrew"""
        self.db = db
        self.context = context
        self.master_repo = master_repo

        # Initialize modular components
        self.crew_utils = ExecutionEngineCrewUtils()
        self.discovery_crews = ExecutionEngineDiscoveryCrews(self.crew_utils)
        self.assessment_crews = ExecutionEngineAssessmentCrews(self.crew_utils)
        self.collection_crews = ExecutionEngineCollectionCrews(self.crew_utils)

        # ServiceRegistry for shared state
        self.service_registry = None

    async def _ensure_service_registry(self):
        """Ensure ServiceRegistry is available for shared state management"""
        if self.service_registry is None:
            try:
                from app.services.service_registry import ServiceRegistry

                self.service_registry = await ServiceRegistry.get_instance()
                logger.info("🔧 ServiceRegistry initialized for crew execution")
            except ImportError as e:
                logger.warning(f"⚠️ ServiceRegistry not available: {e}")
                # Continue without ServiceRegistry - graceful degradation

    async def execute_crew_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a phase through CrewAI by delegating to the actual flow implementation"""
        logger.info(
            f"🔄 Executing CrewAI phase: {phase_config.name} for flow type: {master_flow.flow_type}"
        )

        try:
            # Ensure ServiceRegistry is available
            await self._ensure_service_registry()

            # Delegate based on flow type
            if master_flow.flow_type == "discovery":
                return await self.discovery_crews.execute_discovery_phase(
                    master_flow, phase_config, phase_input
                )
            elif master_flow.flow_type == "assessment":
                return await self.assessment_crews.execute_assessment_phase(
                    master_flow, phase_config, phase_input
                )
            elif master_flow.flow_type == "collection":
                return await self.collection_crews.execute_collection_phase(
                    master_flow, phase_config, phase_input
                )
            else:
                # For other flow types, use placeholder until services are implemented
                logger.warning(
                    f"⚠️ Flow type '{master_flow.flow_type}' delegation not yet implemented"
                )

                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": {
                        "message": f"{master_flow.flow_type} flow delegation pending implementation",
                        "flow_type": master_flow.flow_type,
                        "phase": phase_config.name,
                        "phase_input": phase_input,
                    },
                    "warning": f"{master_flow.flow_type} flow service not yet implemented",
                }

        except Exception as e:
            logger.error(f"❌ Failed to execute crew phase: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return error result but don't raise - let the orchestrator handle it
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "error_during_delegation",
            }

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.service_registry:
                # Perform any necessary cleanup
                logger.info("🧹 Cleaning up crew execution resources")
        except Exception as e:
            logger.warning(f"⚠️ Error during crew cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()


# For backward compatibility, alias to the original class name
FlowCrewExecutor = FlowExecutionCrew
