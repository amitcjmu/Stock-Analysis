"""
Configuration for application deduplication service
"""

from dataclasses import dataclass

# CC: Try importing pgvector utilities with fallback
try:
    import numpy as np  # noqa: F401
    from sentence_transformers import SentenceTransformer  # noqa: F401

    VECTOR_AVAILABLE = True

    # Initialize sentence transformer model (cached globally)
    _embedding_model = None

    def get_embedding_model():
        global _embedding_model
        if _embedding_model is None:
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _embedding_model

except ImportError:
    VECTOR_AVAILABLE = False

    def get_embedding_model():
        return None


@dataclass
class DeduplicationConfig:
    """Configuration for application deduplication behavior"""

    # Similarity thresholds for different matching methods
    exact_match_threshold: float = 1.0
    fuzzy_text_threshold: float = 0.85
    vector_similarity_threshold: float = 0.80

    # Performance settings
    max_candidates_for_fuzzy: int = 100
    enable_vector_search: bool = VECTOR_AVAILABLE
    cache_embeddings: bool = True

    # Behavior settings
    auto_merge_high_confidence: bool = True
    require_manual_verification_threshold: float = 0.95

    # Multi-tenant enforcement
    enforce_tenant_isolation: bool = True
    allow_cross_engagement_matching: bool = False
