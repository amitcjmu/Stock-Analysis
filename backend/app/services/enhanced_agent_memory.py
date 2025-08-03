"""
Enhanced Agent Memory System with CrewAI Integration
Implements optimized memory management for CrewAI agents with:
- Persistent long-term memory using CrewAI's memory features
- Vector-based semantic search for pattern matching
- Multi-tenant isolation with learning scopes
- Performance optimization and caching
- Integration with existing agent learning system
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# CrewAI memory imports with graceful fallback
try:
    from crewai.memory import EntityMemory, LongTermMemory, ShortTermMemory
    from crewai.memory.storage import ChromaStorage, JSONStorage

    CREWAI_MEMORY_AVAILABLE = True
except ImportError:
    CREWAI_MEMORY_AVAILABLE = False
    logging.warning("CrewAI memory features not available, using fallback")

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfiguration:
    """Configuration for agent memory system"""

    enable_long_term_memory: bool = True
    enable_short_term_memory: bool = True
    enable_entity_memory: bool = True
    enable_semantic_search: bool = True
    vector_dimension: int = 1536
    similarity_threshold: float = 0.7
    max_memory_items: int = 10000
    memory_ttl_days: int = 90
    cache_ttl_seconds: int = 3600
    batch_size: int = 100
    use_gpu: bool = False
    storage_backend: str = "chroma"  # "chroma" or "json"
    memory_persistence_path: str = "data/enhanced_memory"


@dataclass
class MemoryItem:
    """Individual memory item with metadata"""

    item_id: str
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.8
    source: str = "agent"
    context: Optional[LearningContext] = None


class EnhancedAgentMemory:
    """
    Enhanced memory system for CrewAI agents with advanced features
    """

    def __init__(self, config: Optional[MemoryConfiguration] = None):
        self.config = config or MemoryConfiguration()
        self.embedding_service = EmbeddingService()

        # Initialize storage paths
        self.storage_path = Path(self.config.memory_persistence_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize memory stores
        self.memory_stores: Dict[str, Dict[str, MemoryItem]] = defaultdict(dict)
        self.embeddings_cache: Dict[str, np.ndarray] = {}

        # Initialize CrewAI memory components if available
        self._initialize_crewai_memory()

        # Performance tracking
        self.performance_metrics = {
            "memory_operations": 0,
            "cache_hits": 0,
            "semantic_searches": 0,
            "avg_search_time": 0.0,
        }

        logger.info("🧠 Enhanced Agent Memory System initialized")

    def _initialize_crewai_memory(self):
        """Initialize CrewAI memory components"""
        if not CREWAI_MEMORY_AVAILABLE:
            self.long_term_memory = None
            self.short_term_memory = None
            self.entity_memory = None
            logger.warning("CrewAI memory not available, using in-memory fallback")
            return

        try:
            # Configure storage backend
            if self.config.storage_backend == "chroma":
                storage = ChromaStorage(
                    collection_name="agent_memory",
                    persist_directory=str(self.storage_path / "chroma"),
                )
            else:
                storage = JSONStorage(file_path=str(self.storage_path / "memory.json"))

            # Initialize memory types
            if self.config.enable_long_term_memory:
                self.long_term_memory = LongTermMemory(
                    storage=storage,
                    embedder_config={
                        "provider": "openai",
                        "model": "text-embedding-3-small",
                    },
                )

            if self.config.enable_short_term_memory:
                self.short_term_memory = ShortTermMemory()

            if self.config.enable_entity_memory:
                self.entity_memory = EntityMemory(storage=storage)

            logger.info("✅ CrewAI memory components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize CrewAI memory: {e}")
            self.long_term_memory = None
            self.short_term_memory = None
            self.entity_memory = None

    async def store_memory(
        self,
        content: Dict[str, Any],
        memory_type: str,
        context: Optional[LearningContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store memory item with context isolation"""
        try:
            # Generate memory ID
            memory_id = self._generate_memory_id(content, context)

            # Get embedding for semantic search
            embedding = None
            if self.config.enable_semantic_search:
                text_content = self._extract_text_content(content)
                embedding = await self.embedding_service.embed_text(text_content)

            # Create memory item
            memory_item = MemoryItem(
                item_id=memory_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                context=context,
                source=memory_type,
            )

            # Store in appropriate context
            context_key = self._get_context_key(context)
            self.memory_stores[context_key][memory_id] = memory_item

            # Store in CrewAI memory if available
            if CREWAI_MEMORY_AVAILABLE:
                await self._store_in_crewai_memory(memory_item, memory_type)

            # Update performance metrics
            self.performance_metrics["memory_operations"] += 1

            # Integrate with existing learning system
            if context:
                await agent_learning_system.track_agent_performance(
                    "memory_storage",
                    {"items_stored": 1, "memory_type": memory_type},
                    context,
                )

            logger.debug(f"Stored memory item {memory_id} in context {context_key}")
            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return ""

    async def retrieve_memories(
        self,
        query: Dict[str, Any],
        context: Optional[LearningContext] = None,
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """Retrieve relevant memories using semantic search"""
        start_time = datetime.utcnow()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, context)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                self.performance_metrics["cache_hits"] += 1
                return cached_result

            # Get relevant memories
            context_key = self._get_context_key(context)
            context_memories = self.memory_stores.get(context_key, {})

            if not context_memories:
                return []

            # Filter by memory types if specified
            filtered_memories = list(context_memories.values())
            if memory_types:
                filtered_memories = [
                    m for m in filtered_memories if m.source in memory_types
                ]

            # Perform semantic search if enabled
            if self.config.enable_semantic_search and query:
                query_text = self._extract_text_content(query)
                query_embedding = await self.embedding_service.embed_text(query_text)

                # Calculate similarities
                similarities = []
                for memory in filtered_memories:
                    if memory.embedding:
                        similarity = self._calculate_similarity(
                            query_embedding, memory.embedding
                        )
                        if similarity >= self.config.similarity_threshold:
                            similarities.append((memory, similarity))

                # Sort by similarity and limit
                similarities.sort(key=lambda x: x[1], reverse=True)
                result = [item[0] for item in similarities[:limit]]
            else:
                # Return most recent memories
                filtered_memories.sort(key=lambda x: x.timestamp, reverse=True)
                result = filtered_memories[:limit]

            # Update access counts
            for memory in result:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()

            # Cache result
            await self._cache_result(cache_key, result)

            # Update performance metrics
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self._update_search_metrics(elapsed)

            return result

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    async def update_memory_confidence(
        self,
        memory_id: str,
        new_confidence: float,
        context: Optional[LearningContext] = None,
    ) -> bool:
        """Update confidence score for a memory item"""
        try:
            context_key = self._get_context_key(context)
            if memory_id in self.memory_stores[context_key]:
                self.memory_stores[context_key][
                    memory_id
                ].confidence_score = new_confidence
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update memory confidence: {e}")
            return False

    async def learn_from_feedback(
        self,
        memory_id: str,
        feedback: Dict[str, Any],
        context: Optional[LearningContext] = None,
    ) -> Dict[str, Any]:
        """Learn from user feedback to improve memory quality"""
        try:
            context_key = self._get_context_key(context)
            memory_item = self.memory_stores[context_key].get(memory_id)

            if not memory_item:
                return {"success": False, "reason": "Memory item not found"}

            # Update memory based on feedback
            if feedback.get("correct", True):
                memory_item.confidence_score = min(
                    1.0, memory_item.confidence_score + 0.1
                )
            else:
                memory_item.confidence_score = max(
                    0.0, memory_item.confidence_score - 0.2
                )

            # Store feedback as new memory
            feedback_content = {
                "original_memory_id": memory_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.store_memory(
                feedback_content, "user_feedback", context, {"related_to": memory_id}
            )

            # Integrate with learning system
            if context:
                await agent_learning_system.process_user_feedback(
                    {"memory_id": memory_id, **feedback}, context
                )

            return {
                "success": True,
                "new_confidence": memory_item.confidence_score,
                "learning_applied": True,
            }

        except Exception as e:
            logger.error(f"Failed to learn from feedback: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_memory_performance(self) -> Dict[str, Any]:
        """Optimize memory performance through cleanup and reorganization"""
        try:
            optimization_results = {
                "expired_items_removed": 0,
                "low_confidence_removed": 0,
                "duplicates_merged": 0,
                "embeddings_updated": 0,
            }

            # Remove expired memories
            cutoff_date = datetime.utcnow() - timedelta(
                days=self.config.memory_ttl_days
            )

            for context_key, memories in self.memory_stores.items():
                # Remove expired items
                expired_ids = [
                    mid
                    for mid, memory in memories.items()
                    if memory.timestamp < cutoff_date
                ]
                for mid in expired_ids:
                    del memories[mid]
                optimization_results["expired_items_removed"] += len(expired_ids)

                # Remove low confidence items
                low_confidence_ids = [
                    mid
                    for mid, memory in memories.items()
                    if memory.confidence_score < 0.3 and memory.access_count < 2
                ]
                for mid in low_confidence_ids:
                    del memories[mid]
                optimization_results["low_confidence_removed"] += len(
                    low_confidence_ids
                )

            # Clear old cache entries
            self.embeddings_cache.clear()

            # Force garbage collection for large cleanups
            if optimization_results["expired_items_removed"] > 100:
                import gc

                gc.collect()

            logger.info(f"Memory optimization completed: {optimization_results}")
            return optimization_results

        except Exception as e:
            logger.error(f"Failed to optimize memory: {e}")
            return {"error": str(e)}

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get detailed memory statistics"""
        total_items = sum(len(memories) for memories in self.memory_stores.values())

        context_stats = {}
        for context_key, memories in self.memory_stores.items():
            if memories:
                avg_confidence = sum(
                    m.confidence_score for m in memories.values()
                ) / len(memories)
                avg_access = sum(m.access_count for m in memories.values()) / len(
                    memories
                )

                context_stats[context_key] = {
                    "total_items": len(memories),
                    "avg_confidence": avg_confidence,
                    "avg_access_count": avg_access,
                    "memory_types": defaultdict(int),
                }

                for memory in memories.values():
                    context_stats[context_key]["memory_types"][memory.source] += 1

        return {
            "total_memory_items": total_items,
            "total_contexts": len(self.memory_stores),
            "context_statistics": context_stats,
            "performance_metrics": self.performance_metrics,
            "cache_size": len(self.embeddings_cache),
            "crewai_memory_available": CREWAI_MEMORY_AVAILABLE,
        }

    # Private helper methods

    def _generate_memory_id(
        self, content: Dict[str, Any], context: Optional[LearningContext]
    ) -> str:
        """Generate unique memory ID"""
        content_str = json.dumps(content, sort_keys=True)
        context_str = str(context.context_hash) if context else "global"
        return hashlib.sha256(
            f"{content_str}:{context_str}:{datetime.utcnow()}".encode()
        ).hexdigest()[:16]

    def _get_context_key(self, context: Optional[LearningContext]) -> str:
        """Get context key for memory isolation"""
        return context.context_hash if context else "global"

    def _extract_text_content(self, content: Dict[str, Any]) -> str:
        """Extract text content for embedding"""
        text_parts = []

        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                text_parts.append(f"{key}: {json.dumps(value)}")
            else:
                text_parts.append(f"{key}: {str(value)}")

        return " ".join(text_parts)

    def _calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    def _generate_cache_key(
        self, query: Dict[str, Any], context: Optional[LearningContext]
    ) -> str:
        """Generate cache key for query results"""
        query_str = json.dumps(query, sort_keys=True)
        context_str = str(context.context_hash) if context else "global"
        return hashlib.sha256(
            f"{query_str}:{context_str}".encode()
        ).hexdigest()  # Use full 64-character SHA-256 hash

    async def _get_cached_result(self, cache_key: str) -> Optional[List[MemoryItem]]:
        """Get cached query result"""
        # Implementation depends on caching backend
        # For now, return None to always perform fresh search
        return None

    async def _cache_result(self, cache_key: str, result: List[MemoryItem]) -> None:
        """Cache query result"""
        # Implementation depends on caching backend
        pass

    def _update_search_metrics(self, elapsed_seconds: float) -> None:
        """Update search performance metrics"""
        self.performance_metrics["semantic_searches"] += 1

        # Calculate running average
        current_avg = self.performance_metrics["avg_search_time"]
        total_searches = self.performance_metrics["semantic_searches"]

        self.performance_metrics["avg_search_time"] = (
            current_avg * (total_searches - 1) + elapsed_seconds
        ) / total_searches

    async def _store_in_crewai_memory(
        self, memory_item: MemoryItem, memory_type: str
    ) -> None:
        """Store memory in CrewAI memory system"""
        if not CREWAI_MEMORY_AVAILABLE:
            return

        try:
            content_str = json.dumps(memory_item.content)

            if memory_type == "long_term" and self.long_term_memory:
                self.long_term_memory.save(content_str, metadata=memory_item.metadata)
            elif memory_type == "short_term" and self.short_term_memory:
                self.short_term_memory.save(content_str)
            elif memory_type == "entity" and self.entity_memory:
                # Extract entities and store
                entities = self._extract_entities(memory_item.content)
                for entity in entities:
                    self.entity_memory.save(entity, content_str)

        except Exception as e:
            logger.error(f"Failed to store in CrewAI memory: {e}")

    def _extract_entities(self, content: Dict[str, Any]) -> List[str]:
        """Extract entities from content for entity memory"""
        entities = []

        # Extract common entity types
        for key in [
            "asset_name",
            "server_name",
            "application_name",
            "owner",
            "location",
        ]:
            if key in content and isinstance(content[key], str):
                entities.append(content[key])

        return entities


# Global instance
enhanced_agent_memory = EnhancedAgentMemory()
