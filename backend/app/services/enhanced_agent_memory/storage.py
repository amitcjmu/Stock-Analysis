"""
Enhanced Agent Memory - Storage Module
Contains storage and retrieval methods.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.enhanced_agent_memory.base import MemoryItem

logger = logging.getLogger(__name__)

try:
    from crewai.memory.storage import ChromaStorage, JSONStorage
except ImportError:
    ChromaStorage = None  # type: ignore
    JSONStorage = None  # type: ignore
# Import from base
try:
    from crewai.memory import EntityMemory, LongTermMemory, ShortTermMemory

    CREWAI_MEMORY_AVAILABLE = True
except ImportError:
    CREWAI_MEMORY_AVAILABLE = False


class StorageMixin:
    """Mixin for storage and retrieval operations"""

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
