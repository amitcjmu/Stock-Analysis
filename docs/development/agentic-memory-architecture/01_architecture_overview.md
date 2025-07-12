# Agentic Memory Architecture for Asset Intelligence

## Overview

This document outlines a truly agentic approach to asset intelligence that leverages the platform's existing CrewAI infrastructure and memory systems. Instead of building hard-coded rule engines, this architecture empowers agents with tools and memory to develop their own reasoning patterns through experience.

## Core Philosophy

**ALL intelligence comes from CrewAI agents.** The platform provides tools, memory, and data access, but reasoning, pattern recognition, and decision-making remain entirely within the domain of AI agents.

## Current State Analysis

### Existing Memory Infrastructure

The platform already has sophisticated memory infrastructure that was disabled due to technical issues:

- **`EnhancedAgentMemory`**: Vector-based episodic memory using ChromaDB
- **Multi-tenant memory concepts**: Client/engagement isolation patterns
- **CrewAI LongTermMemory integration**: Built-in memory capabilities

### Why Memory Was Disabled

From `docs/development/CREWAI_CRITICAL_FIXES_APPLIED.md`:
- `APIStatusError.__init__() missing 2 required keyword-only arguments: 'response' and 'body'`
- Performance issues (40+ second execution times)
- Dependency version mismatches between CrewAI and OpenAI libraries

### The False Solution

The current "solution" was to globally disable memory with:
```python
# backend/app/services/crewai_flows/crews/__init__.py
def patch_crew_init():
    original_init = Crew.__init__
    def new_init(self, *args, **kwargs):
        kwargs['memory'] = False  # Force disable memory
        return original_init(self, *args, **kwargs)
```

This stopped the errors but eliminated any possibility of agent learning and improvement.

## Proposed Three-Tiered Memory Architecture

### Tier 1: Short-Term (Conversational) Memory
- **Purpose**: Immediate task context within single agent execution
- **Implementation**: CrewAI's built-in `ShortTermMemory`
- **Lifecycle**: Duration of single task, discarded after completion
- **Storage**: In-memory only
- **Use Case**: Agent tracks its reasoning steps during current analysis

### Tier 2: Medium-Term (Episodic) Memory  
- **Purpose**: Complete task episodes for contextual learning
- **Implementation**: Existing `EnhancedAgentMemory` with ChromaDB
- **Lifecycle**: Persistent across sessions, client-scoped
- **Storage**: Vector embeddings in ChromaDB
- **Use Case**: Agent recalls how it successfully analyzed similar assets before

### Tier 3: Long-Term (Semantic) Knowledge
- **Purpose**: Distilled, validated patterns discovered through experience
- **Implementation**: New `agent_discovered_patterns` table
- **Lifecycle**: Persistent, continuously refined through user feedback
- **Storage**: Structured relational data
- **Use Case**: Agent queries validated patterns as evidence for reasoning

## Agent-First Tool Architecture

Instead of hard-coded pattern matching, agents receive powerful tools for investigation and reasoning:

### Core Tools

#### `PatternSearchTool`
```python
class PatternSearchTool(BaseTool):
    name = "pattern_search"
    description = "Search discovered patterns for evidence related to your hypothesis"
    
    def _run(self, search_query: str, pattern_type: str = None) -> str:
        """
        Agent decides what to search for based on their reasoning.
        Returns evidence, not directives.
        """
```

#### `AssetDataQueryTool`
```python
class AssetDataQueryTool(BaseTool):
    name = "asset_data_query"
    description = "Inspect specific aspects of asset data based on your hypothesis"
    
    def _run(self, asset_id: str, query_focus: str) -> str:
        """
        Agent asks specific questions about asset data.
        Returns facts, agent interprets meaning.
        """
```

#### `HostnameAnalysisTool`
```python
class HostnameAnalysisTool(BaseTool):
    name = "hostname_analysis"
    description = "Break down hostname components for pattern analysis"
    
    def _run(self, hostname: str) -> str:
        """
        Decomposes hostname into analyzable parts.
        Agent determines significance of each component.
        """
```

### Agent Task Transformation

**Old Approach (Rule-Based):**
```python
def analyze_asset(asset):
    if 'db' in asset.hostname.lower():
        return 'database_server'
    elif 'web' in asset.hostname.lower():
        return 'web_server'
    # ... more hard-coded rules
```

**New Approach (Agentic):**
```python
task_description = """
Analyze the given asset to determine its type, subtype, and business context.

Available tools:
- PatternSearchTool: Query previously discovered patterns for evidence
- AssetDataQueryTool: Inspect specific asset data points
- HostnameAnalysisTool: Analyze hostname structure

Process:
1. Form initial hypothesis based on available data
2. Use tools to gather supporting evidence
3. Reason through the evidence to reach conclusion
4. State confidence level (0-100%)
5. If confidence < 85%, generate specific question for user

Document your reasoning process and evidence clearly.
"""
```

## Memory Flow Integration

### Learning Cycle

1. **Agent Analysis**: Agent uses tools to analyze asset
2. **Hypothesis Formation**: Agent forms conclusion with confidence score
3. **User Interaction**: If confidence low, agent asks targeted question
4. **Learning Extraction**: `LearningSpecialist` analyzes successful interactions
5. **Pattern Discovery**: If generalizable pattern found, store in Tier 3 memory
6. **Episode Storage**: Complete interaction stored in Tier 2 memory

### Memory Retrieval

1. **New Task**: Agent receives asset to analyze
2. **Episodic Search**: Query Tier 2 for similar past episodes
3. **Pattern Search**: Use `PatternSearchTool` to query Tier 3 patterns
4. **Synthesis**: Combine episodic context with pattern evidence
5. **Reasoning**: Apply AI reasoning to reach conclusion

## Technical Architecture

### Database Schema (Tier 3)

```sql
CREATE TABLE agent_discovered_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,     -- 'hostname_segment', 'app_name_keyword'
    pattern_value VARCHAR(255) NOT NULL,    -- 'db', 'portal', 'payment'
    suggested_insight JSONB NOT NULL,      -- Multi-faceted insights
    source_agent VARCHAR(100) NOT NULL,    -- Agent that discovered pattern
    origin_flow_id UUID,                   -- Where pattern was confirmed
    confirmation_count INTEGER DEFAULT 1,   -- User confirmations
    refutation_count INTEGER DEFAULT 0,     -- User corrections
    historical_accuracy DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE 
            WHEN (confirmation_count + refutation_count) = 0 THEN 0
            ELSE confirmation_count::DECIMAL / (confirmation_count + refutation_count)
        END
    ) STORED,
    agent_notes TEXT,                       -- Agent's reasoning for pattern
    last_confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Memory Manager

```python
class UnifiedMemoryManager:
    """Orchestrates all three memory tiers"""
    
    def __init__(self, client_account_id: int, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.tier1 = ShortTermMemory()
        self.tier2 = EnhancedAgentMemory(client_account_id, engagement_id)
        self.tier3 = AgentPatternMemory(client_account_id)
    
    async def store_episode(self, task_summary: str, context: dict):
        """Store complete task episode in Tier 2"""
        await self.tier2.store_memory(task_summary, context)
    
    async def extract_pattern(self, interaction_result: dict):
        """Analyze interaction for generalizable patterns"""
        # Agent-driven analysis to determine if pattern should be stored
    
    async def query_patterns(self, search_query: str, pattern_type: str = None):
        """Agent tool to search discovered patterns"""
        return await self.tier3.search_patterns(search_query, pattern_type)
```

## Integration with Discovery Flow

### Phase Integration

The enhanced agents integrate seamlessly with existing discovery flow phases:

- **Data Cleansing**: `DataCleansingCrew` + Asset Classification Intelligence
- **Inventory Building**: `InventoryBuildingCrew` + Business Context Intelligence  
- **Dependency Analysis**: `DependencyAnalysisCrew` + Risk Assessment Intelligence

### No Workflow Disruption

- Existing UI components remain unchanged
- Agent-UI-Bridge continues to handle questions
- Flow progression logic stays intact
- User experience maintains consistency

### Progressive Enhancement

- Phase 1: Fix memory bugs, re-enable basic memory
- Phase 2: Implement Tier 3 patterns with tools
- Phase 3: Enhanced agent reasoning with unified memory
- Phase 4: Advanced learning and pattern discovery

## Benefits Over Rule-Based Approach

### Flexibility
- Agents discover patterns organically through experience
- No developer intervention needed for new naming conventions
- Adapts to organization-specific patterns automatically

### Intelligence
- True AI reasoning rather than keyword matching
- Agents explain their reasoning process
- Confidence scoring based on evidence quality

### Scalability
- Memory system grows smarter with usage
- Multi-tenant pattern sharing (where appropriate)
- Performance optimized through existing ChromaDB infrastructure

### Maintainability
- No hard-coded rules to maintain
- Self-improving system reduces technical debt
- Clear separation between tools and intelligence

## Success Metrics

### Technical Metrics
- Memory system uptime: 99.9%
- Agent response time: <3 seconds
- Pattern accuracy improvement: 10% monthly
- Zero `APIStatusError` incidents

### Intelligence Metrics
- Agent confidence scores trending upward
- User question frequency decreasing over time
- Pattern discovery rate: 5+ new patterns per week
- User acceptance rate of agent suggestions: >80%

### Business Metrics
- Asset classification accuracy: >90%
- Time to complete discovery flow: 40% reduction
- User satisfaction with AI suggestions: 4.5+ stars
- Migration strategy quality improvement: 25%

---

This architecture represents a fundamental shift from rule-based heuristics to truly intelligent, learning-based AI agents that honor the platform's core principle: **ALL intelligence comes from CrewAI agents.**