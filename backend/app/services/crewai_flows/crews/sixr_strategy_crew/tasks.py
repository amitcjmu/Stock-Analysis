"""
Six R Strategy Tasks - Task Definitions and Crew Factory

This module contains the task definitions for the Six R Strategy Crew.
Three sequential tasks work together to determine component-level 6R strategies,
validate compatibility, and generate move group hints.

Tasks:
1. Determine Component Strategies - Analyze and recommend 6R strategy per component
2. Validate Component Compatibility - Validate treatment compatibility
3. Generate Move Group Hints - Provide wave planning recommendations
"""

import logging
from typing import List

from app.services.crewai_flows.config.crew_factory import create_crew, create_task

logger = logging.getLogger(__name__)

# CrewAI types - imported conditionally
try:
    from crewai import Agent, Crew, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Fallback for type hints
    Agent = object  # type: ignore[misc, assignment]
    Task = object  # type: ignore[misc, assignment]
    Crew = object  # type: ignore[misc, assignment]


def create_sixr_strategy_tasks(agents: List[Agent]) -> List[Task]:
    """
    Create Six R strategy tasks for the crew.

    This function creates three sequential tasks that work together to determine
    component-level 6R strategies with validation and wave planning.

    Args:
        agents: List of three agent instances

    Returns:
        List of three configured Task instances
    """
    determine_component_strategies_task = create_task(
        description="""Analyze each component and determine the optimal 6R strategy based on comprehensive
        assessment of technical and business factors:

        1. Technical Characteristics Assessment:
           - Technology stack maturity and cloud-readiness evaluation
           - Technical debt levels and complexity of remediation
           - Architecture patterns and modernization potential
           - Performance requirements and scalability needs
           - Security posture and compliance requirements
           - Integration complexity and dependency management

        2. Business Factor Analysis:
           - Component criticality and business value contribution
           - User impact and change tolerance assessment
           - Development team capabilities and available expertise
           - Timeline constraints and migration urgency
           - Budget allocation and cost sensitivity
           - Risk tolerance and change management capacity

        3. 6R Strategy Selection Framework:

           REWRITE Criteria:
           - High technical debt with significant architecture limitations
           - Strategic importance justifying complete rebuilding
           - Modern technology stack adoption requirements
           - Team has expertise in target technologies
           - Sufficient budget and timeline for greenfield development
           - Opportunity to significantly improve performance/scalability

           REARCHITECT Criteria:
           - Core functionality is sound but architecture needs modernization
           - Microservices decomposition or event-driven patterns needed
           - Scalability or resilience improvements required
           - Technology stack is modern enough to refactor
           - Team has architecture and refactoring expertise
           - Moderate budget with focus on architectural improvements

           REFACTOR Criteria:
           - Good architectural foundation with moderate technical debt
           - Code quality improvements and optimization needed
           - Technology stack is current but implementation needs enhancement
           - Incremental improvement approach preferred
           - Limited budget but skilled development team
           - Low risk tolerance with gradual improvement preference

           REPLATFORM Criteria:
           - Application is working well but needs cloud optimization
           - Infrastructure modernization without code changes
           - Quick cloud adoption with minimal business disruption
           - Limited development resources or tight timelines
           - Focus on operational efficiency and cost reduction
           - Container or serverless platform adoption opportunity

           REHOST Criteria:
           - Minimal changes required for cloud migration
           - Legacy components that are difficult to modify
           - Urgent timeline with limited resources
           - Low risk tolerance and preference for minimal change
           - Infrastructure consolidation and cost reduction focus
           - Stepping stone to future modernization

           RETIRE Criteria:
           - Component functionality is no longer needed
           - Duplicate functionality exists in other components
           - High maintenance cost with low business value
           - Security or compliance issues make continuation risky
           - Replacement solutions are available and preferred

        4. Decision Factors Matrix:
           For each component, evaluate and score (1-10):
           - Technical debt level (higher = more debt)
           - Business criticality (higher = more critical)
           - Modernization potential (higher = more potential)
           - Development complexity (higher = more complex)
           - Timeline constraints (higher = more urgent)
           - Budget availability (higher = more budget)
           - Team expertise (higher = more expertise)
           - Risk tolerance (higher = more tolerant)

        Components to analyze: {components}
        Technical debt analysis: {tech_debt_analysis}
        Architecture standards: {architecture_standards}
        Business context: {business_context}
        Resource constraints: {resource_constraints}

        For each component, provide detailed 6R recommendation with comprehensive rationale,
        effort estimates, risk assessment, and implementation roadmap.""",
        expected_output="""Component-level 6R strategies containing:

        1. Strategy Recommendations:
           For each component:
           - Recommended 6R strategy with confidence score (0-1)
           - Alternative strategies ranked by suitability
           - Detailed rationale explaining strategy selection
           - Decision factor scores and weighting analysis
           - Key assumptions and constraints considered

        2. Implementation Planning:
           - Effort estimates (hours/weeks) for strategy implementation
           - Cost estimates and budget requirements
           - Timeline recommendations with critical milestones
           - Resource requirements (team size, skills, tools)
           - Dependencies and prerequisites for implementation

        3. Risk Assessment:
           - Technical risks and mitigation strategies
           - Business risks and impact assessment
           - Implementation risks and contingency planning
           - Integration risks with other components
           - Performance and scalability risk evaluation

        4. Success Criteria:
           - Measurable success metrics for each strategy
           - Quality gates and validation checkpoints
           - Performance benchmarks and targets
           - Business outcome expectations
           - Timeline and budget success criteria

        5. Alternative Scenarios:
           - Backup strategy options if primary approach fails
           - Phased implementation alternatives
           - Budget-constrained options and trade-offs
           - Accelerated timeline options and associated risks
           - Risk-averse alternatives with lower complexity""",
        agent=agents[0] if agents else None,
    )

    validate_component_compatibility_task = create_task(
        description="""Validate compatibility between component 6R strategies within the application
        and identify potential integration issues:

        1. Strategy Compatibility Analysis:
           - Interface compatibility between components with different treatments
           - Data flow and consistency requirements across strategy boundaries
           - Communication protocol alignment and version management
           - Transaction boundary preservation during migration
           - Performance impact assessment of mixed strategies

        2. Integration Pattern Validation:
           - API versioning and backward compatibility requirements
           - Event schema compatibility for asynchronous communication
           - Database access pattern alignment and data consistency
           - Shared service dependencies and compatibility requirements
           - Infrastructure service integration (logging, monitoring, security)

        3. Migration Sequence Dependencies:
           - Order dependencies between component migrations
           - Parallel execution opportunities and constraints
           - Rollback dependencies and failure isolation
           - Testing dependencies and integration validation requirements
           - Data migration sequencing and consistency requirements

        4. Risk Identification and Mitigation:
           - Integration risks from strategy combinations
           - Performance risks from architectural mismatches
           - Data consistency risks during transition periods
           - Security risks from mixed authentication/authorization patterns
           - Operational risks from monitoring and management complexity

        Component strategies: {component_strategies}
        Application architecture: {application_architecture}
        Integration patterns: {integration_patterns}

        Provide comprehensive compatibility assessment with risk mitigation recommendations.""",
        expected_output="""Compatibility validation report containing:

        1. Compatibility Matrix:
           - Component-to-component compatibility assessment
           - Strategy combination risk levels (low, medium, high, critical)
           - Specific compatibility issues and their severity
           - Integration points requiring special attention
           - Recommended mitigation strategies for each issue

        2. Integration Requirements:
           - API versioning and compatibility management needs
           - Data synchronization requirements during migration
           - Communication protocol adaptation requirements
           - Shared service compatibility and upgrade coordination
           - Testing and validation integration points

        3. Risk Assessment:
           - High-risk integration points requiring immediate attention
           - Medium-risk areas needing monitoring and contingency planning
           - Low-risk integrations with standard mitigation approaches
           - Critical path dependencies that could block migration
           - Performance impact assessment and optimization needs

        4. Mitigation Strategies:
           - Adapter patterns for incompatible interfaces
           - Proxy services for gradual migration approaches
           - Event-driven patterns for loose coupling
           - Database synchronization strategies for data consistency
           - Testing strategies for integrated system validation

        5. Recommendations:
           - Strategy adjustments to improve compatibility
           - Architecture patterns to enable smoother migration
           - Infrastructure requirements for integration support
           - Timeline adjustments to sequence migrations appropriately
           - Team coordination requirements for successful integration""",
        agent=agents[1] if len(agents) > 1 else None,
        context=[determine_component_strategies_task],
    )

    generate_move_group_hints_task = create_task(
        description="""Analyze component 6R strategies and generate move group hints for Planning Flow
        wave coordination:

        1. Technology Affinity Analysis:
           - Group components with similar technology stacks
           - Identify platform consolidation opportunities
           - Cluster components requiring similar infrastructure
           - Group components with shared operational requirements
           - Identify components benefiting from coordinated migration

        2. Dependency-Based Grouping:
           - Cluster tightly coupled components requiring joint migration
           - Identify dependency chains and critical path sequences
           - Group components with shared data dependencies
           - Cluster components with coordinated deployment requirements
           - Identify components that can migrate independently

        3. Resource Optimization:
           - Group applications requiring similar skill sets
           - Cluster migrations with similar effort profiles
           - Identify opportunities for shared infrastructure provisioning
           - Group applications with similar testing requirements
           - Cluster migrations with compatible timelines

        4. Risk Distribution:
           - Distribute high-risk migrations across different waves
           - Balance complexity across migration waves
           - Ensure each wave has manageable risk profile
           - Group low-risk migrations for parallel execution
           - Identify pilot candidates for early wave execution

        5. Business Value Optimization:
           - Prioritize high-value applications for early migration
           - Group applications with related business outcomes
           - Sequence migrations to maximize business benefit
           - Consider business continuity and change management capacity
           - Balance quick wins with strategic improvements

        Component strategies: {component_strategies}
        Application dependencies: {application_dependencies}
        Resource constraints: {resource_constraints}
        Business priorities: {business_priorities}

        Generate actionable move group recommendations for Planning Flow integration.""",
        expected_output="""Move group hints containing:

        1. Recommended Wave Groupings:
           - Wave composition with applications and rationale
           - Technology affinity clusters and consolidation opportunities
           - Dependency-based groupings and sequencing requirements
           - Resource optimization clusters and shared infrastructure needs
           - Risk-balanced groupings with complexity distribution

        2. Migration Sequence Recommendations:
           - Optimal wave sequencing with dependencies
           - Parallel execution opportunities within waves
           - Critical path identification and bottleneck management
           - Pilot wave recommendations and success criteria
           - Rollback sequence planning and failure isolation

        3. Resource Planning Hints:
           - Skill set requirements by wave
           - Infrastructure provisioning timeline
           - Testing and validation resource needs
           - Change management and training requirements
           - Budget allocation recommendations by wave

        4. Success Metrics by Wave:
           - Business value delivery targets
           - Technical success criteria and quality gates
           - Performance benchmarks and SLA requirements
           - Cost optimization targets and budget constraints
           - Timeline milestones and delivery commitments

        5. Risk Management Strategy:
           - Risk distribution across waves
           - Contingency planning for each wave
           - Success dependencies between waves
           - Early warning indicators and monitoring requirements
           - Escalation procedures and decision points""",
        agent=agents[2] if len(agents) > 2 else None,
        context=[
            determine_component_strategies_task,
            validate_component_compatibility_task,
        ],
    )

    return [
        determine_component_strategies_task,
        validate_component_compatibility_task,
        generate_move_group_hints_task,
    ]


def create_sixr_strategy_crew_instance(agents: List[Agent], tasks: List[Task]) -> Crew:
    """
    Create Six R Strategy Crew instance with agents and tasks.

    Args:
        agents: List of configured agent instances
        tasks: List of configured task instances

    Returns:
        Configured Crew instance ready for execution
    """
    if not CREWAI_AVAILABLE:
        return None

    return create_crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process="sequential",
    )


# Export for backward compatibility
__all__ = [
    "create_sixr_strategy_tasks",
    "create_sixr_strategy_crew_instance",
]
