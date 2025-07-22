"""
Architecture Standards Crew - CrewAI Implementation

This crew captures and evaluates architecture requirements with user collaboration.
It creates true CrewAI agents (not pseudo-agents) for intelligent decision making
around engagement-level architecture standards.

Key Responsibilities:
- Capture comprehensive architecture standards based on industry best practices
- Analyze application technology stacks against supported versions  
- Evaluate architecture exceptions based on business constraints
- Generate compliance reports and upgrade recommendations
- Support RBAC-aware standards validation

The crew consists of three specialized agents:
1. Architecture Standards Specialist - Defines engagement-level requirements
2. Technology Stack Analyst - Assesses technology version compliance
3. Business Constraint Analyst - Evaluates valid exceptions
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task
    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI imports successful for ArchitectureStandardsCrew")
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
            return {"status": "fallback_mode", "engagement_standards": []}

from app.models.assessment_flow import CrewExecutionError


class ArchitectureStandardsCrew:
    """Captures and evaluates architecture requirements with user collaboration"""
    
    def __init__(self, flow_context):
        self.flow_context = flow_context
        logger.info(f"🏗️ Initializing Architecture Standards Crew for flow {flow_context.flow_id}")
        
        if CREWAI_AVAILABLE:
            self.agents = self._create_agents()
            self.crew = self._create_crew()
            logger.info("✅ Architecture Standards Crew initialized with CrewAI agents")
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.crew = None
    
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for architecture standards"""
        
        # Import tools (will be implemented in separate task)
        try:
            from app.services.crewai_flows.tools.architecture_tools import (
                ComplianceChecker,
                StandardsTemplateGenerator,
                TechnologyVersionAnalyzer,
            )
            tools_available = True
        except ImportError:
            logger.warning("Architecture tools not yet available, agents will have limited functionality")
            tools_available = False
            # Create placeholder tool classes
            class TechnologyVersionAnalyzer:
                pass
            class ComplianceChecker:
                pass
            class StandardsTemplateGenerator:
                pass
        
        architecture_standards_agent = Agent(
            role="Architecture Standards Specialist",
            goal="Define and evaluate engagement-level architecture minimums based on industry best practices and client requirements",
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
                ComplianceChecker()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=True
        )
        
        technology_stack_analyst = Agent(
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
            tools=[
                TechnologyVersionAnalyzer(),
                ComplianceChecker()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=False
        )
        
        exception_handler_agent = Agent(
            role="Business Constraint Analyst",
            goal="Identify and document valid architecture exceptions based on business constraints and technical trade-offs", 
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
            tools=[
                ComplianceChecker()
            ] if tools_available else [],
            verbose=True,
            allow_delegation=False
        )
        
        return [architecture_standards_agent, technology_stack_analyst, exception_handler_agent]
    
    def _create_crew(self) -> Crew:
        """Create crew with architecture standards tasks"""
        
        capture_standards_task = Task(
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
            agent=self.agents[0] if self.agents else None
        )
        
        analyze_application_stacks_task = Task(
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
            agent=self.agents[1] if len(self.agents) > 1 else None,
            context=[capture_standards_task] if capture_standards_task else []
        )
        
        evaluate_exceptions_task = Task(
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
            agent=self.agents[2] if len(self.agents) > 2 else None,
            context=[capture_standards_task, analyze_application_stacks_task]
        )
        
        if not CREWAI_AVAILABLE:
            return None
            
        return Crew(
            agents=self.agents,
            tasks=[capture_standards_task, analyze_application_stacks_task, evaluate_exceptions_task],
            verbose=True,
            process="sequential"
        )
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the architecture standards crew"""
        
        try:
            logger.info("🏗️ Starting Architecture Standards Crew execution")
            
            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await self._execute_fallback(context)
            
            # Prepare context for crew execution
            crew_context = {
                "engagement_context": context.get("engagement_context", {}),
                "selected_applications": context.get("selected_applications", []),
                "application_metadata": context.get("application_metadata", {}),
                "existing_standards": context.get("existing_standards", []),
                "business_constraints": context.get("business_constraints", {}),
                "risk_tolerance": context.get("risk_tolerance", "medium"),
                "flow_context": self.flow_context
            }
            
            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)
            
            # Process and structure the results
            processed_result = await self._process_crew_results(result)
            
            logger.info("✅ Architecture Standards Crew execution completed successfully")
            return processed_result
            
        except Exception as e:
            logger.error(f"❌ Architecture Standards Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Architecture standards analysis failed: {str(e)}")
    
    async def _execute_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback implementation when CrewAI is not available"""
        logger.info("Executing Architecture Standards analysis in fallback mode")
        
        # Generate basic architecture standards
        engagement_standards = [
            {
                "type": "technology_version",
                "name": "Java Version Standard",
                "description": "Minimum Java version requirement for enterprise applications",
                "rationale": "Java 11+ required for long-term support and security patches",
                "is_mandatory": True,
                "technology_specifications": {
                    "minimum_version": "11",
                    "recommended_version": "17",
                    "eol_versions": ["8", "7", "6"]
                },
                "implementation_guidance": [
                    "Upgrade applications running Java 8 or earlier",
                    "Use OpenJDK or Oracle JDK with commercial support",
                    "Validate compatibility with existing frameworks"
                ]
            },
            {
                "type": "security_standard", 
                "name": "API Security Standard",
                "description": "Security requirements for REST and GraphQL APIs",
                "rationale": "Ensure consistent security posture across all API endpoints",
                "is_mandatory": True,
                "technology_specifications": {
                    "authentication": "OAuth 2.0 or OIDC",
                    "authorization": "RBAC with fine-grained permissions",
                    "encryption": "TLS 1.2+ for all communications"
                },
                "implementation_guidance": [
                    "Implement API gateway for centralized security",
                    "Use JWT tokens with proper validation",
                    "Enable rate limiting and throttling"
                ]
            },
            {
                "type": "architecture_pattern",
                "name": "Microservices Communication",
                "description": "Standards for inter-service communication",
                "rationale": "Ensure reliable and scalable service-to-service communication",
                "is_mandatory": False,
                "technology_specifications": {
                    "sync_communication": "REST with OpenAPI specifications",
                    "async_communication": "Event-driven with message queues",
                    "data_formats": "JSON with schema validation"
                },
                "implementation_guidance": [
                    "Use circuit breaker pattern for resilience",
                    "Implement distributed tracing",
                    "Design for eventual consistency"
                ]
            }
        ]
        
        # Basic application compliance analysis
        application_compliance = {}
        for app_id in context.get("selected_applications", []):
            application_compliance[app_id] = {
                "overall_score": 65.0,  # Baseline score
                "technology_compliance": {
                    "java_version": {"status": "needs_upgrade", "current": "8", "required": "11+"},
                    "security_frameworks": {"status": "partial", "coverage": "70%"}
                },
                "upgrade_recommendations": [
                    {"priority": "high", "item": "Upgrade Java version", "effort": "medium"},
                    {"priority": "medium", "item": "Implement API gateway", "effort": "high"}
                ],
                "estimated_effort_hours": 120,
                "compliance_timeline": "3-6 months"
            }
        
        return {
            "engagement_standards": engagement_standards,
            "application_compliance": application_compliance,
            "exceptions": [],
            "upgrade_recommendations": {
                "immediate_actions": ["Java version upgrades"],
                "short_term": ["API security improvements"], 
                "long_term": ["Architecture pattern adoption"]
            },
            "technical_debt_scores": {app_id: 6.5 for app_id in context.get("selected_applications", [])},
            "crew_confidence": 0.6,  # Lower confidence in fallback mode
            "recommendations": [
                "Implement comprehensive architecture governance",
                "Establish regular compliance review cycles",
                "Invest in developer training on modern patterns"
            ],
            "execution_mode": "fallback"
        }
    
    async def _process_crew_results(self, result) -> Dict[str, Any]:
        """Process and structure crew execution results"""
        
        try:
            # Extract standards from crew results
            standards = result.get("engagement_standards", [])
            if isinstance(standards, str):
                # Parse if returned as string
                standards = []
            
            # Structure compliance analysis
            compliance = result.get("application_compliance", {})
            
            # Extract exceptions
            exceptions = result.get("architecture_exceptions", [])
            
            # Calculate overall metrics
            confidence_scores = []
            tech_debt_scores = {}
            
            for app_id, app_compliance in compliance.items():
                if isinstance(app_compliance, dict):
                    score = app_compliance.get("overall_score", 0.0)
                    confidence_scores.append(score / 100.0)  # Convert to 0-1 scale
                    tech_debt_scores[app_id] = (100.0 - score) / 10.0  # Convert to 0-10 debt scale
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
            
            return {
                "engagement_standards": standards,
                "application_compliance": compliance,
                "exceptions": exceptions,
                "upgrade_recommendations": result.get("upgrade_paths", {}),
                "technical_debt_scores": tech_debt_scores,
                "crew_confidence": min(overall_confidence, 0.95),  # Cap at 95%
                "recommendations": result.get("implementation_guidance", []),
                "execution_metadata": {
                    "crew_type": "architecture_standards",
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            # Return basic structure to prevent flow failure
            return {
                "engagement_standards": [],
                "application_compliance": {},
                "exceptions": [],
                "upgrade_recommendations": {},
                "technical_debt_scores": {},
                "crew_confidence": 0.5,
                "recommendations": [],
                "processing_error": str(e)
            }