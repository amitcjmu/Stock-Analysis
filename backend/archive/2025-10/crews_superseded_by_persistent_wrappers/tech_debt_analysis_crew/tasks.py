"""
Tech Debt Analysis Tasks - Crew Creation Logic

This module contains the crew creation logic for tech debt analysis.
The crew uses a debate-driven consensus building pattern where agents
dynamically create tasks based on the assets being analyzed.

Unlike other crews with predefined tasks, this crew creates tasks dynamically
during execution based on the specific assets and context provided.
"""

import logging
from typing import TYPE_CHECKING, List

from app.services.crewai_flows.config.crew_factory import create_crew

if TYPE_CHECKING:
    from crewai import Agent, Crew

logger = logging.getLogger(__name__)


def create_tech_debt_analysis_crew_instance(agents: List["Agent"]) -> "Crew":
    """
    Create tech debt analysis crew instance with debate-driven consensus pattern.

    This function creates a crew that uses sequential processing for debate-driven
    consensus building. Tasks are created dynamically during execution based on
    the specific assets being analyzed.

    Args:
        agents: List of three agents [legacy_expert, migration_strategist, risk_specialist]

    Returns:
        Configured Crew instance
    """
    if not agents or len(agents) < 3:
        logger.error(
            f"Expected 3 agents for tech debt analysis, got {len(agents) if agents else 0}"
        )
        raise ValueError(
            "Tech debt analysis crew requires exactly 3 agents: "
            "legacy_modernization_expert, cloud_migration_strategist, risk_assessment_specialist"
        )

    logger.info("Creating Tech Debt Analysis crew with debate-driven consensus pattern")

    # Create crew with sequential processing for debate-driven consensus
    # Tasks will be created dynamically during execution
    crew = create_crew(
        agents=agents,
        tasks=[],  # Tasks created dynamically during execution
        verbose=True,
        process="sequential",  # Sequential for debate-driven consensus
    )

    logger.info("Tech Debt Analysis crew instance created successfully")
    return crew


# Export crew creation function
__all__ = [
    "create_tech_debt_analysis_crew_instance",
]
