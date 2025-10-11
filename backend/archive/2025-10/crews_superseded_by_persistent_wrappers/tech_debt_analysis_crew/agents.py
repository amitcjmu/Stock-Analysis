"""
Tech Debt Analysis Agents - Agent Creation Logic

This module contains the agent creation logic for the Tech Debt Analysis Crew.
Three specialized agents work together to analyze legacy systems, recommend
migration strategies, and assess risks for technical debt remediation.

Agents:
1. Legacy Systems Modernization Expert - Analyzes legacy systems and provides modernization recommendations
2. Cloud Migration Strategist - Develops optimal 6R migration strategies
3. Risk Assessment Specialist - Assesses migration risks and provides mitigation strategies
"""

import logging
from typing import TYPE_CHECKING, List

from app.services.crewai_flows.config.crew_factory import create_agent
from app.services.crewai_flows.crews.tech_debt_analysis_crew.tools import (
    LegacySystemAnalysisTool,
    SixRStrategyTool,
)

if TYPE_CHECKING:
    from crewai import Agent

logger = logging.getLogger(__name__)


def create_tech_debt_analysis_agents() -> List["Agent"]:
    """
    Create specialized agents for tech debt analysis.

    This function creates three expert agents that work together to analyze
    legacy systems, develop migration strategies, and assess risks for
    technical debt remediation.

    Returns:
        List of three configured Agent instances
    """
    logger.info("Creating Tech Debt Analysis agents...")

    # Initialize tools
    legacy_analysis_tool = LegacySystemAnalysisTool()
    sixr_strategy_tool = SixRStrategyTool()

    # Create agents
    agents = [
        _create_legacy_modernization_expert(legacy_analysis_tool),
        _create_cloud_migration_strategist(sixr_strategy_tool),
        _create_risk_assessment_specialist(),
    ]

    logger.info(f"Created {len(agents)} Tech Debt Analysis agents")
    return agents


def _create_legacy_modernization_expert(
    legacy_analysis_tool: LegacySystemAnalysisTool,
) -> "Agent":
    """Create the Legacy Systems Modernization Expert agent"""
    return create_agent(
        role="Legacy Systems Modernization Expert",
        goal=(
            "Analyze legacy systems and provide comprehensive modernization recommendations "
            "based on technical debt assessment"
        ),
        backstory="""You are a legacy systems modernization expert with deep experience in
        transforming outdated technology stacks into modern, maintainable systems. You
        understand the challenges of legacy code, outdated architectures, and technical
        debt accumulation. Your expertise helps organizations make informed decisions
        about modernization investments.""",
        tools=[legacy_analysis_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def _create_cloud_migration_strategist(
    sixr_strategy_tool: SixRStrategyTool,
) -> "Agent":
    """Create the Cloud Migration Strategist agent"""
    return create_agent(
        role="Cloud Migration Strategist",
        goal=(
            "Develop optimal cloud migration strategies using 6R framework and provide "
            "strategic migration recommendations"
        ),
        backstory="""You are a cloud migration strategist with expertise in the 6R migration
        framework (Rehost, Replatform, Refactor, Rearchitect, Retire, Retain). You understand
        the trade-offs between different migration approaches and can recommend the optimal
        strategy based on business requirements, technical constraints, and organizational
        capabilities.""",
        tools=[sixr_strategy_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def _create_risk_assessment_specialist() -> "Agent":
    """Create the Risk Assessment Specialist agent"""
    return create_agent(
        role="Risk Assessment Specialist",
        goal=(
            "Assess migration risks and provide comprehensive risk mitigation strategies "
            "for tech debt remediation"
        ),
        backstory="""You are a risk assessment specialist focused on technology migration
        and modernization risks. You understand the potential pitfalls of legacy system
        migrations and can identify, quantify, and provide mitigation strategies for
        technical, business, and operational risks associated with modernization efforts.""",
        tools=[],  # Uses analysis from other agents
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


# Export agent creation functions
__all__ = [
    "create_tech_debt_analysis_agents",
]
