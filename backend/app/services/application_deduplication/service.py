"""
Application Deduplication Service with Multi-tenant Isolation

This service provides comprehensive application identity management for collection flows:
- Prevents duplicate applications within same engagement
- Provides fuzzy matching with configurable similarity thresholds
- Ensures multi-tenant data isolation
- Implements idempotent updates with proper audit trails
- Optimizes performance with strategic caching and indexing
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
    MatchMethod,
)

from .config import DeduplicationConfig, VECTOR_AVAILABLE
from .types import DeduplicationResult
from .matching import FuzzyMatcher
from .vector_ops import VectorOperations
from .validators import validate_deduplication_inputs
from .tenant_scoped_operations import enforce_tenant_scope
from .matching_strategies import (
    try_exact_match,
    try_fuzzy_text_match,
    try_vector_similarity_match,
)
from .canonical_operations import (
    create_new_canonical_application,
    create_collection_flow_link,
)
from .bulk_operations import bulk_deduplicate_applications

logger = logging.getLogger(__name__)


class ApplicationDeduplicationService:
    """
    Service for managing application identity with deduplication and multi-tenant isolation.

    This service ensures that:
    1. Applications are properly deduplicated within engagement boundaries
    2. Multi-tenant data isolation is strictly enforced
    3. Fuzzy matching handles common name variations
    4. Vector similarity provides semantic matching when available
    5. Audit trails are maintained for all changes
    """

    def __init__(self, config: Optional[DeduplicationConfig] = None):
        self.config = config or DeduplicationConfig()
        self._embedding_cache: Dict[str, List[float]] = {}
        self.fuzzy_matcher = FuzzyMatcher()
        self.vector_ops = VectorOperations(self.config)

        if self.config.enable_vector_search and not VECTOR_AVAILABLE:
            logger.warning("Vector search requested but dependencies not available")
            self.config.enable_vector_search = False

    async def deduplicate_application(
        self,
        db: AsyncSession,
        application_name: str,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        collection_flow_id: Optional[uuid.UUID] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> DeduplicationResult:
        """
        Main entry point for application deduplication.

        This method handles the complete deduplication workflow:
        1. Input validation and normalization
        2. Multi-tenant scope enforcement
        3. Exact matching attempts
        4. Fuzzy text matching
        5. Vector similarity matching (if available)
        6. Canonical application creation/update
        7. Audit trail maintenance
        """

        start_time = datetime.utcnow()

        try:
            # Step 1: Input validation
            validate_deduplication_inputs(
                application_name, client_account_id, engagement_id
            )

            # Step 2: Normalize application name
            normalized_name = CanonicalApplication.normalize_name(application_name)
            name_hash = CanonicalApplication.generate_name_hash(normalized_name)

            logger.info(
                f"🔍 Starting deduplication for '{application_name}' "
                f"(normalized: '{normalized_name}', engagement: {engagement_id})"
            )

            # Step 3: Multi-tenant scope enforcement
            await enforce_tenant_scope(
                db, client_account_id, engagement_id, self.config
            )

            # Step 4: Try exact matching first (fastest path)
            exact_result = await try_exact_match(
                db, normalized_name, name_hash, client_account_id, engagement_id
            )

            if exact_result:
                canonical_app, variant = exact_result
                canonical_app.update_usage_stats()

                # Create collection flow application link if provided
                if collection_flow_id:
                    await create_collection_flow_link(
                        db,
                        collection_flow_id,
                        canonical_app,
                        variant,
                        application_name,
                        client_account_id,
                        engagement_id,
                    )

                await db.commit()

                logger.info(
                    f"✅ Exact match found for '{application_name}' -> '{canonical_app.canonical_name}'"
                )

                return DeduplicationResult(
                    canonical_application=canonical_app,
                    name_variant=variant,
                    is_new_canonical=False,
                    is_new_variant=variant is not None and variant.usage_count == 1,
                    match_method=MatchMethod.EXACT,
                    similarity_score=1.0,
                    confidence_score=1.0,
                    requires_verification=False,
                    potential_duplicates=[],
                )

            # Step 5: Try fuzzy text matching
            fuzzy_result = await try_fuzzy_text_match(
                db,
                normalized_name,
                client_account_id,
                engagement_id,
                self.fuzzy_matcher,
                self.config,
            )

            if fuzzy_result:
                canonical_app, similarity_score = fuzzy_result

                # Create variant for the fuzzy match
                variant = await ApplicationNameVariant.create_variant(
                    db,
                    canonical_app,
                    application_name,
                    MatchMethod.FUZZY_TEXT,
                    similarity_score,
                )

                canonical_app.update_usage_stats()

                # Create collection flow application link if provided
                if collection_flow_id:
                    await create_collection_flow_link(
                        db,
                        collection_flow_id,
                        canonical_app,
                        variant,
                        application_name,
                        client_account_id,
                        engagement_id,
                    )

                await db.commit()

                logger.info(
                    f"🎯 Fuzzy match found for '{application_name}' -> '{canonical_app.canonical_name}' "
                    f"(similarity: {similarity_score:.3f})"
                )

                return DeduplicationResult(
                    canonical_application=canonical_app,
                    name_variant=variant,
                    is_new_canonical=False,
                    is_new_variant=True,
                    match_method=MatchMethod.FUZZY_TEXT,
                    similarity_score=similarity_score,
                    confidence_score=similarity_score,
                    requires_verification=similarity_score
                    < self.config.require_manual_verification_threshold,
                    potential_duplicates=[],
                )

            # Step 6: Try vector similarity matching if available
            if self.config.enable_vector_search:
                vector_result = await try_vector_similarity_match(
                    db,
                    application_name,
                    client_account_id,
                    engagement_id,
                    self.vector_ops,
                    self.config,
                )

                if vector_result:
                    canonical_app, similarity_score = vector_result

                    # Create variant for the vector match
                    variant = await ApplicationNameVariant.create_variant(
                        db,
                        canonical_app,
                        application_name,
                        MatchMethod.VECTOR_SIMILARITY,
                        similarity_score,
                    )

                    canonical_app.update_usage_stats()

                    # Create collection flow application link if provided
                    if collection_flow_id:
                        await self._create_collection_flow_link(
                            db,
                            collection_flow_id,
                            canonical_app,
                            variant,
                            application_name,
                            client_account_id,
                            engagement_id,
                        )

                    await db.commit()

                    logger.info(
                        f"🧠 Vector similarity match found for '{application_name}' -> '{canonical_app.canonical_name}' "
                        f"(similarity: {similarity_score:.3f})"
                    )

                    return DeduplicationResult(
                        canonical_application=canonical_app,
                        name_variant=variant,
                        is_new_canonical=False,
                        is_new_variant=True,
                        match_method=MatchMethod.VECTOR_SIMILARITY,
                        similarity_score=similarity_score,
                        confidence_score=similarity_score,
                        requires_verification=similarity_score
                        < self.config.require_manual_verification_threshold,
                        potential_duplicates=[],
                    )

            # Step 7: No matches found - create new canonical application
            new_canonical = await create_new_canonical_application(
                db,
                application_name,
                client_account_id,
                engagement_id,
                user_id,
                additional_metadata,
                self.vector_ops,
                self.config,
            )

            # Create collection flow application link if provided
            if collection_flow_id:
                await create_collection_flow_link(
                    db,
                    collection_flow_id,
                    new_canonical,
                    None,
                    application_name,
                    client_account_id,
                    engagement_id,
                )

            await db.commit()

            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"🆕 Created new canonical application '{application_name}' "
                f"for engagement {engagement_id} (processed in {processing_time:.3f}s)"
            )

            return DeduplicationResult(
                canonical_application=new_canonical,
                name_variant=None,
                is_new_canonical=True,
                is_new_variant=False,
                match_method=MatchMethod.EXACT,
                similarity_score=1.0,
                confidence_score=1.0,
                requires_verification=False,
                potential_duplicates=[],
            )

        except Exception as e:
            logger.error(
                f"❌ Deduplication failed for '{application_name}' "
                f"in engagement {engagement_id}: {str(e)}"
            )
            raise

    async def bulk_deduplicate_applications(
        self,
        db: AsyncSession,
        applications: List[str],
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        collection_flow_id: Optional[uuid.UUID] = None,
        batch_size: int = 50,
    ) -> List[DeduplicationResult]:
        """
        Bulk deduplication for multiple applications with optimizations.
        """
        return await bulk_deduplicate_applications(
            self,
            db,
            applications,
            client_account_id,
            engagement_id,
            user_id,
            collection_flow_id,
            batch_size,
        )


# Factory function for easy service instantiation
def create_deduplication_service(
    similarity_threshold: float = 0.85, enable_vector_search: bool = VECTOR_AVAILABLE
) -> ApplicationDeduplicationService:
    """Factory function to create deduplication service with custom configuration"""

    config = DeduplicationConfig(
        fuzzy_text_threshold=similarity_threshold,
        enable_vector_search=enable_vector_search,
    )

    return ApplicationDeduplicationService(config)
