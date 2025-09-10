"""
Agent Processing Handler
Handles CrewAI-driven data processing and cleanup operations.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Check CrewAI availability
CREWAI_AVAILABLE = bool(
    os.getenv("DEEPINFRA_API_KEY")
    and os.getenv("CREWAI_ENABLED", "true").lower() == "true"
)

try:
    # Only import what is actually used in this module
    # Note: TenantScopedAgentPool, create_data_cleansing_crew
    # were imported but not used - now handled by persistent agents
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


class AgentProcessingHandler:
    """Handler for CrewAI-driven data processing operations."""

    def __init__(self, llm=None):
        self.llm = llm
        self.crews = {}
        self.service_available = CREWAI_AVAILABLE and AGENTS_AVAILABLE

        if self.service_available:
            self._initialize_agents()

        logger.info(
            f"Agent processing handler initialized (CrewAI: {self.service_available})"
        )

    def _initialize_agents(self):
        """Initialize persistent agents for data processing."""
        try:
            if AGENTS_AVAILABLE:
                # Note: Persistent agents are managed by TenantScopedAgentPool
                # No initialization needed here - agents are created per-tenant on demand
                logger.info("Persistent agents available for data processing")
                self.service_available = True
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            self.service_available = False

    def is_available(self) -> bool:
        """Check if the handler is available."""
        return self.service_available

    async def process_data_cleanup(
        self,
        asset_data: List[Dict[str, Any]],
        agent_operations: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        CrewAI-driven data processing with intelligent cleanup operations.
        """
        try:
            if not self.service_available:
                return await self._fallback_data_processing(
                    asset_data, agent_operations, user_preferences
                )

            # Use Data Cleansing Crew for processing
            if "data_cleansing" in self.crews:
                try:
                    crew_result = self.crews["data_cleansing"].kickoff(
                        {
                            "asset_data": asset_data,
                            "operations": agent_operations,
                            "user_preferences": user_preferences,
                            "task": "data_cleanup_processing",
                            "client_context": {
                                "client_account_id": client_account_id,
                                "engagement_id": engagement_id,
                            },
                        }
                    )

                    if crew_result and isinstance(crew_result, dict):
                        return {
                            "status": "success",
                            "processing_type": "crewai_driven",
                            "cleaned_assets": crew_result.get(
                                "cleaned_assets", asset_data
                            ),
                            "quality_improvement": crew_result.get(
                                "quality_improvement", {}
                            ),
                            "operations_applied": crew_result.get(
                                "operations_applied", []
                            ),
                            "quality_metrics": crew_result.get("quality_metrics", {}),
                            "agent_confidence": crew_result.get("confidence", 0.9),
                            "processing_summary": crew_result.get(
                                "summary", "CrewAI processing completed"
                            ),
                            "ai_analysis_recommended": False,
                        }
                except Exception as e:
                    logger.error(f"Data Cleansing Crew processing failed: {e}")

            # Use Inventory Building Crew as fallback
            if "inventory_building" in self.crews:
                try:
                    crew_result = self.crews["inventory_building"].kickoff(
                        {
                            "asset_data": asset_data,
                            "operations": agent_operations,
                            "task": "data_processing",
                            "client_context": {
                                "client_account_id": client_account_id,
                                "engagement_id": engagement_id,
                            },
                        }
                    )

                    if crew_result and isinstance(crew_result, dict):
                        return {
                            "status": "success",
                            "processing_type": "crewai_inventory_driven",
                            "cleaned_assets": crew_result.get(
                                "processed_assets", asset_data
                            ),
                            "quality_improvement": crew_result.get(
                                "quality_improvement", {}
                            ),
                            "operations_applied": crew_result.get(
                                "operations_applied", []
                            ),
                            "quality_metrics": crew_result.get("quality_metrics", {}),
                            "agent_confidence": crew_result.get("confidence", 0.85),
                            "processing_summary": crew_result.get(
                                "summary", "CrewAI inventory processing completed"
                            ),
                            "ai_analysis_recommended": False,
                        }
                except Exception as e:
                    logger.error(f"Inventory Building Crew processing failed: {e}")

            # Fallback to rule-based processing
            return await self._fallback_data_processing(
                asset_data, agent_operations, user_preferences
            )

        except Exception as e:
            logger.error(f"Error in CrewAI process_data_cleanup: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_type": "error",
                "ai_analysis_recommended": True,
            }

    async def _fallback_data_processing(
        self,
        asset_data: List[Dict[str, Any]],
        agent_operations: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback processing when CrewAI is not available."""
        logger.info("Using fallback processing - CrewAI crews not available")

        return {
            "status": "success",
            "processing_type": "fallback",
            "cleaned_assets": asset_data,  # Return original data
            "quality_improvement": {"processed_count": len(asset_data)},
            "operations_applied": ["fallback_processing"],
            "quality_metrics": {"improvement_score": 0},
            "agent_confidence": 0.5,
            "processing_summary": f"Fallback processing for {len(asset_data)} assets",
            "ai_analysis_recommended": True,
            "recommended_crew": "Data Cleansing Crew",
            "message": "Enable CrewAI for intelligent data processing",
        }

    async def process_agent_driven_cleanup(
        self,
        asset_data: List[Dict[str, Any]],
        agent_operations: List[Dict[str, Any]],
        user_preferences: Dict[str, Any] = None,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process CrewAI-driven cleanup operations on asset data."""
        if user_preferences is None:
            user_preferences = {}

        # Use the main processing method
        return await self.process_data_cleanup(
            asset_data,
            agent_operations,
            user_preferences,
            client_account_id,
            engagement_id,
        )
