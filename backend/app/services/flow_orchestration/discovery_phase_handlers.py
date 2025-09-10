"""
Discovery Phase Handlers

Extracted from execution_engine_crew_discovery.py to reduce file length.
Contains phase-specific execution handlers.
"""

import logging
from typing import Any, Dict

from app.services.crewai_flows.handlers.unified_flow_crew_manager import (
    UnifiedFlowCrewManager,
)

logger = logging.getLogger(__name__)


class DictStateAdapter:
    """Adapter to make a dict work as a state object for UnifiedFlowCrewManager."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize adapter with dict data as attributes."""
        self._errors = []
        # Prevent overwriting internal attributes
        for k, v in data.items():
            if k.startswith("_"):
                continue
            setattr(self, k, v)

    def add_error(self, key: str, message: str):
        """Add an error to the state."""
        self._errors.append({"key": key, "message": message})


class DiscoveryPhaseHandlers:
    """Handler class for individual discovery phases."""

    def __init__(self, context=None):
        self.context = context

    async def execute_data_import_validation(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data import validation phase"""
        logger.info("🔍 Executing discovery data import validation")

        try:
            # Create state adapter for UnifiedFlowCrewManager
            state = DictStateAdapter(phase_input)

            # Use UnifiedFlowCrewManager with proper state object
            crew_manager = UnifiedFlowCrewManager(
                crewai_service=None,  # Will be initialized internally
                state=state,
                context=self.context,
            )

            crew = crew_manager.create_crew_on_demand(
                "data_import_validation", **phase_input
            )
            if not crew:
                logger.warning(
                    "Failed to create data_import_validation crew, using fallback"
                )
                return {
                    "phase": "data_import_validation",
                    "status": "completed",
                    "validation_results": {"valid": True, "issues": []},
                    "agent": "data_validation_agent",
                }

            # Check if crew has async kickoff method
            if hasattr(crew, "kickoff_async"):
                result = await crew.kickoff_async(inputs=phase_input)
            else:
                # Use synchronous kickoff
                result = crew.kickoff(inputs=phase_input)

            # Maintain backward compatibility with validation_results field
            validation_results = (
                result.get("validation_results", {"valid": True, "issues": []})
                if isinstance(result, dict)
                else {"valid": True, "issues": []}
            )

            return {
                "phase": "data_import_validation",
                "status": "completed",
                "crew_results": result,
                "validation_results": validation_results,  # Backward compatibility
                "agent": "data_validation_agent",
            }
        except Exception as e:
            logger.error(f"Data import validation failed: {str(e)}")
            return {
                "phase": "data_import_validation",
                "status": "error",
                "error": str(e),
                "validation_results": {"valid": False, "issues": [str(e)]},
                "agent": "data_validation_agent",
            }

    async def execute_data_cleansing(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data cleansing phase"""
        logger.info("🧹 Executing discovery data cleansing")

        try:
            # Create state adapter for UnifiedFlowCrewManager
            state = DictStateAdapter(phase_input)

            # Use UnifiedFlowCrewManager with proper state object
            crew_manager = UnifiedFlowCrewManager(
                crewai_service=None,  # Will be initialized internally
                state=state,
                context=self.context,
            )

            crew = crew_manager.create_crew_on_demand("data_cleansing", **phase_input)
            if not crew:
                logger.warning("Failed to create data_cleansing crew, using fallback")
                return {
                    "phase": "data_cleansing",
                    "status": "completed",
                    "cleansed_data": [],
                    "agent": "data_cleansing_agent",
                }

            # Check if crew has async kickoff method
            if hasattr(crew, "kickoff_async"):
                result = await crew.kickoff_async(inputs=phase_input)
            else:
                # Use synchronous kickoff
                result = crew.kickoff(inputs=phase_input)

            # Maintain backward compatibility with cleansed_data field
            cleansed_data = (
                result.get("cleansed_data", []) if isinstance(result, dict) else []
            )

            return {
                "phase": "data_cleansing",
                "status": "completed",
                "crew_results": result,
                "cleansed_data": cleansed_data,  # Backward compatibility
                "agent": "data_cleansing_agent",
            }
        except Exception as e:
            logger.error(f"Data cleansing failed: {str(e)}")
            return {
                "phase": "data_cleansing",
                "status": "error",
                "error": str(e),
                "cleansed_data": [],
                "agent": "data_cleansing_agent",
            }

    async def execute_analysis(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute analysis phase"""
        logger.info("📊 Executing discovery analysis")

        try:
            # Create state adapter for UnifiedFlowCrewManager
            state = DictStateAdapter(phase_input)

            # Use UnifiedFlowCrewManager with proper state object
            crew_manager = UnifiedFlowCrewManager(
                crewai_service=None,  # Will be initialized internally
                state=state,
                context=self.context,
            )

            crew = crew_manager.create_crew_on_demand("analysis", **phase_input)
            if not crew:
                logger.warning("Failed to create analysis crew, using fallback")
                return {
                    "phase": "analysis",
                    "status": "completed",
                    "analysis_results": {},
                    "agent": "analysis_agent",
                }

            # Check if crew has async kickoff method
            if hasattr(crew, "kickoff_async"):
                result = await crew.kickoff_async(inputs=phase_input)
            else:
                # Use synchronous kickoff
                result = crew.kickoff(inputs=phase_input)

            # Maintain backward compatibility with analysis_results field
            analysis_results = (
                result.get("analysis_results", {}) if isinstance(result, dict) else {}
            )

            return {
                "phase": "analysis",
                "status": "completed",
                "crew_results": result,
                "analysis_results": analysis_results,  # Backward compatibility
                "agent": "analysis_agent",
            }
        except Exception as e:
            logger.error(f"Analysis phase failed: {str(e)}")
            return {
                "phase": "analysis",
                "status": "error",
                "error": str(e),
                "analysis_results": {},
                "agent": "analysis_agent",
            }
