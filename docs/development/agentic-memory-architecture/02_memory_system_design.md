# Memory System Design and Implementation

## Current Memory Infrastructure Analysis

### Existing Components

The platform already contains sophisticated memory infrastructure that was disabled due to technical issues:

#### 1. Enhanced Agent Memory Service (`backend/app/services/enhanced_agent_memory.py`)
- **ChromaDB Integration**: Vector storage for episodic memory
- **Multi-tenant Support**: Client account and engagement scoping
- **Memory Contexts**: Structured context management
- **JSON Fallback**: Alternative storage when vector DB unavailable

#### 2. Legacy Memory Service (`backend/app/services/memory.py`)
- **Pickle-based Storage**: File-based memory persistence
- **Single-threaded**: Not suitable for concurrent operations
- **Security Concerns**: Pickle deserialization risks

#### 3. CrewAI Memory Integration
- **LongTermMemory**: Built-in CrewAI memory capabilities
- **Multiple Storage Backends**: ChromaStorage, JSONStorage support
- **Agent-specific Memory**: Per-agent memory isolation

### Root Cause Analysis

From codebase investigation, memory was disabled due to:

1. **Dependency Version Conflicts**
   ```python
   # APIStatusError.__init__() missing 2 required keyword-only arguments
   # Likely caused by version mismatch between:
   # - crewai
   # - openai client library  
   # - litellm
   ```

2. **Performance Issues**
   ```python
   # Memory operations + agent delegation + multiple LLM calls
   # Result: 40+ second execution times
   ```

3. **Global Disable Patch**
   ```python
   # backend/app/services/crewai_flows/crews/__init__.py
   def patch_crew_init():
       original_init = Crew.__init__
       def new_init(self, *args, **kwargs):
           kwargs['memory'] = False  # Nuclear option
           return original_init(self, *args, **kwargs)
   ```

## Asset Enrichment Field Integration

### Enhanced Asset Schema

The agentic approach still requires asset table enhancements, but fields are populated through agent reasoning rather than rule engines:

```sql
-- Core enrichment fields (populated by agent analysis)
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
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_reasoning TEXT; -- Agent's explanation
```

### Agent-Driven Field Population

Fields are populated through agent reasoning process:

```python
class AssetEnrichmentResult:
    """Result of agent-driven asset analysis"""
    
    def __init__(self):
        self.asset_subtype: str = None
        self.business_value_score: int = None
        self.availability_requirement: str = None
        self.compliance_requirements: list = []
        self.data_classification: str = None
        self.confidence_score: float = 0.0
        self.reasoning: str = ""
        self.evidence_used: list = []
        self.questions_for_user: list = []

async def enrich_asset_with_agent(asset: Asset, agent_crew: EnhancedDataCleansingCrew) -> AssetEnrichmentResult:
    """Use agent reasoning to enrich asset fields"""
    
    # Agent analyzes asset using tools and reasoning
    analysis_result = await agent_crew.analyze_asset_comprehensive(asset)
    
    # Update asset fields based on agent's reasoned conclusions
    if analysis_result.confidence_score >= 0.75:  # High confidence threshold
        asset.asset_subtype = analysis_result.asset_subtype
        asset.business_value_score = analysis_result.business_value_score
        asset.availability_requirement = analysis_result.availability_requirement
        asset.compliance_requirements = analysis_result.compliance_requirements
        asset.data_classification = analysis_result.data_classification
        
        # Meta-enrichment fields
        asset.ai_confidence_score = analysis_result.confidence_score
        asset.enriching_agent = agent_crew.agent_name
        asset.enrichment_reasoning = analysis_result.reasoning
        asset.last_enrichment_timestamp = datetime.utcnow()
        asset.enrichment_status = 'enhanced' if analysis_result.confidence_score >= 0.85 else 'basic'
    
    return analysis_result
```

## Three-Tiered Memory Architecture Design

### Tier 1: Short-Term (Conversational) Memory

**Purpose**: Maintain context within a single task execution

**Implementation**:
```python
class AgenticShortTermMemory:
    """Enhanced short-term memory for single task context"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.context = {}
        self.reasoning_chain = []
        self.tool_usage = []
        self.hypotheses = []
    
    def add_reasoning_step(self, step: str, evidence: dict):
        """Track agent's reasoning process"""
        self.reasoning_chain.append({
            'step': step,
            'evidence': evidence,
            'timestamp': datetime.utcnow()
        })
    
    def record_hypothesis(self, hypothesis: str, confidence: float, supporting_evidence: list):
        """Record agent hypothesis formation"""
        self.hypotheses.append({
            'hypothesis': hypothesis,
            'confidence': confidence,
            'evidence': supporting_evidence,
            'timestamp': datetime.utcnow()
        })
    
    def get_context_summary(self) -> str:
        """Generate context summary for agent use"""
        return f"Task {self.task_id}: {len(self.reasoning_chain)} reasoning steps, current hypothesis: {self.hypotheses[-1] if self.hypotheses else 'None'}"
```

**Lifecycle**: Created at task start, destroyed at task completion
**Storage**: In-memory only, no persistence required

### Tier 2: Medium-Term (Episodic) Memory

**Purpose**: Store complete task episodes for learning and context

**Implementation**: Enhance existing `EnhancedAgentMemory` service

```python
class EpisodicMemoryManager:
    """Enhanced episodic memory using existing ChromaDB infrastructure"""
    
    def __init__(self, client_account_id: int, engagement_id: str):
        self.enhanced_memory = EnhancedAgentMemory(client_account_id, engagement_id)
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    async def store_episode(self, episode: TaskEpisode):
        """Store complete task episode with rich context"""
        episode_data = {
            'episode_id': episode.id,
            'agent_type': episode.agent_type,
            'task_description': episode.task_description,
            'input_data': episode.input_data,
            'reasoning_chain': episode.reasoning_chain,
            'tool_usage': episode.tool_usage,
            'final_conclusion': episode.conclusion,
            'user_feedback': episode.user_feedback,
            'confidence_score': episode.confidence,
            'success_indicators': episode.success_indicators,
            'timestamp': episode.completion_time
        }
        
        # Create semantic embedding of the episode
        episode_summary = self._create_episode_summary(episode)
        
        await self.enhanced_memory.store_memory(
            memory_content=episode_summary,
            memory_type='task_episode',
            context=episode_data
        )
    
    async def search_similar_episodes(self, current_task: dict, limit: int = 5) -> list:
        """Find similar past episodes for context"""
        query = self._create_search_query(current_task)
        
        similar_memories = await self.enhanced_memory.search_memories(
            query=query,
            memory_type='task_episode',
            limit=limit
        )
        
        return [self._parse_episode_memory(memory) for memory in similar_memories]
    
    def _create_episode_summary(self, episode: TaskEpisode) -> str:
        """Create searchable summary of episode"""
        return f"""
        Agent {episode.agent_type} analyzed {episode.input_data.get('asset_type', 'unknown')} asset.
        Task: {episode.task_description}
        Reasoning: {' -> '.join([step['step'] for step in episode.reasoning_chain])}
        Conclusion: {episode.conclusion}
        User feedback: {episode.user_feedback.get('accepted', 'unknown')}
        Success: {episode.success_indicators.get('accurate', False)}
        """
```

**Storage**: ChromaDB vector embeddings via existing `EnhancedAgentMemory`
**Lifecycle**: Persistent, client-scoped, searchable by semantic similarity

### Tier 3: Long-Term (Semantic) Knowledge

**Purpose**: Store validated, generalizable patterns discovered through experience

**Database Schema**:
```sql
CREATE TABLE agent_discovered_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    
    -- Pattern identification
    pattern_type VARCHAR(50) NOT NULL,         -- 'hostname_analysis', 'application_naming', 'port_analysis'
    pattern_value VARCHAR(255) NOT NULL,       -- 'db-*', 'payment*', '3306,3307'
    pattern_context JSONB,                     -- Additional pattern context
    
    -- AI-discovered insights
    suggested_insight JSONB NOT NULL,          -- Multi-faceted insights from AI analysis
    reasoning_summary TEXT,                    -- AI's explanation of why this pattern is valid
    
    -- Learning metrics
    source_agent VARCHAR(100) NOT NULL,       -- Agent that discovered/validated pattern
    origin_flow_id UUID,                      -- Flow where pattern was first confirmed
    discovery_method VARCHAR(50),             -- 'user_confirmation', 'pattern_analysis', 'correlation'
    
    -- Validation tracking
    confirmation_count INTEGER DEFAULT 1,     -- Times pattern was confirmed by users
    refutation_count INTEGER DEFAULT 0,       -- Times pattern was contradicted
    last_validation_flow_id UUID,             -- Most recent validation
    
    -- Calculated reliability
    historical_accuracy DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE 
            WHEN (confirmation_count + refutation_count) = 0 THEN 0.0
            ELSE confirmation_count::DECIMAL / (confirmation_count + refutation_count)
        END
    ) STORED,
    
    -- Learning evolution
    pattern_evolution JSONB DEFAULT '[]',     -- Track how pattern has evolved
    related_patterns UUID[],                  -- Links to related patterns
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(client_account_id, pattern_type, pattern_value)
);

-- Performance indexes
CREATE INDEX idx_agent_patterns_client_type ON agent_discovered_patterns(client_account_id, pattern_type);
CREATE INDEX idx_agent_patterns_accuracy ON agent_discovered_patterns(historical_accuracy DESC) WHERE is_active = TRUE;
CREATE INDEX idx_agent_patterns_recent ON agent_discovered_patterns(last_confirmed_at DESC) WHERE is_active = TRUE;

-- Full-text search on insights
CREATE INDEX idx_agent_patterns_insights_search ON agent_discovered_patterns USING GIN(to_tsvector('english', suggested_insight::text));
```

**Implementation**:
```python
class AgentPatternMemory:
    """Manages long-term semantic patterns discovered by agents"""
    
    def __init__(self, client_account_id: int):
        self.client_account_id = client_account_id
        self.db = AsyncSessionLocal()
    
    async def store_discovered_pattern(self, pattern: DiscoveredPattern):
        """Store new pattern discovered by agent reasoning"""
        async with self.db as session:
            # Check if pattern already exists
            existing = await session.execute(
                select(AgentDiscoveredPattern).where(
                    AgentDiscoveredPattern.client_account_id == self.client_account_id,
                    AgentDiscoveredPattern.pattern_type == pattern.type,
                    AgentDiscoveredPattern.pattern_value == pattern.value
                )
            )
            
            if existing_pattern := existing.scalar_one_or_none():
                # Update existing pattern
                await self._update_pattern_validation(existing_pattern, pattern)
            else:
                # Create new pattern
                new_pattern = AgentDiscoveredPattern(
                    client_account_id=self.client_account_id,
                    pattern_type=pattern.type,
                    pattern_value=pattern.value,
                    suggested_insight=pattern.insight,
                    reasoning_summary=pattern.reasoning,
                    source_agent=pattern.source_agent,
                    origin_flow_id=pattern.origin_flow_id,
                    discovery_method=pattern.discovery_method
                )
                session.add(new_pattern)
            
            await session.commit()
    
    async def search_patterns(self, search_query: str, pattern_type: str = None) -> list:
        """Agent tool to search for relevant patterns"""
        async with self.db as session:
            query = select(AgentDiscoveredPattern).where(
                AgentDiscoveredPattern.client_account_id == self.client_account_id,
                AgentDiscoveredPattern.is_active == True
            )
            
            if pattern_type:
                query = query.where(AgentDiscoveredPattern.pattern_type == pattern_type)
            
            # Semantic search on insights and reasoning
            query = query.where(
                or_(
                    AgentDiscoveredPattern.pattern_value.ilike(f'%{search_query}%'),
                    func.to_tsvector('english', AgentDiscoveredPattern.suggested_insight.astext).op('@@')(
                        func.plainto_tsquery('english', search_query)
                    )
                )
            ).order_by(AgentDiscoveredPattern.historical_accuracy.desc())
            
            result = await session.execute(query)
            patterns = result.scalars().all()
            
            return [self._format_pattern_for_agent(pattern) for pattern in patterns]
    
    def _format_pattern_for_agent(self, pattern: AgentDiscoveredPattern) -> dict:
        """Format pattern data for agent consumption"""
        return {
            'pattern_type': pattern.pattern_type,
            'pattern_value': pattern.pattern_value,
            'insights': pattern.suggested_insight,
            'accuracy': float(pattern.historical_accuracy),
            'confidence_level': self._calculate_confidence_level(pattern),
            'discovery_context': pattern.reasoning_summary,
            'validation_count': pattern.confirmation_count,
            'last_confirmed': pattern.last_confirmed_at.isoformat() if pattern.last_confirmed_at else None
        }
    
    def _calculate_confidence_level(self, pattern: AgentDiscoveredPattern) -> str:
        """Calculate human-readable confidence level"""
        accuracy = float(pattern.historical_accuracy)
        total_validations = pattern.confirmation_count + pattern.refutation_count
        
        if total_validations < 3:
            return 'emerging'
        elif accuracy >= 0.9:
            return 'highly_reliable'
        elif accuracy >= 0.75:
            return 'reliable'
        elif accuracy >= 0.6:
            return 'moderate'
        else:
            return 'questionable'
```

## Memory Orchestration

### Unified Memory Manager

```python
class UnifiedMemoryManager:
    """Coordinates all three memory tiers for agent operations"""
    
    def __init__(self, client_account_id: int, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.tier1_memories = {}  # task_id -> AgenticShortTermMemory
        self.tier2 = EpisodicMemoryManager(client_account_id, engagement_id)
        self.tier3 = AgentPatternMemory(client_account_id)
    
    def create_task_memory(self, task_id: str) -> AgenticShortTermMemory:
        """Create short-term memory for new task"""
        memory = AgenticShortTermMemory(task_id)
        self.tier1_memories[task_id] = memory
        return memory
    
    async def complete_task(self, task_id: str, episode: TaskEpisode):
        """Complete task and transfer to long-term memory"""
        # Store episode in Tier 2
        await self.tier2.store_episode(episode)
        
        # Analyze for patterns in Tier 3
        patterns = await self._extract_patterns_from_episode(episode)
        for pattern in patterns:
            await self.tier3.store_discovered_pattern(pattern)
        
        # Clean up short-term memory
        if task_id in self.tier1_memories:
            del self.tier1_memories[task_id]
    
    async def prepare_agent_context(self, task_description: str, input_data: dict) -> dict:
        """Prepare rich context for agent from all memory tiers"""
        # Search for similar episodes
        similar_episodes = await self.tier2.search_similar_episodes({
            'task_description': task_description,
            'input_data': input_data
        })
        
        # Search for relevant patterns
        search_terms = self._extract_search_terms(input_data)
        relevant_patterns = []
        for term in search_terms:
            patterns = await self.tier3.search_patterns(term)
            relevant_patterns.extend(patterns)
        
        return {
            'similar_episodes': similar_episodes[:3],  # Top 3 most relevant
            'relevant_patterns': relevant_patterns[:5],  # Top 5 patterns
            'context_summary': self._create_context_summary(similar_episodes, relevant_patterns)
        }
    
    async def _extract_patterns_from_episode(self, episode: TaskEpisode) -> list:
        """Use AI to analyze episode for generalizable patterns"""
        # This would use a specialized LearningSpecialist agent
        # to analyze successful interactions for patterns
        pass
    
    def _extract_search_terms(self, input_data: dict) -> list:
        """Extract relevant search terms from input data"""
        terms = []
        if hostname := input_data.get('hostname'):
            terms.append(hostname)
            # Extract hostname components
            terms.extend(hostname.split('-'))
            terms.extend(hostname.split('.'))
        
        if asset_name := input_data.get('name'):
            terms.append(asset_name)
            terms.extend(asset_name.lower().split())
        
        if asset_type := input_data.get('asset_type'):
            terms.append(asset_type)
        
        return list(set(terms))  # Remove duplicates
```

## Memory Performance Optimization

### ChromaDB Configuration

```python
# Enhanced ChromaDB settings for episodic memory
CHROMA_CONFIG = {
    'persist_directory': '/app/data/chroma',
    'collection_metadata': {
        'hnsw:space': 'cosine',
        'hnsw:construction_ef': 200,
        'hnsw:M': 16
    },
    'embedding_function': 'all-MiniLM-L6-v2',  # Optimized for speed
    'batch_size': 100,
    'max_concurrent_operations': 5
}
```

### Memory Lifecycle Management

```python
class MemoryLifecycleManager:
    """Manages memory cleanup and optimization"""
    
    async def cleanup_old_episodes(self, retention_days: int = 90):
        """Clean up old episodic memories beyond retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        await self.tier2.cleanup_memories_before(cutoff_date)
    
    async def consolidate_patterns(self):
        """Merge similar patterns and update confidence scores"""
        # Find patterns with high similarity
        # Merge patterns with low validation counts
        # Update accuracy scores based on recent validations
        pass
    
    async def optimize_memory_performance(self):
        """Optimize memory system performance"""
        # Rebuild ChromaDB indexes
        # Vacuum pattern database
        # Update search optimization
        pass
```

## Error Recovery and Fallbacks

### Memory System Resilience

```python
class ResilientMemoryManager:
    """Provides fallback mechanisms for memory system failures"""
    
    def __init__(self, primary_manager: UnifiedMemoryManager):
        self.primary = primary_manager
        self.fallback_storage = JSONFileMemory()  # Simple file-based fallback
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=30)
    
    async def store_with_fallback(self, operation, *args, **kwargs):
        """Execute memory operation with fallback on failure"""
        try:
            if self.circuit_breaker.is_closed():
                return await operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary memory operation failed: {e}")
            self.circuit_breaker.record_failure()
            
            # Fall back to simple storage
            return await self.fallback_storage.store(*args, **kwargs)
    
    async def health_check(self) -> dict:
        """Check health of all memory tiers"""
        health = {
            'tier1': 'healthy',  # Always healthy (in-memory)
            'tier2': await self._check_chromadb_health(),
            'tier3': await self._check_postgres_health(),
            'overall': 'degraded'
        }
        
        if all(status == 'healthy' for status in health.values() if status != 'overall'):
            health['overall'] = 'healthy'
        
        return health
```

---

This memory system design provides a robust, scalable foundation for truly agentic intelligence while leveraging the platform's existing infrastructure and fixing the root causes of the current memory system failures.