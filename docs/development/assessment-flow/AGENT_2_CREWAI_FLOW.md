# AI Coding Agent 2: CrewAI Flow & Agents Implementation

## Agent Overview
You are responsible for implementing the core CrewAI Flow logic, creating the specialized crews and agents, and ensuring proper state management throughout the Assessment Flow. Your work orchestrates the AI-driven assessment process.

## Context

### Project Overview
The Assessment Flow is the second major CrewAI flow in the platform, following Discovery Flow. It performs:
1. Architecture requirement verification
2. Technical debt analysis (moved from Discovery Flow)
3. 6R strategy determination for each selected application
4. User review and override capabilities

### Technical Stack
- **CrewAI**: Flow framework with @start/@listen/@router decorators
- **LLM**: DeepInfra API for agent intelligence
- **State Management**: PostgreSQL-based FlowStateBridge
- **Multi-tenancy**: Client account isolation

### Existing Patterns to Follow
Study these files for patterns:
- `backend/app/services/crewai_flows/unified_discovery_flow.py` - Flow structure
- `backend/app/services/crewai_flows/flow_state_manager.py` - State management
- `backend/app/services/crewai_flows/crews/` - Existing crew implementations

## Your Assigned Tasks

### 🐍 Backend Tasks

#### BE-003: Implement AssessmentFlow Class
**Priority**: P0 - Critical  
**Effort**: 8 hours  
**Location**: `backend/app/services/crewai_flows/assessment_flow.py`

```python
from crewai import Flow
from typing import Dict, Any, List
import logging
from app.models.assessment_flow_state import AssessmentFlowState
from app.services.crewai_flows.persistence.flow_state_bridge import FlowStateBridge
from app.services.crewai_service import CrewAIService
from app.core.flow_context import FlowContext

logger = logging.getLogger(__name__)

class AssessmentFlow(Flow[AssessmentFlowState]):
    """
    CrewAI Flow for assessing selected applications and determining 6R strategies.
    
    Flow phases:
    1. Initialize with selected applications
    2. Verify architecture requirements
    3. Analyze technical debt
    4. Determine 6R strategies
    5. Route for review based on confidence
    6. Allow user overrides
    7. Finalize assessment
    """
    
    def __init__(self, crewai_service: CrewAIService, context: FlowContext):
        super().__init__()
        self.crewai_service = crewai_service
        self.context = context
        self.state_bridge = FlowStateBridge(context.flow_id)
        
    @start()
    def initialize_assessment(self) -> Dict[str, Any]:
        """
        Initialize assessment flow with selected applications.
        
        Tasks:
        - Load selected applications from discovery flow
        - Create assessment flow record
        - Initialize state tracking
        - Set up architecture requirements based on client
        """
        logger.info(f"Initializing assessment flow for {len(self.state.selected_application_ids)} applications")
        
        # Update flow state
        self.state.status = "initialized"
        self.state.current_phase = "initialization"
        self.state.progress = 10
        
        # Persist state
        self.state_bridge.update_state(self.state)
        
        return {
            "status": "initialized",
            "application_count": len(self.state.selected_application_ids),
            "next_phase": "architecture_verification"
        }
    
    @listen(initialize_assessment)
    def verify_architecture_minimums(self, init_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify architecture requirements using Architecture Verification Crew.
        """
        logger.info("Starting architecture verification phase")
        
        # Create and execute Architecture Verification Crew
        from app.services.crewai_flows.crews.architecture_verification_crew import ArchitectureVerificationCrew
        
        crew = ArchitectureVerificationCrew(self.crewai_service, self.context)
        result = crew.kickoff({
            "applications": self.state.selected_application_ids,
            "client_requirements": self.context.client_requirements
        })
        
        # Update state with results
        self.state.architecture_requirements = result.get("requirements", [])
        self.state.architecture_verified = result.get("all_verified", False)
        self.state.architecture_issues = result.get("issues", [])
        self.state.current_phase = "architecture_verification"
        self.state.progress = 25
        
        # Add agent insights
        self.state.agent_insights.extend(result.get("insights", []))
        
        # Persist state
        self.state_bridge.update_state(self.state)
        
        return result
    
    @listen(verify_architecture_minimums)
    def analyze_technical_debt(self, arch_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical debt using Technical Debt Analysis Crew.
        """
        logger.info("Starting technical debt analysis phase")
        
        # Create and execute Tech Debt Analysis Crew
        from app.services.crewai_flows.crews.tech_debt_analysis_crew import TechnicalDebtAnalysisCrew
        
        crew = TechnicalDebtAnalysisCrew(self.crewai_service, self.context)
        result = crew.kickoff({
            "applications": self.state.selected_application_ids,
            "architecture_issues": self.state.architecture_issues
        })
        
        # Update state with tech debt analysis
        self.state.tech_debt_analysis = result.get("tech_debt_by_app", {})
        self.state.overall_tech_debt_score = result.get("overall_score", 0.0)
        self.state.current_phase = "tech_debt_analysis"
        self.state.progress = 50
        
        # Add agent insights
        self.state.agent_insights.extend(result.get("insights", []))
        
        # Persist state
        self.state_bridge.update_state(self.state)
        
        return result
    
    @listen(analyze_technical_debt)
    def determine_sixr_strategies(self, debt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine 6R strategies using Six R Strategy Crew.
        """
        logger.info("Starting 6R strategy determination phase")
        
        # Create and execute Six R Strategy Crew
        from app.services.crewai_flows.crews.sixr_strategy_crew import SixRStrategyCrew
        
        crew = SixRStrategyCrew(self.crewai_service, self.context)
        result = crew.kickoff({
            "applications": self.state.selected_application_ids,
            "tech_debt_analysis": self.state.tech_debt_analysis,
            "architecture_verified": self.state.architecture_verified
        })
        
        # Update state with 6R decisions
        self.state.sixr_decisions = result.get("decisions", {})
        self.state.current_phase = "sixr_strategy"
        self.state.progress = 75
        
        # Add agent insights
        self.state.agent_insights.extend(result.get("insights", []))
        
        # Persist state
        self.state_bridge.update_state(self.state)
        
        return result
    
    @router(determine_sixr_strategies)
    def route_for_review(self, strategies_result: Dict[str, Any]) -> str:
        """
        Route based on confidence scores.
        If average confidence > 80%, go straight to finalization.
        Otherwise, route to collaborative review.
        """
        decisions = strategies_result.get("decisions", {})
        
        if not decisions:
            return "collaborative_review"
        
        # Calculate average confidence
        total_confidence = sum(d.get("confidence_score", 0) for d in decisions.values())
        avg_confidence = total_confidence / len(decisions)
        
        logger.info(f"Average confidence score: {avg_confidence:.2f}")
        
        if avg_confidence > 0.8:
            return "finalize_assessment"
        else:
            return "collaborative_review"
    
    @listen(route_for_review)
    def collaborative_review(self, routing_result: str) -> Dict[str, Any]:
        """
        Pause flow for user review and potential overrides.
        This is where the flow waits for user input via API.
        """
        logger.info("Entering collaborative review phase")
        
        self.state.status = "awaiting_review"
        self.state.current_phase = "collaborative_review"
        self.state.progress = 90
        
        # Persist state
        self.state_bridge.update_state(self.state)
        
        # Return review summary
        return {
            "status": "awaiting_review",
            "decisions_for_review": len(self.state.sixr_decisions),
            "low_confidence_count": sum(
                1 for d in self.state.sixr_decisions.values() 
                if d.get("confidence_score", 0) < 0.8
            )
        }
    
    @listen(collaborative_review)
    def finalize_assessment(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize assessment and prepare for Planning Flow.
        """
        logger.info("Finalizing assessment flow")
        
        # Update final state
        self.state.status = "completed"
        self.state.current_phase = "finalized"
        self.state.progress = 100
        self.state.completed_at = datetime.utcnow()
        
        # Calculate summary statistics
        strategy_distribution = {}
        for decision in self.state.sixr_decisions.values():
            strategy = decision.get("user_override") or decision.get("recommended_strategy")
            strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
        
        # Persist final state
        self.state_bridge.update_state(self.state)
        
        return {
            "status": "completed",
            "total_applications": len(self.state.selected_application_ids),
            "strategy_distribution": strategy_distribution,
            "user_overrides": sum(
                1 for d in self.state.sixr_decisions.values() 
                if d.get("user_override") is not None
            ),
            "completion_time": self.state.completed_at.isoformat()
        }
```

#### BE-004: Create FlowStateBridge for Assessment
**Priority**: P1 - High  
**Effort**: 4 hours  
**Location**: `backend/app/services/crewai_flows/persistence/assessment_state_bridge.py`

Implement state persistence following the pattern from Discovery Flow.

---

### 🤖 CrewAI Tasks

#### AI-001: Create Architecture Verification Crew
**Priority**: P1 - High  
**Effort**: 6 hours  
**Location**: `backend/app/services/crewai_flows/crews/architecture_verification_crew.py`

```python
from crewai import Agent, Task, Crew
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ArchitectureVerificationCrew:
    """Crew for verifying architecture requirements and compliance"""
    
    def __init__(self, crewai_service, context):
        self.crewai_service = crewai_service
        self.context = context
        
    def _create_agents(self) -> List[Agent]:
        """Create specialized agents for architecture verification"""
        
        architecture_standards_agent = Agent(
            role="Architecture Standards Expert",
            goal="Verify applications meet enterprise architecture standards and best practices",
            backstory="""You are an expert cloud architect with deep knowledge of:
            - Enterprise architecture patterns (microservices, SOA, monolithic)
            - Cloud-native design principles
            - Security architecture standards
            - Data architecture patterns
            - Integration standards and APIs
            You evaluate applications against industry best practices and client-specific requirements.""",
            verbose=True,
            allow_delegation=False,
            llm=self.crewai_service.llm
        )
        
        compliance_checker_agent = Agent(
            role="Compliance and Security Specialist",
            goal="Ensure applications meet regulatory and security compliance requirements",
            backstory="""You are a compliance expert specializing in:
            - Regulatory frameworks (SOC2, HIPAA, PCI-DSS, GDPR)
            - Security standards (NIST, ISO 27001)
            - Industry-specific compliance requirements
            - Data privacy and governance
            - Audit and compliance reporting
            You identify compliance gaps and recommend remediation strategies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.crewai_service.llm
        )
        
        return [architecture_standards_agent, compliance_checker_agent]
    
    def _create_tasks(self, agents: List[Agent], inputs: Dict[str, Any]) -> List[Task]:
        """Create tasks for architecture verification"""
        
        architecture_standards_agent, compliance_checker_agent = agents
        
        # Task 1: Review architecture standards
        review_architecture_task = Task(
            description=f"""Review the architecture of {len(inputs['applications'])} applications against enterprise standards.
            
            Client Requirements:
            {inputs.get('client_requirements', {})}
            
            For each application, verify:
            1. Architecture pattern compliance (microservices, SOA, etc.)
            2. Cloud readiness assessment
            3. API standards and integration patterns
            4. Data architecture compliance
            5. Security architecture standards
            
            Provide a detailed assessment with:
            - Compliance status for each requirement
            - Identified gaps and issues
            - Risk level for non-compliance
            - Recommendations for remediation""",
            agent=architecture_standards_agent,
            expected_output="Detailed architecture compliance report with issues and recommendations"
        )
        
        # Task 2: Check compliance requirements
        check_compliance_task = Task(
            description=f"""Perform compliance and security assessment for the applications.
            
            Industry: {self.context.industry}
            Compliance Requirements: {self.context.compliance_requirements}
            
            Evaluate:
            1. Regulatory compliance (SOC2, HIPAA, PCI-DSS as applicable)
            2. Security standards compliance
            3. Data privacy requirements
            4. Audit trail capabilities
            5. Access control and authentication
            
            Output:
            - Compliance status by framework
            - Critical compliance gaps
            - Security vulnerabilities
            - Remediation priorities""",
            agent=compliance_checker_agent,
            expected_output="Comprehensive compliance assessment with gap analysis"
        )
        
        # Task 3: Consolidate verification results
        consolidate_results_task = Task(
            description="""Consolidate architecture and compliance verification results.
            
            Create a unified assessment that:
            1. Summarizes all verification results
            2. Prioritizes issues by severity
            3. Identifies blockers for migration
            4. Provides clear pass/fail status
            5. Recommends remediation actions
            
            Format the output for use in 6R strategy determination.""",
            agent=architecture_standards_agent,
            expected_output="Consolidated verification report with clear recommendations",
            context=[review_architecture_task, check_compliance_task]
        )
        
        return [review_architecture_task, check_compliance_task, consolidate_results_task]
    
    def kickoff(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the architecture verification crew"""
        logger.info(f"Starting Architecture Verification Crew for {len(inputs['applications'])} applications")
        
        try:
            # Create agents and tasks
            agents = self._create_agents()
            tasks = self._create_tasks(agents, inputs)
            
            # Create and execute crew
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                manager_llm=self.crewai_service.llm
            )
            
            result = crew.kickoff()
            
            # Parse and structure results
            return self._parse_results(result)
            
        except Exception as e:
            logger.error(f"Architecture Verification Crew failed: {str(e)}")
            raise
    
    def _parse_results(self, crew_output: Any) -> Dict[str, Any]:
        """Parse crew output into structured format"""
        # Implementation to parse crew output into structured requirements
        return {
            "requirements": [...],  # List of ArchitectureRequirement objects
            "all_verified": True/False,
            "issues": [...],
            "insights": [...]
        }
```

#### AI-002: Create Technical Debt Analysis Crew
**Priority**: P1 - High  
**Effort**: 8 hours  
**Location**: `backend/app/services/crewai_flows/crews/tech_debt_analysis_crew.py`

Similar structure to above, with agents for:
- Code Quality Analyst
- Security Scanner Agent  
- Performance Analyzer

#### AI-003: Create Six R Strategy Crew
**Priority**: P1 - High  
**Effort**: 8 hours  
**Location**: `backend/app/services/crewai_flows/crews/sixr_strategy_crew.py`

Agents:
- Migration Strategy Expert
- Cost-Benefit Analyst
- Risk Assessment Specialist

#### AI-004: Create Agent Tools for Assessment
**Priority**: P2 - Medium  
**Effort**: 6 hours  
**Location**: `backend/app/services/crewai_flows/tools/assessment_tools.py`

```python
from crewai_tools import BaseTool
from typing import Dict, Any

class ArchitecturePatternMatcher(BaseTool):
    name: str = "Architecture Pattern Matcher"
    description: str = "Matches application architecture against known patterns"
    
    def _run(self, application_data: Dict[str, Any]) -> str:
        """Analyze application and identify architecture pattern"""
        # Implementation

class TechDebtCalculator(BaseTool):
    name: str = "Technical Debt Calculator"
    description: str = "Calculates technical debt score based on multiple factors"
    
    def _run(self, debt_items: List[Dict[str, Any]]) -> float:
        """Calculate overall tech debt score"""
        # Implementation

class MigrationCostEstimator(BaseTool):
    name: str = "Migration Cost Estimator"
    description: str = "Estimates migration cost for different 6R strategies"
    
    def _run(self, app_data: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """Estimate cost for given strategy"""
        # Implementation

class RiskScoringTool(BaseTool):
    name: str = "Risk Scoring Tool"
    description: str = "Calculates migration risk score"
    
    def _run(self, risk_factors: List[str]) -> float:
        """Calculate risk score"""
        # Implementation
```

#### AI-005: Implement Learning Feedback System
**Priority**: P2 - Medium  
**Effort**: 6 hours  
**Location**: `backend/app/services/learning/assessment_learning.py`

Implement feedback capture and learning system.

---

### 🔄 Migration Tasks

#### MIG-001: Move Tech Debt Analysis from Discovery
**Priority**: P1 - High  
**Effort**: 4 hours  

1. Remove Tech Debt Analysis Agent from `unified_discovery_flow.py`
2. Update the parallel analysis phase to only include:
   - Asset Inventory Agent
   - Dependency Analysis Agent
3. Update flow progress percentages
4. Test Discovery Flow still works without tech debt

## Development Guidelines

### CrewAI Best Practices
- Each crew should have a clear manager LLM
- Agents should have detailed backstories for better context
- Tasks should reference previous task outputs using `context=[]`
- Use verbose=True during development for debugging
- Handle crew failures gracefully with try/except

### State Management
- Always update state after each phase
- Use FlowStateBridge for persistence
- Include progress percentage updates
- Capture agent insights for learning

### Testing Your Implementation
```bash
# Test your flow
docker exec -it migration_backend python -c "
from app.services.crewai_flows.assessment_flow import AssessmentFlow
from app.services.crewai_service import CrewAIService
from app.core.flow_context import FlowContext

# Create test context
context = FlowContext(
    flow_id='test-assessment-001',
    client_account_id=1,
    engagement_id=1
)

# Initialize flow
crewai_service = CrewAIService()
flow = AssessmentFlow(crewai_service, context)

# Test initialization
result = flow.initialize_assessment()
print(result)
"

# Run crew tests
docker exec -it migration_backend python -m pytest tests/crews/test_assessment_crews.py -v
```

### Integration Requirements
- Coordinate with Agent 1 for model availability
- Work with Agent 3 for API integration points
- Ensure state updates trigger real-time notifications
- Follow existing CrewAI patterns from Discovery Flow

### Performance Considerations
- Crews can run for several minutes - implement proper async handling
- Use crew manager for parallel agent execution where possible
- Cache LLM responses for similar assessments
- Implement timeout handling for long-running crews

## Completion Checklist
- [ ] BE-003: Complete AssessmentFlow implementation
- [ ] BE-004: FlowStateBridge for assessment
- [ ] AI-001: Architecture Verification Crew
- [ ] AI-002: Technical Debt Analysis Crew  
- [ ] AI-003: Six R Strategy Crew
- [ ] AI-004: Assessment tools for agents
- [ ] AI-005: Learning feedback system
- [ ] MIG-001: Remove tech debt from Discovery
- [ ] Integration tests for full flow
- [ ] Performance testing with multiple apps

## Dependencies
- Requires Agent 1's models and database schema
- Your flow will be called by Agent 3's API endpoints
- Agent 4 needs your state structure for frontend