"""
Architecture Standards Crew - Task and Crew Creation Logic

This module contains the logic for creating CrewAI tasks and assembling
the complete crew for architecture standards analysis.

Task Definitions:
1. Capture Standards Task - Define engagement-level architecture requirements
2. Analyze Application Stacks Task - Assess technology compliance
3. Evaluate Exceptions Task - Identify valid architecture exceptions

Each task includes:
- Detailed description with analysis requirements
- Expected output format and structure
- Agent assignment and context dependencies

References:
- Original file: architecture_standards_crew.py (lines 199-450)
- Pattern source: component_analysis_crew/tasks.py
"""

import logging

# CrewAI imports with fallback
try:
    from crewai import Crew, Task

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Task/Crew imports successful for ArchitectureStandardsCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Task:
        """Fallback Task class when CrewAI is not available"""

        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")
            self.agent = kwargs.get("agent")
            self.context = kwargs.get("context", [])

    class Crew:
        """Fallback Crew class when CrewAI is not available"""

        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])
            self.verbose = kwargs.get("verbose", False)
            self.process = kwargs.get("process", "sequential")

        def kickoff(self, inputs=None):
            return {"status": "fallback_mode", "engagement_standards": []}


def create_task(
    description: str, expected_output: str, agent, context: list = None
) -> Task:
    """
    Factory function to create a task with consistent configuration.

    Args:
        description: Task description with analysis requirements
        expected_output: Expected output format and structure
        agent: Agent instance to execute the task
        context: List of task dependencies (optional)

    Returns:
        Task instance
    """
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context or [],
    )


def create_crew(
    agents: list, tasks: list, verbose: bool = True, process: str = "sequential"
) -> Crew:
    """
    Factory function to create a crew with consistent configuration.

    Args:
        agents: List of Agent instances
        tasks: List of Task instances
        verbose: Enable verbose logging
        process: Execution process type (sequential or hierarchical)

    Returns:
        Crew instance
    """
    return Crew(
        agents=agents,
        tasks=tasks,
        verbose=verbose,
        process=process,
    )


def create_architecture_standards_tasks(agents: list) -> list:
    """
    Create the tasks for architecture standards analysis.

    Args:
        agents: List of Agent instances [standards_agent, stack_analyst, constraint_analyst]

    Returns:
        List of Task instances:
        1. Capture Standards Task
        2. Analyze Application Stacks Task
        3. Evaluate Exceptions Task
    """
    logger.info("Creating Architecture Standards Crew tasks")

    if len(agents) < 3:
        logger.warning(f"Expected 3 agents, got {len(agents)}. Using available agents.")
        # Pad with None if needed
        while len(agents) < 3:
            agents.append(None)

    # Task 1: Capture Architecture Standards
    capture_standards_task = create_task(
        description="""Analyze the engagement requirements and client context to capture comprehensive
        architecture standards. Consider the following key areas:

        1. Technology Version Requirements:
           - Programming languages (Java 11+, .NET 6+, Python 3.8+, Node.js 16+)
           - Web frameworks and libraries with security patch currency
           - Database systems and minimum supported versions
           - Operating systems and container runtime requirements
           - Infrastructure components (load balancers, message brokers)

        2. Security and Compliance Standards:
           - Authentication patterns (OAuth 2.0, OIDC, SAML)
           - Authorization models (RBAC, ABAC, policy-based)
           - Data encryption requirements (at rest and in transit)
           - Audit logging and monitoring capabilities
           - Regulatory compliance needs (map to client industry)

        3. Architecture Pattern Requirements:
           - API design standards (REST, GraphQL, OpenAPI specifications)
           - Event-driven architecture patterns and message formats
           - Data persistence patterns and consistency models
           - Caching strategies and distributed system patterns
           - Error handling and circuit breaker patterns

        4. Cloud-Native Capabilities:
           - Containerization standards (Docker, OCI compliance)
           - Infrastructure as Code requirements (Terraform, CloudFormation)
           - CI/CD pipeline integration and deployment automation
           - Observability requirements (metrics, logs, traces)
           - Auto-scaling and load balancing patterns

        5. Integration Standards:
           - Inter-service communication patterns
           - Data exchange formats and schemas
           - Protocol standards and version compatibility
           - Service mesh and API gateway requirements

        Base your analysis on:
        - Engagement context: {engagement_context}
        - Selected applications: {selected_applications}
        - Existing standards: {existing_standards}
        - Industry best practices for the client's domain
        - Current technology landscape and emerging trends

        Output a comprehensive set of architecture standards with clear rationale.""",
        expected_output="""A structured list of architecture standards containing:

        1. Technology Standards:
           - Minimum and recommended versions for each technology
           - End-of-life dates and upgrade timelines
           - Security vulnerability thresholds and patch requirements
           - Performance and compatibility requirements

        2. Security Standards:
           - Authentication and authorization requirements
           - Data protection and encryption specifications
           - Network security and access control policies
           - Audit logging and compliance monitoring requirements

        3. Architecture Patterns:
           - Required design patterns and architectural principles
           - Integration standards and communication protocols
           - Data management and persistence requirements
           - Scalability and resilience patterns

        4. Implementation Guidance:
           - Detailed implementation guidelines for each standard
           - Code examples and reference architectures
           - Tooling recommendations and approved technologies
           - Exception criteria and approval processes

        Each standard should include:
        - Clear rationale linking to business value
        - Implementation difficulty and timeline estimates
        - Dependencies and prerequisites
        - Success metrics and validation criteria""",
        agent=agents[0],
    )

    # Task 2: Analyze Application Technology Stacks
    analyze_application_stacks_task = create_task(
        description="""For each selected application, analyze its current technology stack against
        the captured architecture standards. Perform a comprehensive assessment including:

        1. Technology Version Compliance Analysis:
           - Compare current technology versions vs. minimum requirements
           - Identify end-of-life technologies requiring immediate attention
           - Calculate version-based technical debt scores (0-10 scale)
           - Assess security vulnerability exposure and patch currency
           - Evaluate compatibility with target cloud platforms

        2. Architecture Pattern Compliance:
           - Assess current architecture against required patterns
           - Identify anti-patterns and design debt
           - Evaluate API design and integration compliance
           - Review data management and persistence approaches
           - Analyze error handling and resilience patterns

        3. Security and Compliance Assessment:
           - Evaluate authentication and authorization implementations
           - Assess data protection and encryption usage
           - Review audit logging and monitoring capabilities
           - Identify compliance gaps and regulatory risks
           - Validate network security and access controls

        4. Upgrade Path Analysis:
           - Identify clear migration paths for non-compliant technologies
           - Estimate effort and complexity for version upgrades
           - Highlight breaking changes and compatibility issues
           - Recommend incremental vs. wholesale upgrade strategies
           - Assess business impact and downtime requirements

        5. Risk and Priority Assessment:
           - Categorize compliance gaps by severity (critical, high, medium, low)
           - Estimate business and technical risks of current state
           - Recommend prioritization based on risk and effort
           - Identify quick wins and long-term improvements

        Application metadata: {application_metadata}
        Architecture standards: {architecture_standards}

        Provide detailed analysis with actionable recommendations.""",
        expected_output="""For each application, provide a comprehensive compliance report:

        1. Executive Summary:
           - Overall compliance score (0-100)
           - Key findings and priority recommendations
           - Estimated effort and timeline for full compliance
           - Business impact assessment

        2. Technology Compliance Matrix:
           - Technology-by-technology compliance status
           - Current vs. required versions with gap analysis
           - Security vulnerability assessment
           - Upgrade complexity ratings

        3. Architecture Assessment:
           - Pattern compliance evaluation
           - Identified design debt and anti-patterns
           - Integration and API compliance review
           - Data management assessment

        4. Detailed Recommendations:
           - Prioritized list of improvements with effort estimates
           - Specific upgrade paths and migration strategies
           - Risk mitigation approaches for each gap
           - Timeline recommendations with dependencies

        5. Compliance Roadmap:
           - Phase-based improvement plan
           - Quick wins vs. long-term investments
           - Resource requirements and skill needs
           - Success metrics and validation checkpoints""",
        agent=agents[1],
        context=[capture_standards_task],
    )

    # Task 3: Evaluate Architecture Exceptions
    evaluate_exceptions_task = create_task(
        description="""Evaluate potential exceptions to architecture standards based on business
        constraints and technical realities. Conduct a thorough analysis including:

        1. Business Constraint Evaluation:
           - Vendor support agreements and licensing limitations
           - Legacy system integration requirements and dependencies
           - Regulatory or industry-specific compliance needs
           - Business continuity and operational stability requirements
           - Budget constraints and resource availability
           - Timeline pressures and market competitive factors

        2. Technical Trade-off Analysis:
           - Cost vs. benefit analysis for standard compliance
           - Technical debt implications of maintaining exceptions
           - Integration complexity and system coupling considerations
           - Performance and scalability impact assessment
           - Security risk evaluation and mitigation options
           - Maintenance burden and long-term sustainability

        3. Risk Assessment and Mitigation:
           - Quantify risks associated with each proposed exception
           - Develop specific mitigation strategies and controls
           - Define monitoring and alerting requirements
           - Establish review cycles and compliance checkpoints
           - Create contingency plans for risk scenarios

        4. Exception Documentation and Governance:
           - Clear rationale for each proposed exception
           - Time-bounded approval with specific review dates
           - Escalation paths and approval authority requirements
           - Monitoring and reporting obligations
           - Exit strategy and compliance pathway definition

        Application analysis results: {application_analysis_results}
        Business constraints: {business_constraints}
        Risk tolerance guidelines: {risk_tolerance}

        Provide recommendations for valid exceptions with proper business justification.""",
        expected_output="""A comprehensive exception analysis containing:

        1. Exception Summary:
           - Total applications requiring exceptions
           - Category breakdown (technology, security, architecture, compliance)
           - Overall risk assessment and business impact
           - Resource implications and ongoing costs

        2. Detailed Exception Proposals:
           For each proposed exception:
           - Specific standard(s) affected and deviation details
           - Clear business rationale and constraint analysis
           - Quantified risk assessment with severity levels
           - Proposed mitigation strategies and controls
           - Time-bounded approval recommendation
           - Exit strategy and compliance timeline

        3. Risk Management Framework:
           - Risk categorization and severity matrix
           - Monitoring and alerting requirements
           - Review cycle and approval renewal process
           - Escalation procedures for risk threshold breaches
           - Compliance reporting and audit trail requirements

        4. Governance Recommendations:
           - Exception approval authority and process
           - Documentation and tracking requirements
           - Regular review and reassessment schedule
           - Compliance pathway and improvement plans
           - Budget allocation for risk management activities

        5. Strategic Recommendations:
           - Long-term architecture evolution planning
           - Investment priorities for reducing exceptions
           - Capability building and skill development needs
           - Vendor relationship and contract considerations""",
        agent=agents[2],
        context=[capture_standards_task, analyze_application_stacks_task],
    )

    tasks = [
        capture_standards_task,
        analyze_application_stacks_task,
        evaluate_exceptions_task,
    ]

    logger.info(f"Created {len(tasks)} architecture standards tasks")
    return tasks


def create_architecture_standards_crew_instance(agents: list, tasks: list) -> Crew:
    """
    Create the complete Architecture Standards Crew instance.

    Args:
        agents: List of Agent instances
        tasks: List of Task instances

    Returns:
        Crew instance configured for architecture standards analysis
    """
    logger.info("Creating Architecture Standards Crew instance")

    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, returning fallback crew")
        return None

    crew = create_crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process="sequential",
    )

    logger.info("Architecture Standards Crew instance created successfully")
    return crew


# Export factory functions
__all__ = [
    "create_architecture_standards_tasks",
    "create_architecture_standards_crew_instance",
    "create_task",
    "create_crew",
]
