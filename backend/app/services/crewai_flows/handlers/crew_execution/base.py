"""
Base class and common utilities for crew execution
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CrewExecutionBase:
    """Base class for all crew execution handlers"""

    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def create_crew_status(
        self,
        status: str,
        manager: str,
        agents: list,
        success_criteria_met: bool = True,
        process_type: str = "hierarchical",
        collaboration_enabled: bool = True,
        additional_fields: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create standardized crew status object"""
        crew_status = {
            "status": status,
            "manager": manager,
            "agents": agents,
            "completion_time": datetime.utcnow().isoformat(),
            "success_criteria_met": success_criteria_met,
            "process_type": process_type,
            "collaboration_enabled": collaboration_enabled,
        }

        if additional_fields:
            crew_status.update(additional_fields)

        return crew_status

    def handle_crew_error(self, error: Exception, crew_name: str):
        """Common error handling for crew execution"""
        logger.error(f"❌ {crew_name} Crew execution failed: {error}")

        # Check if it's a rate limit error
        error_str = str(error).lower()
        if any(
            indicator in error_str
            for indicator in ["429", "rate limit", "too many requests"]
        ):
            logger.warning(f"⚠️ Rate limit detected in {crew_name} Crew")
            return {"is_rate_limit": True, "error": error}

        return {"is_rate_limit": False, "error": error}
