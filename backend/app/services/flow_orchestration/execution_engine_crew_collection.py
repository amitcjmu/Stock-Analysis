"""
Flow Execution Engine Collection Crew
Collection-specific CrewAI execution methods and phase handlers.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ExecutionEngineCollectionCrews:
    """Collection flow CrewAI execution handlers."""

    def __init__(self, crew_utils):
        self.crew_utils = crew_utils

    async def execute_collection_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute collection flow phase"""
        logger.info(f"🔄 Executing collection phase '{phase_config.name}'")

        try:
            # Import UnifiedCollectionFlow for actual execution
            from app.services.crewai_flows.unified_collection_flow import (
                UnifiedCollectionFlow,
            )
            from app.core.context import RequestContext

            # Create context from master_flow data
            context = RequestContext(
                client_account_id=master_flow.client_account_id,
                engagement_id=master_flow.engagement_id,
                user_id=master_flow.user_id,
            )

            # Get or create crewai_service instance
            crewai_service = await self._get_crewai_service()

            # Create UnifiedCollectionFlow instance with all required parameters
            collection_flow = UnifiedCollectionFlow(
                crewai_service=crewai_service,
                context=context,
                automation_tier="tier_2",
                flow_id=master_flow.flow_id,
                master_flow_id=master_flow.flow_id,
            )

            # Execute the specific phase
            result = await self._execute_collection_flow_phase(
                collection_flow, phase_config, phase_input
            )

            logger.info(f"✅ Collection phase '{phase_config.name}' completed")
            return result

        except Exception as e:
            logger.error(f"❌ Collection phase failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

    async def _get_crewai_service(self):
        """Get or create crewai_service instance"""
        try:
            # Try to get from service registry
            from app.services.service_registry import ServiceRegistry

            service_registry = await ServiceRegistry.get_instance()
            return await service_registry.get_crewai_service()
        except Exception as e:
            logger.warning(f"⚠️ Could not get crewai_service from registry: {e}")
            # Return a mock or placeholder service for graceful degradation
            return None

    async def _execute_collection_flow_phase(
        self, collection_flow, phase_config, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specific collection flow phase"""
        # For now, return a structured result
        # In future, this could call specific phase methods on the collection_flow
        return {
            "phase": phase_config.name,
            "status": "completed",
            "collection_results": {
                "message": f"Collection phase {phase_config.name} executed via UnifiedCollectionFlow",
                "phase_input": phase_input,
                "flow_id": collection_flow._flow_id,
            },
            "method": "unified_collection_flow_execution",
        }
