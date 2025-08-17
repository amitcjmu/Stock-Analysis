"""
Flow orchestration module for CrewAI Flow Service.

This module contains the main CrewAI Flow Service class that orchestrates
flow operations and combines all the modularized functionality.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base import CrewAIFlowServiceBase
from .execution import FlowExecutionMixin
from .state_manager import FlowStateManagerMixin
from .task_manager import FlowTaskManagerMixin
from .validators import FlowValidationMixin

logger = logging.getLogger(__name__)


class CrewAIFlowService(
    CrewAIFlowServiceBase,
    FlowStateManagerMixin,
    FlowTaskManagerMixin,
    FlowExecutionMixin,
    FlowValidationMixin,
):
    """
    Main CrewAI Flow Service class - V2 Discovery Flow Integration.

    This service bridges CrewAI flows with the V2 Discovery Flow architecture
    by combining all modularized functionality through multiple inheritance.

    Key Features:
    - Flow initialization and lifecycle management
    - State management and persistence
    - Task execution and resumption
    - Data validation and processing
    - Multi-tenant isolation
    - Graceful fallback when CrewAI unavailable

    The service is composed of the following mixins:
    - CrewAIFlowServiceBase: Core initialization and utilities
    - FlowStateManagerMixin: State transitions and persistence
    - FlowTaskManagerMixin: Task lifecycle and resumption
    - FlowExecutionMixin: Flow execution engine
    - FlowValidationMixin: Input/output validation
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize the CrewAI Flow Service with all mixins.

        Args:
            db: Optional database session. If not provided, a new session will be created.
        """
        # Initialize the base class
        super().__init__(db=db)

        logger.info("✅ CrewAI Flow Service initialized with all modules")

    async def initialize_flow(
        self,
        flow_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a new CrewAI flow using V2 Discovery Flow architecture.

        Args:
            flow_id: Discovery Flow ID (replaces session_id)
            context: Request context with client/engagement info
            metadata: Optional flow metadata

        Returns:
            Dict containing initialization results
        """
        try:
            logger.info(f"🚀 Initializing CrewAI flow: {flow_id}")

            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)

            # Check if flow already exists
            existing_flow = await discovery_service.get_flow_by_id(flow_id)
            if existing_flow:
                logger.info(f"✅ Flow already exists: {flow_id}")
                return {
                    "status": "existing",
                    "flow_id": flow_id,
                    "current_phase": existing_flow.current_phase,
                    "progress": existing_flow.progress_percentage,
                }

            # Note: CrewAI flow initialization is now handled by MasterFlowOrchestrator
            # This service should not create flows directly
            logger.info(
                f"✅ Flow initialization delegated to MasterFlowOrchestrator: {flow_id}"
            )

            # Create flow through discovery service
            result = await discovery_service.create_flow(
                data_import_id=metadata.get("data_import_id") if metadata else None,
                initial_phase="data_import",
                metadata=metadata or {},
            )

            logger.info(f"✅ Flow initialization complete: {flow_id}")

            from .base import CREWAI_FLOWS_AVAILABLE

            return {
                "status": "initialized",
                "flow_id": flow_id,
                "crewai_available": CREWAI_FLOWS_AVAILABLE,
                "result": {
                    "flow_id": result.flow_id,
                    "status": result.status,
                    "current_phase": result.current_phase,
                },
            }

        except Exception as e:
            logger.error(f"❌ Failed to initialize flow {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Flow initialization failed",
            }
