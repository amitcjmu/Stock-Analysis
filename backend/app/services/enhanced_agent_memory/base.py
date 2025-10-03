"""
Enhanced Agent Memory System with CrewAI Integration
Implements optimized memory management for CrewAI agents with:
- Persistent long-term memory using CrewAI's memory features
- Vector-based semantic search for pattern matching
- Multi-tenant isolation with learning scopes
- Performance optimization and caching
- Integration with existing agent learning system
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# CrewAI memory imports with graceful fallback
try:
    pass  # noqa
    pass  # noqa  # Imported in storage.py

    CREWAI_MEMORY_AVAILABLE = True
except ImportError:
    CREWAI_MEMORY_AVAILABLE = False
    logging.warning("CrewAI memory features not available, using fallback")

from app.services.agent_learning_system import (
    LearningContext,
)  # noqa: F401
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfiguration:
    """Configuration for agent memory system"""

    enable_long_term_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
    enable_short_term_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
    enable_entity_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
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
