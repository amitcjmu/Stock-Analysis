"""
Agent Manager for CrewAI crews and flows.
Manages specialized AI crews for CMDB analysis and migration planning using CrewAI Flow architecture.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Check for required environment variables early
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
CREWAI_ENABLED = os.getenv("CREWAI_ENABLED", "true").lower() == "true"

# Determine if full CrewAI functionality is available
CREWAI_AVAILABLE = bool(DEEPINFRA_API_KEY and CREWAI_ENABLED)

if not CREWAI_AVAILABLE:
    logging.warning("CrewAI not available. Using fallback mode.")

try:
    from app.services.crewai_flows.app_server_dependency_crew import (
        create_app_server_dependency_crew,
    )
    from app.services.crewai_flows.crews.field_mapping_crew import (
        create_field_mapping_crew,
    )
    from app.services.crewai_flows.crews.inventory_building_crew import (
        create_inventory_building_crew,
    )
    from app.services.crewai_flows.crews.technical_debt_crew import (
        create_technical_debt_crew,
    )
    from app.services.crewai_flows.data_cleansing_crew import create_data_cleansing_crew

    CREWS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI crews not available: {e}")
    CREWS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages all CrewAI crews and flows."""

    def __init__(self, llm=None):
        """Initialize the agent manager with CrewAI crews."""
        self.crews = {}
        self.llm = llm

        if CREWAI_AVAILABLE and CREWS_AVAILABLE and self.llm:
            self._create_crews()
            logger.info(f"Created {len(self.crews)} specialized crews")
        else:
            logger.warning(
                "AgentManager initialized in limited mode (CrewAI crews not available)"
            )

    def reinitialize_with_fresh_llm(self, fresh_llm: Any) -> None:
        """Reinitialize all crews with a fresh LLM instance."""
        if not CREWAI_AVAILABLE or not CREWS_AVAILABLE:
            logger.warning("Cannot reinitialize crews - CrewAI not available")
            return

        logger.info("Reinitializing crews with fresh LLM instance")

        # Clear existing crews
        self.crews.clear()

        # Set new LLM
        self.llm = fresh_llm

        # Recreate crews
        self._create_crews()

        logger.info(f"Successfully reinitialized {len(self.crews)} crews")

    def _create_crews(self):
        """Create all specialized crews with graceful error handling."""
        try:
            crews = {}

            # Inventory Building Crew (replaces individual discovery agents)
            try:
                crews["inventory_building"] = create_inventory_building_crew(
                    llm=self.llm
                )
                logger.info("Created Inventory Building Crew")
            except Exception as e:
                logger.error(f"Failed to create Inventory Building Crew: {e}")

            # Field Mapping Crew (replaces field mapping agents)
            try:
                crews["field_mapping"] = create_field_mapping_crew(llm=self.llm)
                logger.info("Created Field Mapping Crew")
            except Exception as e:
                logger.error(f"Failed to create Field Mapping Crew: {e}")

            # Technical Debt Crew (replaces 6R strategy agents)
            try:
                crews["technical_debt"] = create_technical_debt_crew(llm=self.llm)
                logger.info("Created Technical Debt Crew")
            except Exception as e:
                logger.error(f"Failed to create Technical Debt Crew: {e}")

            # Data Cleansing Crew (replaces data quality agents)
            try:
                crews["data_cleansing"] = create_data_cleansing_crew(llm=self.llm)
                logger.info("Created Data Cleansing Crew")
            except Exception as e:
                logger.error(f"Failed to create Data Cleansing Crew: {e}")

            # App-Server Dependency Crew (replaces dependency analysis agents)
            try:
                crews["app_server_dependency"] = create_app_server_dependency_crew(
                    llm=self.llm
                )
                logger.info("Created App-Server Dependency Crew")
            except Exception as e:
                logger.error(f"Failed to create App-Server Dependency Crew: {e}")

            self.crews = crews

        except Exception as e:
            logger.error(f"Error creating crews: {e}")
            self.crews = {}

    # Legacy compatibility methods (deprecated - use crews instead)
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Legacy method - returns None (use get_crew instead)."""
        logger.warning(
            f"get_agent() is deprecated. Agent '{agent_name}' replaced by crews."
        )
        return None

    def get_crew(self, crew_name: str) -> Optional[Any]:
        """Get a specific crew by name."""
        return self.crews.get(crew_name)

    def list_agents(self) -> Dict[str, str]:
        """Legacy method - returns empty dict (use list_crews instead)."""
        logger.warning("list_agents() is deprecated. Use list_crews() instead.")
        return {}

    def list_crews(self) -> Dict[str, list]:
        """List all available crews and their capabilities."""
        if not self.crews:
            return {}

        crew_info = {}
        for name, crew in self.crews.items():
            if hasattr(crew, "agents"):
                crew_info[name] = [agent.role for agent in crew.agents]
            else:
                crew_info[name] = ["Crew available"]

        return crew_info

    def get_agent_capabilities(self) -> Dict[str, Dict[str, str]]:
        """Get crew capabilities (replaces agent capabilities)."""
        if not CREWAI_AVAILABLE or not self.crews:
            return {}

        capabilities = {}

        # Define crew capabilities
        crew_capabilities = {
            "inventory_building": {
                "role": "Asset Inventory Management",
                "goal": "Analyze and manage enterprise asset inventory",
                "capability": "Asset discovery, classification, and inventory management",
            },
            "field_mapping": {
                "role": "Field Mapping Intelligence",
                "goal": "Intelligent field mapping and data structure analysis",
                "capability": "AI-driven field mapping and data relationship analysis",
            },
            "technical_debt": {
                "role": "6R Migration Strategy",
                "goal": "Analyze assets and recommend optimal migration strategies",
                "capability": "6R strategy analysis and migration planning",
            },
            "data_cleansing": {
                "role": "Data Quality Management",
                "goal": "Assess and improve data quality for migration",
                "capability": "Data quality assessment and cleansing recommendations",
            },
            "app_server_dependency": {
                "role": "Dependency Analysis",
                "goal": "Analyze application and server dependencies",
                "capability": "Dependency mapping and relationship analysis",
            },
        }

        for crew_name in self.crews.keys():
            if crew_name in crew_capabilities:
                capabilities[crew_name] = crew_capabilities[crew_name]

        return capabilities

    def validate_agents(self) -> Dict[str, bool]:
        """Legacy method - returns empty dict (use validate_crews instead)."""
        logger.warning("validate_agents() is deprecated. Use validate_crews() instead.")
        return {}

    def validate_crews(self) -> Dict[str, bool]:
        """Validate that all crews are properly initialized."""
        if not CREWAI_AVAILABLE:
            return {"crewai_available": False}

        validation_results = {}

        for crew_name, crew in self.crews.items():
            try:
                # Basic validation - check if crew has required attributes
                is_valid = (
                    crew is not None
                    and hasattr(crew, "agents")
                    and len(crew.agents) > 0
                )
                validation_results[crew_name] = is_valid
            except Exception as e:
                logger.error(f"Error validating crew {crew_name}: {e}")
                validation_results[crew_name] = False

        return validation_results

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status for crews."""
        crew_validation = self.validate_crews()

        return {
            "crewai_available": CREWAI_AVAILABLE,
            "crews_available": CREWS_AVAILABLE,
            "total_crews": len(self.crews),
            "active_crews": sum(1 for valid in crew_validation.values() if valid),
            "crew_status": crew_validation,
            "llm_configured": self.llm is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }
