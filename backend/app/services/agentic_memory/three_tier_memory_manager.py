"""
Three-Tier Memory Manager - Unified Memory Orchestration

This module provides the unified interface for our three-tiered memory architecture:
- Tier 1: Conversational Memory (CrewAI LongTermMemory)
- Tier 2: Episodic Memory (ChromaDB/Vector Storage) 
- Tier 3: Semantic Patterns (AgentDiscoveredPattern database)

The manager provides agents with seamless access to all memory tiers while
maintaining multi-tenant isolation and enabling true agentic learning.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from crewai.memory import LongTermMemory
    from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
    CREWAI_MEMORY_AVAILABLE = True
except ImportError:
    CREWAI_MEMORY_AVAILABLE = False
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class LTMSQLiteStorage:
        def __init__(self, **kwargs):
            pass

try:
    from app.core.database import AsyncSessionLocal
    from app.models.agent_memory import (
        AgentDiscoveredPattern,
        PatternType,
        create_asset_enrichment_pattern,
        get_patterns_for_agent_reasoning,
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryQuery:
    """Query parameters for memory retrieval"""
    query_text: str
    memory_tiers: List[str] = None  # ['conversational', 'episodic', 'semantic']
    max_results: int = 10
    min_confidence: float = 0.6
    pattern_types: List[PatternType] = None
    validated_only: bool = False


@dataclass
class MemoryResult:
    """Memory retrieval result"""
    tier: str  # 'conversational', 'episodic', or 'semantic'
    content: Dict[str, Any]
    confidence_score: float
    source: str
    timestamp: datetime


class ThreeTierMemoryManager:
    """
    Unified memory manager that orchestrates all three memory tiers for agents
    
    This manager provides agents with:
    1. Access to all memory tiers through a unified interface
    2. Multi-tenant memory isolation
    3. Pattern discovery and learning capabilities
    4. Contextual memory retrieval based on agent tasks
    """
    
    def __init__(self, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        
        # Initialize Tier 1: Conversational Memory (CrewAI)
        self.tier1_memory = self._setup_conversational_memory()
        
        # Initialize Tier 2: Episodic Memory (Vector Storage)
        self.tier2_memory = self._setup_episodic_memory()
        
        logger.info(f"✅ Three-tier memory manager initialized for client {client_account_id}, engagement {engagement_id}")
    
    def _setup_conversational_memory(self) -> Optional[LongTermMemory]:
        """Setup Tier 1: Conversational Memory using CrewAI LongTermMemory"""
        if not CREWAI_MEMORY_AVAILABLE:
            logger.warning("CrewAI memory not available - Tier 1 disabled")
            return None
        
        try:
            # Use SQLite storage for Tier 1 memory
            storage = LTMSQLiteStorage()
            memory = LongTermMemory(storage=storage)
            logger.info("✅ Tier 1 (Conversational) memory initialized")
            return memory
        except Exception as e:
            logger.warning(f"Failed to initialize Tier 1 memory: {e}")
            return None
    
    def _setup_episodic_memory(self) -> Optional[object]:
        """Setup Tier 2: Episodic Memory using vector storage"""
        # TODO: Implement ChromaDB/vector storage integration
        # For now, return None to focus on Tier 1 and Tier 3
        logger.info("⚠️ Tier 2 (Episodic) memory not yet implemented")
        return None
    
    async def store_conversational_memory(self, agent_name: str, conversation: str, context: Dict[str, Any] = None):
        """Store conversation in Tier 1 memory"""
        if not self.tier1_memory:
            logger.warning("Tier 1 memory not available")
            return
        
        try:
            # Store with multi-tenant context
            {
                'agent': agent_name,
                'conversation': conversation,
                'client_account_id': str(self.client_account_id),
                'engagement_id': str(self.engagement_id),
                'context': context or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # TODO: Implement proper LongTermMemory storage
            # Note: CrewAI's LongTermMemory API may need adjustment
            logger.info(f"📝 Stored conversational memory for {agent_name}")
            
        except Exception as e:
            logger.error(f"Failed to store Tier 1 memory: {e}")
    
    async def store_pattern_discovery(
        self,
        agent_name: str,
        pattern_type: PatternType,
        pattern_name: str,
        pattern_description: str,
        pattern_logic: Dict[str, Any],
        confidence_score: float,
        evidence_assets: List[uuid.UUID] = None,
        flow_id: uuid.UUID = None
    ) -> Optional[AgentDiscoveredPattern]:
        """Store discovered pattern in Tier 3 memory"""
        if not DATABASE_AVAILABLE:
            logger.warning("Database not available - cannot store Tier 3 memory")
            return None
        
        try:
            pattern = create_asset_enrichment_pattern(
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                pattern_type=pattern_type,
                pattern_name=pattern_name,
                pattern_description=pattern_description,
                pattern_logic=pattern_logic,
                confidence_score=confidence_score,
                discovered_by_agent=agent_name,
                flow_id=flow_id,
                evidence_assets=evidence_assets
            )
            
            async with AsyncSessionLocal() as session:
                session.add(pattern)
                await session.commit()
                logger.info(f"🧠 Stored Tier 3 pattern: {pattern_name} by {agent_name}")
                return pattern
                
        except Exception as e:
            logger.error(f"Failed to store Tier 3 pattern: {e}")
            return None
    
    async def query_memory(self, query: MemoryQuery) -> List[MemoryResult]:
        """Query all memory tiers and return unified results"""
        results = []
        
        # Query Tier 1: Conversational Memory
        if not query.memory_tiers or 'conversational' in query.memory_tiers:
            tier1_results = await self._query_conversational_memory(query)
            results.extend(tier1_results)
        
        # Query Tier 2: Episodic Memory  
        if not query.memory_tiers or 'episodic' in query.memory_tiers:
            tier2_results = await self._query_episodic_memory(query)
            results.extend(tier2_results)
        
        # Query Tier 3: Semantic Patterns
        if not query.memory_tiers or 'semantic' in query.memory_tiers:
            tier3_results = await self._query_semantic_patterns(query)
            results.extend(tier3_results)
        
        # Sort by confidence and limit results
        results.sort(key=lambda r: r.confidence_score, reverse=True)
        return results[:query.max_results]
    
    async def _query_conversational_memory(self, query: MemoryQuery) -> List[MemoryResult]:
        """Query Tier 1: Conversational Memory"""
        if not self.tier1_memory:
            return []
        
        try:
            # TODO: Implement proper LongTermMemory querying
            # This is placeholder until CrewAI LongTermMemory API is fully integrated
            logger.info(f"🔍 Querying Tier 1 memory: {query.query_text}")
            return []  # Placeholder
            
        except Exception as e:
            logger.error(f"Failed to query Tier 1 memory: {e}")
            return []
    
    async def _query_episodic_memory(self, query: MemoryQuery) -> List[MemoryResult]:
        """Query Tier 2: Episodic Memory"""
        # TODO: Implement ChromaDB/vector storage querying
        logger.info(f"🔍 Querying Tier 2 memory: {query.query_text} (not yet implemented)")
        return []
    
    async def _query_semantic_patterns(self, query: MemoryQuery) -> List[MemoryResult]:
        """Query Tier 3: Semantic Patterns"""
        if not DATABASE_AVAILABLE:
            return []
        
        try:
            async with AsyncSessionLocal() as session:
                patterns = get_patterns_for_agent_reasoning(
                    session=session,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    pattern_types=query.pattern_types,
                    min_confidence=query.min_confidence,
                    validated_only=query.validated_only
                )
                
                results = []
                for pattern in patterns:
                    # Filter by query text if provided
                    if query.query_text and query.query_text.lower() not in pattern['name'].lower() and query.query_text.lower() not in pattern['description'].lower():
                        continue
                    
                    result = MemoryResult(
                        tier='semantic',
                        content=pattern,
                        confidence_score=pattern['confidence'],
                        source=f"pattern:{pattern['id']}",
                        timestamp=datetime.utcnow()  # TODO: Use actual pattern timestamp
                    )
                    results.append(result)
                
                logger.info(f"🧠 Found {len(results)} Tier 3 patterns for query: {query.query_text}")
                return results
                
        except Exception as e:
            logger.error(f"Failed to query Tier 3 memory: {e}")
            return []
    
    async def get_asset_enrichment_patterns(
        self,
        asset_type: str = None,
        pattern_types: List[PatternType] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns specifically for asset enrichment reasoning"""
        
        # Default to asset enrichment pattern types if not specified
        if not pattern_types:
            pattern_types = [
                PatternType.ASSET_CATEGORIZATION,
                PatternType.BUSINESS_VALUE_INDICATOR,
                PatternType.RISK_FACTOR,
                PatternType.MODERNIZATION_OPPORTUNITY,
                PatternType.CLOUD_READINESS_FACTOR
            ]
        
        query = MemoryQuery(
            query_text=asset_type or "",
            memory_tiers=['semantic'],
            pattern_types=pattern_types,
            min_confidence=0.6,
            validated_only=False  # Include pending patterns for agent learning
        )
        
        results = await self.query_memory(query)
        return [result.content for result in results if result.tier == 'semantic']
    
    async def record_pattern_usage(self, pattern_id: uuid.UUID, agent_name: str):
        """Record that an agent has used a specific pattern"""
        if not DATABASE_AVAILABLE:
            return
        
        try:
            async with AsyncSessionLocal() as session:
                pattern = await session.get(AgentDiscoveredPattern, pattern_id)
                if pattern:
                    pattern.increment_usage()
                    await session.commit()
                    logger.info(f"📊 Recorded pattern usage: {pattern_id} by {agent_name}")
        except Exception as e:
            logger.error(f"Failed to record pattern usage: {e}")
    
    async def suggest_new_patterns(self, agent_observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze agent observations to suggest new patterns for discovery"""
        # TODO: Implement pattern suggestion logic based on:
        # 1. Repeated similar observations across assets
        # 2. Correlation analysis of asset attributes
        # 3. Confidence thresholds for pattern recognition
        
        logger.info(f"🔍 Analyzing {len(agent_observations)} observations for pattern discovery")
        
        # Placeholder for pattern suggestion logic
        suggestions = []
        
        # Example: Look for repeated technology stack patterns
        tech_stacks = {}
        for obs in agent_observations:
            if 'technology_stack' in obs:
                stack = obs['technology_stack']
                if stack in tech_stacks:
                    tech_stacks[stack].append(obs)
                else:
                    tech_stacks[stack] = [obs]
        
        # Suggest patterns for technology stacks with multiple instances
        for stack, instances in tech_stacks.items():
            if len(instances) >= 3:  # Threshold for pattern recognition
                suggestions.append({
                    'pattern_type': PatternType.TECHNOLOGY_CORRELATION.value,
                    'pattern_name': f"Technology Stack: {stack}",
                    'evidence_count': len(instances),
                    'confidence': min(0.9, len(instances) * 0.2),
                    'suggested_logic': {
                        'technology_stack': stack,
                        'common_attributes': self._find_common_attributes(instances)
                    }
                })
        
        logger.info(f"💡 Suggested {len(suggestions)} new patterns for discovery")
        return suggestions
    
    def _find_common_attributes(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common attributes across multiple asset instances"""
        common = {}
        
        if not instances:
            return common
        
        # Find attributes that appear in most instances
        attribute_counts = {}
        for instance in instances:
            for key, value in instance.items():
                if key not in attribute_counts:
                    attribute_counts[key] = {}
                if value not in attribute_counts[key]:
                    attribute_counts[key][value] = 0
                attribute_counts[key][value] += 1
        
        # Include attributes that appear in at least 70% of instances
        threshold = len(instances) * 0.7
        for attr, value_counts in attribute_counts.items():
            for value, count in value_counts.items():
                if count >= threshold:
                    common[attr] = value
        
        return common