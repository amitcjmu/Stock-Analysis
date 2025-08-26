"""
Application matching strategies for deduplication.

This module implements different matching strategies:
- Exact matching using hash lookup
- Fuzzy text matching
- Vector similarity matching
"""

import uuid
from typing import Optional, Tuple
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
)
from .config import DeduplicationConfig
from .matching import FuzzyMatcher
from .vector_ops import VectorOperations


async def try_exact_match(
    db: AsyncSession,
    normalized_name: str,
    name_hash: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Optional[Tuple[CanonicalApplication, Optional[ApplicationNameVariant]]]:
    """Try to find exact match using hash lookup for optimal performance"""

    # Try canonical application exact match first
    canonical_query = select(CanonicalApplication).where(
        and_(
            CanonicalApplication.client_account_id == client_account_id,
            CanonicalApplication.engagement_id == engagement_id,
            CanonicalApplication.name_hash == name_hash,
        )
    )

    result = await db.execute(canonical_query)
    canonical_app = result.scalar_one_or_none()

    if canonical_app:
        return canonical_app, None

    # Try variant exact match
    variant_query = (
        select(ApplicationNameVariant)
        .where(
            and_(
                ApplicationNameVariant.client_account_id == client_account_id,
                ApplicationNameVariant.engagement_id == engagement_id,
                ApplicationNameVariant.variant_hash == name_hash,
            )
        )
        .options(selectinload(ApplicationNameVariant.canonical_application))
    )

    result = await db.execute(variant_query)
    variant = result.scalar_one_or_none()

    if variant:
        return variant.canonical_application, variant

    return None


async def try_fuzzy_text_match(
    db: AsyncSession,
    normalized_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    fuzzy_matcher: FuzzyMatcher,
    config: DeduplicationConfig,
) -> Optional[Tuple[CanonicalApplication, float]]:
    """Try fuzzy text matching using the FuzzyMatcher"""

    return await fuzzy_matcher.find_fuzzy_match(
        db,
        normalized_name,
        client_account_id,
        engagement_id,
        config.fuzzy_text_threshold,
        config.max_candidates_for_fuzzy,
    )


async def try_vector_similarity_match(
    db: AsyncSession,
    application_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    vector_ops: VectorOperations,
    config: DeduplicationConfig,
) -> Optional[Tuple[CanonicalApplication, float]]:
    """Try vector similarity matching using VectorOperations"""

    return await vector_ops.find_vector_similarity_match(
        db,
        application_name,
        client_account_id,
        engagement_id,
        config.vector_similarity_threshold,
        config.max_candidates_for_fuzzy,
    )
