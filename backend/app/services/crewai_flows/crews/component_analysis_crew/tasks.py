"""
Component Analysis Tasks - Task and Crew Creation Logic

This module contains the task and crew creation logic for component analysis.
Three sequential tasks work together to identify components, analyze technical debt,
and map dependencies.

Tasks:
1. Identify Components - Catalog all application components
2. Analyze Technical Debt - Assess debt across multiple dimensions
3. Map Dependencies - Create dependency graphs and migration groups
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


def create_component_analysis_tasks(agents: List[Agent]) -> List[Task]:
    """
    Create component analysis tasks.

    This function creates three sequential tasks that work together to:
    1. Identify and catalog all application components
    2. Analyze technical debt for each component
    3. Map dependencies and create migration groupings

    Args:
        agents: List of three agents [component_analyst, debt_specialist, dependency_expert]

    Returns:
        List of three configured Task instances
    """
    if not agents or len(agents) < 3:
        logger.error(
            f"Expected 3 agents for component analysis, got {len(agents) if agents else 0}"
        )
        return []

    identify_components_task = create_task(
        description="""Analyze the application metadata to identify all components within the application
        architecture. Go beyond traditional frontend/middleware/backend categories to identify modern
        architectural patterns and component types:

        1. User Interface Components:
           - Single Page Applications (React, Angular, Vue.js)
           - Multi-page web applications with server-side rendering
           - Mobile applications (native iOS/Android, React Native, Flutter)
           - Desktop applications (Electron, native desktop apps)
           - Progressive Web Apps (PWA) and mobile-web hybrids
           - Administrative interfaces and dashboards
           - API documentation and developer portals

        2. API and Service Components:
           - REST APIs with OpenAPI/Swagger specifications
           - GraphQL endpoints and schema definitions
           - gRPC services and protocol buffer definitions
           - SOAP services and legacy web services
           - WebSocket servers and real-time communication layers
           - Message queue consumers and producers (Kafka, RabbitMQ, SQS)
           - Background job processors and task queues
           - Scheduled tasks, cron jobs, and batch processors
           - Webhook handlers and event processors

        3. Business Logic Components:
           - Core business services and domain logic
           - Integration services and data transformation layers
           - Workflow engines and business process automation
           - Business rule engines and decision services
           - Data processing pipelines and ETL components
           - Analytics and reporting services
           - Search and indexing services

        4. Data Components:
           - Primary databases (PostgreSQL, MySQL, SQL Server, Oracle)
           - NoSQL databases (MongoDB, Cassandra, DynamoDB)
           - Cache layers (Redis, Memcached, application caches)
           - Data warehouses and analytics platforms (Snowflake, BigQuery)
           - Search engines (Elasticsearch, Solr, CloudSearch)
           - File storage and content management systems
           - Time-series databases and metrics stores
           - Graph databases and knowledge graphs

        5. Infrastructure and Platform Components:
           - Load balancers and reverse proxies (nginx, HAProxy, ALB)
           - API gateways and service mesh components
           - Message brokers and event streaming platforms
           - Monitoring and observability services (metrics, logs, traces)
           - Security services (authentication, authorization, secrets management)
           - Container orchestration components (Kubernetes workloads)
           - Serverless functions and FaaS components

        6. Integration and External Components:
           - Third-party service integrations and connectors
           - Legacy system adapters and wrapper services
           - B2B integration endpoints and EDI processors
           - Payment processing and financial service integrations
           - Social media and marketing platform connectors
           - Analytics and tracking service integrations

        For each identified component, analyze:
        - Component name and logical function
        - Technology stack and implementation details
        - Deployment characteristics and runtime requirements
        - Resource consumption and scaling patterns
        - Security and access control requirements

        Application metadata to analyze: {application_metadata}
        Discovery data available: {discovery_data}
        Architecture context: {architecture_context}

        Use metadata indicators such as:
        - Package.json, pom.xml, requirements.txt for technology identification
        - Docker compose files and Kubernetes manifests for deployment patterns
        - Configuration files for service definitions and dependencies
        - Network topology and port configurations
        - Database schemas and data model definitions""",
        expected_output="""A comprehensive component inventory containing:

        1. Component Catalog:
           - Complete list of identified components with unique names
           - Component type classification using modern architecture patterns
           - Technology stack details (languages, frameworks, databases, tools)
           - Component responsibilities and business functions
           - Deployment patterns and runtime characteristics
           - Resource requirements and scaling behavior

        2. Component Details:
           For each component:
           - Primary technologies and versions
           - Key dependencies and integration points
           - Data access patterns and persistence requirements
           - Security and compliance considerations
           - Performance characteristics and SLA requirements
           - Development team ownership and maintenance responsibility

        3. Architecture Insights:
           - Overall architectural pattern (monolithic, microservices, hybrid)
           - Component communication patterns and protocols
           - Data flow and transaction boundaries
           - Shared infrastructure and platform dependencies
           - Evolution indicators (legacy vs. modern patterns)

        4. Discovery Confidence:
           - Confidence score (0-1) for each component identification
           - Data sources used for component discovery
           - Assumptions made and potential gaps in analysis
           - Recommendations for additional discovery if needed""",
        agent=agents[0],
    )

    analyze_technical_debt_task = create_task(
        description="""Analyze technical debt for each identified component based on available
        metadata and discovery data. Focus on comprehensive debt assessment across multiple dimensions:

        1. Technology Obsolescence Analysis:
           - Programming language versions vs. current LTS and security support
           - Framework and library versions vs. actively maintained releases
           - Database system versions and end-of-life timeline assessment
           - Operating system and runtime environment currency
           - Security vulnerability exposure based on known CVEs
           - License compliance and commercial support availability

        2. Architecture Debt Assessment:
           - Anti-pattern identification from architectural metadata
           - Monolithic vs. modular design indicators and decomposition opportunities
           - Tight coupling indicators and dependency complexity analysis
           - Code organization and separation of concerns evaluation
           - Configuration management and environment-specific customizations
           - API design maturity and RESTful/GraphQL best practices adherence

        3. Operational Debt Evaluation:
           - Deployment automation maturity and CI/CD integration
           - Infrastructure as Code adoption and configuration drift indicators
           - Monitoring and observability instrumentation completeness
           - Logging standardization and centralized log management
           - Documentation quality and knowledge management practices
           - Backup and disaster recovery preparedness

        4. Security and Compliance Debt:
           - Authentication and authorization implementation maturity
           - Data protection and encryption implementation gaps
           - Audit trail and compliance logging deficiencies
           - Network security and access control configuration
           - Secrets management and credential storage practices
           - Regulatory compliance gaps based on industry requirements

        5. Performance and Scalability Debt:
           - Performance bottleneck indicators from configuration analysis
           - Scalability limitation identification (stateful components, shared resources)
           - Resource utilization patterns and optimization opportunities
           - Caching strategy implementation and effectiveness
           - Database query optimization and indexing opportunities
           - Network communication efficiency and protocol optimization

        6. Maintainability Debt:
           - Code complexity indicators from build and dependency analysis
           - Test coverage and quality assurance process maturity
           - Development workflow and tooling standardization
           - Technical documentation completeness and currency
           - Knowledge concentration and bus factor assessment

        Component inventory: {component_inventory}
        Architecture standards: {architecture_standards}
        Technology lifecycle data: {technology_lifecycle}
        Security requirements: {security_requirements}

        Calculate quantitative debt scores and prioritize remediation efforts.""",
        expected_output="""Technical debt analysis containing:

        1. Component-Level Debt Assessment:
           For each component:
           - Overall technical debt score (0-10 scale, 10 = highest debt)
           - Debt category breakdown (technology, architecture, security, operational)
           - Specific debt items with severity levels (critical, high, medium, low)
           - Remediation effort estimates (hours) and complexity ratings
           - Impact assessment on migration and modernization efforts
           - Priority ranking for debt remediation

        2. Detailed Debt Inventory:
           - Technology debt items (version upgrades, EOL components, security patches)
           - Architecture debt items (anti-patterns, coupling issues, design flaws)
           - Security debt items (vulnerabilities, compliance gaps, access control issues)
           - Operational debt items (automation gaps, monitoring deficiencies)
           - Performance debt items (bottlenecks, scalability limitations)

        3. Remediation Roadmap:
           - Quick wins (low effort, high impact improvements)
           - Critical path items (blocking migration or creating security risks)
           - Long-term investments (architectural refactoring, technology upgrades)
           - Effort estimates and resource requirements
           - Dependencies between remediation activities

        4. Risk Assessment:
           - Business impact of current technical debt levels
           - Security and compliance risk exposure
           - Operational stability and reliability concerns
           - Development velocity and maintenance cost implications
           - Cloud migration complexity and risk factors

        5. Metrics and Benchmarks:
           - Industry benchmark comparisons where applicable
           - Debt trend analysis and accumulation patterns
           - Remediation ROI estimates and business case data
           - Success metrics for debt reduction initiatives""",
        agent=agents[1],
        context=[identify_components_task],
    )

    map_dependencies_task = create_task(
        description="""Map dependencies between identified components and analyze coupling patterns
        that will influence migration strategies. Perform comprehensive dependency analysis:

        1. Internal Component Dependencies:
           - Direct component-to-component communication patterns
           - Shared database and data store dependencies
           - Shared configuration and environment dependencies
           - Runtime service discovery and registration dependencies
           - Build-time and deployment-time dependencies
           - Shared library and framework dependencies

        2. Data Flow and Integration Analysis:
           - Synchronous communication patterns (REST calls, gRPC, direct DB access)
           - Asynchronous communication patterns (message queues, events, webhooks)
           - Batch data processing and ETL dependencies
           - Real-time data streaming and event processing flows
           - File-based data exchange and shared file system dependencies
           - Database transaction boundaries and consistency requirements

        3. External System Dependencies:
           - Third-party service integrations and API dependencies
           - Legacy system connections and mainframe integrations
           - Cloud service dependencies (AWS, Azure, GCP services)
           - Vendor software and commercial platform dependencies
           - Infrastructure service dependencies (DNS, load balancers, certificates)
           - Monitoring and logging service dependencies

        4. Coupling Pattern Analysis:
           - Tight coupling indicators (shared databases, synchronous calls, shared state)
           - Loose coupling patterns (message queues, event-driven architecture)
           - Temporal coupling (time-dependent interactions, scheduled processes)
           - Data coupling (shared data structures, schemas, formats)
           - Platform coupling (OS-specific, cloud-provider specific dependencies)
           - Implementation coupling (shared libraries, frameworks, languages)

        5. Migration Grouping Analysis:
           - Components that must migrate together due to tight coupling
           - Components that can be migrated independently
           - Dependencies that can be refactored to enable independent migration
           - Integration points requiring special handling (adapters, proxies, gateways)
           - Sequence dependencies for migration wave planning
           - Rollback dependencies and failure isolation boundaries

        Component inventory: {component_inventory}
        Technical debt analysis: {tech_debt_analysis}
        Architecture patterns: {architecture_patterns}
        Network topology data: {network_topology}

        Create comprehensive dependency maps and migration grouping recommendations.""",
        expected_output="""Dependency analysis containing:

        1. Component Dependency Map:
           - Visual representation of component relationships
           - Dependency types and communication protocols
           - Data flow directions and volume characteristics
           - Criticality assessment for each dependency
           - Performance and latency requirements

        2. Coupling Assessment:
           - Tight coupling identification with impact analysis
           - Loose coupling patterns and decoupling opportunities
           - Temporal coupling risks and mitigation strategies
           - Data coupling implications for migration
           - Platform coupling constraints and portability concerns

        3. Migration Grouping Recommendations:
           - Component clusters that should migrate together
           - Independent components suitable for parallel migration
           - Dependencies requiring refactoring before migration
           - Integration points needing special handling
           - Migration sequence recommendations with rationale

        4. Critical Path Analysis:
           - Critical dependencies that could block migration
           - Single points of failure in the dependency graph
           - High-risk integration points requiring careful planning
           - Dependencies with long lead times or complex refactoring needs
           - Bottleneck components affecting multiple migration waves

        5. Refactoring Opportunities:
           - Dependencies that can be eliminated or simplified
           - Integration patterns that can be modernized
           - Shared components that can be extracted as services
           - Data dependencies that can be decoupled
           - Communication patterns that can be made more resilient

        6. Migration Strategy Insights:
           - Strangler pattern opportunities for gradual migration
           - Big bang migration requirements and constraints
           - Hybrid cloud deployment implications
           - Testing and validation requirements for each dependency
           - Rollback strategies and dependency reversal planning""",
        agent=agents[2],
        context=[identify_components_task, analyze_technical_debt_task],
    )

    return [
        identify_components_task,
        analyze_technical_debt_task,
        map_dependencies_task,
    ]


def create_component_analysis_crew_instance(
    agents: List[Agent], tasks: List[Task]
) -> Crew:
    """
    Create the component analysis crew with configured agents and tasks.

    Args:
        agents: List of configured agents
        tasks: List of configured tasks

    Returns:
        Configured Crew instance ready for execution
    """
    if not CREWAI_AVAILABLE:
        logger.error("CrewAI not available, cannot create crew")
        return None  # type: ignore[return-value]

    return create_crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process="sequential",
    )


# Export for backward compatibility
__all__ = [
    "create_component_analysis_tasks",
    "create_component_analysis_crew_instance",
]
