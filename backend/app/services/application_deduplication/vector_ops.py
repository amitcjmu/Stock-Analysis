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

    def _validate_embedding_input(self, text: str) -> Optional[str]:
        """Validate and normalize input text for embedding generation."""
        if not self.config.enable_vector_search or not VECTOR_AVAILABLE:
            logger.debug("Vector search disabled or vector libraries not available")
            return None

        if not text or not text.strip():
            logger.debug("Empty or whitespace-only text provided for embedding")
            return None

        return text.strip()

    def _check_embedding_cache(self, text: str) -> Optional[List[float]]:
        """Check cache for existing embedding and clean up invalid entries."""
        if not self.config.cache_embeddings or text not in self._embedding_cache:
            return None

        cached_result = self._embedding_cache[text]
        if isinstance(cached_result, list) and all(
            isinstance(x, (int, float)) for x in cached_result
        ):
            return cached_result
        else:
            # Clean up invalid cache entry
            logger.warning("Invalid cached embedding for text, removing from cache")
            del self._embedding_cache[text]
            return None

    def _encode_with_model(self, text: str) -> Optional[any]:
        """Encode text using the embedding model with error handling."""
        model = get_embedding_model()
        if not model:
            logger.debug("No embedding model available")
            return None

        try:
            return model.encode(text, convert_to_tensor=False)
        except Exception as model_error:
            logger.warning(
                f"Model encoding failed for text '{text[:50]}...': {str(model_error)}"
            )
            return None

    def _convert_embedding_to_list(self, embedding) -> Optional[List[float]]:
        """Convert embedding to list format with validation."""
        if embedding is None:
            logger.warning("Model returned None embedding")
            return None

        try:
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            elif isinstance(embedding, (list, tuple)):
                return list(embedding)
            else:
                logger.warning(f"Unexpected embedding type: {type(embedding)}")
                return None
        except Exception as conversion_error:
            logger.warning(
                f"Failed to convert embedding to list: {str(conversion_error)}"
            )
            return None

    def _validate_embedding_values(self, embedding_list: List) -> Optional[List[float]]:
        """Validate embedding dimensions and numeric values."""
        if not isinstance(embedding_list, list) or len(embedding_list) == 0:
            logger.warning("Generated embedding is empty or not a list")
            return None

        try:
            numeric_embedding = [float(x) for x in embedding_list]
            if not all(
                isinstance(x, (int, float)) and not (x != x) for x in numeric_embedding
            ):  # NaN check
                logger.warning("Embedding contains non-numeric or NaN values")
                return None
        except (ValueError, TypeError) as numeric_error:
            logger.warning(
                f"Failed to validate embedding numeric values: {str(numeric_error)}"
            )
            return None

        # Check for reasonable embedding dimensions
        if len(numeric_embedding) < 50 or len(numeric_embedding) > 4096:
            logger.warning(f"Embedding dimension suspicious: {len(numeric_embedding)}")

        return numeric_embedding

    def _cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache the validated embedding result."""
        if self.config.cache_embeddings:
            self._embedding_cache[text] = embedding

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text using sentence transformers with robust error handling.

        Args:
            text: Input text to encode

        Returns:
            List of floats representing the embedding vector, or None if generation fails
        """
        # Step 1: Validate input
        normalized_text = self._validate_embedding_input(text)
        if not normalized_text:
            return None

        # Step 2: Check cache
        cached_result = self._check_embedding_cache(normalized_text)
        if cached_result is not None:
            return cached_result

        try:
            # Step 3: Generate embedding with model
            raw_embedding = self._encode_with_model(normalized_text)
            if raw_embedding is None:
                return None

            # Step 4: Convert to list format
            embedding_list = self._convert_embedding_to_list(raw_embedding)
            if embedding_list is None:
                return None

            # Step 5: Validate values
            validated_embedding = self._validate_embedding_values(embedding_list)
            if validated_embedding is None:
                return None

            # Step 6: Cache result
            self._cache_embedding(normalized_text, validated_embedding)

            return validated_embedding

        except ImportError as e:
            logger.warning(f"Missing dependency for embedding generation: {str(e)}")
            return None
        except MemoryError as e:
            logger.error(f"Out of memory while generating embedding: {str(e)}")
            return None
        except Exception as e:
            logger.warning(
                f"Failed to generate embedding for '{text[:50]}...': {str(e)}"
            )
            return None

    def calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors with robust error handling.

        Args:
            vec1: First vector as list of floats
            vec2: Second vector as list of floats

        Returns:
            Cosine similarity score (0.0-1.0), or 0.0 if calculation fails
        """
        # Input validation with detailed logging
        if not NUMPY_AVAILABLE:
            logger.debug("NumPy not available for vector similarity calculation")
            return 0.0

        if not vec1 or not vec2:
            logger.debug("One or both vectors are empty")
            return 0.0

        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0

        # Validate vector contents are numeric
        try:
            vec1_numeric = [float(x) for x in vec1 if isinstance(x, (int, float))]
            vec2_numeric = [float(x) for x in vec2 if isinstance(x, (int, float))]
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid vector values: {str(e)}")
            return 0.0

        if len(vec1_numeric) != len(vec1) or len(vec2_numeric) != len(vec2):
            logger.warning("Vectors contain non-numeric values")
            return 0.0

        try:
            # Convert to numpy arrays with explicit dtype for stability
            arr1 = np.array(vec1_numeric, dtype=np.float64)
            arr2 = np.array(vec2_numeric, dtype=np.float64)

            # Check for NaN or infinite values
            if not (np.isfinite(arr1).all() and np.isfinite(arr2).all()):
                logger.warning("Vectors contain NaN or infinite values")
                return 0.0

            # Calculate norms first to check for zero vectors
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)

            # Handle zero vectors or very small norms
            if norm1 < 1e-10 or norm2 < 1e-10:
                logger.debug("One or both vectors have zero or near-zero norm")
                return 0.0

            # Calculate cosine similarity
            dot_product = np.dot(arr1, arr2)
            similarity = dot_product / (norm1 * norm2)

            # Ensure result is finite and in valid range [-1, 1]
            if not np.isfinite(similarity):
                logger.warning(
                    "Cosine similarity calculation resulted in non-finite value"
                )
                return 0.0

            # Clamp to valid range and convert to non-negative [0, 1]
            similarity_clamped = max(0.0, min(1.0, float(similarity)))

            return similarity_clamped

        except (np.linalg.LinAlgError, ValueError, OverflowError) as e:
            logger.warning(
                f"NumPy error during cosine similarity calculation: {str(e)}"
            )
            return 0.0
        except Exception as e:
            logger.error(f"Unexpected error in cosine similarity calculation: {str(e)}")
            return 0.0

    def _validate_similarity_search_params(
        self, application_name: str, threshold: float, max_candidates: int
    ) -> Optional[tuple[str, float, int]]:
        """Validate parameters for similarity search."""
        if not self.config.enable_vector_search:
            logger.debug("Vector search disabled in configuration")
            return None

        if not application_name or not application_name.strip():
            logger.debug("Empty application name provided for vector similarity search")
            return None

        # Validate threshold parameter
        if (
            not isinstance(threshold, (int, float))
            or threshold < 0.0
            or threshold > 1.0
        ):
            logger.warning(f"Invalid threshold value: {threshold}, using default 0.7")
            threshold = 0.7

        # Validate max_candidates parameter
        if not isinstance(max_candidates, int) or max_candidates <= 0:
            logger.warning(
                f"Invalid max_candidates value: {max_candidates}, using default 100"
            )
            max_candidates = 100

        return application_name.strip(), threshold, max_candidates

    async def _fetch_candidate_applications(
        self,
        db: AsyncSession,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        max_candidates: int,
    ) -> Optional[List]:
        """Fetch candidate applications with embeddings from database."""
        try:
            apps_query = (
                select(CanonicalApplication)
                .where(
                    and_(
                        CanonicalApplication.client_account_id == client_account_id,
                        CanonicalApplication.engagement_id == engagement_id,
                        CanonicalApplication.name_embedding.isnot(None),
                    )
                )
                .limit(min(max_candidates, 1000))  # Cap at reasonable limit
            )

            result = await db.execute(apps_query)
            all_apps = result.scalars().all()

            if not all_apps:
                logger.debug("No canonical applications with embeddings found in scope")
                return None

            return all_apps

        except Exception as db_error:
            logger.error(
                f"Database error during vector similarity query: {str(db_error)}"
            )
            return None

    def _find_best_similarity_match(
        self, input_embedding: List[float], candidate_apps: List, threshold: float
    ) -> Optional[tuple]:
        """Find the best similarity match from candidate applications."""
        best_match = None
        best_similarity = 0.0
        comparison_count = 0

        for app in candidate_apps:
            try:
                if app.name_embedding and isinstance(app.name_embedding, list):
                    similarity = self.calculate_cosine_similarity(
                        input_embedding, app.name_embedding
                    )

                    comparison_count += 1

                    # Update best match if this similarity is better and meets threshold
                    if (
                        similarity > best_similarity
                        and similarity >= threshold
                        and isinstance(similarity, (int, float))
                        and 0.0 <= similarity <= 1.0
                    ):
                        best_similarity = similarity
                        best_match = app

            except Exception as comparison_error:
                logger.warning(
                    f"Error comparing with app {getattr(app, 'id', 'unknown')}: {str(comparison_error)}"
                )
                continue

        logger.debug(f"Completed {comparison_count} similarity comparisons")

        if best_match and best_similarity >= threshold:
            return best_match, best_similarity

        return None

    async def find_vector_similarity_match(
        self,
        db: AsyncSession,
        application_name: str,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        threshold: float,
        max_candidates: int = 100,
    ) -> Optional[tuple]:
        """
        Try vector similarity matching using sentence transformers with robust error handling.

        Args:
            db: Database session
            application_name: Name to find similar matches for
            client_account_id: Client account scope
            engagement_id: Engagement scope
            threshold: Minimum similarity threshold (0.0-1.0)
            max_candidates: Maximum number of candidates to compare

        Returns:
            Tuple of (best_match, similarity_score) or None if no match found
        """
        try:
            # Step 1: Validate parameters
            validated_params = self._validate_similarity_search_params(
                application_name, threshold, max_candidates
            )
            if not validated_params:
                return None

            app_name, validated_threshold, validated_max_candidates = validated_params

            # Step 2: Generate embedding for input application name
            input_embedding = await self.generate_embedding(app_name)
            if not input_embedding:
                logger.debug(f"Could not generate embedding for '{application_name}'")
                return None

            # Step 3: Fetch candidate applications
            candidate_apps = await self._fetch_candidate_applications(
                db, client_account_id, engagement_id, validated_max_candidates
            )
            if not candidate_apps:
                return None

            # Step 4: Find best similarity match
            best_match_result = self._find_best_similarity_match(
                input_embedding, candidate_apps, validated_threshold
            )

            if best_match_result:
                best_match, best_similarity = best_match_result
                logger.info(
                    f"Vector similarity match found: {best_similarity:.3f} for '{application_name}'"
                )
                return best_match, best_similarity
            else:
                logger.debug(
                    f"No vector similarity match found above threshold {validated_threshold}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Unexpected error in vector similarity matching for '{application_name}': {str(e)}"
            )
            return None
