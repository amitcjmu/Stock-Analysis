# Collection Flow - CrewAI Agent Architecture Specifications

## Document Purpose

This document provides detailed specifications for implementing the Adaptive Data Collection System (ADCS) using CrewAI agents, crews, and flows. It ensures complete adherence to the DETAILED_SPECIFICATIONS.md requirements while maintaining consistency with existing Discovery and Assessment flow implementations.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent Reuse Strategy](#agent-reuse-strategy) 
3. [Collection Flow Definition](#collection-flow-definition)
4. [Phase-Specific Crew Compositions](#phase-specific-crew-compositions)
5. [Agent Specifications](#agent-specifications)
6. [Tool Specifications](#tool-specifications)
7. [Task Definitions](#task-definitions)
8. [Master Flow Orchestrator Integration](#master-flow-orchestrator-integration)
9. [Implementation Guidelines](#implementation-guidelines)

## Architecture Overview

The Collection Flow follows CrewAI Flow patterns with four distinct phases orchestrated by the Master Flow Orchestrator:

```
Collection Flow (Tier-Adaptive Data Collection)
├── Phase 1: Platform Detection (Tier Assessment)
├── Phase 2: Automated Collection (API/Scanner Based)
├── Phase 3: Gap Analysis (Critical Attribute Assessment) 
└── Phase 4: Manual Collection (Adaptive Forms & Validation)
```

### Core Principles

1. **Agent-First Architecture**: All logic is controlled by CrewAI agents - no hardcoded heuristics
2. **Agentic Decision Making**: Tier assessment, gap analysis, and collection strategies emerge from agent collaboration
3. **Reuse Existing Agents**: Leverage existing AssetIntelligenceAgent, DataValidationExpert, etc.
4. **Deterministic Confidence Scoring**: Based on 22 critical attributes framework
5. **Master Flow Integration**: Registers as 9th flow type in the Migration UI Orchestrator

## Agent Reuse Strategy

### Existing Agents to Leverage

From existing Discovery and Assessment flows:

```python
# Core Intelligence Agents (from Discovery Flow)
- AssetIntelligenceAgent: Asset discovery, classification, environment analysis
- DataValidationExpert: Data quality assessment, validation rules
- PatternRecognitionAgent: Technology stack detection, architecture patterns

# Analysis Agents (from Assessment Flow) 
- BusinessContextAnalyzer: Criticality scoring, stakeholder impact
- TechnologyStackAnalyzer: Framework detection, dependency analysis
- ComplianceAnalyzer: Regulatory requirements, security constraints

# Data Processing Agents (from Discovery Flow)
- DataCleansingAgent: Data normalization, duplicate detection
- FieldMappingAgent: Schema mapping, field transformation
```

### New Collection-Specific Agents

```python
# Platform Detection Specialists
- PlatformDetectionAgent: Automation capability assessment
- CredentialValidationAgent: Access level verification
- TierRecommendationAgent: Automation tier determination

# Collection Orchestration
- CollectionOrchestratorAgent: Collection strategy coordination
- QuestionnaireDynamicsAgent: Adaptive form generation
- ProgressTrackingAgent: Collection progress monitoring

# Gap Analysis Specialists  
- CriticalAttributeAssessor: 22-attribute framework evaluation
- GapPrioritizationAgent: Missing attribute impact analysis
- ValidationWorkflowAgent: Data completeness verification
```

## Collection Flow Definition

### UnifiedCollectionFlow Class

```python
from crewai import Flow
from crewai.flow.flow import listen, start
from app.services.crewai_flows.unified_discovery_flow.base_flow import UnifiedDiscoveryFlow

class UnifiedCollectionFlow(Flow):
    """
    Unified Collection Flow - Tier-Adaptive Data Collection
    
    Integrates with Master Flow Orchestrator as the 9th flow type.
    Implements 4-phase collection strategy with full agent autonomy.
    """
    
    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        super().__init__()
        
        self.crewai_service = crewai_service
        self.context = context
        self._flow_id = kwargs.get('flow_id') or str(uuid.uuid4())
        self._master_flow_id = kwargs.get('master_flow_id')
        
        # Initialize phase managers
        self.platform_detection_manager = PlatformDetectionManager(crewai_service, context)
        self.automated_collection_manager = AutomatedCollectionManager(crewai_service, context)
        self.gap_analysis_manager = GapAnalysisManager(crewai_service, context)  
        self.manual_collection_manager = ManualCollectionManager(crewai_service, context)
        
        logger.info(f"🚀 Collection Flow {self._flow_id} initialized with agent-first architecture")

    @start()
    def initialize_collection(self) -> Dict[str, Any]:
        """Entry point - Initialize collection flow with discovery context"""
        return {
            "flow_id": self._flow_id,
            "flow_type": "collection",
            "phase": "initialization",
            "automation_tier": None,
            "collected_attributes": {},
            "confidence_score": 0.0,
            "critical_gaps": [],
            "collection_strategy": None
        }

    @listen(initialize_collection)
    def platform_detection_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Platform Detection and Tier Assessment"""
        return self.platform_detection_manager.execute_phase(state)

    @listen(platform_detection_phase)  
    def automated_collection_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Automated Collection via APIs and Scanners"""
        return self.automated_collection_manager.execute_phase(state)

    @listen(automated_collection_phase)
    def gap_analysis_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Gap Analysis and Critical Attribute Assessment"""
        return self.gap_analysis_manager.execute_phase(state)

    @listen(gap_analysis_phase)
    def manual_collection_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Manual Collection via Adaptive Forms"""
        return self.manual_collection_manager.execute_phase(state)
```

## Phase-Specific Crew Compositions

### Phase 1: Platform Detection Crew

**Objective**: Determine automation tier and platform capabilities through agent collaboration

```python
class PlatformDetectionCrew:
    """
    Determines automation tier through intelligent agent assessment
    NO hardcoded logic - agents collaboratively evaluate capabilities
    """
    
    def create_crew(self) -> Crew:
        return Crew(
            agents=[
                self.asset_intelligence_agent,  # Reused from Discovery
                self.platform_detection_agent,  # New specialist
                self.credential_validation_agent,  # New specialist  
                self.tier_recommendation_agent  # New specialist
            ],
            tasks=[
                DetectCloudPlatformsTask(),
                ValidateAccessCredentialsTask(), 
                AssessAutomationCapabilitiesTask(),
                RecommendOptimalTierTask()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            max_iter=3,
            allow_delegation=True
        )

# Agent Configurations
platform_detection_agent = Agent(
    role="Platform Detection Specialist",
    goal="Intelligently assess automation capabilities across cloud and on-premise platforms",
    backstory="Expert in evaluating platform automation capabilities through API analysis, credential validation, and service discovery. Makes tier recommendations based on access levels and automation potential.",
    tools=[
        AWSCapabilityAssessor(),
        AzureCapabilityAssessor(), 
        GCPCapabilityAssessor(),
        OnPremiseCapabilityAssessor(),
        AutomationPotentialEvaluator()
    ],
    allow_delegation=True,
    verbose=True
)

credential_validation_agent = Agent(
    role="Credential and Access Validator",
    goal="Validate and assess the scope of available credentials and access permissions",
    backstory="Security-focused agent that evaluates credential strength, permission scope, and access limitations to determine automation feasibility.",
    tools=[
        CredentialScopeAnalyzer(),
        PermissionValidator(),
        APIAccessTester(),
        SecurityConstraintAnalyzer()
    ],
    allow_delegation=True,
    verbose=True
)

tier_recommendation_agent = Agent(
    role="Tier Strategy Recommender", 
    goal="Synthesize platform capabilities into optimal automation tier recommendation",
    backstory="Strategic agent that combines platform assessment, access analysis, and business context to recommend the most effective automation tier (1-4) with detailed justification.",
    tools=[
        TierEvaluationMatrix(),
        BusinessContextIntegrator(),
        RiskAssessmentTool(),
        ConfidenceScoreCalculator()
    ],
    allow_delegation=True,
    verbose=True
)
```

### Phase 2: Automated Collection Crew

**Objective**: Execute automated data collection based on determined tier

```python
class AutomatedCollectionCrew:
    """
    Executes automated collection strategies based on tier assessment
    Adapts collection approach based on platform capabilities
    """
    
    def create_crew(self) -> Crew:
        return Crew(
            agents=[
                self.collection_orchestrator_agent,  # New specialist
                self.asset_intelligence_agent,  # Reused from Discovery
                self.data_validation_expert,  # Reused from Discovery
                self.technology_stack_analyzer  # Reused from Assessment
            ],
            tasks=[
                OrchestratePlatformCollectionTask(),
                ExecuteCloudAPICollectionTask(),
                ValidateCollectedDataTask(),
                AnalyzeTechnologyStackTask(),
                CalculateInitialConfidenceTask()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            max_iter=5,
            allow_delegation=True
        )

# New Agent Configuration
collection_orchestrator_agent = Agent(
    role="Collection Strategy Orchestrator",
    goal="Coordinate and execute automated collection strategies across multiple platforms and data sources",
    backstory="Master coordinator that orchestrates collection workflows, manages platform adapters, and ensures comprehensive data gathering within automation tier constraints.",
    tools=[
        PlatformAdapterOrchestrator(),
        CollectionStrategyPlanner(), 
        DataSourcePrioritizer(),
        CollectionProgressTracker(),
        ErrorRecoveryManager()
    ],
    allow_delegation=True,
    verbose=True
)
```

### Phase 3: Gap Analysis Crew

**Objective**: Identify missing critical attributes and prioritize collection efforts

```python
class GapAnalysisCrew:
    """
    Analyzes collected data against 22 critical attributes framework
    Identifies high-priority gaps for manual collection
    """
    
    def create_crew(self) -> Crew:
        return Crew(
            agents=[
                self.critical_attribute_assessor,  # New specialist
                self.gap_prioritization_agent,  # New specialist
                self.business_context_analyzer,  # Reused from Assessment
                self.data_validation_expert  # Reused from Discovery  
            ],
            tasks=[
                AssessCriticalAttributeCompletenessTask(),
                IdentifyHighImpactGapsTask(),
                PrioritizeCollectionEffortsTask(),
                GenerateTargetedQuestionsTask(),
                UpdateConfidenceScoreTask()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            max_iter=3,
            allow_delegation=True
        )

# New Agent Configurations
critical_attribute_assessor = Agent(
    role="Critical Attribute Assessment Specialist",
    goal="Evaluate collected data completeness against the 22 critical attributes framework for accurate 6R recommendations",
    backstory="Expert in migration-critical data assessment, specializing in identifying which of the 22 essential attributes (infrastructure, application, business context, technical debt) are present, missing, or incomplete.",
    tools=[
        CriticalAttributeMapper(),
        AttributeCompletenessAnalyzer(),
        ConfidenceImpactCalculator(),
        DataQualityAssessor()
    ],
    allow_delegation=True,
    verbose=True
)

gap_prioritization_agent = Agent(
    role="Gap Impact Prioritization Specialist", 
    goal="Prioritize missing attributes based on business impact and 6R recommendation confidence improvement potential",
    backstory="Strategic analyst that determines which missing data points have the highest impact on recommendation quality, considering business criticality, technical complexity, and collection feasibility.",
    tools=[
        BusinessImpactCalculator(),
        GapImpactAnalyzer(),
        CollectionFeasibilityAssessor(),
        PrioritizationMatrix()
    ],
    allow_delegation=True,
    verbose=True
)
```

### Phase 4: Manual Collection Crew

**Objective**: Orchestrate adaptive forms and manual data collection workflows

```python
class ManualCollectionCrew:
    """
    Manages adaptive questionnaires and manual collection workflows
    Generates dynamic forms based on gap analysis results
    """
    
    def create_crew(self) -> Crew:
        return Crew(
            agents=[
                self.questionnaire_dynamics_agent,  # New specialist
                self.validation_workflow_agent,  # New specialist
                self.progress_tracking_agent,  # New specialist
                self.data_validation_expert  # Reused from Discovery
            ],
            tasks=[
                GenerateAdaptiveQuestionnaireTask(),
                CreateValidationWorkflowTask(),
                MonitorCollectionProgressTask(),
                ValidateManualInputsTask(),
                CalculateFinalConfidenceTask()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            max_iter=4,
            allow_delegation=True
        )

# New Agent Configurations
questionnaire_dynamics_agent = Agent(
    role="Adaptive Questionnaire Generator",
    goal="Generate intelligent, context-aware questionnaires that adapt based on collected data and missing critical attributes",
    backstory="Expert in creating dynamic forms that adapt question flow, validation rules, and user experience based on business context, technical complexity, and user expertise level.",
    tools=[
        AdaptiveFormGenerator(),
        ConditionalLogicBuilder(),
        ValidationRuleCreator(),
        UserExperienceOptimizer()
    ],
    allow_delegation=True,
    verbose=True
)

validation_workflow_agent = Agent(
    role="Data Validation Workflow Specialist",
    goal="Design and implement comprehensive validation workflows for manually collected data",
    backstory="Quality assurance expert that creates multi-stage validation processes, ensuring data integrity, completeness, and business rule compliance for manually collected information.",
    tools=[
        ValidationWorkflowDesigner(),
        BusinessRuleValidator(),
        DataIntegrityChecker(),
        QualityAssuranceTools()
    ],
    allow_delegation=True,
    verbose=True
)

progress_tracking_agent = Agent(
    role="Collection Progress Monitor",
    goal="Track collection progress, identify bottlenecks, and optimize collection workflows for maximum efficiency",
    backstory="Process optimization specialist that monitors collection metrics, identifies workflow inefficiencies, and provides real-time insights to improve collection completion rates.",
    tools=[
        ProgressAnalyticsTool(),
        BottleneckDetector(),
        WorkflowOptimizer(),
        UserEngagementTracker()
    ],
    allow_delegation=True,
    verbose=True
)
```

## Tool Specifications

### Platform Detection Tools

```python
class AWSCapabilityAssessor(BaseTool):
    """Assess AWS automation capabilities"""
    name = "aws_capability_assessor"
    description = "Evaluate AWS platform automation capabilities based on available credentials and services"
    
    def _run(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess AWS automation tier potential:
        - API access scope
        - Service discovery capabilities  
        - CloudFormation/CDK support
        - Resource enumeration permissions
        """
        # Implementation details...

class CriticalAttributeMapper(BaseTool):
    """Map collected data to the 22 critical attributes framework"""
    name = "critical_attribute_mapper"
    description = "Maps collected data against the 22 critical attributes required for 6R recommendations"
    
    def _run(self, collected_data: Dict[str, Any]) -> AttributeMapping:
        """
        Evaluates data completeness against:
        - Infrastructure attributes (6)
        - Application attributes (8) 
        - Business context attributes (4)
        - Technical debt attributes (4)
        
        Returns completeness matrix with impact scores
        """
        # Implementation details...

class AdaptiveFormGenerator(BaseTool):
    """Generate adaptive questionnaires based on gap analysis"""
    name = "adaptive_form_generator"
    description = "Creates dynamic questionnaires with conditional logic based on missing critical attributes"
    
    def _run(self, gap_analysis: Dict[str, Any], business_context: Dict[str, Any]) -> AdaptiveForm:
        """
        Generates adaptive forms that:
        - Prioritize high-impact missing attributes
        - Adapt question flow based on user responses
        - Include validation rules and help text
        - Optimize for user expertise level
        """
        # Implementation details...
```

### Confidence Scoring Tools

```python
class ConfidenceScoreCalculator(BaseTool):
    """Calculate deterministic confidence scores for 6R recommendations"""
    name = "confidence_score_calculator"
    description = "Calculates confidence scores using the deterministic methodology from DETAILED_SPECIFICATIONS.md"
    
    def _run(self, collected_attributes: Dict[str, Any]) -> ConfidenceScore:
        """
        Implements deterministic confidence calculation:
        confidence_score = Σ(attribute_weight × attribute_quality_score × attribute_completeness)
        
        Uses predefined weights from DETAILED_SPECIFICATIONS.md:
        - Infrastructure attributes: 25% total weight
        - Application attributes: 45% total weight  
        - Business context attributes: 20% total weight
        - Technical debt attributes: 10% total weight
        """
        
        CRITICAL_ATTRIBUTE_WEIGHTS = {
            # Infrastructure attributes (total: 0.25)
            'os_version': 0.05,
            'specifications': 0.05,
            'network_config': 0.04,
            'virtualization': 0.04,
            'performance_baseline': 0.04,
            'availability_requirements': 0.03,
            
            # Application attributes (total: 0.45)
            'technology_stack': 0.08,
            'architecture_pattern': 0.07,
            'integration_dependencies': 0.06,
            'data_characteristics': 0.06,
            'user_load_patterns': 0.05,
            'business_logic_complexity': 0.05,
            'configuration_complexity': 0.04,
            'security_requirements': 0.04,
            
            # Business context attributes (total: 0.20)
            'business_criticality': 0.08,
            'change_tolerance': 0.05,
            'compliance_constraints': 0.04,
            'stakeholder_impact': 0.03,
            
            # Technical debt attributes (total: 0.10)
            'code_quality': 0.03,
            'security_vulnerabilities': 0.03,
            'eol_technology': 0.02,
            'documentation_quality': 0.02
        }
        
        # Implementation follows DETAILED_SPECIFICATIONS.md methodology
        # Implementation details...
```

## Task Definitions

### Platform Detection Tasks

```python
class DetectCloudPlatformsTask(Task):
    description = """
    Analyze the target environment to identify available cloud platforms and access levels.
    
    Key objectives:
    1. Discover AWS, Azure, GCP, and on-premise platforms
    2. Validate credential scope and permissions
    3. Assess API access capabilities
    4. Identify service discovery potential
    
    Expected output: Structured platform inventory with capability assessment
    """
    expected_output = "JSON structure containing platform inventory, access assessment, and automation potential scores"
    agent = platform_detection_agent

class RecommendOptimalTierTask(Task):
    description = """
    Synthesize platform capabilities and business context to recommend optimal automation tier.
    
    Tier Assessment Criteria (NO hardcoded logic - agent decision):
    - Tier 1 (90% automation): Modern cloud-native with full API access
    - Tier 2 (70% automation): Mixed environments with good automation potential  
    - Tier 3 (40% automation): Restricted access or legacy constraints
    - Tier 4 (10% automation): Highly constrained or air-gapped environments
    
    Expected output: Tier recommendation with detailed justification and confidence score
    """
    expected_output = "Tier recommendation (1-4) with justification, confidence score, and collection strategy"
    agent = tier_recommendation_agent
```

### Gap Analysis Tasks

```python
class AssessCriticalAttributeCompletenessTask(Task):
    description = """
    Evaluate collected data against the 22 critical attributes framework for 6R recommendations.
    
    Critical Attributes to Assess:
    Infrastructure (6): OS version, specifications, network, virtualization, performance, availability
    Application (8): tech stack, architecture, dependencies, data, load patterns, business logic, config, security
    Business Context (4): criticality, change tolerance, compliance, stakeholder impact
    Technical Debt (4): code quality, vulnerabilities, EOL tech, documentation
    
    Expected output: Completeness matrix showing which attributes are present, missing, or incomplete
    """
    expected_output = "Attribute completeness matrix with quality scores and impact assessment"
    agent = critical_attribute_assessor

class IdentifyHighImpactGapsTask(Task):
    description = """
    Identify which missing attributes have the highest impact on 6R recommendation confidence.
    
    Consider:
    1. Attribute weight in confidence calculation
    2. Business criticality of the application
    3. Migration complexity factors
    4. Regulatory/compliance requirements
    
    Expected output: Prioritized list of missing attributes with impact scores and collection feasibility
    """
    expected_output = "Prioritized gap analysis with business impact scores and recommended collection methods"
    agent = gap_prioritization_agent
```

### Manual Collection Tasks

```python
class GenerateAdaptiveQuestionnaireTask(Task):
    description = """
    Create intelligent questionnaires that adapt based on missing critical attributes and business context.
    
    Questionnaire Features:
    1. Conditional logic based on user responses
    2. Progressive disclosure for complex topics
    3. Context-aware help and validation
    4. User expertise level adaptation
    5. Business criticality-based prioritization
    
    Expected output: Adaptive questionnaire with conditional logic, validation rules, and user experience optimization
    """
    expected_output = "Adaptive questionnaire configuration with conditional logic and validation rules"
    agent = questionnaire_dynamics_agent

class MonitorCollectionProgressTask(Task):
    description = """
    Monitor collection progress, identify bottlenecks, and provide optimization recommendations.
    
    Progress Metrics:
    1. Attribute completion percentage
    2. User engagement metrics
    3. Data quality indicators
    4. Confidence score improvement
    5. Collection time efficiency
    
    Expected output: Progress analytics with bottleneck identification and optimization recommendations
    """
    expected_output = "Progress analytics dashboard with optimization recommendations and efficiency metrics"
    agent = progress_tracking_agent
```

## Master Flow Orchestrator Integration

### Flow Registration

```python
# In app/services/flow_type_registry.py
class FlowTypeRegistry:
    SUPPORTED_FLOW_TYPES = {
        "discovery": UnifiedDiscoveryFlow,
        "assessment": UnifiedAssessmentFlow,
        "collection": UnifiedCollectionFlow,  # NEW: 9th flow type
        # ... other flows
    }

# In app/services/master_flow_orchestrator.py  
class MasterFlowOrchestrator:
    def create_collection_flow(
        self,
        context: RequestContext,
        collection_config: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Create and initialize Collection Flow"""
        
        flow_id = str(uuid.uuid4())
        master_flow_id = kwargs.get('master_flow_id')
        
        # Initialize Collection Flow with CrewAI agents
        collection_flow = UnifiedCollectionFlow(
            crewai_service=self.crewai_service,
            context=context,
            flow_id=flow_id,
            master_flow_id=master_flow_id,
            **collection_config
        )
        
        # Register with flow manager
        self._register_flow(flow_id, collection_flow, "collection")
        
        # Start collection flow execution
        flow_result = collection_flow.kickoff()
        
        return {
            "flow_id": flow_id,
            "flow_type": "collection", 
            "status": "initialized",
            "automation_tier": flow_result.get("automation_tier"),
            "collection_strategy": flow_result.get("collection_strategy"),
            "progress": flow_result.get("progress", {})
        }
```

### Flow State Management

```python
# Collection Flow State Extensions
class CollectionFlowState(BaseModel):
    """State management for Collection Flow"""
    
    # Core flow identifiers
    flow_id: str
    master_flow_id: Optional[str]
    
    # Phase tracking
    current_phase: str  # platform_detection, automated_collection, gap_analysis, manual_collection
    automation_tier: Optional[int]  # 1-4 based on agent assessment
    
    # Collection progress
    collected_attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    critical_gaps: List[str] = Field(default_factory=list)
    
    # Platform capabilities
    platform_inventory: Dict[str, Any] = Field(default_factory=dict)
    collection_strategy: Optional[str] = None
    
    # Manual collection state
    adaptive_questionnaire: Optional[Dict[str, Any]] = None
    user_responses: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Progress tracking
    completion_percentage: float = 0.0
    phase_completion: Dict[str, bool] = Field(default_factory=dict)
    collection_metrics: Dict[str, Any] = Field(default_factory=dict)
```

## Implementation Guidelines

### 1. Agent Autonomy Requirements

- **NO hardcoded tier assessment logic**: Agents must collaboratively determine automation tiers
- **NO fixed collection strategies**: Collection approaches emerge from agent analysis
- **NO predetermined questionnaire templates**: Forms are dynamically generated by agents
- **Agent-driven confidence scoring**: While using deterministic formula, agents assess data quality

### 2. Integration with Existing Flows

- **Reuse Discovery assets**: Collection Flow can access Discovery Flow results
- **Coordinate with Assessment**: Share collected attributes with Assessment Flow
- **Master Flow coordination**: Report progress and results to Master Flow Orchestrator
- **State persistence**: Use existing CrewAI Flow state management patterns

### 3. Error Handling and Recovery

```python
class CollectionFlowErrorHandler:
    """Specialized error handling for Collection Flow"""
    
    def handle_platform_detection_failure(self, error: Exception, context: Dict[str, Any]):
        """Handle platform detection phase failures"""
        # Graceful degradation to manual collection
        # Agent-driven recovery strategy
        
    def handle_automation_failure(self, error: Exception, tier: int):
        """Handle automated collection failures"""
        # Tier adjustment through agent analysis
        # Fallback strategy determination
        
    def handle_questionnaire_generation_failure(self, error: Exception, gaps: List[str]):
        """Handle adaptive questionnaire failures"""
        # Simplified form generation
        # Manual fallback procedures
```

### 4. Performance and Scalability

- **Async execution**: All agent crews support async execution
- **Batch processing**: Support for multi-application collection
- **Progress streaming**: Real-time progress updates to UI
- **Resource management**: Memory and compute optimization for large datasets

### 5. Testing Strategy

```python
# Unit tests for individual agents
class TestPlatformDetectionAgent:
    def test_aws_capability_assessment(self):
        # Test agent decisions for AWS tier assessment
        
    def test_tier_recommendation_logic(self):
        # Verify agent collaboration produces consistent tier recommendations

# Integration tests for crew coordination  
class TestCollectionFlowIntegration:
    def test_end_to_end_tier_1_collection(self):
        # Test complete flow for modern cloud-native environment
        
    def test_gap_analysis_to_questionnaire_flow(self):
        # Test gap analysis driving adaptive questionnaire generation

# Performance tests
class TestCollectionFlowPerformance:
    def test_large_scale_collection(self):
        # Test collection across 100+ applications
        
    def test_concurrent_collection_flows(self):
        # Test multiple concurrent collection flows
```

## Conclusion

This specification ensures the Collection Flow implementation:

1. **Maintains agent autonomy**: All decisions emerge from CrewAI agent collaboration
2. **Reuses existing agents**: Leverages proven Discovery and Assessment agents  
3. **Follows established patterns**: Consistent with existing flow implementations
4. **Integrates seamlessly**: Registers as 9th flow type with Master Flow Orchestrator
5. **Implements requirements**: Adheres to all DETAILED_SPECIFICATIONS.md requirements
6. **Supports scalability**: Designed for enterprise-scale collection operations

The implementation must prioritize agent-driven decision making over procedural logic, ensuring the system's intelligence emerges from agent collaboration rather than hardcoded heuristics.