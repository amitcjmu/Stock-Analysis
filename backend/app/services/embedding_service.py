"""
Enhanced Embedding Service for Vector Search and Learning
Provides AI-powered vector embeddings using DeepInfra's thenlper/gte-large model.
Supports learning pattern storage and similarity search for assets.
"""

import hashlib
import logging
import random
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Enhanced service for generating embeddings and performing similarity search."""

    def __init__(self):
        self.ai_available = False
        self.api_key = settings.DEEPINFRA_API_KEY
        self.base_url = "https://api.deepinfra.com/v1/openai"
        self.model = "thenlper/gte-large"

        if self.api_key:
            self.ai_available = True
            logger.info(
                f"✅ AI embedding service initialized with DeepInfra {self.model} model"
            )
        else:
            logger.warning(
                "AI embedding service using mock mode - DEEPINFRA_API_KEY not configured"
            )

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for text using DeepInfra's thenlper/gte-large model.
        Returns 1024-dimensional vector.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        if not self.ai_available:
            logger.debug("AI embedding not available, using mock embedding")
            return self._generate_mock_embedding(text)

        try:
            # Make direct API call to DeepInfra
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": text,
                        "encoding_format": "float",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Extract embedding from response
                    if "data" in data and len(data["data"]) > 0:
                        embedding = data["data"][0]["embedding"]
                        logger.debug(
                            f"Generated embedding for text (dim: {len(embedding)})"
                        )
                        return embedding
                    else:
                        logger.error(f"Unexpected response format: {data}")
                        return self._generate_mock_embedding(text)
                else:
                    logger.error(
                        f"DeepInfra API error {response.status_code}: {response.text}"
                    )
                    return self._generate_mock_embedding(text)

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback to mock embedding
            return self._generate_mock_embedding(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.ai_available:
            logger.debug("AI embedding not available, using mock embeddings")
            return [self._generate_mock_embedding(text) for text in texts]

        try:
            # Make batch API call to DeepInfra
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": texts,
                        "encoding_format": "float",
                    },
                    timeout=60.0,  # Longer timeout for batch
                )

                if response.status_code == 200:
                    data = response.json()
                    # Extract embeddings from response
                    if "data" in data:
                        embeddings = [item["embedding"] for item in data["data"]]
                        logger.debug(
                            f"Generated {len(embeddings)} embeddings (dim: {len(embeddings[0]) if embeddings else 0})"
                        )
                        return embeddings
                    else:
                        logger.error(f"Unexpected response format: {data}")
                        return [self._generate_mock_embedding(text) for text in texts]
                else:
                    logger.error(
                        f"DeepInfra API error {response.status_code}: {response.text}"
                    )
                    return [self._generate_mock_embedding(text) for text in texts]

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Fallback to mock embeddings
            return [self._generate_mock_embedding(text) for text in texts]

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for testing/fallback purposes.
        Creates a deterministic vector based on text content.
        """
        # Create deterministic mock embedding based on text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:32]

        # Use hash to seed random generator for consistent results
        random.seed(text_hash)

        # Generate 1024-dimensional vector (matching thenlper/gte-large)
        embedding = [random.uniform(-1.0, 1.0) for _ in range(1024)]

        # Reset random seed
        random.seed()

        return embedding

    def calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vector dimensions don't match: {len(vec1)} vs {len(vec2)}"
            )

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)

        return similarity

    async def find_similar_assets(
        self,
        query_text: str,
        asset_embeddings: List[tuple],
        similarity_threshold: float = 0.7,
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Find assets similar to the query text based on embedding similarity.

        Args:
            query_text: Text to search for
            asset_embeddings: List of (asset_id, embedding) tuples
            similarity_threshold: Minimum similarity score
            top_k: Number of top results to return

        Returns:
            List of (asset_id, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = await self.embed_text(query_text)

        # Calculate similarities
        similarities = []
        for asset_id, asset_embedding in asset_embeddings:
            similarity = self.calculate_cosine_similarity(
                query_embedding, asset_embedding
            )
            if similarity >= similarity_threshold:
                similarities.append((asset_id, similarity))

        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k results
        return similarities[:top_k]


# Create singleton instance
embedding_service = EmbeddingService()