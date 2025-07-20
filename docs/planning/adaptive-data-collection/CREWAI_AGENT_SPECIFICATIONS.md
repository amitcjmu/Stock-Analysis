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

## Agent Implementations

### Base Agent Pattern

All new agents must inherit from `BaseCrewAIAgent` and provide metadata for registration:

```python
# File: backend/app/services/agents/platform_detection_agent.py

from typing import List, Dict, Any
from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.registry import AgentMetadata
from app.services.llm_config import get_crewai_llm

class PlatformDetectionAgent(BaseCrewAIAgent):
    """
    Assesses platform automation capabilities through intelligent analysis.
    
    Capabilities:
    - Cloud platform detection (AWS, Azure, GCP)
    - On-premise environment assessment
    - API access validation
    - Service discovery
    - Automation potential scoring
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Platform Detection Specialist",
            goal="Intelligently assess automation capabilities across cloud and on-premise platforms",
            backstory="""You are an expert in evaluating platform automation capabilities. 
            You excel at:
            - Analyzing cloud platform features and limitations
            - Validating API access and permissions
            - Discovering available services and resources
            - Assessing automation potential based on access levels
            - Making tier recommendations without hardcoded logic
            
            Your assessments enable optimal collection strategies.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="platform_detection_agent",
            description="Assesses platform automation capabilities and tier potential",
            agent_class=cls,
            required_tools=[
                "aws_capability_assessor",
                "azure_capability_assessor",
                "gcp_capability_assessor",
                "on_premise_capability_assessor",
                "automation_potential_evaluator"
            ],
            capabilities=[
                "platform_detection",
                "tier_assessment",
                "capability_analysis",
                "access_validation"
            ],
            max_iter=3,
            memory=True,
            verbose=True,
            allow_delegation=True
        )
```

### Critical Attribute Assessor Example

```python
# File: backend/app/services/agents/critical_attribute_assessor.py

class CriticalAttributeAssessor(BaseCrewAIAgent):
    """
    Evaluates collected data against 22 critical attributes framework.
    
    Capabilities:
    - Attribute completeness assessment
    - Quality scoring
    - Impact analysis
    - Gap identification
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Critical Attribute Assessment Specialist",
            goal="Evaluate collected data completeness against the 22 critical attributes framework",
            backstory="""You are an expert in migration-critical data assessment. 
            You specialize in:
            - Evaluating infrastructure attributes (OS, specs, network, etc.)
            - Assessing application attributes (tech stack, architecture, etc.)
            - Analyzing business context (criticality, compliance, etc.)
            - Measuring technical debt indicators
            - Calculating confidence impacts
            
            Your analysis ensures accurate 6R recommendations.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        return AgentMetadata(
            name="critical_attribute_assessor",
            description="Evaluates data completeness against 22 critical attributes",
            agent_class=cls,
            required_tools=[
                "critical_attribute_mapper",
                "attribute_completeness_analyzer",
                "confidence_impact_calculator",
                "data_quality_assessor"
            ],
            capabilities=[
                "attribute_assessment",
                "completeness_analysis",
                "quality_scoring",
                "gap_detection"
            ],
            max_iter=3,
            memory=True,
            verbose=True,
            allow_delegation=True
        )
```

## Crew Implementations

### Phase 1: Platform Detection Crew

**Objective**: Determine automation tier and platform capabilities through agent collaboration

```python
# File: backend/app/services/crewai_flows/crews/platform_detection_crew.py

import logging
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process

from app.services.agents.platform_detection_agent import PlatformDetectionAgent
from app.services.agents.credential_validation_agent import CredentialValidationAgent
from app.services.agents.tier_recommendation_agent import TierRecommendationAgent
from app.services.agents.asset_intelligence_agent_crewai import AssetIntelligenceAgent

logger = logging.getLogger(__name__)

def create_platform_detection_crew(
    crewai_service,
    platform_config: Dict[str, Any],
    discovery_context: Dict[str, Any],
    shared_memory: Optional[Any] = None
) -> Crew:
    """
    Create platform detection crew for tier assessment.
    
    Args:
        crewai_service: CrewAI service instance
        platform_config: Platform detection configuration
        discovery_context: Context from discovery flow
        shared_memory: Shared memory for agent learning
    
    Returns:
        CrewAI Crew for platform detection
    """
    
    try:
        # Get LLM from service
        llm = crewai_service.get_llm()
        
        # Import optimized config
        from .crew_config import DEFAULT_AGENT_CONFIG, get_optimized_crew_config
        
        # Initialize agents with proper tools
        asset_intelligence = AssetIntelligenceAgent(
            tools=crewai_service.get_tools_for_agent("asset_intelligence_agent"),
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG
        )
        
        platform_detection = PlatformDetectionAgent(
            tools=crewai_service.get_tools_for_agent("platform_detection_agent"),
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG
        )
        
        credential_validation = CredentialValidationAgent(
            tools=crewai_service.get_tools_for_agent("credential_validation_agent"),
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG
        )
        
        tier_recommendation = TierRecommendationAgent(
            tools=crewai_service.get_tools_for_agent("tier_recommendation_agent"),
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG
        )
        
        # Create tasks
        detect_platforms_task = Task(
            description=f"""Analyze the target environment to identify available platforms.
            
            Context:
            - Discovery data: {discovery_context}
            - Platform config: {platform_config}
            
            Identify all cloud platforms (AWS, Azure, GCP) and on-premise environments.
            Validate access credentials and assess automation capabilities.
            
            Output JSON with platform inventory and capability scores.""",
            agent=platform_detection,
            expected_output="Platform inventory with automation capability assessment"
        )
        
        validate_credentials_task = Task(
            description="""Validate credentials and assess access scope.
            
            Analyze credential strength, permission boundaries, and API access.
            Identify any security constraints or limitations.
            
            Output credential validation results and access assessment.""",
            agent=credential_validation,
            expected_output="Credential scope analysis with security assessment"
        )
        
        assess_capabilities_task = Task(
            description="""Assess overall automation capabilities.
            
            Synthesize platform features and access levels.
            Evaluate service discovery and API coverage.
            
            Output comprehensive capability assessment.""",
            agent=asset_intelligence,
            expected_output="Automation capability assessment across all platforms"
        )
        
        recommend_tier_task = Task(
            description="""Recommend optimal automation tier (1-4).
            
            NO HARDCODED LOGIC - Use intelligent assessment:
            - Tier 1: 90% automation potential
            - Tier 2: 70% automation potential
            - Tier 3: 40% automation potential
            - Tier 4: 10% automation potential
            
            Provide detailed justification and confidence score.""",
            agent=tier_recommendation,
            expected_output="Tier recommendation with justification and collection strategy"
        )
        
        # Create crew with optimized config
        crew_config = get_optimized_crew_config()
        crew = Crew(
            agents=[asset_intelligence, platform_detection, credential_validation, tier_recommendation],
            tasks=[detect_platforms_task, validate_credentials_task, assess_capabilities_task, recommend_tier_task],
            process=Process.sequential,
            **crew_config
        )
        
        logger.info("✅ Platform Detection Crew created successfully")
        return crew
        
    except Exception as e:
        logger.error(f"❌ Failed to create platform detection crew: {e}")
        raise
```

### Phase 2: Automated Collection Crew

**Objective**: Execute automated data collection based on determined tier

```python
# File: backend/app/services/crewai_flows/crews/automated_collection_crew.py

def create_automated_collection_crew(
    crewai_service,
    automation_tier: int,
    platform_inventory: Dict[str, Any],
    shared_memory: Optional[Any] = None
) -> Crew:
    """
    Create automated collection crew based on tier assessment.
    
    Args:
        crewai_service: CrewAI service instance
        automation_tier: Determined automation tier (1-4)
        platform_inventory: Platform capabilities from detection phase
        shared_memory: Shared memory for agent learning
    
    Returns:
        CrewAI Crew for automated collection
    """
    
    # Initialize agents
    collection_orchestrator = CollectionOrchestratorAgent(
        tools=crewai_service.get_tools_for_agent("collection_orchestrator_agent"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    # Reuse existing agents
    asset_intelligence = crewai_service.get_agent("asset_intelligence_agent")
    data_validation = crewai_service.get_agent("data_validation_expert")
    tech_stack_analyzer = crewai_service.get_agent("technology_stack_analyzer")
    
    # Create tier-specific tasks
    orchestrate_task = Task(
        description=f"""Orchestrate collection strategy for Tier {automation_tier}.
        
        Platform inventory: {platform_inventory}
        
        Plan and coordinate collection across all available platforms.
        Prioritize data sources based on automation capabilities.""",
        agent=collection_orchestrator,
        expected_output="Collection strategy with prioritized data sources"
    )
    
    # Additional tasks based on tier...
    
    return Crew(
        agents=[collection_orchestrator, asset_intelligence, data_validation, tech_stack_analyzer],
        tasks=[orchestrate_task, ...],
        process=Process.sequential,
        **get_optimized_crew_config()
    )
```

### Phase 3: Gap Analysis Crew

**Objective**: Identify missing critical attributes and prioritize collection efforts

```python
# File: backend/app/services/crewai_flows/crews/gap_analysis_crew.py

def create_gap_analysis_crew(
    crewai_service,
    collected_attributes: Dict[str, Any],
    critical_framework: Dict[str, Any],
    shared_memory: Optional[Any] = None
) -> Crew:
    """
    Create gap analysis crew to assess missing critical attributes.
    
    Args:
        crewai_service: CrewAI service instance
        collected_attributes: Data collected from automated phase
        critical_framework: 22 critical attributes framework
        shared_memory: Shared memory for agent learning
    
    Returns:
        CrewAI Crew for gap analysis
    """
    
    # Initialize new specialists
    critical_assessor = CriticalAttributeAssessor(
        tools=crewai_service.get_tools_for_agent("critical_attribute_assessor"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    gap_prioritizer = GapPrioritizationAgent(
        tools=crewai_service.get_tools_for_agent("gap_prioritization_agent"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    # Reuse existing agents
    business_analyzer = crewai_service.get_agent("business_context_analyzer")
    data_validator = crewai_service.get_agent("data_validation_expert")
    
    # Create tasks
    assess_completeness_task = Task(
        description=f"""Evaluate collected data against 22 critical attributes.
        
        Collected data: {collected_attributes}
        Framework: {critical_framework}
        
        Identify present, missing, and incomplete attributes.
        Calculate quality scores for each attribute.""",
        agent=critical_assessor,
        expected_output="Attribute completeness matrix with quality scores"
    )
    
    identify_gaps_task = Task(
        description="""Identify high-impact missing attributes.
        
        Consider:
        - Confidence score impact
        - Business criticality
        - Collection feasibility
        - Regulatory requirements""",
        agent=gap_prioritizer,
        expected_output="Prioritized gap list with impact scores"
    )
    
    # Additional tasks...
    
    return Crew(
        agents=[critical_assessor, gap_prioritizer, business_analyzer, data_validator],
        tasks=[assess_completeness_task, identify_gaps_task, ...],
        process=Process.sequential,
        **get_optimized_crew_config()
    )
```

### Phase 4: Manual Collection Crew

**Objective**: Orchestrate adaptive forms and manual data collection workflows

```python
# File: backend/app/services/crewai_flows/crews/manual_collection_crew.py

def create_manual_collection_crew(
    crewai_service,
    critical_gaps: List[Dict[str, Any]],
    business_context: Dict[str, Any],
    shared_memory: Optional[Any] = None
) -> Crew:
    """
    Create manual collection crew for adaptive questionnaires.
    
    Args:
        crewai_service: CrewAI service instance
        critical_gaps: Prioritized missing attributes from gap analysis
        business_context: Business and technical context
        shared_memory: Shared memory for agent learning
    
    Returns:
        CrewAI Crew for manual collection
    """
    
    # Initialize manual collection specialists
    questionnaire_generator = QuestionnaireDynamicsAgent(
        tools=crewai_service.get_tools_for_agent("questionnaire_dynamics_agent"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    validation_specialist = ValidationWorkflowAgent(
        tools=crewai_service.get_tools_for_agent("validation_workflow_agent"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    progress_monitor = ProgressTrackingAgent(
        tools=crewai_service.get_tools_for_agent("progress_tracking_agent"),
        llm=crewai_service.get_llm(),
        memory=shared_memory,
        **DEFAULT_AGENT_CONFIG
    )
    
    # Reuse data validation expert
    data_validator = crewai_service.get_agent("data_validation_expert")
    
    # Create adaptive questionnaire task
    generate_questionnaire_task = Task(
        description=f"""Generate adaptive questionnaire for missing attributes.
        
        Critical gaps: {critical_gaps}
        Business context: {business_context}
        
        Create intelligent forms with:
        - Conditional logic
        - Progressive disclosure
        - Context-aware help
        - Validation rules""",
        agent=questionnaire_generator,
        expected_output="Adaptive questionnaire configuration"
    )
    
    # Additional tasks...
    
    return Crew(
        agents=[questionnaire_generator, validation_specialist, progress_monitor, data_validator],
        tasks=[generate_questionnaire_task, ...],
        process=Process.sequential,
        **get_optimized_crew_config()
    )
```

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

## Flow Configuration and Registration

### Flow Configuration

```python
# File: backend/app/services/flow_configs/collection_flow_config.py

from typing import Dict, Any, List
from app.services.flow_type_registry import (
    FlowTypeConfig, 
    PhaseConfig, 
    FlowCapabilities,
    RetryConfig
)

def get_collection_flow_config() -> FlowTypeConfig:
    """Get configuration for Collection Flow"""
    
    return FlowTypeConfig(
        name="collection",
        display_name="Adaptive Data Collection Flow",
        description="Tier-adaptive data collection for 6R migration decisions",
        version="1.0.0",
        phases=[
            PhaseConfig(
                name="platform_detection",
                display_name="Platform Detection",
                description="Assess automation capabilities and determine tier",
                required_inputs=["discovery_context", "platform_config"],
                optional_inputs=["credentials", "access_tokens"],
                validators=["platform_detection_validator"],
                crew_config={
                    "crew_creator": "create_platform_detection_crew",
                    "timeout_seconds": 300
                },
                can_pause=True,
                retry_config=RetryConfig(max_attempts=3),
                metadata={"tier_output": True}
            ),
            PhaseConfig(
                name="automated_collection",
                display_name="Automated Collection",
                description="Execute tier-based automated data collection",
                required_inputs=["automation_tier", "platform_inventory"],
                validators=["collection_data_validator"],
                crew_config={
                    "crew_creator": "create_automated_collection_crew",
                    "timeout_seconds": 600
                },
                can_pause=True,
                metadata={"tier_dependent": True}
            ),
            PhaseConfig(
                name="gap_analysis",
                display_name="Gap Analysis",
                description="Analyze against 22 critical attributes",
                required_inputs=["collected_attributes", "critical_framework"],
                validators=["gap_analysis_validator"],
                crew_config={
                    "crew_creator": "create_gap_analysis_crew",
                    "timeout_seconds": 300
                },
                can_pause=True
            ),
            PhaseConfig(
                name="manual_collection",
                display_name="Manual Collection",
                description="Adaptive questionnaire-based collection",
                required_inputs=["critical_gaps", "business_context"],
                validators=["manual_collection_validator"],
                crew_config={
                    "crew_creator": "create_manual_collection_crew",
                    "timeout_seconds": 900
                },
                can_pause=True,
                can_skip=True,
                metadata={"user_interaction": True}
            )
        ],
        capabilities=FlowCapabilities(
            supports_pause_resume=True,
            supports_rollback=False,
            supports_branching=True,
            supports_iterations=True,
            max_iterations=5,
            supports_scheduling=False,
            supports_parallel_phases=False,
            supports_checkpointing=True,
            required_permissions=["collection.create", "collection.read"]
        ),
        crew_class=UnifiedCollectionFlow,
        initialization_handler="collection_initialization_handler",
        finalization_handler="collection_finalization_handler",
        error_handler="collection_error_handler",
        metadata={
            "confidence_based": True,
            "tier_adaptive": True,
            "critical_attributes": 22
        },
        tags=["collection", "adaptive", "tier-based"]
    )
```

### Flow Registration

```python
# File: backend/app/services/flow_configs/__init__.py
# Add to the FlowConfigurationManager.register_all_flow_types() method:

from .collection_flow_config import get_collection_flow_config

def register_all_flow_types(self) -> None:
    """Register all supported flow types"""
    
    # Existing flows...
    self.registry.register(get_discovery_flow_config())
    self.registry.register(get_assessment_flow_config())
    
    # Register Collection Flow (9th flow type)
    self.registry.register(get_collection_flow_config())
    logger.info("✅ Registered Collection Flow as 9th flow type")
    
    # Other flows...
```

## Master Flow Orchestrator Integration

### Flow Creation Support

```python
# The Master Flow Orchestrator already supports dynamic flow creation
# No changes needed - it uses the registry to validate and create flows

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

## Database Models

### Collection Flow Model

```python
# File: backend/app/models/collection_flow.py

from sqlalchemy import Column, String, Integer, Float, JSON, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import enum

from app.models.base import BaseModel

class CollectionPhase(str, enum.Enum):
    """Collection flow phases"""
    INITIALIZATION = "initialization"
    PLATFORM_DETECTION = "platform_detection"
    AUTOMATED_COLLECTION = "automated_collection"
    GAP_ANALYSIS = "gap_analysis"
    MANUAL_COLLECTION = "manual_collection"
    COMPLETED = "completed"

class AutomationTier(int, enum.Enum):
    """Automation tier levels"""
    TIER_1 = 1  # 90% automation
    TIER_2 = 2  # 70% automation
    TIER_3 = 3  # 40% automation
    TIER_4 = 4  # 10% automation

class CollectionFlow(BaseModel):
    """Main collection flow tracking model"""
    
    __tablename__ = "collection_flows"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.flow_id"))
    
    # Multi-tenant fields
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Flow metadata
    flow_name = Column(String, nullable=False)
    description = Column(String)
    
    # Phase tracking
    current_phase = Column(Enum(CollectionPhase), default=CollectionPhase.INITIALIZATION)
    automation_tier = Column(Enum(AutomationTier), nullable=True)
    
    # Collection progress
    collected_attributes = Column(JSON, default=dict)
    confidence_score = Column(Float, default=0.0)
    critical_gaps = Column(JSON, default=list)
    
    # Platform capabilities
    platform_inventory = Column(JSON, default=dict)
    collection_strategy = Column(String)
    
    # Manual collection state
    adaptive_questionnaire = Column(JSON)
    user_responses = Column(JSON, default=dict)
    validation_results = Column(JSON, default=dict)
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    phase_completion = Column(JSON, default=dict)
    collection_metrics = Column(JSON, default=dict)
    
    # Status tracking
    status = Column(String, default="initialized")
    error_message = Column(String)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    master_flow = relationship("CrewAIFlowStateExtensions", back_populates="collection_flow")
    gap_analysis_results = relationship("CollectionGapAnalysis", back_populates="collection_flow")
    
    def update_phase(self, phase: CollectionPhase) -> None:
        """Update current phase and track completion"""
        if self.current_phase:
            self.phase_completion[self.current_phase.value] = True
        self.current_phase = phase
        self.updated_at = datetime.utcnow()
    
    def calculate_completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        total_phases = len(CollectionPhase) - 2  # Exclude INITIALIZATION and COMPLETED
        completed_phases = sum(1 for v in self.phase_completion.values() if v)
        return (completed_phases / total_phases) * 100 if total_phases > 0 else 0.0

class CollectionGapAnalysis(BaseModel):
    """Gap analysis results for collection flow"""
    
    __tablename__ = "collection_gap_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_flow_id = Column(UUID(as_uuid=True), ForeignKey("collection_flows.id"))
    
    # Gap details
    attribute_name = Column(String, nullable=False)
    attribute_category = Column(String)  # infrastructure, application, business, technical_debt
    
    # Impact assessment
    impact_score = Column(Float)
    confidence_impact = Column(Float)
    business_criticality = Column(Float)
    
    # Collection metadata
    collection_method = Column(String)  # api, scanner, manual
    collection_feasibility = Column(Float)
    estimated_effort = Column(String)
    
    # Questionnaire reference
    questionnaire_id = Column(UUID(as_uuid=True), ForeignKey("adaptive_questionnaires.id"))
    
    # Relationships
    collection_flow = relationship("CollectionFlow", back_populates="gap_analysis_results")
    questionnaire = relationship("AdaptiveQuestionnaire")

class AdaptiveQuestionnaire(BaseModel):
    """Adaptive questionnaire templates"""
    
    __tablename__ = "adaptive_questionnaires"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    
    # Questionnaire structure
    questions = Column(JSON, nullable=False)
    conditional_logic = Column(JSON)
    validation_rules = Column(JSON)
    
    # Metadata
    target_attributes = Column(JSON)  # List of attributes this questionnaire collects
    complexity_level = Column(String)  # basic, intermediate, advanced
    estimated_time_minutes = Column(Integer)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    average_completion_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
# File: backend/tests/services/agents/test_collection_agents.py

import pytest
from unittest.mock import Mock, patch
from app.services.agents.platform_detection_agent import PlatformDetectionAgent
from app.services.agents.critical_attribute_assessor import CriticalAttributeAssessor

class TestPlatformDetectionAgent:
    """Unit tests for PlatformDetectionAgent"""
    
    def test_agent_initialization(self):
        """Test agent initializes with correct metadata"""
        tools = [Mock()]
        agent = PlatformDetectionAgent(tools=tools)
        
        assert agent.role == "Platform Detection Specialist"
        assert "platform_detection" in agent.agent_metadata().capabilities
        
    def test_aws_capability_assessment(self):
        """Test agent decisions for AWS tier assessment"""
        # Test agent collaboration with mocked tools
        
    def test_tier_recommendation_consistency(self):
        """Verify agent produces consistent tier recommendations"""
        # Test multiple runs with same input produce similar results

# File: backend/tests/services/crewai_flows/test_collection_flow_integration.py

class TestCollectionFlowIntegration:
    """Integration tests for complete collection flow"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tier_1_collection(self, test_context):
        """Test complete flow for modern cloud-native environment"""
        # Setup test data with full API access
        # Run collection flow
        # Verify 90% automation achieved
        
    @pytest.mark.asyncio
    async def test_gap_analysis_to_questionnaire_flow(self, test_context):
        """Test gap analysis driving adaptive questionnaire generation"""
        # Create flow with known gaps
        # Verify questionnaire targets missing attributes
        # Test adaptive logic based on responses

# File: backend/tests/performance/test_collection_flow_performance.py

class TestCollectionFlowPerformance:
    """Performance tests for collection flow scalability"""
    
    @pytest.mark.performance
    async def test_large_scale_collection(self):
        """Test collection across 100+ applications"""
        # Create batch of test applications
        # Run concurrent collections
        # Measure throughput and resource usage
        
    @pytest.mark.performance
    async def test_concurrent_collection_flows(self):
        """Test multiple concurrent collection flows"""
        # Spawn multiple flows
        # Verify no resource contention
        # Check completion times
```

### 6. Agent Registration

```python
# File: backend/app/services/agents/__init__.py
# Add new agents to the registry initialization

from app.services.agents.registry import agent_registry

# Import new collection agents
from .platform_detection_agent import PlatformDetectionAgent
from .credential_validation_agent import CredentialValidationAgent
from .tier_recommendation_agent import TierRecommendationAgent
from .collection_orchestrator_agent import CollectionOrchestratorAgent
from .critical_attribute_assessor import CriticalAttributeAssessor
from .gap_prioritization_agent import GapPrioritizationAgent
from .questionnaire_dynamics_agent import QuestionnaireDynamicsAgent
from .validation_workflow_agent import ValidationWorkflowAgent
from .progress_tracking_agent import ProgressTrackingAgent

def register_collection_agents():
    """Register all collection flow agents"""
    
    # Platform Detection Phase
    agent_registry.register(PlatformDetectionAgent.agent_metadata())
    agent_registry.register(CredentialValidationAgent.agent_metadata())
    agent_registry.register(TierRecommendationAgent.agent_metadata())
    
    # Collection Orchestration
    agent_registry.register(CollectionOrchestratorAgent.agent_metadata())
    
    # Gap Analysis Phase
    agent_registry.register(CriticalAttributeAssessor.agent_metadata())
    agent_registry.register(GapPrioritizationAgent.agent_metadata())
    
    # Manual Collection Phase
    agent_registry.register(QuestionnaireDynamicsAgent.agent_metadata())
    agent_registry.register(ValidationWorkflowAgent.agent_metadata())
    agent_registry.register(ProgressTrackingAgent.agent_metadata())
    
    logger.info("✅ Registered 9 new Collection Flow agents")
```

## Conclusion

This specification ensures the Collection Flow implementation:

1. **Maintains agent autonomy**: All decisions emerge from CrewAI agent collaboration
2. **Reuses existing agents**: Leverages proven Discovery and Assessment agents  
3. **Follows established patterns**: Consistent with existing flow implementations
4. **Integrates seamlessly**: Registers as 9th flow type with Master Flow Orchestrator
5. **Implements requirements**: Adheres to all DETAILED_SPECIFICATIONS.md requirements
6. **Supports scalability**: Designed for enterprise-scale collection operations

### Key Implementation Patterns:

- **Agent Structure**: All agents inherit from `BaseCrewAIAgent` and provide `agent_metadata()`
- **Crew Organization**: Separate crew files in `/crews/` directory with standardized creation functions
- **Flow Configuration**: Proper `FlowTypeConfig` in `/flow_configs/` with phase definitions
- **Database Models**: Dedicated models for flow state tracking and gap analysis
- **Testing Strategy**: Comprehensive unit, integration, and performance tests
- **Registration**: Agents and flows registered during application initialization

The implementation must prioritize agent-driven decision making over procedural logic, ensuring the system's intelligence emerges from agent collaboration rather than hardcoded heuristics.