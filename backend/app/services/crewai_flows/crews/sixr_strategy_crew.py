"""
Six R Strategy Crew - CrewAI Implementation

This crew determines component-level 6R strategies with validation and compatibility checking.
It analyzes each component's characteristics, technical debt, and business context to recommend
the optimal migration strategy (Rewrite, ReArchitect, Refactor, Replatform, Rehost, Retire).

Key Responsibilities:
- Determine optimal 6R strategy for each application component
- Validate compatibility between component treatments within applications
- Generate move group hints for Planning Flow wave coordination
- Assess business value, effort, and risk factors for each strategy
- Provide confidence scoring and detailed rationale for decisions

The crew consists of three specialized agents:
1. Component Modernization Strategist - Determines optimal 6R strategy per component
2. Architecture Compatibility Validator - Validates treatment compatibility
3. Migration Wave Planning Advisor - Provides move group hints for Planning Flow
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI imports successful for SixRStrategyCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Agent:
        def __init__(self, **kwargs):
            self.role = kwargs.get("role", "")
            self.goal = kwargs.get("goal", "")
            self.backstory = kwargs.get("backstory", "")

    class Task:
        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")

    class Crew:
        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])

        def kickoff(self, inputs=None):
            return {
                "status": "fallback_mode",
                "component_treatments": [],
                "overall_strategy": "replatform",
            }


from app.models.assessment_flow import CrewExecutionError
from app.models.asset import SixRStrategy


class SixRStrategyCrew:
    """Determines component-level 6R strategies with validation"""

    def __init__(self, flow_context):
        self.flow_context = flow_context
        logger.info(
            f"📋 Initializing Six R Strategy Crew for flow {flow_context.flow_id}"
        )

        if CREWAI_AVAILABLE:
            self.agents = self._create_agents()
            self.crew = self._create_crew()
            logger.info("✅ Six R Strategy Crew initialized with CrewAI agents")
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.crew = None

    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for 6R strategy determination"""

        # Import tools (will be implemented in separate task)
        try:
            from app.services.crewai_flows.tools.sixr_tools import (
                BusinessValueCalculator,
                CompatibilityChecker,
                ComponentAnalyzer,
                DependencyOptimizer,
                IntegrationAnalyzer,
                MoveGroupAnalyzer,
                SixRDecisionEngine,
            )

            tools_available = True
        except ImportError:
            logger.warning(
                "Six R strategy tools not yet available, agents will have limited functionality"
            )
            tools_available = False

            # Create placeholder tool classes
            class SixRDecisionEngine:
                pass

            class ComponentAnalyzer:
                pass

            class BusinessValueCalculator:
                pass

            class CompatibilityChecker:
                pass

            class IntegrationAnalyzer:
                pass

            class MoveGroupAnalyzer:
                pass

            class DependencyOptimizer:
                pass

        component_strategy_expert = Agent(
            role="Component Modernization Strategist",
            goal="Determine optimal 6R strategy for each application component based on technical characteristics and business constraints",
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
                [SixRDecisionEngine(), ComponentAnalyzer(), BusinessValueCalculator()]
                if tools_available
                else []
            ),
            verbose=True,
            allow_delegation=True,
        )

        compatibility_validator = Agent(
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
                [CompatibilityChecker(), IntegrationAnalyzer()]
                if tools_available
                else []
            ),
            verbose=True,
            allow_delegation=False,
        )

        move_group_advisor = Agent(
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
            tools=(
                [MoveGroupAnalyzer(), DependencyOptimizer()] if tools_available else []
            ),
            verbose=True,
            allow_delegation=False,
        )

        return [component_strategy_expert, compatibility_validator, move_group_advisor]

    def _create_crew(self) -> Crew:
        """Create crew with 6R strategy tasks"""

        determine_component_strategies_task = Task(
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
            agent=self.agents[0] if self.agents else None,
        )

        validate_component_compatibility_task = Task(
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
            agent=self.agents[1] if len(self.agents) > 1 else None,
            context=[determine_component_strategies_task],
        )

        generate_move_group_hints_task = Task(
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
            agent=self.agents[2] if len(self.agents) > 2 else None,
            context=[
                determine_component_strategies_task,
                validate_component_compatibility_task,
            ],
        )

        if not CREWAI_AVAILABLE:
            return None

        return Crew(
            agents=self.agents,
            tasks=[
                determine_component_strategies_task,
                validate_component_compatibility_task,
                generate_move_group_hints_task,
            ],
            verbose=True,
            process="sequential",
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the six R strategy crew"""

        try:
            logger.info(
                f"📋 Starting Six R Strategy Crew for application {context.get('application_id')}"
            )

            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await self._execute_fallback(context)

            # Prepare context for crew execution
            crew_context = {
                "components": context.get("components", []),
                "tech_debt_analysis": context.get("tech_debt_analysis", []),
                "architecture_standards": context.get("architecture_standards", []),
                "business_context": context.get("business_context", {}),
                "resource_constraints": context.get("resource_constraints", {}),
                "application_architecture": context.get("application_architecture", {}),
                "integration_patterns": context.get("integration_patterns", {}),
                "application_dependencies": context.get("application_dependencies", {}),
                "business_priorities": context.get("business_priorities", {}),
                "flow_context": self.flow_context,
            }

            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)

            # Process and structure the results
            processed_result = await self._process_crew_results(
                result, context["application_id"]
            )

            logger.info(
                f"✅ Six R Strategy Crew completed for application {context.get('application_id')}"
            )
            return processed_result

        except Exception as e:
            logger.error(f"❌ Six R Strategy Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Six R strategy determination failed: {str(e)}")

    async def _execute_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback implementation when CrewAI is not available"""
        app_id = context.get("application_id", "unknown")
        components = context.get("components", [])
        context.get("tech_debt_analysis", [])

        logger.info(f"Executing Six R Strategy analysis in fallback mode for {app_id}")

        # Generate component treatments based on simple heuristics
        component_treatments = []
        for component in components:
            component_name = component.get("name", "unknown")
            component_type = component.get("type", "unknown")
            complexity_score = component.get("complexity_score", 5.0)

            # Simple strategy selection based on complexity and type
            if complexity_score >= 8.0:
                strategy = SixRStrategy.REWRITE.value
                confidence = 0.7
                rationale = "High complexity suggests rewrite for modernization"
            elif complexity_score >= 6.0:
                strategy = SixRStrategy.REFACTOR.value
                confidence = 0.8
                rationale = "Moderate complexity suitable for refactoring"
            else:
                strategy = SixRStrategy.REPLATFORM.value
                confidence = 0.75
                rationale = "Low complexity suitable for replatforming"

            # Adjust for component type
            if "database" in component_type.lower():
                strategy = SixRStrategy.REHOST.value
                rationale = (
                    "Database components typically rehosted with minimal changes"
                )
            elif "frontend" in component_type.lower():
                strategy = SixRStrategy.REFACTOR.value
                rationale = "Frontend components benefit from modernization"

            component_treatments.append(
                {
                    "component_name": component_name,
                    "component_type": component_type,
                    "strategy": strategy,
                    "confidence": confidence,
                    "rationale": rationale,
                    "effort_estimate_hours": int(complexity_score * 20),
                    "risk_factors": ["Limited analysis in fallback mode"],
                    "business_benefits": [
                        "Cloud cost optimization",
                        "Improved maintainability",
                    ],
                }
            )

        # Determine overall strategy (most common component strategy)
        strategy_counts = {}
        for treatment in component_treatments:
            strategy = treatment["strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        overall_strategy = (
            max(strategy_counts, key=strategy_counts.get)
            if strategy_counts
            else SixRStrategy.REPLATFORM.value
        )

        # Calculate overall confidence
        confidence_scores = [t["confidence"] for t in component_treatments]
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.6
        )

        # Generate move group hints
        move_group_hints = [
            {
                "group_type": "technology_affinity",
                "group_name": f"{app_id}_components",
                "applications": [app_id],
                "rationale": "Components within same application should migrate together",
                "priority": "medium",
                "estimated_effort": sum(
                    t["effort_estimate_hours"] for t in component_treatments
                ),
            }
        ]

        return {
            "component_treatments": component_treatments,
            "overall_strategy": overall_strategy,
            "confidence_score": overall_confidence,
            "rationale": f"Application assessment recommends {overall_strategy} approach based on component analysis",
            "move_group_hints": move_group_hints,
            "compatibility_issues": [],  # No detailed analysis in fallback mode
            "crew_confidence": 0.6,  # Lower confidence in fallback mode
            "execution_mode": "fallback",
        }

    async def _process_crew_results(
        self, result, application_id: str
    ) -> Dict[str, Any]:
        """Process and structure crew execution results"""

        try:
            # Extract component treatments
            component_treatments = result.get("component_treatments", [])

            # Structure treatments for consistency
            structured_treatments = []
            for treatment in component_treatments:
                structured_treatments.append(
                    {
                        "component_name": treatment.get("component_name", ""),
                        "component_type": treatment.get("component_type", ""),
                        "strategy": treatment.get(
                            "strategy", SixRStrategy.REPLATFORM.value
                        ),
                        "confidence": treatment.get("confidence", 0.7),
                        "rationale": treatment.get("rationale", ""),
                        "effort_estimate_hours": treatment.get(
                            "effort_estimate_hours", 0
                        ),
                        "risk_factors": treatment.get("risk_factors", []),
                        "business_benefits": treatment.get("business_benefits", []),
                        "technical_benefits": treatment.get("technical_benefits", []),
                    }
                )

            # Extract overall strategy and confidence
            overall_strategy = result.get(
                "overall_strategy", SixRStrategy.REPLATFORM.value
            )
            confidence_score = result.get("confidence_score", 0.7)
            rationale = result.get("rationale", "Strategy determined by crew analysis")

            # Extract move group hints
            move_group_hints = result.get("move_group_hints", [])

            # Extract compatibility issues
            compatibility_issues = result.get("compatibility_issues", [])

            return {
                "component_treatments": structured_treatments,
                "overall_strategy": overall_strategy,
                "confidence_score": confidence_score,
                "rationale": rationale,
                "move_group_hints": move_group_hints,
                "compatibility_issues": compatibility_issues,
                "crew_confidence": result.get("crew_confidence", 0.8),
                "execution_metadata": {
                    "crew_type": "sixr_strategy",
                    "application_id": application_id,
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id,
                },
            }

        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            # Return basic structure to prevent flow failure
            return {
                "component_treatments": [],
                "overall_strategy": SixRStrategy.REPLATFORM.value,
                "confidence_score": 0.5,
                "rationale": "Error processing crew results",
                "move_group_hints": [],
                "compatibility_issues": [],
                "crew_confidence": 0.5,
                "processing_error": str(e),
            }
