# Assessment Flow - Backend & CrewAI Tasks

## Overview
This document tracks all backend logic, CrewAI agent implementations, and flow orchestration tasks for the Assessment Flow implementation.

## Key Implementation Context
- **UnifiedAssessmentFlow** with @start/@listen decorators following Discovery patterns
- **True CrewAI agents** (not pseudo-agents) for intelligent decision making
- **Component-level analysis** with flexible architecture support beyond 3-tier
- **Pause/resume at each node** for user input and collaboration
- **PostgreSQL-only state management** with FlowStateManager integration

---

## 🐍 Backend Core Tasks

### BE-001: Create UnifiedAssessmentFlow Implementation
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 16 hours  
**Dependencies**: Database Foundation (DB-001, FOUND-001, FOUND-002)  
**Sprint**: Backend Week 3-4  

**Description**: Implement the main CrewAI Flow class for assessment orchestration with pause/resume capabilities and state management

**Location**: `backend/app/services/crewai_flows/unified_assessment_flow.py`

**Technical Requirements**:
- CrewAI Flow inheritance with proper @start/@listen decorators
- Integration with FlowStateManager and PostgresStore patterns
- Pause/resume functionality at each node for user interaction
- Multi-tenant context preservation throughout flow execution
- Agent coordination and result aggregation

**Flow Implementation Structure**:
```python
from crewai import Flow
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.services.crewai_flows.persistence.postgres_store import PostgresStore
from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository

class UnifiedAssessmentFlow(Flow[AssessmentFlowState]):
    """
    Unified CrewAI Flow for assessing applications and determining component-level 6R strategies.
    Follows the same patterns as UnifiedDiscoveryFlow with PostgreSQL-only persistence.
    """
    
    def __init__(self, crewai_service: CrewAIService, context: FlowContext):
        super().__init__()
        self.crewai_service = crewai_service
        self.context = context
        self.state_manager = FlowStateManager(context.flow_id)
        self.postgres_store = PostgresStore(context.flow_id)
        self.repository = AssessmentFlowRepository(
            context.db_session, 
            context.client_account_id
        )
        
    @start()
    def initialize_assessment(self) -> AssessmentFlowState:
        """
        Initialize flow with selected applications from inventory
        """
        logger.info(f"Initializing assessment flow {self.context.flow_id}")
        
        try:
            # Load selected applications marked "ready for assessment" 
            applications = await self._load_selected_applications()
            
            # Create initial flow state
            initial_state = AssessmentFlowState(
                flow_id=self.context.flow_id,
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                selected_application_ids=applications,
                current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
                next_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
                status="initialized",
                progress=10,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Persist initial state
            await self.postgres_store.save_flow_state(initial_state)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "architecture_minimums",
                "architecture_minimums",
                10
            )
            
            logger.info(f"Assessment flow initialized with {len(applications)} applications")
            return initial_state
            
        except Exception as e:
            logger.error(f"Failed to initialize assessment flow: {str(e)}")
            raise AssessmentFlowError(f"Initialization failed: {str(e)}")
    
    @listen(initialize_assessment)
    def capture_architecture_minimums(self, init_result: AssessmentFlowState) -> AssessmentFlowState:
        """
        Capture and verify architecture requirements at multiple levels
        """
        logger.info("Starting architecture minimums capture phase")
        
        try:
            # Load engagement-level standards (if they exist)
            engagement_standards = await self._load_engagement_standards()
            
            # Initialize with default standards if none exist
            if not engagement_standards:
                engagement_standards = await self._initialize_default_standards()
            
            # Update flow state with architecture standards
            init_result.engagement_architecture_standards = engagement_standards
            init_result.current_phase = AssessmentPhase.ARCHITECTURE_MINIMUMS
            init_result.progress = 20
            
            # Add pause point for user input
            init_result.pause_points.append("architecture_minimums")
            init_result.status = "paused_for_user_input"
            
            # Persist state with pause
            await self.postgres_store.save_flow_state(init_result)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "architecture_minimums",
                "tech_debt_analysis",
                20
            )
            
            logger.info("Architecture minimums phase completed - paused for user input")
            return init_result
            
        except Exception as e:
            logger.error(f"Architecture minimums capture failed: {str(e)}")
            raise AssessmentFlowError(f"Architecture capture failed: {str(e)}")
    
    @listen(capture_architecture_minimums)
    def analyze_technical_debt(self, arch_result: AssessmentFlowState) -> AssessmentFlowState:
        """
        Analyze tech debt for selected applications and identify components
        """
        logger.info("Starting technical debt analysis phase")
        
        try:
            # Get user input from previous phase
            user_arch_input = arch_result.user_inputs.get("architecture_minimums", {})
            
            # Update architecture standards with user modifications
            if user_arch_input:
                await self._apply_architecture_modifications(arch_result, user_arch_input)
            
            # Invoke Component Analysis Crew for each application
            for app_id in arch_result.selected_application_ids:
                logger.info(f"Analyzing tech debt for application {app_id}")
                
                # Get application metadata from Discovery
                app_metadata = await self._get_application_metadata(app_id)
                
                # Run Component Analysis Crew
                crew_result = await self.crewai_service.run_crew(
                    "component_analysis_crew",
                    context={
                        "application_id": app_id,
                        "application_metadata": app_metadata,
                        "architecture_standards": arch_result.engagement_architecture_standards,
                        "flow_context": self.context
                    }
                )
                
                # Process crew results
                components = crew_result.get("components", [])
                tech_debt_items = crew_result.get("tech_debt_analysis", [])
                tech_debt_scores = crew_result.get("component_scores", {})
                
                # Store results in flow state
                arch_result.application_components[app_id] = components
                arch_result.tech_debt_analysis[app_id] = tech_debt_items
                arch_result.component_tech_debt[app_id] = tech_debt_scores
                
                # Save components to database
                await self.repository.save_application_components(
                    self.context.flow_id, app_id, components
                )
            
            # Update flow progress and add pause point
            arch_result.current_phase = AssessmentPhase.TECH_DEBT_ANALYSIS
            arch_result.progress = 50
            arch_result.pause_points.append("tech_debt_analysis")
            arch_result.status = "paused_for_user_input"
            
            # Persist updated state
            await self.postgres_store.save_flow_state(arch_result)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "tech_debt_analysis", 
                "component_sixr_strategies",
                50
            )
            
            logger.info("Technical debt analysis completed - paused for user input")
            return arch_result
            
        except Exception as e:
            logger.error(f"Technical debt analysis failed: {str(e)}")
            raise AssessmentFlowError(f"Tech debt analysis failed: {str(e)}")
    
    @listen(analyze_technical_debt)
    def determine_component_sixr_strategies(self, tech_debt_result: AssessmentFlowState) -> AssessmentFlowState:
        """
        Determine 6R treatment for each application component
        """
        logger.info("Starting component 6R strategy determination")
        
        try:
            # Get user input from tech debt phase
            user_tech_debt_input = tech_debt_result.user_inputs.get("tech_debt_analysis", {})
            
            # Apply any user modifications to tech debt analysis
            if user_tech_debt_input:
                await self._apply_tech_debt_modifications(tech_debt_result, user_tech_debt_input)
            
            # Run Six R Strategy Crew for each application
            for app_id in tech_debt_result.selected_application_ids:
                logger.info(f"Determining 6R strategies for application {app_id}")
                
                app_components = tech_debt_result.application_components.get(app_id, [])
                tech_debt_analysis = tech_debt_result.tech_debt_analysis.get(app_id, [])
                arch_standards = tech_debt_result.engagement_architecture_standards
                
                # Run Six R Strategy Crew
                crew_result = await self.crewai_service.run_crew(
                    "sixr_strategy_crew",
                    context={
                        "application_id": app_id,
                        "components": app_components,
                        "tech_debt_analysis": tech_debt_analysis,
                        "architecture_standards": arch_standards,
                        "flow_context": self.context
                    }
                )
                
                # Process crew results
                component_treatments = crew_result.get("component_treatments", [])
                overall_strategy = crew_result.get("overall_strategy")
                confidence_score = crew_result.get("confidence_score", 0.0)
                rationale = crew_result.get("rationale", "")
                move_group_hints = crew_result.get("move_group_hints", [])
                
                # Create SixR decision
                sixr_decision = SixRDecision(
                    application_id=app_id,
                    application_name=await self._get_application_name(app_id),
                    component_treatments=component_treatments,
                    overall_strategy=overall_strategy,
                    confidence_score=confidence_score,
                    rationale=rationale,
                    move_group_hints=move_group_hints,
                    tech_debt_score=self._calculate_overall_tech_debt_score(app_id, tech_debt_result),
                    architecture_exceptions=self._get_architecture_exceptions(app_id, tech_debt_result)
                )
                
                # Validate component compatibility
                compatibility_issues = tech_debt_result.validate_component_compatibility(app_id)
                if compatibility_issues:
                    sixr_decision.risk_factors.extend(compatibility_issues)
                
                # Store decision in flow state
                tech_debt_result.sixr_decisions[app_id] = sixr_decision
                
                # Save decision to database
                await self.repository.save_sixr_decision(
                    self.context.flow_id, sixr_decision
                )
            
            # Update flow progress and add pause point
            tech_debt_result.current_phase = AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            tech_debt_result.progress = 75
            tech_debt_result.pause_points.append("component_sixr_strategies")
            tech_debt_result.status = "paused_for_user_input"
            
            # Persist updated state
            await self.postgres_store.save_flow_state(tech_debt_result)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "component_sixr_strategies",
                "app_on_page_generation", 
                75
            )
            
            logger.info("Component 6R strategies determined - paused for user input")
            return tech_debt_result
            
        except Exception as e:
            logger.error(f"6R strategy determination failed: {str(e)}")
            raise AssessmentFlowError(f"6R strategy determination failed: {str(e)}")
    
    @listen(determine_component_sixr_strategies)
    def generate_app_on_page(self, strategies_result: AssessmentFlowState) -> AssessmentFlowState:
        """
        Generate comprehensive "App on a page" view
        """
        logger.info("Starting app on a page generation")
        
        try:
            # Get user input from 6R strategies phase
            user_sixr_input = strategies_result.user_inputs.get("component_sixr_strategies", {})
            
            # Apply any user modifications to 6R decisions
            if user_sixr_input:
                await self._apply_sixr_modifications(strategies_result, user_sixr_input)
            
            # Generate app on a page for each application
            for app_id in strategies_result.selected_application_ids:
                logger.info(f"Generating app on a page for application {app_id}")
                
                decision = strategies_result.sixr_decisions[app_id]
                
                # Consolidate all application data
                app_on_page_data = await self._generate_app_on_page_data(
                    app_id, strategies_result, decision
                )
                
                # Update decision with app on a page data
                decision.app_on_page_data = app_on_page_data
                
                # Save updated decision
                await self.repository.save_sixr_decision(
                    self.context.flow_id, decision
                )
            
            # Update flow progress and add pause point
            strategies_result.current_phase = AssessmentPhase.APP_ON_PAGE_GENERATION
            strategies_result.progress = 90
            strategies_result.pause_points.append("app_on_page_generation")
            strategies_result.status = "paused_for_user_input"
            
            # Persist updated state
            await self.postgres_store.save_flow_state(strategies_result)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "app_on_page_generation",
                "finalization",
                90
            )
            
            logger.info("App on a page generation completed - paused for user input")
            return strategies_result
            
        except Exception as e:
            logger.error(f"App on a page generation failed: {str(e)}")
            raise AssessmentFlowError(f"App on a page generation failed: {str(e)}")
    
    @listen(generate_app_on_page)
    def finalize_assessment(self, review_result: AssessmentFlowState) -> AssessmentFlowState:
        """
        Finalize and persist 6R decisions
        """
        logger.info("Starting assessment finalization")
        
        try:
            # Get user input from app on a page phase
            user_final_input = review_result.user_inputs.get("app_on_page_generation", {})
            
            # Apply any final user modifications
            if user_final_input:
                await self._apply_final_modifications(review_result, user_final_input)
            
            # Determine which apps are ready for planning
            apps_ready = []
            for app_id, decision in review_result.sixr_decisions.items():
                # Apps are ready if they have confident decisions and no critical issues
                if (decision.confidence_score >= 0.7 and 
                    not any("critical" in str(risk).lower() for risk in decision.risk_factors)):
                    apps_ready.append(app_id)
            
            # Mark apps as ready for planning
            if apps_ready:
                await self.repository.mark_apps_ready_for_planning(
                    self.context.flow_id, apps_ready
                )
                review_result.apps_ready_for_planning = apps_ready
            
            # Update flow to completed status
            review_result.current_phase = AssessmentPhase.FINALIZATION
            review_result.status = "completed"
            review_result.progress = 100
            review_result.completed_at = datetime.utcnow()
            
            # Persist final state
            await self.postgres_store.save_flow_state(review_result)
            await self.repository.update_flow_phase(
                self.context.flow_id,
                "finalization",
                None,
                100
            )
            
            # Generate assessment summary
            summary = await self._generate_assessment_summary(review_result)
            review_result.phase_results["final_summary"] = summary
            
            logger.info(f"Assessment finalized - {len(apps_ready)} apps ready for planning")
            return review_result
            
        except Exception as e:
            logger.error(f"Assessment finalization failed: {str(e)}")
            raise AssessmentFlowError(f"Assessment finalization failed: {str(e)}")
    
    # Resume functionality for user interactions
    async def resume_from_phase(
        self, 
        phase: AssessmentPhase, 
        user_input: Dict[str, Any]
    ) -> AssessmentFlowState:
        """Resume flow from specific phase with user input"""
        
        try:
            # Load current flow state
            current_state = await self.postgres_store.load_flow_state()
            if not current_state:
                raise AssessmentFlowError("No flow state found for resume")
            
            # Save user input for the phase
            await self.repository.save_user_input(
                self.context.flow_id, phase.value, user_input
            )
            current_state.user_inputs[phase.value] = user_input
            
            # Update current phase and status
            current_state.current_phase = phase
            current_state.status = "processing"
            current_state.last_user_interaction = datetime.utcnow()
            
            # Resume from the appropriate phase
            if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
                return await self.analyze_technical_debt(current_state)
            elif phase == AssessmentPhase.TECH_DEBT_ANALYSIS:
                return await self.determine_component_sixr_strategies(current_state)
            elif phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES:
                return await self.generate_app_on_page(current_state)
            elif phase == AssessmentPhase.APP_ON_PAGE_GENERATION:
                return await self.finalize_assessment(current_state)
            else:
                raise AssessmentFlowError(f"Cannot resume from phase: {phase}")
                
        except Exception as e:
            logger.error(f"Failed to resume from phase {phase}: {str(e)}")
            raise AssessmentFlowError(f"Resume failed: {str(e)}")
    
    # Helper methods for data processing and integration
    async def _load_selected_applications(self) -> List[str]:
        """Load applications marked ready for assessment"""
        # Implementation details...
        pass
    
    async def _load_engagement_standards(self) -> List[ArchitectureRequirement]:
        """Load existing engagement architecture standards"""
        # Implementation details...
        pass
    
    async def _initialize_default_standards(self) -> List[ArchitectureRequirement]:
        """Initialize default architecture standards for engagement"""
        # Implementation details...
        pass
    
    async def _get_application_metadata(self, app_id: str) -> Dict[str, Any]:
        """Get application metadata from Discovery flow results"""
        # Implementation details...
        pass
    
    async def _generate_app_on_page_data(
        self, 
        app_id: str, 
        flow_state: AssessmentFlowState,
        decision: SixRDecision
    ) -> Dict[str, Any]:
        """Generate comprehensive app on a page data"""
        # Implementation details...
        pass
```

**Error Handling and Recovery**:
```python
class AssessmentFlowError(Exception):
    """Custom exception for assessment flow errors"""
    pass

class AssessmentFlowRecovery:
    """Recovery mechanisms for assessment flow failures"""
    
    @staticmethod
    async def recover_from_crew_failure(
        flow_id: str, 
        phase: str, 
        error: Exception
    ) -> bool:
        """Attempt to recover from crew execution failure"""
        
        logger.warning(f"Attempting recovery from crew failure in {phase}: {str(error)}")
        
        # Implement retry logic with exponential backoff
        # Save error state for user review
        # Provide manual override options
        
        return True  # or False if recovery impossible
```

**Acceptance Criteria**:
- [ ] Complete CrewAI Flow with @start/@listen decorators
- [ ] Pause/resume functionality at each node
- [ ] Integration with FlowStateManager and PostgresStore
- [ ] Multi-tenant context preservation
- [ ] Component-level analysis and 6R decision logic
- [ ] Error handling and recovery mechanisms
- [ ] User input capture and application
- [ ] State persistence throughout flow execution

---

## 🤖 CrewAI Agent Tasks

### CREW-001: Implement Architecture Standards Crew
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 14 hours  
**Dependencies**: BE-001  
**Sprint**: Backend Week 3-4  

**Description**: Create true CrewAI agents for capturing and evaluating architecture requirements with user collaboration

**Location**: `backend/app/services/crewai_flows/crews/architecture_standards_crew.py`

**Technical Requirements**:
- True CrewAI Agent and Crew patterns (not pseudo-agents)
- Integration with engagement-level standards and app-specific overrides
- RBAC-aware architecture requirement validation
- Technology lifecycle and version compatibility analysis
- Exception handling for business constraints

**Crew Implementation**:
```python
from crewai import Agent, Task, Crew
from app.services.crewai_flows.tools.architecture_tools import (
    TechnologyVersionAnalyzer,
    ComplianceChecker,
    StandardsTemplateGenerator
)

class ArchitectureStandardsCrew:
    """Captures and evaluates architecture requirements with user collaboration"""
    
    def __init__(self, flow_context: FlowContext):
        self.flow_context = flow_context
        self.agents = self._create_agents()
        self.crew = self._create_crew()
    
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for architecture standards"""
        
        architecture_standards_agent = Agent(
            role="Architecture Standards Specialist",
            goal="Define and evaluate engagement-level architecture minimums based on industry best practices and client requirements",
            backstory="""You are an expert cloud architect with 15+ years of experience in enterprise 
            architecture standards. You specialize in defining technology lifecycle policies, security 
            requirements, and cloud-native architecture patterns. You understand the balance between 
            innovation and risk management in large enterprise environments.""",
            tools=[
                TechnologyVersionAnalyzer(),
                StandardsTemplateGenerator(),
                ComplianceChecker()
            ],
            verbose=True,
            allow_delegation=True
        )
        
        technology_stack_analyst = Agent(
            role="Technology Stack Analyst", 
            goal="Assess application technology stacks against supported versions and identify upgrade paths",
            backstory="""You are a technology lifecycle expert who tracks the evolution of programming 
            languages, frameworks, and platforms. You have deep knowledge of version compatibility, 
            end-of-life schedules, and migration paths. You can quickly identify technical debt related 
            to outdated technology versions and recommend practical upgrade strategies.""",
            tools=[
                TechnologyVersionAnalyzer(),
                ComplianceChecker()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        exception_handler_agent = Agent(
            role="Business Constraint Analyst",
            goal="Identify and document valid architecture exceptions based on business constraints and technical trade-offs", 
            backstory="""You are a business-technology liaison with expertise in evaluating when 
            architecture standards should have exceptions. You understand vendor relationships, 
            licensing constraints, integration dependencies, and business continuity requirements. 
            You can articulate the business case for exceptions while quantifying associated risks.""",
            tools=[
                ComplianceChecker()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        return [architecture_standards_agent, technology_stack_analyst, exception_handler_agent]
    
    def _create_crew(self) -> Crew:
        """Create crew with architecture standards tasks"""
        
        capture_standards_task = Task(
            description="""Analyze the engagement requirements and client context to capture comprehensive 
            architecture standards. Consider:
            
            1. Technology Version Requirements:
               - Programming languages (Java, .NET, Python, Node.js)
               - Frameworks and libraries (Spring, Django, React, Angular)
               - Database systems and versions
               - Operating systems and container runtimes
            
            2. Security and Compliance Standards:
               - Authentication and authorization patterns
               - Data encryption requirements
               - Audit and logging capabilities
               - Regulatory compliance needs (SOC2, PCI-DSS, GDPR)
            
            3. Architecture Pattern Requirements:
               - API design standards (REST, GraphQL, OpenAPI)
               - Containerization and orchestration
               - Monitoring and observability
               - Scalability and performance patterns
            
            4. Cloud-Native Capabilities:
               - Infrastructure as Code
               - CI/CD integration
               - Auto-scaling and load balancing
               - Disaster recovery and backup
            
            Base your analysis on the provided engagement context: {engagement_context}
            Consider the following applications: {selected_applications}
            
            Output a comprehensive set of architecture standards with:
            - Requirement type and description
            - Mandatory vs. optional designation  
            - Supported technology versions
            - Business rationale for each standard
            - Implementation guidance and best practices""",
            expected_output="""A structured list of architecture standards containing:
            - Technology version requirements with specific version ranges
            - Security and compliance standards with implementation details
            - Architecture pattern requirements with design guidelines
            - Cloud-native capability requirements with tooling recommendations
            Each standard should include rationale, implementation guidance, and exceptions criteria.""",
            agent=self.agents[0]  # Architecture Standards Specialist
        )
        
        analyze_application_stacks_task = Task(
            description="""For each selected application, analyze its current technology stack against 
            the captured architecture standards. Evaluate:
            
            1. Technology Version Compliance:
               - Compare current versions vs. minimum supported versions
               - Identify end-of-life technologies and upgrade urgency
               - Calculate version-based technical debt scores
            
            2. Compatibility Assessment:
               - Framework compatibility with target cloud platforms
               - Integration compatibility with modern architecture patterns
               - Security vulnerability assessment for current versions
            
            3. Upgrade Path Analysis:
               - Identify clear upgrade paths for non-compliant technologies
               - Estimate effort and complexity for version upgrades
               - Highlight breaking changes and migration considerations
            
            Application metadata to analyze: {application_metadata}
            Architecture standards to validate against: {architecture_standards}
            
            Provide detailed analysis for each application including compliance status, 
            technical debt calculation, and recommended upgrade paths.""",
            expected_output="""For each application, provide:
            - Technology stack compliance matrix (compliant/non-compliant/upgrade needed)
            - Technical debt scores based on version obsolescence
            - Specific upgrade recommendations with effort estimates
            - Risk assessment for current technology versions
            - Integration considerations for cloud migration""",
            agent=self.agents[1],  # Technology Stack Analyst
            context=[capture_standards_task]
        )
        
        evaluate_exceptions_task = Task(
            description="""Evaluate potential exceptions to architecture standards based on business 
            constraints and technical realities. Consider:
            
            1. Business Constraint Evaluation:
               - Vendor support agreements and licensing terms
               - Integration dependencies with external systems
               - Regulatory or compliance specific requirements
               - Business continuity and operational constraints
            
            2. Technical Trade-off Analysis:
               - Cost vs. benefit analysis for standard compliance
               - Timeline and resource constraints for upgrades
               - Risk assessment for maintaining exceptions
               - Migration complexity and business impact
            
            3. Exception Documentation:
               - Clear rationale for each proposed exception
               - Risk mitigation strategies for non-compliance
               - Timeline for future compliance (if applicable)
               - Monitoring and review requirements for exceptions
            
            Application analysis results: {application_analysis_results}
            Business context and constraints: {business_constraints}
            
            Provide recommendations for valid exceptions with proper business justification.""",
            expected_output="""A comprehensive exception analysis containing:
            - List of applications requiring architecture standard exceptions
            - Business rationale for each exception with risk assessment
            - Mitigation strategies for non-compliance risks
            - Timeline and criteria for future compliance review
            - Monitoring requirements for exception management""",
            agent=self.agents[2],  # Business Constraint Analyst
            context=[capture_standards_task, analyze_application_stacks_task]
        )
        
        return Crew(
            agents=self.agents,
            tasks=[capture_standards_task, analyze_application_stacks_task, evaluate_exceptions_task],
            verbose=True,
            process="sequential"
        )
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the architecture standards crew"""
        
        try:
            logger.info("Starting Architecture Standards Crew execution")
            
            # Prepare context for crew execution
            crew_context = {
                "engagement_context": context.get("engagement_context", {}),
                "selected_applications": context.get("selected_applications", []),
                "application_metadata": context.get("application_metadata", {}),
                "architecture_standards": context.get("existing_standards", []),
                "business_constraints": context.get("business_constraints", {}),
                "flow_context": self.flow_context
            }
            
            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)
            
            # Process and structure the results
            processed_result = await self._process_crew_results(result)
            
            logger.info("Architecture Standards Crew execution completed successfully")
            return processed_result
            
        except Exception as e:
            logger.error(f"Architecture Standards Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Architecture standards analysis failed: {str(e)}")
    
    async def _process_crew_results(self, result) -> Dict[str, Any]:
        """Process and structure crew execution results"""
        
        return {
            "engagement_standards": result.get("architecture_standards", []),
            "application_compliance": result.get("compliance_analysis", {}),
            "exceptions": result.get("architecture_exceptions", []),
            "upgrade_recommendations": result.get("upgrade_paths", {}),
            "technical_debt_scores": result.get("tech_debt_scores", {}),
            "crew_confidence": result.get("confidence_score", 0.8),
            "recommendations": result.get("implementation_guidance", [])
        }
```

**Architecture Tools Implementation**:
```python
# In app/services/crewai_flows/tools/architecture_tools.py

from crewai_tools import BaseTool
from typing import Dict, List, Any

class TechnologyVersionAnalyzer(BaseTool):
    name: str = "Technology Version Analyzer"
    description: str = "Analyzes technology versions against lifecycle and support policies"
    
    def _run(self, technology_stack: Dict[str, str]) -> Dict[str, Any]:
        """Analyze technology versions for compliance and technical debt"""
        
        # Version lifecycle data (could be loaded from external sources)
        version_policies = {
            "java": {"minimum": "11", "recommended": "17", "eol_versions": ["8", "7", "6"]},
            "python": {"minimum": "3.8", "recommended": "3.11", "eol_versions": ["3.7", "3.6", "2.7"]},
            "node": {"minimum": "16", "recommended": "18", "eol_versions": ["14", "12", "10"]},
            "dotnet": {"minimum": "6.0", "recommended": "7.0", "eol_versions": ["5.0", "3.1", "2.1"]}
        }
        
        analysis = {}
        for tech, version in technology_stack.items():
            if tech.lower() in version_policies:
                policy = version_policies[tech.lower()]
                analysis[tech] = {
                    "current_version": version,
                    "compliant": self._is_version_compliant(version, policy["minimum"]),
                    "recommended_upgrade": policy["recommended"],
                    "is_eol": version in policy["eol_versions"],
                    "tech_debt_score": self._calculate_version_debt(version, policy),
                    "upgrade_urgency": self._get_upgrade_urgency(version, policy)
                }
        
        return analysis
    
    def _is_version_compliant(self, current: str, minimum: str) -> bool:
        """Check if current version meets minimum requirements"""
        # Implementation for version comparison logic
        pass
    
    def _calculate_version_debt(self, version: str, policy: Dict) -> float:
        """Calculate technical debt score based on version age"""
        # Implementation for debt calculation
        pass

class ComplianceChecker(BaseTool):
    name: str = "Compliance Checker"
    description: str = "Checks architecture compliance against security and regulatory standards"
    
    def _run(self, architecture_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance against various standards"""
        
        compliance_checks = {
            "security": self._check_security_compliance(architecture_config),
            "data_protection": self._check_data_protection(architecture_config),
            "authentication": self._check_auth_patterns(architecture_config),
            "monitoring": self._check_observability(architecture_config)
        }
        
        return compliance_checks

class StandardsTemplateGenerator(BaseTool):
    name: str = "Standards Template Generator"
    description: str = "Generates architecture standards templates based on industry best practices"
    
    def _run(self, domain: str, technology_focus: List[str]) -> Dict[str, Any]:
        """Generate standards template for specific domain and technologies"""
        
        templates = {
            "financial_services": self._generate_finserv_template(),
            "healthcare": self._generate_healthcare_template(),
            "retail": self._generate_retail_template(),
            "manufacturing": self._generate_manufacturing_template()
        }
        
        return templates.get(domain, self._generate_generic_template())
```

**Acceptance Criteria**:
- [ ] True CrewAI agents with proper role definitions and backstories
- [ ] Technology version analysis and compliance checking
- [ ] Architecture standards capture with user collaboration
- [ ] Exception handling for business constraints
- [ ] Integration with assessment flow context
- [ ] Comprehensive tool implementation for standards analysis
- [ ] Structured output for flow state integration
- [ ] Error handling and recovery mechanisms

---

### CREW-002: Implement Component Analysis Crew
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 16 hours  
**Dependencies**: BE-001  
**Sprint**: Backend Week 3-4  

**Description**: Create crew for identifying application components and analyzing technical debt based on discovered metadata

**Location**: `backend/app/services/crewai_flows/crews/component_analysis_crew.py`

**Technical Requirements**:
- Component identification beyond traditional 3-tier architecture
- Tech debt analysis based on Discovery flow metadata
- Dependency mapping and coupling analysis
- Flexible component structures for modern architectures
- Integration with architecture standards validation

**Crew Implementation**:
```python
from crewai import Agent, Task, Crew
from app.services.crewai_flows.tools.component_tools import (
    ComponentDiscoveryTool,
    MetadataAnalyzer,
    DependencyMapper,
    TechDebtCalculator
)

class ComponentAnalysisCrew:
    """Identifies components and analyzes technical debt based on discovered metadata"""
    
    def __init__(self, flow_context: FlowContext):
        self.flow_context = flow_context
        self.agents = self._create_agents()
        self.crew = self._create_crew()
    
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for component analysis"""
        
        component_discovery_agent = Agent(
            role="Component Architecture Analyst",
            goal="Identify and catalog all application components beyond traditional 3-tier architecture",
            backstory="""You are a modern application architecture expert specializing in component 
            identification across diverse architectural patterns. You have deep expertise in monolithic, 
            microservices, serverless, and hybrid architectures. You can identify UI components, API 
            layers, business services, data access layers, background workers, and integration components 
            from application metadata and discovery data.""",
            tools=[
                ComponentDiscoveryTool(),
                MetadataAnalyzer()
            ],
            verbose=True,
            allow_delegation=True
        )
        
        metadata_analyst_agent = Agent(
            role="Technical Debt Assessment Specialist",
            goal="Analyze technical debt from discovered application metadata and identify modernization opportunities",
            backstory="""You are a technical debt analysis expert with extensive experience in code 
            quality assessment, architecture evaluation, and modernization planning. You can identify 
            technical debt patterns from metadata such as technology versions, dependency structures, 
            code metrics, and architectural patterns. You excel at quantifying technical debt and 
            prioritizing remediation efforts.""",
            tools=[
                MetadataAnalyzer(),
                TechDebtCalculator()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        dependency_mapper_agent = Agent(
            role="Dependency Analysis Expert",
            goal="Map component dependencies and identify coupling patterns for migration grouping",
            backstory="""You are a systems integration specialist with expertise in dependency analysis 
            and coupling assessment. You understand how components interact across different architectural 
            patterns and can identify tight coupling, loose coupling, and integration patterns. You excel 
            at creating dependency maps that inform migration wave planning and component treatment decisions.""",
            tools=[
                DependencyMapper(),
                ComponentDiscoveryTool()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        return [component_discovery_agent, metadata_analyst_agent, dependency_mapper_agent]
    
    def _create_crew(self) -> Crew:
        """Create crew with component analysis tasks"""
        
        identify_components_task = Task(
            description="""Analyze the application metadata to identify all components within the application 
            architecture. Go beyond traditional frontend/middleware/backend categories to identify:
            
            1. User Interface Components:
               - Web frontends (SPA, MPA, static sites)
               - Mobile applications (native, hybrid, PWA)
               - Desktop applications
               - Administrative interfaces
            
            2. API and Service Components:
               - REST APIs and GraphQL endpoints
               - SOAP services and legacy web services
               - Message queue consumers/producers
               - Background job processors
               - Scheduled tasks and batch jobs
            
            3. Business Logic Components:
               - Core business services
               - Integration services
               - Workflow engines
               - Business rule engines
               - Data processing pipelines
            
            4. Data Components:
               - Database systems (relational, NoSQL, cache)
               - Data warehouses and analytics platforms
               - File storage and content management
               - Search engines and indexes
            
            5. Infrastructure Components:
               - Load balancers and proxies
               - Message brokers and queues
               - Monitoring and logging services
               - Security and authentication services
            
            Application metadata to analyze: {application_metadata}
            Discovery data available: {discovery_data}
            Architecture context: {architecture_context}
            
            For each identified component, provide:
            - Component name and type classification
            - Technology stack details
            - Primary responsibilities and functions
            - Deployment and runtime characteristics""",
            expected_output="""A comprehensive component inventory containing:
            - List of all identified components with names and types
            - Technology stack for each component (languages, frameworks, databases)
            - Component responsibilities and business functions
            - Deployment patterns and runtime characteristics
            - Initial assessment of component complexity and criticality""",
            agent=self.agents[0]  # Component Architecture Analyst
        )
        
        analyze_technical_debt_task = Task(
            description="""Analyze technical debt for each identified component based on the available 
            metadata and discovery data. Focus on:
            
            1. Technology Obsolescence:
               - Framework and library versions vs. current standards
               - Programming language version compliance
               - Database and infrastructure technology age
               - Security vulnerability exposure
            
            2. Architecture Debt:
               - Anti-patterns and code smells evident from metadata
               - Monolithic vs. modular design indicators
               - Tight coupling and dependency issues
               - Scalability and performance limitations
            
            3. Operational Debt:
               - Deployment complexity and automation gaps
               - Monitoring and observability deficiencies
               - Documentation and knowledge management issues
               - Configuration management and environment drift
            
            4. Compliance Debt:
               - Security compliance gaps
               - Data protection and privacy issues
               - Audit trail and logging deficiencies
               - Regulatory compliance risks
            
            Component inventory: {component_inventory}
            Architecture standards: {architecture_standards}
            Technology lifecycle data: {technology_lifecycle}
            
            Calculate technical debt scores and prioritize remediation efforts for each component.""",
            expected_output="""Technical debt analysis containing:
            - Component-level technical debt scores (0-10 scale)
            - Detailed debt category breakdown (technology, architecture, operational, compliance)
            - Specific debt items with severity levels and remediation estimates
            - Prioritized remediation recommendations
            - Impact assessment for migration and modernization efforts""",
            agent=self.agents[1],  # Technical Debt Assessment Specialist
            context=[identify_components_task]
        )
        
        map_dependencies_task = Task(
            description="""Map dependencies between identified components and analyze coupling patterns 
            that will influence migration strategies. Analyze:
            
            1. Internal Dependencies:
               - Component-to-component communication patterns
               - Data flow and shared data dependencies
               - Synchronous vs. asynchronous interaction patterns
               - Transaction boundaries and consistency requirements
            
            2. External Dependencies:
               - Third-party service integrations
               - External API dependencies
               - Vendor system connections
               - Infrastructure service dependencies
            
            3. Coupling Analysis:
               - Tight coupling indicators (shared databases, direct calls)
               - Loose coupling patterns (message queues, event-driven)
               - Temporal coupling (synchronous dependencies)
               - Data coupling (shared data structures)
            
            4. Migration Grouping Insights:
               - Components that must move together
               - Dependencies that can be refactored for independent migration
               - Integration points that require special handling
               - Sequence dependencies for migration waves
            
            Component inventory: {component_inventory}
            Technical debt analysis: {tech_debt_analysis}
            Architecture patterns: {architecture_patterns}
            
            Create dependency maps and provide grouping recommendations for migration planning.""",
            expected_output="""Dependency analysis containing:
            - Complete dependency map showing component relationships
            - Coupling assessment with tight/loose coupling identification
            - Migration grouping recommendations based on dependencies
            - Critical path analysis for component migration sequencing
            - Integration points requiring special handling or refactoring""",
            agent=self.agents[2],  # Dependency Analysis Expert
            context=[identify_components_task, analyze_technical_debt_task]
        )
        
        return Crew(
            agents=self.agents,
            tasks=[identify_components_task, analyze_technical_debt_task, map_dependencies_task],
            verbose=True,
            process="sequential"
        )
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the component analysis crew"""
        
        try:
            logger.info(f"Starting Component Analysis Crew for application {context.get('application_id')}")
            
            # Prepare context for crew execution
            crew_context = {
                "application_metadata": context.get("application_metadata", {}),
                "discovery_data": context.get("discovery_data", {}),
                "architecture_context": context.get("architecture_standards", []),
                "architecture_standards": context.get("architecture_standards", []),
                "technology_lifecycle": context.get("technology_lifecycle", {}),
                "architecture_patterns": context.get("architecture_patterns", {}),
                "flow_context": self.flow_context
            }
            
            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)
            
            # Process and structure the results
            processed_result = await self._process_crew_results(result, context["application_id"])
            
            logger.info(f"Component Analysis Crew completed for application {context.get('application_id')}")
            return processed_result
            
        except Exception as e:
            logger.error(f"Component Analysis Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Component analysis failed: {str(e)}")
    
    async def _process_crew_results(self, result, application_id: str) -> Dict[str, Any]:
        """Process and structure crew execution results"""
        
        # Extract components from crew results
        components = result.get("component_inventory", [])
        
        # Structure components for flow state
        structured_components = []
        for component in components:
            structured_components.append(ApplicationComponent(
                component_name=component.get("name"),
                component_type=ComponentType(component.get("type", "custom")),
                technology_stack=component.get("technology_stack", {}),
                dependencies=component.get("dependencies", [])
            ))
        
        # Extract and structure technical debt analysis
        tech_debt_analysis = result.get("tech_debt_analysis", [])
        structured_tech_debt = []
        component_scores = {}
        
        for debt_item in tech_debt_analysis:
            structured_tech_debt.append(TechDebtItem(
                category=debt_item.get("category"),
                severity=TechDebtSeverity(debt_item.get("severity", "medium")),
                description=debt_item.get("description"),
                remediation_effort_hours=debt_item.get("effort_hours"),
                impact_on_migration=debt_item.get("migration_impact"),
                tech_debt_score=debt_item.get("score"),
                detected_by_agent="component_analysis_crew",
                agent_confidence=debt_item.get("confidence", 0.8)
            ))
            
            # Track component-level scores
            component_name = debt_item.get("component")
            if component_name:
                component_scores[component_name] = debt_item.get("score", 0.0)
        
        return {
            "components": structured_components,
            "tech_debt_analysis": structured_tech_debt,
            "component_scores": component_scores,
            "dependency_map": result.get("dependency_map", {}),
            "migration_groups": result.get("migration_grouping", []),
            "crew_confidence": result.get("confidence_score", 0.8),
            "analysis_insights": result.get("analysis_insights", [])
        }
```

**Component Analysis Tools**:
```python
# In app/services/crewai_flows/tools/component_tools.py

class ComponentDiscoveryTool(BaseTool):
    name: str = "Component Discovery Tool"
    description: str = "Discovers application components from metadata and discovery data"
    
    def _run(self, application_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover components from application metadata"""
        
        components = []
        
        # Analyze technology stack to infer component types
        if "frontend_technologies" in application_metadata:
            components.extend(self._identify_frontend_components(application_metadata))
        
        if "backend_technologies" in application_metadata:
            components.extend(self._identify_backend_components(application_metadata))
        
        if "database_systems" in application_metadata:
            components.extend(self._identify_data_components(application_metadata))
        
        if "integration_points" in application_metadata:
            components.extend(self._identify_integration_components(application_metadata))
        
        return components
    
    def _identify_frontend_components(self, metadata: Dict) -> List[Dict]:
        """Identify frontend components from metadata"""
        # Implementation for frontend component identification
        pass
    
    def _identify_backend_components(self, metadata: Dict) -> List[Dict]:
        """Identify backend service components"""
        # Implementation for backend component identification
        pass

class MetadataAnalyzer(BaseTool):
    name: str = "Metadata Analyzer"
    description: str = "Analyzes application metadata for technical debt indicators"
    
    def _run(self, metadata: Dict[str, Any], standards: List[Dict]) -> Dict[str, Any]:
        """Analyze metadata against architecture standards"""
        
        analysis = {
            "version_compliance": self._analyze_version_compliance(metadata, standards),
            "security_indicators": self._analyze_security_metadata(metadata),
            "architecture_patterns": self._identify_architecture_patterns(metadata),
            "performance_indicators": self._analyze_performance_metadata(metadata)
        }
        
        return analysis

class TechDebtCalculator(BaseTool):
    name: str = "Technical Debt Calculator"
    description: str = "Calculates technical debt scores based on various factors"
    
    def _run(self, analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate technical debt scores for components"""
        
        scores = {}
        
        # Version obsolescence scoring
        version_score = self._calculate_version_debt_score(analysis_data.get("version_compliance", {}))
        
        # Security debt scoring
        security_score = self._calculate_security_debt_score(analysis_data.get("security_indicators", {}))
        
        # Architecture debt scoring
        architecture_score = self._calculate_architecture_debt_score(analysis_data.get("architecture_patterns", {}))
        
        # Overall score calculation (weighted average)
        overall_score = (version_score * 0.4 + security_score * 0.3 + architecture_score * 0.3)
        
        return {
            "overall_score": overall_score,
            "version_debt": version_score,
            "security_debt": security_score,
            "architecture_debt": architecture_score
        }

class DependencyMapper(BaseTool):
    name: str = "Dependency Mapper"
    description: str = "Maps dependencies between components and external systems"
    
    def _run(self, components: List[Dict], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Map dependencies between components"""
        
        dependency_map = {
            "internal_dependencies": self._map_internal_dependencies(components),
            "external_dependencies": self._map_external_dependencies(metadata),
            "coupling_analysis": self._analyze_coupling_patterns(components),
            "migration_groups": self._suggest_migration_groups(components)
        }
        
        return dependency_map
```

**Acceptance Criteria**:
- [ ] Component identification beyond 3-tier architecture
- [ ] Technical debt analysis from Discovery metadata
- [ ] Dependency mapping and coupling analysis
- [ ] Integration with architecture standards validation
- [ ] Structured output for component treatments
- [ ] Move group hints for Planning Flow integration
- [ ] Comprehensive tool implementation
- [ ] Error handling and confidence scoring

---

### CREW-003: Implement Six R Strategy Crew
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 18 hours  
**Dependencies**: BE-001, CREW-001, CREW-002  
**Sprint**: Backend Week 4  

**Description**: Create crew for determining component-level 6R strategies with validation and compatibility checking

**Location**: `backend/app/services/crewai_flows/crews/sixr_strategy_crew.py`

**Technical Requirements**:
- Component-level 6R strategy determination
- Compatibility validation between component treatments
- Integration with tech debt analysis and architecture standards
- Move group hint generation for Planning Flow
- Confidence scoring and rationale generation

**Crew Implementation** (abbreviated due to length constraints):
```python
from crewai import Agent, Task, Crew
from app.models.assessment_flow import SixRStrategy, ComponentTreatment

class SixRStrategyCrew:
    """Determines component-level 6R strategies with validation"""
    
    def __init__(self, flow_context: FlowContext):
        self.flow_context = flow_context
        self.agents = self._create_agents()
        self.crew = self._create_crew()
    
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for 6R strategy determination"""
        
        component_strategy_expert = Agent(
            role="Component Modernization Strategist",
            goal="Determine optimal 6R strategy for each application component based on technical characteristics and business constraints",
            backstory="""You are a cloud migration strategist with deep expertise in component-level 
            modernization approaches. You understand the nuances of different 6R strategies (Rewrite, 
            ReArchitect, Refactor, Replatform, Rehost) and can assess which approach is optimal for 
            different component types based on technical debt, architecture fit, and business value.""",
            tools=[
                SixRDecisionEngine(),
                ComponentAnalyzer(),
                BusinessValueCalculator()
            ],
            verbose=True,
            allow_delegation=True
        )
        
        compatibility_validator = Agent(
            role="Architecture Compatibility Validator", 
            goal="Validate treatment compatibility between dependent components and identify integration risks",
            backstory="""You are an integration architecture expert specializing in validating that 
            component modernization strategies will work together cohesively. You understand how different 
            6R treatments affect component interfaces, data flow, and system integration patterns.""",
            tools=[
                CompatibilityChecker(),
                IntegrationAnalyzer()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        move_group_advisor = Agent(
            role="Migration Wave Planning Advisor",
            goal="Identify move group hints based on technology proximity, dependencies, and migration logistics",
            backstory="""You are a migration logistics expert who understands how to group applications 
            and components for efficient migration waves. You consider technology affinity, dependency 
            relationships, team ownership, and infrastructure requirements when recommending groupings.""",
            tools=[
                MoveGroupAnalyzer(),
                DependencyOptimizer()
            ],
            verbose=True,
            allow_delegation=False
        )
        
        return [component_strategy_expert, compatibility_validator, move_group_advisor]
    
    def _create_crew(self) -> Crew:
        """Create crew with 6R strategy tasks"""
        
        determine_component_strategies_task = Task(
            description="""Analyze each component and determine the optimal 6R strategy based on:
            
            1. Technical Characteristics:
               - Technology stack maturity and cloud-readiness
               - Technical debt levels and remediation complexity
               - Architecture patterns and modernization potential
               - Performance and scalability requirements
            
            2. Business Factors:
               - Component criticality and business value
               - Development team capabilities and capacity
               - Timeline constraints and migration priorities
               - Risk tolerance and change management considerations
            
            3. 6R Strategy Selection Criteria:
               - REWRITE: High tech debt, strategic importance, team capacity
               - REARCHITECT: Architectural limitations, scalability needs
               - REFACTOR: Moderate tech debt, good foundation, incremental improvement
               - REPLATFORM: Cloud optimization, minimal changes, quick wins
               - REHOST: Legacy compatibility, minimal disruption, infrastructure focus
            
            Components to analyze: {components}
            Technical debt analysis: {tech_debt_analysis}
            Architecture standards: {architecture_standards}
            Business context: {business_context}
            
            For each component, provide detailed 6R recommendation with rationale.""",
            expected_output="""Component-level 6R strategies containing:
            - Recommended strategy for each component with confidence score
            - Detailed rationale explaining the strategy selection
            - Effort and cost estimates for implementation
            - Risk factors and mitigation strategies
            - Timeline and dependency considerations""",
            agent=self.agents[0]  # Component Modernization Strategist
        )
        
        # Additional tasks for compatibility validation and move group analysis...
        
        return Crew(
            agents=self.agents,
            tasks=[determine_component_strategies_task],  # Plus other tasks
            verbose=True,
            process="sequential"
        )
    
    # Implementation continues with execution logic...
```

**Acceptance Criteria**:
- [ ] Component-level 6R strategy determination with rationale
- [ ] Compatibility validation between component treatments
- [ ] Move group hints for Planning Flow integration
- [ ] Confidence scoring and business value assessment
- [ ] Integration with tech debt and architecture analysis
- [ ] Structured output for assessment flow integration

---

## Next Steps

After completing these backend and CrewAI tasks, proceed to:
1. **API & Integration Tasks** (Document 03)
2. **Frontend & UX Tasks** (Document 04) 
3. **Testing & DevOps Tasks** (Document 05)

## Dependencies Map

- **BE-001** depends on Database Foundation tasks
- **CREW-001** depends on **BE-001**
- **CREW-002** depends on **BE-001** 
- **CREW-003** depends on **BE-001, CREW-001, CREW-002**

All API and frontend development depends on completing these backend tasks first.