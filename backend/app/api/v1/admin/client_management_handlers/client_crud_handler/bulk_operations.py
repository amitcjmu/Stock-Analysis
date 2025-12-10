"""
Client Bulk Operations

Handles bulk create, update, and delete operations for client accounts.
"""

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.admin_schemas import AdminSuccessResponse
from .cascade_delete import cascade_delete_client_data

logger = logging.getLogger(__name__)

# Import models with fallback
try:
    from app.models.client_account import ClientAccount

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = None


async def bulk_delete_clients(
    client_ids: list, db: AsyncSession, admin_user: str
) -> AdminSuccessResponse:
    """Bulk delete multiple client accounts.

    Each deletion runs in its own nested transaction (savepoint) to ensure
    that failures in one client deletion don't affect others.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")

        deleted_count = 0
        failed_count = 0
        errors = []

        for client_id in client_ids:
            try:
                # Use nested transaction (savepoint) for each deletion
                # This ensures failures don't cascade to other deletions
                async with db.begin_nested():
                    result = await _delete_client_internal(client_id, db, admin_user)
                    if result.get("success"):
                        deleted_count += 1
                    else:
                        # Soft deleted counts as success
                        deleted_count += 1
            except Exception as e:
                # Savepoint automatically rolled back on exception
                # Try soft delete as fallback
                try:
                    async with db.begin_nested():
                        await _soft_delete_client(client_id, db, admin_user)
                        deleted_count += 1
                        logger.info(f"Client {client_id} soft-deleted as fallback")
                except Exception:
                    failed_count += 1
                    error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
                    errors.append(f"Client {client_id}: {error_msg}")
                    logger.warning(f"Failed to delete client {client_id}: {error_msg}")

        # Commit the overall transaction with all successful deletions
        await db.commit()

        message = (
            f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
        )
        if errors:
            message += f". Errors: {'; '.join(errors[:5])}"
            if len(errors) > 5:
                message += f" (+{len(errors) - 5} more)"

        return AdminSuccessResponse(
            message=message,
            data={
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "errors": errors,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in bulk delete clients: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk delete clients: {str(e)}"
        )


async def _delete_client_internal(
    client_id: str, db: AsyncSession, admin_user: str
) -> dict:
    """Internal delete method for use within savepoints.

    Unlike delete_client(), this doesn't manage its own transaction
    and returns a dict instead of raising HTTPException for soft deletes.
    """
    if not CLIENT_MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Client models not available")

    query = select(ClientAccount).where(ClientAccount.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client account not found")

    client_name = client.name

    try:
        # Perform comprehensive cascade deletion
        await cascade_delete_client_data(db, client_id)

        # Delete the client itself
        await db.delete(client)
        # Don't commit here - let the caller manage the transaction

        logger.info(
            f"Client account deleted with cascade cleanup: {client_name} by admin {admin_user}"
        )

        return {"success": True, "hard_delete": True, "name": client_name}

    except Exception as cascade_error:
        logger.warning(
            f"Cascade deletion failed for client {client_id}, attempting soft delete: {cascade_error}"
        )
        # Re-raise to trigger savepoint rollback, then try soft delete separately
        raise


async def _soft_delete_client(
    client_id: str, db: AsyncSession, admin_user: str
) -> dict:
    """Soft delete a client by setting is_active to False.

    Used as fallback when cascade deletion fails due to foreign key constraints.
    """
    query = select(ClientAccount).where(ClientAccount.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client account not found")

    client_name = client.name
    client.is_active = False
    # Don't commit - let caller manage the transaction

    logger.info(
        f"Client account soft-deleted due to constraints: {client_name} by admin {admin_user}"
    )

    return {"success": True, "soft_delete": True, "name": client_name}
