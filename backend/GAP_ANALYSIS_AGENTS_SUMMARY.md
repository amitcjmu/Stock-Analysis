# Gap Analysis Phase Agents - Implementation Summary

## Overview
Created two specialized CrewAI agents for the Gap Analysis phase of the migration discovery process:

1. **CriticalAttributeAssessor** - Evaluates collected data against the 22 critical attributes framework
2. **GapPrioritizationAgent** - Prioritizes missing attributes by business impact and migration strategy requirements

## Critical Attributes Framework (22 Attributes)

### Infrastructure (8 attributes)
- hostname, environment, os_type, os_version
- cpu_cores, memory_gb, storage_gb, network_zone
- Business Impact: High
- 6R Relevance: rehost, replatform, refactor

### Application (6 attributes)
- application_name, application_type, technology_stack
- criticality_level, data_classification, compliance_scope
- Business Impact: Critical
- 6R Relevance: refactor, repurchase, retire

### Operational (6 attributes)
- owner, cost_center, backup_strategy, monitoring_status
- patch_level, last_scan_date
- Business Impact: Medium
- 6R Relevance: retain, rehost, replatform

### Dependencies (4 attributes)
- application_dependencies, database_dependencies
- integration_points, data_flows
- Business Impact: Critical
- 6R Relevance: refactor, replatform, repurchase

## Agents Created

### 1. CriticalAttributeAssessorAgent
**Location**: `backend/app/services/agents/critical_attribute_assessor_crewai.py`

**Purpose**: Evaluates collected data against the 22 critical attributes framework

**Key Features**:
- Maps collected data fields to critical attributes
- Calculates attribute coverage and completeness
- Assesses data quality for each attribute
- Identifies gaps in critical migration data
- Evaluates impact on 6R migration strategies

**Required Tools**:
- attribute_mapper
- completeness_analyzer
- quality_scorer
- gap_identifier

### 2. GapPrioritizationAgent
**Location**: `backend/app/services/agents/gap_prioritization_agent_crewai.py`

**Purpose**: Prioritizes missing critical attributes based on business impact

**Key Features**:
- Analyzes business impact of missing attributes
- Calculates effort vs. value for gap resolution
- Prioritizes gaps by migration strategy requirements
- Recommends collection strategies and sequences
- Estimates time and resources for gap closure

**Required Tools**:
- impact_calculator
- effort_estimator
- priority_ranker
- collection_planner

## Tools Created

**Location**: `backend/app/services/tools/gap_analysis_tools.py`

### 1. AttributeMapperTool
- Maps raw data fields to the 22 critical attributes framework
- Uses pattern matching and similarity scoring
- Provides confidence scores for mappings

### 2. CompletenessAnalyzerTool
- Analyzes completeness of critical attributes in collected data
- Calculates coverage percentages by category
- Identifies quality issues and generates recommendations

### 3. QualityScorerTool
- Calculates quality scores for critical attribute data
- Evaluates accuracy, completeness, consistency, timeliness, and validity
- Provides attribute-specific quality assessments

### 4. GapIdentifierTool
- Identifies missing critical attributes and their impact
- Categorizes gaps by priority (critical, high, medium, low)
- Determines which 6R strategies are affected by each gap
- Recommends data sources for collection

### 5. ImpactCalculatorTool
- Calculates business and technical impact of missing attributes
- Assesses migration confidence impact per strategy
- Evaluates timeline and cost implications
- Identifies migration risks

### 6. EffortEstimatorTool
- Estimates time and resources needed to collect missing attributes
- Calculates effort by priority and collection method
- Identifies optimization opportunities
- Provides resource allocation recommendations

### 7. PriorityRankerTool
- Ranks gaps using multi-criteria decision analysis
- Considers business impact, strategy alignment, feasibility, and cost-benefit
- Groups gaps into priority buckets (immediate action, next sprint, backlog)

### 8. CollectionPlannerTool
- Creates detailed collection plans for prioritized gaps
- Defines phases with specific activities and deliverables
- Creates resource schedules and identifies required tools
- Provides risk mitigation strategies

## Integration Points

### Agent Registry
The agents are automatically discovered and registered through:
- `backend/app/services/agents/registry.py` - Auto-discovers agents ending with `_agent.py` or `_agent_crewai.py`
- Agents must implement the `agent_metadata()` class method

### Tool Registry
The tools are automatically discovered and registered through:
- `backend/app/services/tools/registry.py` - Auto-discovers tools in files ending with `_tool.py` or `_tools.py`
- Tools must implement the `tool_metadata()` class method

### Base Classes
- **Agents**: Inherit from `BaseCrewAIAgent` (in `base_agent.py`)
- **Tools**: Inherit from `AsyncBaseDiscoveryTool` (in `base_tool.py`)

## Usage Example

```python
# Initialize agents
assessor = CriticalAttributeAssessorAgent(
    tools=[attribute_mapper, completeness_analyzer, quality_scorer, gap_identifier],
    llm=llm_instance
)

prioritizer = GapPrioritizationAgent(
    tools=[impact_calculator, effort_estimator, priority_ranker, collection_planner],
    llm=llm_instance
)

# Assess critical attributes
assessment_result = assessor.assess_attributes(collected_data)

# Prioritize identified gaps
prioritization_result = prioritizer.prioritize_gaps(
    gaps=assessment_result['gaps'],
    context=migration_context
)
```

## Testing

A test script is provided at `backend/test_gap_analysis_agents.py` that verifies:
- Agent imports and metadata
- Tool imports and metadata
- Critical attributes framework structure
- Basic tool functionality

## Notes

- The implementation follows the existing CrewAI patterns in the codebase
- All tools are context-aware and support multi-tenancy
- The agents work with or without CrewAI installed (graceful fallback)
- Tools use async operations for better performance
- Comprehensive logging is included for debugging and monitoring