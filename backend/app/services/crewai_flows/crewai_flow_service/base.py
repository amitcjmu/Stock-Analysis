"""
Base CrewAI Flow Service module.

This module contains the core service class initialization, constants,
and basic configuration for the CrewAI Flow Service.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.discovery_flow_service import DiscoveryFlowService

# CrewAI Flow Integration (Conditional)
if TYPE_CHECKING:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
else:
    try:
        from app.services.crewai_flows.unified_discovery_flow import (
            UnifiedDiscoveryFlow,
        )

        CREWAI_FLOWS_AVAILABLE = True
    except ImportError:
        CREWAI_FLOWS_AVAILABLE = False
        UnifiedDiscoveryFlow = None

logger = logging.getLogger(__name__)


class CrewAIFlowServiceBase:
    """
    Base class for CrewAI Flow Service - V2 Discovery Flow Integration.

    This service bridges CrewAI flows with the V2 Discovery Flow architecture.
    Uses flow_id as single source of truth instead of session_id.

    Key Features:
    - Uses flow_id instead of session_id
    - Integrates with V2 Discovery Flow models
    - Provides graceful fallback when CrewAI flows unavailable
    - Multi-tenant isolation through context-aware repositories
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize the CrewAI Flow Service.

        Args:
            db: Optional database session. If not provided, a new session will be created.
        """
        self.db = db
        self._discovery_flow_service: Optional[DiscoveryFlowService] = None
        self._llm = None

    async def _get_discovery_flow_service(
        self, context: Dict[str, Any]
    ) -> DiscoveryFlowService:
        """
        Get or create discovery flow service with context.

        Args:
            context: Request context containing client/engagement info

        Returns:
            Configured DiscoveryFlowService instance
        """
        if not self._discovery_flow_service:
            # Create a new database session if one wasn't provided
            from app.core.database import AsyncSessionLocal

            if not self.db:
                logger.info(
                    "🔍 Creating new database session for V2 Discovery Flow service"
                )
                self.db = AsyncSessionLocal()

            # Create RequestContext from the context dict
            from app.core.context import RequestContext

            request_context = RequestContext(
                client_account_id=context.get("client_account_id"),
                engagement_id=context.get("engagement_id"),
                user_id=context.get("approved_by") or context.get("user_id"),
            )

            self._discovery_flow_service = DiscoveryFlowService(
                self.db, request_context
            )

        return self._discovery_flow_service

    def get_llm(self):
        """
        Get the LLM instance for CrewAI agents.

        Returns:
            LLM instance or mock LLM for fallback
        """
        if not self._llm:
            try:
                from app.services.llm_config import get_crewai_llm

                self._llm = get_crewai_llm()
                logger.info("✅ LLM initialized for CrewAI flows")
            except ImportError as e:
                logger.error(f"❌ Failed to import LLM config: {e}")

                # Return a mock LLM for fallback
                class MockLLM:
                    def __call__(self, prompt):
                        return "LLM not available - using fallback response"

                self._llm = MockLLM()
        return self._llm

    def get_agents(self) -> Dict[str, Any]:
        """
        Get all CrewAI agents for the discovery flow.

        Note: UnifiedDiscoveryFlow uses crews managed by UnifiedFlowCrewManager,
        not individual agents. This method returns None for all agents to match
        the flow_initialization.py pattern.

        Returns:
            Dict with all agent keys set to None (managed by crews)
        """
        logger.info(
            "✅ UnifiedDiscoveryFlow uses crews - returning None for individual agents"
        )

        # Return None for all agents as they are managed by crews
        return {
            "orchestrator": None,  # Not needed - UnifiedFlowCrewManager handles orchestration
            "data_validation_agent": None,  # Replaced by data_import_validation_crew
            "attribute_mapping_agent": None,  # Replaced by field_mapping_crew
            "data_cleansing_agent": None,  # Replaced by data_cleansing_crew
            "asset_inventory_agent": None,  # Replaced by inventory_building_crew
            "dependency_analysis_agent": None,  # Replaced by app_server_dependency_crew
            "tech_debt_analysis_agent": None,  # Replaced by technical_debt_crew
        }

    def add_error(
        self, error_message: str, phase: str = None, details: Dict[str, Any] = None
    ):
        """
        Add error to the flow service for tracking.

        Args:
            error_message: Error message to track
            phase: Optional phase where error occurred
            details: Optional additional error details
        """
        from datetime import datetime

        error_entry = {
            "error": error_message,
            "phase": phase or "unknown",
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

        # Store in internal error list for tracking
        if not hasattr(self, "_errors"):
            self._errors = []
        self._errors.append(error_entry)

        logger.error(f"❌ CrewAI Flow Error in phase {phase}: {error_message}")
        if details:
            logger.error(f"   Details: {details}")


# Factory function for dependency injection
async def get_crewai_flow_service(
    db: AsyncSession = None, context: Dict[str, Any] = None
):
    """
    Factory function to create CrewAI Flow Service with proper dependencies.

    Args:
        db: Optional database session
        context: Optional request context

    Returns:
        CrewAIFlowService instance
    """
    # Import inside function to avoid circular imports
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from .orchestrator import CrewAIFlowService
    else:
        from .orchestrator import CrewAIFlowService

    if not db:
        # Get database session from dependency injection
        async with get_db() as session:
            return CrewAIFlowService(db=session)

    return CrewAIFlowService(db=db)
