"""
Vector operations for semantic similarity matching
"""

import logging
from typing import List, Optional
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_applications import CanonicalApplication

from .config import get_embedding_model, VECTOR_AVAILABLE, DeduplicationConfig

logger = logging.getLogger(__name__)

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class VectorOperations:
    """Handles vector similarity operations for application deduplication"""

    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self._embedding_cache: dict = {}

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for text using sentence transformers"""

        if not self.config.enable_vector_search or not VECTOR_AVAILABLE:
            return None

        # Check cache first
        if self.config.cache_embeddings and text in self._embedding_cache:
            return self._embedding_cache[text]

        try:
            model = get_embedding_model()
            if not model:
                return None

            embedding = model.encode(text, convert_to_tensor=False)
            embedding_list = embedding.tolist()

            # Cache the result
            if self.config.cache_embeddings:
                self._embedding_cache[text] = embedding_list

            return embedding_list

        except Exception as e:
            logger.warning(f"Failed to generate embedding for '{text}': {str(e)}")
            return None

    def calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""

        if not vec1 or not vec2 or len(vec1) != len(vec2) or not NUMPY_AVAILABLE:
            return 0.0

        try:
            # Convert to numpy arrays for efficient computation
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)

            # Calculate cosine similarity
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.warning(f"Failed to calculate cosine similarity: {str(e)}")
            return 0.0

    async def find_vector_similarity_match(
        self,
        db: AsyncSession,
        application_name: str,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        threshold: float,
        max_candidates: int = 100,
    ) -> Optional[tuple]:
        """Try vector similarity matching using sentence transformers"""

        if not self.config.enable_vector_search:
            return None

        # Generate embedding for input application name
        input_embedding = await self.generate_embedding(application_name)
        if not input_embedding:
            return None

        # Get applications with embeddings
        apps_query = (
            select(CanonicalApplication)
            .where(
                and_(
                    CanonicalApplication.client_account_id == client_account_id,
                    CanonicalApplication.engagement_id == engagement_id,
                    CanonicalApplication.name_embedding.isnot(None),
                )
            )
            .limit(max_candidates)
        )

        result = await db.execute(apps_query)
        all_apps = result.scalars().all()

        best_match = None
        best_similarity = 0.0

        for app in all_apps:
            if app.name_embedding:
                similarity = self.calculate_cosine_similarity(
                    input_embedding, app.name_embedding
                )

                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match = app

        if best_match:
            return best_match, best_similarity

        return None
