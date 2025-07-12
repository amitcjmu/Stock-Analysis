# Implementation Plan: Agentic Memory Architecture

## Overview

This implementation plan transforms the platform from a disabled-memory, rule-based system to a fully functional, learning-based agentic platform. The approach fixes existing infrastructure rather than rebuilding, following a careful, risk-managed rollout.

## Implementation Phases

### Phase 1: Memory System Recovery (Week 1)

**Objective**: Fix the root causes that led to memory system disable and restore basic functionality.

#### 1.1 Dependency Analysis and Upgrade

**Investigation Tasks:**
```bash
# Check current versions
pip list | grep -E "(crewai|openai|litellm)"

# Identify APIStatusError source
grep -r "APIStatusError" backend/
grep -r "missing 2 required keyword-only arguments" backend/

# Test memory functionality in isolation
docker exec migration_backend python -c "
from crewai import LongTermMemory
from crewai.memory.storage import ChromaStorage
try:
    memory = LongTermMemory(storage=ChromaStorage())
    print('Memory initialization successful')
except Exception as e:
    print(f'Memory error: {e}')
"
```

**Expected Issues:**
- CrewAI version incompatibility with OpenAI client library
- LiteLLM version mismatch causing API response parsing errors
- ChromaDB initialization failures

**Resolution Steps:**
1. **Test Environment Setup**
   ```bash
   # Create isolated test environment
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Dependency Upgrade Strategy**
   ```python
   # Updated requirements.txt versions (to be tested)
   crewai>=0.30.0
   openai>=1.12.0
   litellm>=1.35.0
   chromadb>=0.4.0
   ```

3. **Incremental Testing**
   ```python
   # Test script: test_memory_recovery.py
   import asyncio
   from crewai import Agent, Task, Crew
   from crewai.memory import LongTermMemory
   
   async def test_basic_memory():
       try:
           # Test memory initialization
           memory = LongTermMemory()
           
           # Test simple crew with memory
           agent = Agent(
               role="Test Agent",
               goal="Test memory functionality",
               backstory="Testing agent",
               memory=True
           )
           
           task = Task(
               description="Simple test task",
               agent=agent
           )
           
           crew = Crew(agents=[agent], tasks=[task], memory=True)
           result = crew.kickoff()
           
           print("Memory test successful")
           return True
           
       except Exception as e:
           print(f"Memory test failed: {e}")
           return False
   ```

#### 1.2 Memory System Restoration

**Rollback Global Disable:**
```python
# backend/app/services/crewai_flows/crews/__init__.py
# REMOVE the memory disable patch:
# def patch_crew_init():
#     original_init = Crew.__init__
#     def new_init(self, *args, **kwargs):
#         kwargs['memory'] = False  # REMOVE THIS LINE
#         return original_init(self, *args, **kwargs)
```

**Enable Memory Selectively:**
```python
# Start with one crew for testing
class TestMemoryDataCleansingCrew(Crew):
    def __init__(self):
        super().__init__(
            agents=[...],
            tasks=[...],
            memory=True,  # Re-enable for testing
            verbose=True
        )
```

**Performance Monitoring:**
```python
# Add performance tracking
import time
from functools import wraps

def track_memory_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Memory operation completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Memory operation failed after {duration:.2f}s: {e}")
            raise
    return wrapper
```

**Deliverables:**
- [ ] Memory system functioning without `APIStatusError`
- [ ] Performance under 5 seconds for basic operations
- [ ] One crew successfully using memory
- [ ] Error monitoring and alerting in place

### Phase 2: Three-Tier Memory Implementation (Week 2)

**Objective**: Implement the unified three-tier memory architecture using existing infrastructure.

#### 2.1 Asset Table Enhancements

**First, add the asset enrichment fields:**
```sql
-- Migration: 001_add_asset_enrichment_fields.sql
BEGIN;

-- Core enrichment fields that agents will populate
ALTER TABLE assets ADD COLUMN IF NOT EXISTS asset_subtype VARCHAR(50);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS business_value_score INTEGER CHECK (business_value_score >= 1 AND business_value_score <= 10);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS availability_requirement VARCHAR(10);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS compliance_requirements JSONB DEFAULT '[]';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS data_classification VARCHAR(20);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS application_version VARCHAR(50);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS end_of_support_date DATE;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS container_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS api_maturity_level VARCHAR(20);

-- Agent enrichment metadata
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(20) DEFAULT 'basic' CHECK (enrichment_status IN ('basic', 'enhanced', 'complete'));
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_score INTEGER DEFAULT 0 CHECK (enrichment_score >= 0 AND enrichment_score <= 100);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS ai_confidence_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enriching_agent VARCHAR(100);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS last_enrichment_timestamp TIMESTAMPTZ;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_reasoning TEXT;

-- Indexes for enrichment queries
CREATE INDEX idx_assets_enrichment_status ON assets(enrichment_status);
CREATE INDEX idx_assets_enrichment_score ON assets(enrichment_score DESC);
CREATE INDEX idx_assets_business_value ON assets(business_value_score DESC) WHERE business_value_score IS NOT NULL;
CREATE INDEX idx_assets_confidence ON assets(ai_confidence_score DESC) WHERE ai_confidence_score IS NOT NULL;

COMMIT;
```

#### 2.2 Tier 3 Database Schema

**Create Agent Pattern Memory Table:**
```sql
-- Migration: 001_add_agent_discovered_patterns.sql
BEGIN;

CREATE TABLE agent_discovered_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    
    -- Pattern identification
    pattern_type VARCHAR(50) NOT NULL,
    pattern_value VARCHAR(255) NOT NULL,
    pattern_context JSONB DEFAULT '{}',
    
    -- AI insights
    suggested_insight JSONB NOT NULL,
    reasoning_summary TEXT,
    
    -- Learning metrics
    source_agent VARCHAR(100) NOT NULL,
    origin_flow_id UUID,
    discovery_method VARCHAR(50) DEFAULT 'agent_analysis',
    
    -- Validation tracking
    confirmation_count INTEGER DEFAULT 1,
    refutation_count INTEGER DEFAULT 0,
    last_validation_flow_id UUID,
    
    -- Calculated reliability
    historical_accuracy DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE 
            WHEN (confirmation_count + refutation_count) = 0 THEN 0.0
            ELSE confirmation_count::DECIMAL / (confirmation_count + refutation_count)
        END
    ) STORED,
    
    -- Evolution tracking
    pattern_evolution JSONB DEFAULT '[]',
    related_patterns UUID[],
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(client_account_id, pattern_type, pattern_value)
);

-- Indexes for performance
CREATE INDEX idx_agent_patterns_client_type ON agent_discovered_patterns(client_account_id, pattern_type);
CREATE INDEX idx_agent_patterns_accuracy ON agent_discovered_patterns(historical_accuracy DESC) WHERE is_active = TRUE;
CREATE INDEX idx_agent_patterns_search ON agent_discovered_patterns USING GIN(to_tsvector('english', suggested_insight::text));

COMMIT;
```

**Initialize with Seed Patterns:**
```sql
-- Basic seed patterns for testing
INSERT INTO agent_discovered_patterns (
    client_account_id, pattern_type, pattern_value, suggested_insight, 
    reasoning_summary, source_agent, discovery_method
) VALUES 
(1, 'hostname_analysis', 'db-*', 
 '{"asset_type": "database", "confidence": 0.85}',
 'Hostnames starting with db- consistently indicate database servers',
 'DataCleansingCrew', 'seed_data'),
(1, 'port_analysis', '3306', 
 '{"asset_type": "database", "subtype": "mysql", "confidence": 0.95}',
 'Port 3306 is the default MySQL port',
 'DataCleansingCrew', 'seed_data');
```

#### 2.2 Memory Manager Implementation

**Unified Memory Manager:**
```python
# backend/app/services/memory/unified_memory_manager.py
class UnifiedMemoryManager:
    def __init__(self, client_account_id: int, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        
        # Initialize memory tiers
        self.tier1_memories = {}  # task_id -> AgenticShortTermMemory
        self.tier2 = EpisodicMemoryManager(client_account_id, engagement_id)
        self.tier3 = AgentPatternMemory(client_account_id)
        
        # Performance tracking
        self.performance_tracker = MemoryPerformanceTracker()
    
    @track_memory_performance
    async def create_task_memory(self, task_id: str, agent_type: str) -> AgenticShortTermMemory:
        """Create short-term memory for new task"""
        memory = AgenticShortTermMemory(task_id, agent_type)
        self.tier1_memories[task_id] = memory
        return memory
    
    @track_memory_performance  
    async def complete_task(self, task_id: str, episode: TaskEpisode):
        """Complete task and distribute to long-term memory"""
        try:
            # Store in Tier 2 (episodic)
            await self.tier2.store_episode(episode)
            
            # Extract patterns for Tier 3
            if episode.success_indicators.get('accurate', False):
                patterns = await self._extract_patterns_from_episode(episode)
                for pattern in patterns:
                    await self.tier3.store_discovered_pattern(pattern)
            
            # Cleanup Tier 1
            if task_id in self.tier1_memories:
                del self.tier1_memories[task_id]
                
        except Exception as e:
            logger.error(f"Error completing task memory: {e}")
            raise
```

**Pattern Memory Implementation:**
```python
# backend/app/services/memory/agent_pattern_memory.py
class AgentPatternMemory:
    def __init__(self, client_account_id: int):
        self.client_account_id = client_account_id
    
    async def search_patterns(self, search_query: str, pattern_type: str = None, min_accuracy: float = 0.5) -> list:
        """Search for patterns matching agent's query"""
        async with AsyncSessionLocal() as session:
            query = select(AgentDiscoveredPattern).where(
                AgentDiscoveredPattern.client_account_id == self.client_account_id,
                AgentDiscoveredPattern.is_active == True,
                AgentDiscoveredPattern.historical_accuracy >= min_accuracy
            )
            
            if pattern_type:
                query = query.where(AgentDiscoveredPattern.pattern_type == pattern_type)
            
            # Semantic search
            if search_query:
                query = query.where(
                    or_(
                        AgentDiscoveredPattern.pattern_value.ilike(f'%{search_query}%'),
                        func.to_tsvector('english', AgentDiscoveredPattern.suggested_insight.astext).op('@@')(
                            func.plainto_tsquery('english', search_query)
                        )
                    )
                )
            
            query = query.order_by(AgentDiscoveredPattern.historical_accuracy.desc())
            result = await session.execute(query)
            patterns = result.scalars().all()
            
            return [self._format_pattern_for_agent(p) for p in patterns]
    
    async def store_discovered_pattern(self, pattern: DiscoveredPattern):
        """Store new pattern discovered by agent"""
        async with AsyncSessionLocal() as session:
            # Check for existing pattern
            existing = await session.execute(
                select(AgentDiscoveredPattern).where(
                    AgentDiscoveredPattern.client_account_id == self.client_account_id,
                    AgentDiscoveredPattern.pattern_type == pattern.type,
                    AgentDiscoveredPattern.pattern_value == pattern.value
                )
            )
            
            if existing_pattern := existing.scalar_one_or_none():
                # Update existing pattern
                existing_pattern.confirmation_count += 1
                existing_pattern.last_confirmed_at = datetime.utcnow()
                
                # Update insights if new ones provided
                if pattern.insight:
                    existing_pattern.suggested_insight = {
                        **existing_pattern.suggested_insight,
                        **pattern.insight
                    }
            else:
                # Create new pattern
                new_pattern = AgentDiscoveredPattern(
                    client_account_id=self.client_account_id,
                    pattern_type=pattern.type,
                    pattern_value=pattern.value,
                    suggested_insight=pattern.insight,
                    reasoning_summary=pattern.reasoning,
                    source_agent=pattern.source_agent,
                    origin_flow_id=pattern.origin_flow_id
                )
                session.add(new_pattern)
            
            await session.commit()
```

**Deliverables:**
- [ ] Three-tier memory architecture operational
- [ ] Database schema deployed and tested
- [ ] Memory managers handling concurrent operations
- [ ] Performance monitoring showing <3 second operations

### Phase 3: Agent Tools Implementation (Week 3)

**Objective**: Implement the core agent tools that enable intelligent reasoning.

#### 3.1 Core Tool Development

**Tool Implementation Priority:**
1. `PatternSearchTool` - Access to learned patterns
2. `AssetDataQueryTool` - Asset investigation capabilities  
3. `HostnameAnalysisTool` - Hostname decomposition
4. `LearningTool` - Pattern storage capability
5. `EpisodeRetrievalTool` - Historical context

**Tool Testing Framework:**
```python
# backend/tests/test_agent_tools.py
class TestAgentTools:
    def __init__(self):
        self.memory_manager = UnifiedMemoryManager(client_account_id=1, engagement_id="test")
        
    async def test_pattern_search_tool(self):
        """Test pattern search functionality"""
        tool = PatternSearchTool(self.memory_manager)
        
        # Test basic search
        result = await tool.arun("database")
        assert "Found" in result or "No reliable patterns" in result
        
        # Test with type filter
        result = await tool.arun("db", pattern_type="hostname_analysis")
        assert isinstance(result, str)
        
    async def test_asset_data_query_tool(self):
        """Test asset data querying"""
        tool = AssetDataQueryTool(AsyncSessionLocal())
        
        # Create test asset
        test_asset = self.create_test_asset()
        
        # Test hostname analysis
        result = await tool.arun(test_asset.id, "hostname")
        assert "Hostname Analysis" in result
        
        # Test network analysis
        result = await tool.arun(test_asset.id, "network")
        assert "Network Analysis" in result
```

**Tool Integration with Existing Crews:**
```python
# backend/app/services/crewai_flows/crews/enhanced_data_cleansing_crew.py
class EnhancedDataCleansingCrew:
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
        
        # Initialize tools
        self.agent_tools = [
            PatternSearchTool(memory_manager),
            AssetDataQueryTool(AsyncSessionLocal()),
            HostnameAnalysisTool(),
            LearningTool(memory_manager, "DataCleansingCrew")
        ]
        
        # Create agent with tools
        self.classification_agent = Agent(
            role="Asset Classification Specialist",
            goal="Accurately classify assets using systematic analysis",
            backstory="""Expert in IT infrastructure with systematic approach to asset analysis.""",
            tools=self.agent_tools,
            memory=True,
            verbose=True
        )
        
        # Create classification task
        self.classification_task = Task(
            description=self.get_classification_task_description(),
            agent=self.classification_agent,
            expected_output="""Structured analysis with asset classification, confidence score, and reasoning."""
        )
        
        # Initialize crew
        self.crew = Crew(
            agents=[self.classification_agent],
            tasks=[self.classification_task],
            memory=True,
            verbose=True
        )
    
    def get_classification_task_description(self) -> str:
        return """
        Analyze the provided asset to determine its type, subtype, and characteristics.
        
        Process:
        1. Use AssetDataQueryTool to inspect asset details
        2. Use HostnameAnalysisTool to analyze naming patterns
        3. Use PatternSearchTool to check for relevant historical patterns
        4. Apply reasoning to synthesize findings
        5. If you discover reliable new patterns, use LearningTool to store them
        
        Provide confidence score (0-100%). If confidence < 85%, ask specific question.
        """
```

#### 3.2 Enhanced Agent Task Descriptions

**Update Agent Prompting:**
```python
# backend/app/services/crewai_flows/tasks/asset_classification_tasks.py
ENHANCED_CLASSIFICATION_TASK = """
You are analyzing asset: {asset_name}

Available data:
- Hostname: {hostname}
- Asset type (if known): {asset_type}
- Raw data: {raw_data_summary}

Your mission:
1. Form hypothesis about asset type/purpose
2. Use tools to gather evidence
3. Reason through evidence to reach conclusion
4. Assess confidence in your analysis
5. Store any reliable patterns you discover

Think step by step and explain your reasoning.
"""
```

**Deliverables:**
- [ ] All core tools implemented and tested
- [ ] Enhanced crews using tools instead of hard-coded logic
- [ ] Agent task descriptions updated for reasoning-focused approach
- [ ] Tool performance under 2 seconds per operation

### Phase 4: Learning and Pattern Discovery (Week 4)

**Objective**: Enable agents to learn from interactions and improve over time.

#### 4.1 Learning Specialist Agent

**Dedicated Learning Agent:**
```python
# backend/app/services/agents/learning_specialist.py
class LearningSpecialist:
    """Agent specialized in analyzing interactions for patterns"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
        self.agent = Agent(
            role="Learning and Pattern Discovery Specialist",
            goal="Analyze successful interactions to discover generalizable patterns",
            backstory="""Expert in pattern recognition and machine learning with ability to 
            extract meaningful insights from agent-user interactions.""",
            tools=[
                InteractionAnalysisTool(),
                PatternExtractionTool(),
                StatisticalAnalysisTool()
            ],
            memory=True
        )
    
    async def analyze_successful_interaction(self, interaction: dict) -> list:
        """Analyze interaction for learnable patterns"""
        
        task = Task(
            description=f"""
            Analyze this successful asset classification interaction:
            
            User Question: {interaction['question']}
            User Response: {interaction['user_response']}
            Asset Data: {interaction['asset_data']}
            Agent Reasoning: {interaction['agent_reasoning']}
            
            Determine if this interaction reveals any generalizable patterns that could help 
            future asset classification. Look for:
            1. Correlations between asset characteristics and correct classifications
            2. Naming patterns that reliably indicate asset types
            3. Data patterns that suggest business context
            
            If you find reliable patterns (confidence > 75%), specify:
            - Pattern type and value
            - Associated insights
            - Reasoning for reliability
            - Recommended confidence level
            """,
            agent=self.agent,
            expected_output="List of discovered patterns with confidence assessments"
        )
        
        result = task.execute()
        return self._parse_discovered_patterns(result)
    
    async def analyze_pattern_effectiveness(self, pattern_id: str) -> dict:
        """Analyze how well a stored pattern is performing"""
        
        # Get pattern usage statistics
        pattern_stats = await self.memory_manager.tier3.get_pattern_statistics(pattern_id)
        
        task = Task(
            description=f"""
            Analyze the effectiveness of this stored pattern:
            
            Pattern: {pattern_stats['pattern_value']}
            Type: {pattern_stats['pattern_type']}
            Accuracy: {pattern_stats['historical_accuracy']}
            Usage count: {pattern_stats['confirmation_count'] + pattern_stats['refutation_count']}
            Recent confirmations: {pattern_stats['recent_confirmations']}
            Recent refutations: {pattern_stats['recent_refutations']}
            
            Determine:
            1. Is this pattern still reliable?
            2. Should confidence be adjusted?
            3. Are there related patterns that should be merged?
            4. Should this pattern be deprecated?
            
            Provide specific recommendations for pattern management.
            """,
            agent=self.agent,
            expected_output="Pattern effectiveness analysis with management recommendations"
        )
        
        return task.execute()
```

#### 4.2 Feedback Learning Loop

**User Feedback Integration:**
```python
# backend/app/services/learning/feedback_processor.py
class FeedbackProcessor:
    """Processes user feedback to improve agent learning"""
    
    def __init__(self, learning_specialist: LearningSpecialist):
        self.learning_specialist = learning_specialist
    
    async def process_user_correction(self, correction: dict):
        """Process user correction of agent analysis"""
        
        # Extract learning opportunity
        learning_data = {
            'original_analysis': correction['agent_analysis'],
            'correct_classification': correction['user_correction'],
            'asset_data': correction['asset_data'],
            'correction_reasoning': correction.get('user_explanation', '')
        }
        
        # Have learning specialist analyze
        patterns = await self.learning_specialist.analyze_correction(learning_data)
        
        # Update existing patterns or create new ones
        for pattern in patterns:
            if pattern['action'] == 'update':
                await self._update_pattern_accuracy(pattern)
            elif pattern['action'] == 'create':
                await self._create_new_pattern(pattern)
            elif pattern['action'] == 'deprecate':
                await self._deprecate_pattern(pattern)
    
    async def process_user_confirmation(self, confirmation: dict):
        """Process user confirmation of agent analysis"""
        
        # Strengthen confidence in used patterns
        used_patterns = confirmation['agent_analysis']['patterns_used']
        for pattern_id in used_patterns:
            await self.memory_manager.tier3.increment_pattern_confirmation(pattern_id)
        
        # Look for new patterns in successful analysis
        if confirmation['agent_analysis']['confidence'] > 85:
            patterns = await self.learning_specialist.analyze_successful_interaction(confirmation)
            for pattern in patterns:
                await self.memory_manager.tier3.store_discovered_pattern(pattern)
```

#### 4.3 Pattern Evolution and Maintenance

**Automated Pattern Maintenance:**
```python
# backend/app/services/learning/pattern_maintenance.py
class PatternMaintenanceService:
    """Maintains and evolves agent patterns over time"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
    
    async def daily_maintenance(self):
        """Daily pattern maintenance routine"""
        
        # Find patterns needing review
        patterns_to_review = await self._identify_patterns_needing_review()
        
        for pattern in patterns_to_review:
            # Analyze pattern effectiveness
            analysis = await self.learning_specialist.analyze_pattern_effectiveness(pattern['id'])
            
            # Apply recommended changes
            if analysis['recommendation'] == 'deprecate':
                await self._deprecate_pattern(pattern['id'])
            elif analysis['recommendation'] == 'merge':
                await self._merge_patterns(pattern['id'], analysis['merge_target'])
            elif analysis['recommendation'] == 'adjust_confidence':
                await self._adjust_pattern_confidence(pattern['id'], analysis['new_confidence'])
    
    async def _identify_patterns_needing_review(self) -> list:
        """Identify patterns that may need maintenance"""
        
        # Patterns with declining accuracy
        declining_patterns = await self.memory_manager.tier3.get_patterns_with_declining_accuracy()
        
        # Patterns with conflicting evidence
        conflicted_patterns = await self.memory_manager.tier3.get_patterns_with_high_refutation_rate()
        
        # Old patterns that haven't been validated recently
        stale_patterns = await self.memory_manager.tier3.get_stale_patterns()
        
        return declining_patterns + conflicted_patterns + stale_patterns
```

**Deliverables:**
- [ ] Learning specialist agent operational
- [ ] Feedback processing pipeline implemented
- [ ] Pattern maintenance service running
- [ ] Observable improvement in agent accuracy over time

## Risk Management and Rollback Plans

### Performance Monitoring

**Memory Performance Alerts:**
```python
# backend/app/services/monitoring/memory_monitoring.py
class MemoryPerformanceMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'operation_time': 5.0,  # seconds
            'error_rate': 0.05,     # 5%
            'memory_usage': 0.8     # 80% of available memory
        }
    
    async def check_memory_performance(self) -> dict:
        """Check memory system performance metrics"""
        
        metrics = {
            'tier1_memory_count': len(self.memory_manager.tier1_memories),
            'tier2_operation_time': await self._measure_tier2_performance(),
            'tier3_operation_time': await self._measure_tier3_performance(),
            'error_rate': await self._calculate_error_rate(),
            'memory_usage': await self._get_memory_usage()
        }
        
        # Check for alerts
        alerts = []
        if metrics['tier2_operation_time'] > self.alert_thresholds['operation_time']:
            alerts.append('Tier 2 memory operations too slow')
        if metrics['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append('High memory operation error rate')
        
        return {'metrics': metrics, 'alerts': alerts}
```

### Rollback Procedures

**Phase-by-Phase Rollback:**
```python
# scripts/rollback_memory_implementation.py
class MemoryRollbackManager:
    def __init__(self, target_phase: int):
        self.target_phase = target_phase
    
    async def rollback_to_phase(self):
        """Rollback to specific implementation phase"""
        
        if self.target_phase < 4:
            # Disable learning and pattern discovery
            await self._disable_learning_agents()
        
        if self.target_phase < 3:
            # Disable agent tools, revert to simplified crews
            await self._disable_agent_tools()
        
        if self.target_phase < 2:
            # Disable three-tier memory, revert to basic memory
            await self._disable_tier3_memory()
        
        if self.target_phase < 1:
            # Complete memory disable (back to original state)
            await self._disable_all_memory()
    
    async def _disable_all_memory(self):
        """Emergency rollback to completely disabled memory"""
        # Re-apply the global memory disable patch
        self._apply_memory_disable_patch()
        
        # Clear all memory configurations
        await self._clear_memory_configurations()
        
        # Restart affected services
        await self._restart_services()
```

### Success Criteria and Gates

**Phase Gate Criteria:**

**Phase 1 Gate:**
- [ ] Zero `APIStatusError` incidents for 24 hours
- [ ] Memory operations complete in <5 seconds
- [ ] At least one crew successfully using memory
- [ ] Error rate <1% for memory operations

**Phase 2 Gate:**
- [ ] Three-tier memory architecture functional
- [ ] Pattern storage and retrieval working
- [ ] Memory operations complete in <3 seconds
- [ ] No memory-related performance degradation

**Phase 3 Gate:**
- [ ] All agent tools operational and tested
- [ ] Tools provide useful, accurate information
- [ ] Agent reasoning improved with tool usage
- [ ] Tool operations complete in <2 seconds

**Phase 4 Gate:**
- [ ] Learning system discovering valid patterns
- [ ] Agent accuracy improving measurably over time
- [ ] User feedback being processed correctly
- [ ] Pattern maintenance functioning automatically

## Deployment Strategy

### Environment Progression

1. **Development Environment**: Full implementation and testing
2. **Staging Environment**: Integration testing with real data
3. **Production Canary**: Single client account testing
4. **Production Rollout**: Gradual expansion to all clients

### Feature Flags

```python
# Feature flag configuration
MEMORY_FEATURES = {
    'BASIC_MEMORY_ENABLED': True,
    'TIER3_PATTERNS_ENABLED': True,
    'AGENT_TOOLS_ENABLED': True,
    'LEARNING_SYSTEM_ENABLED': False,  # Gradual rollout
    'PATTERN_MAINTENANCE_ENABLED': False
}
```

### Data Migration

**Pattern Data Seeding:**
```sql
-- Seed common patterns for faster initial learning
INSERT INTO agent_discovered_patterns (
    client_account_id, pattern_type, pattern_value, suggested_insight,
    reasoning_summary, source_agent, confirmation_count
) 
SELECT 
    ca.id,
    'hostname_analysis',
    'web-*',
    '{"asset_type": "web_server", "confidence": 0.8}',
    'Hostnames starting with web- typically indicate web servers',
    'SeedData',
    5
FROM client_accounts ca;
```

## Success Metrics and KPIs

### Technical Metrics
- **Memory System Uptime**: >99.5%
- **Memory Operation Performance**: <3 seconds average
- **Error Rate**: <1% of memory operations
- **Learning Pattern Discovery**: >5 new patterns per week

### Intelligence Metrics  
- **Agent Confidence Improvement**: +10% monthly
- **Question Reduction**: -20% in user questions needed
- **Classification Accuracy**: >90% agent suggestions accepted
- **Pattern Reliability**: >80% accuracy for patterns with 5+ validations

### Business Metrics
- **Discovery Flow Completion Time**: 30% reduction
- **User Satisfaction**: 4.5+ rating for AI suggestions
- **Migration Strategy Quality**: 25% improvement in recommendation accuracy
- **Platform Adoption**: Maintain current usage levels during transition

---

This implementation plan provides a structured, risk-managed approach to transforming the platform into a truly agentic, learning-based system while preserving stability and user experience throughout the transition.