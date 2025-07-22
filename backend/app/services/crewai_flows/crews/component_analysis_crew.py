"""
Component Analysis Crew - CrewAI Implementation

This crew identifies application components and analyzes technical debt based on discovered metadata.
It goes beyond traditional 3-tier architecture to identify modern component patterns and provides
detailed technical debt analysis for migration decision making.

Key Responsibilities:
- Identify components beyond traditional frontend/middleware/backend patterns
- Analyze technical debt from Discovery flow metadata
- Map dependencies and coupling patterns between components
- Assess migration complexity and modernization opportunities
- Generate component-level insights for 6R strategy determination

The crew consists of three specialized agents:
1. Component Architecture Analyst - Identifies all types of components
2. Technical Debt Assessment Specialist - Analyzes debt from metadata
3. Dependency Analysis Expert - Maps component relationships and coupling
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task
    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI imports successful for ComponentAnalysisCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False
    
    # Fallback classes
    class Agent:
        def __init__(self, **kwargs):
            self.role = kwargs.get('role', '')
            self.goal = kwargs.get('goal', '')
            self.backstory = kwargs.get('backstory', '')
    
    class Task:
        def __init__(self, **kwargs):
            self.description = kwargs.get('description', '')
            self.expected_output = kwargs.get('expected_output', '')
    
    class Crew:
        def __init__(self, **kwargs):
            self.agents = kwargs.get('agents', [])
            self.tasks = kwargs.get('tasks', [])
        
        def kickoff(self, inputs=None):
            return {"status": "fallback_mode", "components": [], "tech_debt_analysis": []}

from app.models.assessment_flow import ComponentType, CrewExecutionError, TechDebtSeverity


class ComponentAnalysisCrew:
    """Identifies components and analyzes technical debt based on discovered metadata"""
    
    def __init__(self, flow_context):
        self.flow_context = flow_context
        logger.info(f"🔍 Initializing Component Analysis Crew for flow {flow_context.flow_id}")
        
        if CREWAI_AVAILABLE:
            self.agents = self._create_agents()
            self.crew = self._create_crew()
            logger.info("✅ Component Analysis Crew initialized with CrewAI agents")
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.crew = None
    
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for component analysis"""
        
        # Import tools (will be implemented in separate task)
        try:
            from app.services.crewai_flows.tools.component_tools import (
                ComponentDiscoveryTool,
                DependencyMapper,
                MetadataAnalyzer,
                TechDebtCalculator,
            )
            tools_available = True
        except ImportError:
            logger.warning("Component analysis tools not yet available, agents will have limited functionality")
            tools_available = False
            # Create placeholder tool classes
            class ComponentDiscoveryTool:
                pass
            class MetadataAnalyzer:
                pass
            class DependencyMapper:
                pass
            class TechDebtCalculator:
                pass
        
        component_discovery_agent = Agent(
            role="Component Architecture Analyst",
            goal="Identify and catalog all application components beyond traditional 3-tier architecture",
            backstory="""You are a modern application architecture expert specializing in component 
            identification across diverse architectural patterns. You have deep expertise in monolithic, 
            microservices, serverless, and hybrid architectures developed over 12+ years of hands-on experience.
            
            Your expertise spans:
            - Modern web architectures (SPA, PWA, JAMstack, micro-frontends)
            - Service-oriented and microservices architectures
            - Event-driven and message-based systems
            - Serverless and Function-as-a-Service patterns
            - Container-based and cloud-native architectures
            - Legacy mainframe and client-server systems
            - Data pipelines and analytics platforms
            
            You can identify UI components, API layers, business services, data access layers, 
            background workers, integration components, and infrastructure services from application 
            metadata and discovery data. You understand how different deployment patterns affect 
            component identification and can distinguish between logical and physical components.
            
            You excel at recognizing architectural evolution patterns where monolithic applications
            have been partially decomposed or where microservices have been aggregated for efficiency.""",
            tools=[
                ComponentDiscoveryTool(),
                MetadataAnalyzer()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=True
        )
        
        metadata_analyst_agent = Agent(
            role="Technical Debt Assessment Specialist",
            goal="Analyze technical debt from discovered application metadata and identify modernization opportunities",
            backstory="""You are a technical debt analysis expert with extensive experience in code 
            quality assessment, architecture evaluation, and modernization planning. Over 10+ years,
            you have developed expertise in identifying technical debt patterns from various sources
            including static analysis, runtime metrics, deployment artifacts, and architectural metadata.
            
            Your specializations include:
            - Code quality analysis and technical debt quantification
            - Security vulnerability assessment and remediation planning
            - Performance bottleneck identification and optimization
            - Architecture anti-pattern detection and refactoring strategies
            - Technology obsolescence tracking and upgrade planning
            - Dependency analysis and library management
            - Infrastructure debt and cloud readiness assessment
            
            You excel at quantifying technical debt and prioritizing remediation efforts based on
            business impact, migration complexity, and risk factors. You can identify technical debt
            from metadata such as technology versions, dependency structures, code metrics, deployment
            patterns, and architectural decisions. You understand the relationship between technical
            debt and migration strategy selection.""",
            tools=[
                MetadataAnalyzer(),
                TechDebtCalculator()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=False
        )
        
        dependency_mapper_agent = Agent(
            role="Dependency Analysis Expert",
            goal="Map component dependencies and identify coupling patterns for migration grouping",
            backstory="""You are a systems integration specialist with expertise in dependency analysis 
            and coupling assessment developed over 15+ years working with complex enterprise systems.
            You understand how components interact across different architectural patterns and technology
            stacks, from monolithic applications to distributed microservices ecosystems.
            
            Your expertise includes:
            - Dependency graph analysis and visualization
            - Coupling pattern identification (tight, loose, temporal, data)
            - Integration pattern analysis (synchronous, asynchronous, batch)
            - Data flow mapping and consistency boundary identification
            - Network topology and communication protocol analysis
            - Service mesh and API gateway integration patterns
            - Legacy system integration and wrapper pattern identification
            
            You excel at creating dependency maps that inform migration wave planning and component
            treatment decisions. You can identify which components must move together, which dependencies
            can be refactored for independent migration, and which integration points require special
            handling during cloud migration. You understand the difference between compile-time,
            runtime, and deployment dependencies and their impact on migration sequencing.""",
            tools=[
                DependencyMapper(),
                ComponentDiscoveryTool()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=False
        )
        
        return [component_discovery_agent, metadata_analyst_agent, dependency_mapper_agent]
    
    def _create_crew(self) -> Crew:
        """Create crew with component analysis tasks"""
        
        identify_components_task = Task(
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
            agent=self.agents[0] if self.agents else None
        )
        
        analyze_technical_debt_task = Task(
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
            agent=self.agents[1] if len(self.agents) > 1 else None,
            context=[identify_components_task] if identify_components_task else []
        )
        
        map_dependencies_task = Task(
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
            agent=self.agents[2] if len(self.agents) > 2 else None,
            context=[identify_components_task, analyze_technical_debt_task]
        )
        
        if not CREWAI_AVAILABLE:
            return None
            
        return Crew(
            agents=self.agents,
            tasks=[identify_components_task, analyze_technical_debt_task, map_dependencies_task],
            verbose=True,
            process="sequential"
        )
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the component analysis crew"""
        
        try:
            logger.info(f"🔍 Starting Component Analysis Crew for application {context.get('application_id')}")
            
            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await self._execute_fallback(context)
            
            # Prepare context for crew execution
            crew_context = {
                "application_metadata": context.get("application_metadata", {}),
                "discovery_data": context.get("discovery_data", {}),
                "architecture_context": context.get("architecture_standards", []),
                "architecture_standards": context.get("architecture_standards", []),
                "technology_lifecycle": context.get("technology_lifecycle", {}),
                "security_requirements": context.get("security_requirements", {}),
                "architecture_patterns": context.get("architecture_patterns", {}),
                "network_topology": context.get("network_topology", {}),
                "flow_context": self.flow_context
            }
            
            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)
            
            # Process and structure the results
            processed_result = await self._process_crew_results(result, context["application_id"])
            
            logger.info(f"✅ Component Analysis Crew completed for application {context.get('application_id')}")
            return processed_result
            
        except Exception as e:
            logger.error(f"❌ Component Analysis Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Component analysis failed: {str(e)}")
    
    async def _execute_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback implementation when CrewAI is not available"""
        app_id = context.get("application_id", "unknown")
        logger.info(f"Executing Component Analysis in fallback mode for {app_id}")
        
        # Generate basic component identification
        components = [
            {
                "name": "web_frontend",
                "type": ComponentType.WEB_FRONTEND.value,
                "technology_stack": {"framework": "React", "language": "JavaScript"},
                "responsibilities": ["User interface", "Client-side logic"],
                "complexity_score": 6.0,
                "business_value_score": 8.0
            },
            {
                "name": "api_service",
                "type": ComponentType.REST_API.value,
                "technology_stack": {"framework": "Spring Boot", "language": "Java"},
                "responsibilities": ["Business logic", "Data access"],
                "complexity_score": 7.0,
                "business_value_score": 9.0
            },
            {
                "name": "database",
                "type": ComponentType.RELATIONAL_DATABASE.value,
                "technology_stack": {"database": "PostgreSQL", "version": "12"},
                "responsibilities": ["Data persistence", "Transaction management"],
                "complexity_score": 5.0,
                "business_value_score": 9.0
            }
        ]
        
        # Generate basic technical debt analysis
        tech_debt_analysis = [
            {
                "category": "technology",
                "subcategory": "version_obsolescence",
                "title": "Outdated Java Version",
                "description": "Application running on Java 8, which is end-of-life",
                "severity": TechDebtSeverity.HIGH.value,
                "tech_debt_score": 7.5,
                "component": "api_service",
                "remediation_effort_hours": 40,
                "impact_on_migration": "high"
            },
            {
                "category": "architecture",
                "subcategory": "coupling",
                "title": "Tight Database Coupling",
                "description": "Frontend directly accesses database without API layer",
                "severity": TechDebtSeverity.MEDIUM.value,
                "tech_debt_score": 6.0,
                "component": "web_frontend",
                "remediation_effort_hours": 80,
                "impact_on_migration": "medium"
            },
            {
                "category": "security",
                "subcategory": "authentication",
                "title": "Legacy Authentication",
                "description": "Using outdated authentication mechanism",
                "severity": TechDebtSeverity.HIGH.value,
                "tech_debt_score": 8.0,
                "component": "api_service",
                "remediation_effort_hours": 60,
                "impact_on_migration": "high"
            }
        ]
        
        # Generate component scores
        component_scores = {
            "web_frontend": 6.0,
            "api_service": 7.2,
            "database": 5.0
        }
        
        # Generate dependency map
        dependency_map = {
            "internal_dependencies": [
                {"from": "web_frontend", "to": "api_service", "type": "REST", "coupling": "loose"},
                {"from": "api_service", "to": "database", "type": "JDBC", "coupling": "tight"}
            ],
            "external_dependencies": [],
            "migration_groups": [
                {
                    "group_id": "core_backend",
                    "components": ["api_service", "database"],
                    "rationale": "Tight coupling requires joint migration"
                },
                {
                    "group_id": "frontend",
                    "components": ["web_frontend"],
                    "rationale": "Can be migrated independently"
                }
            ]
        }
        
        return {
            "components": components,
            "tech_debt_analysis": tech_debt_analysis,
            "component_scores": component_scores,
            "dependency_map": dependency_map,
            "migration_groups": dependency_map["migration_groups"],
            "crew_confidence": 0.6,  # Lower confidence in fallback mode
            "analysis_insights": [
                "Application follows traditional 3-tier architecture",
                "High technical debt in technology versions",
                "Modernization opportunities in authentication and API design"
            ],
            "execution_mode": "fallback"
        }
    
    async def _process_crew_results(self, result, application_id: str) -> Dict[str, Any]:
        """Process and structure crew execution results"""
        
        try:
            # Extract components from crew results
            components_data = result.get("component_inventory", [])
            
            # Structure components for flow state
            structured_components = []
            for component in components_data:
                structured_components.append({
                    "name": component.get("name", "unknown"),
                    "type": component.get("type", ComponentType.CUSTOM.value),
                    "technology_stack": component.get("technology_stack", {}),
                    "responsibilities": component.get("responsibilities", []),
                    "complexity_score": component.get("complexity_score", 5.0),
                    "business_value_score": component.get("business_value_score", 5.0),
                    "dependencies": component.get("dependencies", [])
                })
            
            # Extract and structure technical debt analysis
            tech_debt_data = result.get("tech_debt_analysis", [])
            structured_tech_debt = []
            component_scores = {}
            
            for debt_item in tech_debt_data:
                structured_tech_debt.append({
                    "category": debt_item.get("category", "unknown"),
                    "subcategory": debt_item.get("subcategory", ""),
                    "title": debt_item.get("title", ""),
                    "description": debt_item.get("description", ""),
                    "severity": debt_item.get("severity", TechDebtSeverity.MEDIUM.value),
                    "tech_debt_score": debt_item.get("tech_debt_score", 5.0),
                    "component": debt_item.get("component", ""),
                    "remediation_effort_hours": debt_item.get("remediation_effort_hours", 0),
                    "impact_on_migration": debt_item.get("impact_on_migration", "medium"),
                    "detected_by_agent": "component_analysis_crew",
                    "agent_confidence": debt_item.get("confidence", 0.8)
                })
                
                # Track component-level scores
                component_name = debt_item.get("component")
                if component_name:
                    component_scores[component_name] = debt_item.get("tech_debt_score", 5.0)
            
            # Calculate average scores for components without explicit scores
            for component in structured_components:
                if component["name"] not in component_scores:
                    component_scores[component["name"]] = component.get("complexity_score", 5.0)
            
            return {
                "components": structured_components,
                "tech_debt_analysis": structured_tech_debt,
                "component_scores": component_scores,
                "dependency_map": result.get("dependency_map", {}),
                "migration_groups": result.get("migration_grouping", []),
                "crew_confidence": result.get("confidence_score", 0.8),
                "analysis_insights": result.get("analysis_insights", []),
                "execution_metadata": {
                    "crew_type": "component_analysis",
                    "application_id": application_id,
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            # Return basic structure to prevent flow failure
            return {
                "components": [],
                "tech_debt_analysis": [],
                "component_scores": {},
                "dependency_map": {},
                "migration_groups": [],
                "crew_confidence": 0.5,
                "analysis_insights": [],
                "processing_error": str(e)
            }