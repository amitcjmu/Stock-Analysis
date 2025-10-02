"""
Memory Management Admin API Endpoints (ADR-024)

Provides administrative endpoints for managing tenant memory and learning patterns.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models.client_account.user import User
from app.services.crewai_flows.memory.tenant_memory_manager import LearningScope

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/memory",
)


@router.get("/stats")
async def get_memory_statistics(
    client_account_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get learning statistics and pattern counts.

    Args:
        client_account_id: Optional client account UUID filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        Memory statistics including pattern counts, types, and storage metrics
    """
    try:
        from sqlalchemy import func, select

        from app.models.agent_discovered_patterns import AgentDiscoveredPatterns

        # Build base query
        query = select(
            func.count(AgentDiscoveredPatterns.id).label("total_patterns"),
            AgentDiscoveredPatterns.pattern_type,
            func.sum(func.pg_column_size(AgentDiscoveredPatterns.pattern_data)).label(
                "metadata_size"
            ),
        )

        # Apply client filter if provided
        if client_account_id:
            query = query.where(
                AgentDiscoveredPatterns.client_account_id == client_account_id
            )

        # Group by pattern type
        query = query.group_by(AgentDiscoveredPatterns.pattern_type)

        # Execute query
        result = await db.execute(query)
        pattern_stats = result.fetchall()

        # Calculate total counts
        total_patterns = sum(row.total_patterns for row in pattern_stats)
        patterns_by_type = {
            row.pattern_type: {
                "count": row.total_patterns,
                "metadata_size_bytes": row.metadata_size or 0,
            }
            for row in pattern_stats
        }

        # Count unique tenants (clients)
        tenant_query = select(
            func.count(func.distinct(AgentDiscoveredPatterns.client_account_id))
        )
        if client_account_id:
            tenant_query = tenant_query.where(
                AgentDiscoveredPatterns.client_account_id == client_account_id
            )

        tenant_result = await db.execute(tenant_query)
        tenant_count = tenant_result.scalar() or 0

        # Calculate total memory usage
        total_memory_bytes = sum(
            stats["metadata_size_bytes"] for stats in patterns_by_type.values()
        )
        memory_usage_mb = total_memory_bytes / (1024 * 1024)

        return {
            "success": True,
            "statistics": {
                "total_patterns": total_patterns,
                "patterns_by_type": patterns_by_type,
                "memory_usage_mb": round(memory_usage_mb, 2),
                "tenant_count": tenant_count,
            },
            "filter_applied": (
                {"client_account_id": client_account_id} if client_account_id else None
            ),
        }

    except Exception as e:
        logger.error(f"Error retrieving memory statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve memory statistics: {str(e)}",
        )


@router.post("/scope")
async def update_memory_scope(
    client_account_id: UUID,
    scope: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update learning scope for a client.

    This endpoint allows administrators to configure memory isolation levels per client.
    The scope determines what patterns can be shared:
    - DISABLED: No learning or pattern storage
    - ENGAGEMENT: Patterns isolated to specific engagements
    - CLIENT: Patterns shared across client engagements
    - GLOBAL: Patterns available globally (requires consent)

    Args:
        client_account_id: Client account UUID
        scope: Learning scope (ENGAGEMENT, CLIENT, GLOBAL, DISABLED)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Update confirmation with old and new scope
    """
    try:
        from sqlalchemy import select, update

        from app.models.client_account import ClientAccount

        # Validate scope
        try:
            learning_scope = LearningScope[scope.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scope: {scope}. Must be one of: ENGAGEMENT, CLIENT, GLOBAL, DISABLED",
            )

        # Check if client exists
        client_query = select(ClientAccount).where(
            ClientAccount.id == client_account_id
        )
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client account {client_account_id} not found",
            )

        # Get current scope from client metadata
        old_scope = (
            client.metadata.get("learning_scope", "ENGAGEMENT")
            if client.metadata
            else "ENGAGEMENT"
        )

        # Update client metadata with new scope
        new_metadata = client.metadata or {}
        new_metadata["learning_scope"] = learning_scope.value
        new_metadata["learning_scope_updated_at"] = str(
            __import__("datetime").datetime.utcnow()
        )
        new_metadata["learning_scope_updated_by"] = current_user.username

        update_stmt = (
            update(ClientAccount)
            .where(ClientAccount.id == client_account_id)
            .values(metadata=new_metadata)
        )

        await db.execute(update_stmt)
        await db.commit()

        logger.info(
            f"Updated learning scope for client {client_account_id}: {old_scope} -> {learning_scope.value}"
        )

        return {
            "success": True,
            "client_account_id": client_account_id,
            "old_scope": old_scope,
            "new_scope": learning_scope.value,
            "updated_by": current_user.username,
            "message": "Memory scope updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory scope: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory scope: {str(e)}",
        )


@router.delete("/purge")
async def purge_client_memory(
    client_account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purge all learning data for a client (GDPR compliance).

    This endpoint permanently deletes all stored learning patterns for a specific client,
    supporting GDPR "right to be forgotten" requirements. The operation is irreversible.

    Args:
        client_account_id: Client account UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Purge confirmation with count of deleted patterns
    """
    try:
        from sqlalchemy import delete, select

        from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
        from app.models.client_account import ClientAccount

        # Verify client exists
        client_query = select(ClientAccount).where(
            ClientAccount.id == client_account_id
        )
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client account {client_account_id} not found",
            )

        # Count patterns before deletion
        count_query = select(
            __import__("sqlalchemy").func.count(AgentDiscoveredPatterns.id)
        ).where(AgentDiscoveredPatterns.client_account_id == client_account_id)
        count_result = await db.execute(count_query)
        patterns_count = count_result.scalar() or 0

        # Delete all patterns for this client
        delete_stmt = delete(AgentDiscoveredPatterns).where(
            AgentDiscoveredPatterns.client_account_id == client_account_id
        )

        await db.execute(delete_stmt)
        await db.commit()

        logger.warning(
            f"GDPR PURGE: Deleted {patterns_count} patterns for client {client_account_id} "
            f"(requested by {current_user.username})"
        )

        return {
            "success": True,
            "client_account_id": client_account_id,
            "patterns_deleted": patterns_count,
            "purged_by": current_user.username,
            "purged_at": str(__import__("datetime").datetime.utcnow()),
            "message": f"Successfully purged {patterns_count} learning patterns for client",
            "warning": "This operation is irreversible. All learning data has been permanently deleted.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purging client memory: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge client memory: {str(e)}",
        )
