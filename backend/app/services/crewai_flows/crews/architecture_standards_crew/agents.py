"""
Architecture Standards Crew - Agent Creation Logic

This module contains the logic for creating specialized CrewAI agents
for architecture standards analysis and evaluation.

Agent Definitions:
1. Architecture Standards Specialist - Defines engagement-level requirements
2. Technology Stack Analyst - Assesses technology version compliance
3. Business Constraint Analyst - Evaluates valid exceptions

Each agent has:
- Clear role and goal definition
- Detailed backstory with expertise areas
- Appropriate tool assignments
- Delegation permissions based on role

References:
- Original file: architecture_standards_crew.py (lines 79-197)
- Pattern source: component_analysis_crew/agents.py
"""

import logging

# CrewAI imports with fallback
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Agent imports successful for ArchitectureStandardsCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback Agent class
    class Agent:
        """Fallback Agent class when CrewAI is not available"""

        def __init__(self, **kwargs):
            self.role = kwargs.get("role", "")
            self.goal = kwargs.get("goal", "")
            self.backstory = kwargs.get("backstory", "")
            self.tools = kwargs.get("tools", [])
            self.verbose = kwargs.get("verbose", False)
            self.allow_delegation = kwargs.get("allow_delegation", False)


# Import tool classes (with fallback handling)
try:
    from app.services.crewai_flows.tools.architecture_tools import (
        ComplianceChecker,
        StandardsTemplateGenerator,
        TechnologyVersionAnalyzer,
    )

    TOOLS_AVAILABLE = True
except ImportError:
    logger.warning("Architecture tools not available, using local placeholder tools")
    from app.services.crewai_flows.crews.architecture_standards_crew.tools import (
        ComplianceChecker,
        StandardsTemplateGenerator,
        TechnologyVersionAnalyzer,
    )

    TOOLS_AVAILABLE = False


def create_agent(role: str, goal: str, backstory: str, tools: list, **kwargs) -> Agent:
    """
    Factory function to create an agent with consistent configuration.

    Args:
        role: The agent's role
        goal: The agent's goal
        backstory: The agent's backstory
        tools: List of tool instances
        **kwargs: Additional agent configuration (verbose, allow_delegation, etc.)

    Returns:
        Agent instance
    """
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        verbose=kwargs.get("verbose", True),
        allow_delegation=kwargs.get("allow_delegation", True),
    )


def create_architecture_standards_agents() -> list:
    """
    Create the specialized agents for architecture standards analysis.

    Returns:
        List of Agent instances:
        1. Architecture Standards Specialist
        2. Technology Stack Analyst
        3. Business Constraint Analyst
    """
    logger.info("Creating Architecture Standards Crew agents")

    # Architecture Standards Specialist Agent
    architecture_standards_agent = create_agent(
        role="Architecture Standards Specialist",
        goal=(
            "Define and evaluate engagement-level architecture minimums based on "
            "industry best practices and client requirements"
        ),
        backstory="""You are an expert cloud architect with 15+ years of experience in enterprise
        architecture standards. You specialize in defining technology lifecycle policies, security
        requirements, and cloud-native architecture patterns. You understand the balance between
        innovation and risk management in large enterprise environments.

        Your expertise includes:
        - Technology version lifecycle management and EOL planning
        - Cloud-native architecture patterns and microservices design
        - Security frameworks (Zero Trust, NIST, ISO 27001)
        - Compliance requirements (SOC2, PCI-DSS, GDPR, HIPAA)
        - Enterprise integration patterns and API design standards
        - Infrastructure as Code and DevOps best practices

        You work collaboratively with business stakeholders to balance technical excellence
        with practical business constraints and timelines.""",
        tools=[
            TechnologyVersionAnalyzer(),
            StandardsTemplateGenerator(),
            ComplianceChecker(),
        ],
        verbose=True,
        allow_delegation=True,
    )

    # Technology Stack Analyst Agent
    technology_stack_analyst = create_agent(
        role="Technology Stack Analyst",
        goal="Assess application technology stacks against supported versions and identify upgrade paths",
        backstory="""You are a technology lifecycle expert who tracks the evolution of programming
        languages, frameworks, and platforms. You have deep knowledge of version compatibility,
        end-of-life schedules, and migration paths across the entire technology landscape.

        Your specializations include:
        - Programming language ecosystems (Java, .NET, Python, Node.js, Go, Rust)
        - Web frameworks and libraries (Spring, Django, React, Angular, Vue)
        - Database systems and data platforms (PostgreSQL, MySQL, MongoDB, Redis)
        - Container and orchestration technologies (Docker, Kubernetes, OpenShift)
        - Cloud platform services (AWS, Azure, GCP native services)
        - Security vulnerability tracking and patch management

        You can quickly identify technical debt related to outdated technology versions
        and recommend practical upgrade strategies that minimize business disruption.""",
        tools=[TechnologyVersionAnalyzer(), ComplianceChecker()],
        verbose=True,
        allow_delegation=False,
    )

    # Business Constraint Analyst Agent
    exception_handler_agent = create_agent(
        role="Business Constraint Analyst",
        goal=(
            "Identify and document valid architecture exceptions based on "
            "business constraints and technical trade-offs"
        ),
        backstory="""You are a business-technology liaison with expertise in evaluating when
        architecture standards should have exceptions. You understand vendor relationships,
        licensing constraints, integration dependencies, and business continuity requirements.

        Your expertise covers:
        - Vendor relationship management and licensing constraints
        - Legacy system integration patterns and dependencies
        - Regulatory compliance requirements and audit considerations
        - Business continuity and disaster recovery planning
        - Cost-benefit analysis for technical upgrades vs. exceptions
        - Risk assessment and mitigation strategy development

        You can articulate the business case for exceptions while quantifying associated risks
        and developing appropriate mitigation strategies. You ensure exceptions are properly
        documented, time-bounded, and include clear paths to future compliance.""",
        tools=[ComplianceChecker()],
        verbose=True,
        allow_delegation=False,
    )

    agents = [
        architecture_standards_agent,
        technology_stack_analyst,
        exception_handler_agent,
    ]

    logger.info(f"Created {len(agents)} architecture standards agents")
    return agents


# Export factory function
__all__ = ["create_architecture_standards_agents", "create_agent"]
