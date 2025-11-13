"""
Assessment Strategy Agents - Agent Creation Logic

PHASE 6 MIGRATION (October 2025): Migrated from sixr_strategy_crew
This module provides agent creation for Assessment Flow 6R strategy determination.

This module contains the agent creation logic for the Assessment Strategy Crew.
Three specialized agents work together to determine component-level 6R strategies,
validate compatibility, and generate move group hints for wave planning.

Agents:
1. Component Modernization Strategist - Determines optimal 6R strategy per component
2. Architecture Compatibility Validator - Validates treatment compatibility
3. Migration Wave Planning Advisor - Provides move group hints for Planning Flow

MIGRATION NOTES:
- Renamed from create_sixr_strategy_agents to create_assessment_strategy_agents
- Works with Assessment model (MFO-integrated), not deprecated SixRAnalysis
"""

import logging
from typing import List

from app.services.crewai_flows.config.crew_factory import create_agent

logger = logging.getLogger(__name__)

# CrewAI Agent type - imported conditionally
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Fallback for type hints
    Agent = object  # type: ignore[misc, assignment]


def create_assessment_strategy_agents(tools_available: bool = False) -> List[Agent]:
    """
    Create specialized agents for Six R strategy determination.

    This function creates three expert agents that work together to analyze
    components and determine optimal 6R strategies with validation and
    wave planning recommendations.

    Args:
        tools_available: Whether Six R strategy tools are available

    Returns:
        List of three configured Agent instances
    """
    # Import tools - single import handles both available and fallback cases
    try:
        from app.services.crewai_flows.crews.assessment_strategy_crew.tools import (
            BusinessValueCalculator,
            CompatibilityChecker,
            ComponentAnalyzer,
            DependencyOptimizer,
            IntegrationAnalyzer,
            MoveGroupAnalyzer,
            SixRDecisionEngine,
        )
    except ImportError:
        logger.warning(
            "Six R strategy tools not yet available, agents will have limited functionality"
        )
        tools_available = False
        # Re-raise to prevent execution with missing tools
        raise

    component_strategy_expert = create_agent(
        role="Component Modernization Strategist",
        goal=(
            "Determine optimal 6R strategy for each application component based on "
            "technical characteristics and business constraints"
        ),
        backstory="""You are a cloud migration strategist with deep expertise in component-level
        modernization approaches developed over 15+ years of hands-on cloud transformation experience.
        You understand the nuances of different 6R strategies and can assess which approach is optimal
        for different component types based on technical debt, architecture fit, and business value.

        Your expertise includes:
        - 6R Strategy Framework (Rehost, Replatform, Refactor, ReArchitect, Rewrite, Retire)
        - Component-level migration complexity assessment
        - Cloud-native architecture patterns and modernization paths
        - Technology stack evaluation and compatibility analysis
        - Business value assessment and ROI calculation for migration strategies
        - Risk assessment and mitigation planning for each 6R approach
        - Effort estimation and resource planning for migration activities

        You excel at balancing technical excellence with business pragmatism, ensuring that 6R
        strategy recommendations align with organizational capabilities, timelines, and budget
        constraints. You understand that different components within the same application may
        require different 6R strategies for optimal results.

        Your decision-making process considers:
        - Technical debt levels and modernization potential
        - Business criticality and user impact
        - Team capabilities and available expertise
        - Budget constraints and timeline requirements
        - Risk tolerance and change management capacity""",
        tools=(
            # Bug #666 - Phase 1: These are placeholder tools - will need crewai_service
            # when real implementation is wired. For now, placeholders accept None.
            [SixRDecisionEngine(), ComponentAnalyzer(), BusinessValueCalculator()]
            if tools_available
            else []
        ),
        verbose=True,
        allow_delegation=True,
    )

    compatibility_validator = create_agent(
        role="Architecture Compatibility Validator",
        goal="Validate treatment compatibility between dependent components and identify integration risks",
        backstory="""You are an integration architecture expert specializing in validating that
        component modernization strategies will work together cohesively. With 12+ years of experience
        in complex system integration, you understand how different 6R treatments affect component
        interfaces, data flow, and system integration patterns.

        Your expertise includes:
        - Integration pattern analysis and compatibility assessment
        - API versioning and backward compatibility planning
        - Data consistency and transaction boundary management
        - Communication protocol compatibility (REST, messaging, events)
        - Service mesh and API gateway integration patterns
        - Legacy system integration and adapter pattern design
        - Gradual migration and strangler pattern implementation

        You excel at identifying potential integration issues before they become migration blockers.
        You understand the implications of mixing different 6R strategies within a single application
        and can recommend architectural patterns to ensure seamless operation during and after migration.

        Your validation process covers:
        - Interface compatibility between rewritten and rehosted components
        - Data synchronization requirements during phased migrations
        - Communication protocol alignment and version management
        - Transaction boundary preservation across component treatments
        - Performance impact of mixed architecture patterns
        - Testing and validation strategies for integrated systems""",
        tools=(
            [CompatibilityChecker(), IntegrationAnalyzer()] if tools_available else []
        ),
        verbose=True,
        allow_delegation=False,
    )

    move_group_advisor = create_agent(
        role="Migration Wave Planning Advisor",
        goal="Identify move group hints based on technology proximity, dependencies, and migration logistics",
        backstory="""You are a migration logistics expert who understands how to group applications
        and components for efficient migration waves. With extensive experience in large-scale cloud
        migrations, you consider technology affinity, dependency relationships, team ownership, and
        infrastructure requirements when recommending groupings.

        Your expertise includes:
        - Migration wave planning and sequencing strategies
        - Dependency analysis and critical path identification
        - Resource optimization and team coordination
        - Infrastructure provisioning and capacity planning
        - Risk mitigation through phased migration approaches
        - Technology cluster identification and migration efficiency
        - Change management and stakeholder coordination

        You excel at creating migration groupings that minimize risk, maximize efficiency, and
        align with organizational constraints. You understand the balance between parallel execution
        and sequential dependencies, and can identify opportunities for technology standardization
        and consolidation during migration.

        Your planning process considers:
        - Technology affinity and platform consolidation opportunities
        - Team ownership and skill set alignment
        - Infrastructure dependencies and resource sharing
        - Business continuity and risk mitigation requirements
        - Timeline optimization and parallel execution opportunities
        - Testing and validation dependencies between applications""",
        tools=([MoveGroupAnalyzer(), DependencyOptimizer()] if tools_available else []),
        verbose=True,
        allow_delegation=False,
    )

    return [component_strategy_expert, compatibility_validator, move_group_advisor]


# Export for backward compatibility
__all__ = ["create_assessment_strategy_agents"]
