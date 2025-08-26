"""
Canonical application creation and management operations.

This module handles:
- Creating new canonical applications
- Managing collection flow application links
- Proper embedding generation and metadata handling
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
    CollectionFlowApplication,
    MatchMethod,
    VerificationSource,
)
from .config import DeduplicationConfig
from .vector_ops import VectorOperations


async def create_new_canonical_application(
    db: AsyncSession,
    application_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    additional_metadata: Optional[Dict[str, Any]],
    vector_ops: VectorOperations,
    config: DeduplicationConfig,
) -> CanonicalApplication:
    """Create a new canonical application with proper normalization and embedding"""

    normalized_name = CanonicalApplication.normalize_name(application_name)
    name_hash = CanonicalApplication.generate_name_hash(normalized_name)

    # Generate embedding if vector search is enabled
    embedding = None
    if config.enable_vector_search:
        embedding = await vector_ops.generate_embedding(application_name)

    new_canonical = CanonicalApplication(
        canonical_name=application_name.strip(),
        normalized_name=normalized_name,
        name_hash=name_hash,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        name_embedding=embedding,
        created_by=user_id,
        verification_source=VerificationSource.USER_INPUT.value,
        **(additional_metadata or {}),
    )

    db.add(new_canonical)
    await db.flush()  # Get the ID without committing

    return new_canonical


async def create_collection_flow_link(
    db: AsyncSession,
    collection_flow_id: uuid.UUID,
    canonical_app: CanonicalApplication,
    variant: Optional[ApplicationNameVariant],
    original_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
):
    """Create or update collection flow application link"""

    # Check if link already exists
    existing_query = select(CollectionFlowApplication).where(
        and_(
            CollectionFlowApplication.collection_flow_id == collection_flow_id,
            CollectionFlowApplication.canonical_application_id == canonical_app.id,
        )
    )

    result = await db.execute(existing_query)
    existing_link = result.scalar_one_or_none()

    if existing_link:
        # Update existing link
        existing_link.name_variant_id = variant.id if variant else None
        existing_link.updated_at = datetime.utcnow()
        return existing_link

    # Create new link
    new_link = CollectionFlowApplication(
        collection_flow_id=collection_flow_id,
        canonical_application_id=canonical_app.id,
        name_variant_id=variant.id if variant else None,
        application_name=original_name,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        deduplication_method=(
            variant.match_method if variant else MatchMethod.EXACT.value
        ),
        match_confidence=variant.match_confidence if variant else 1.0,
    )

    db.add(new_link)
    return new_link
