"""
Bulk deduplication operations for processing multiple applications efficiently.

This module handles batch processing of multiple applications with optimizations
for database performance and error handling.
"""

import asyncio
import logging
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .types import DeduplicationResult

logger = logging.getLogger(__name__)


async def bulk_deduplicate_applications(
    service_instance,  # ApplicationDeduplicationService instance
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

    if not applications:
        return []

    results = []
    unique_applications = list(
        dict.fromkeys(applications)
    )  # Preserve order, remove duplicates

    logger.info(
        f"🔄 Starting bulk deduplication for {len(unique_applications)} applications "
        f"in engagement {engagement_id}"
    )

    # Process in batches to avoid overwhelming the database
    for i in range(0, len(unique_applications), batch_size):
        batch = unique_applications[i : i + batch_size]
        batch_results = []

        for app_name in batch:
            try:
                result = await service_instance.deduplicate_application(
                    db,
                    app_name,
                    client_account_id,
                    engagement_id,
                    user_id,
                    collection_flow_id,
                )
                batch_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to deduplicate '{app_name}' in batch: {str(e)}")
                # Continue processing other applications
                continue

        results.extend(batch_results)

        # Small delay between batches to avoid overwhelming the system
        if i + batch_size < len(unique_applications):
            await asyncio.sleep(0.1)

    logger.info(
        f"✅ Bulk deduplication completed: {len(results)}/{len(unique_applications)} successful"
    )

    return results
