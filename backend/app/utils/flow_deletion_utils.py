"""Flow Deletion Utilities

Defensive utilities for handling flow deletion audit operations
even when the database table might not exist yet.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def safely_create_deletion_audit(
    db: AsyncSession,
    audit_record,
    flow_id: str,
    operation_context: str = "flow_deletion",
) -> Optional[str]:
    """
    Safely create a flow deletion audit record with defensive handling.

    This function handles the case where the flow_deletion_audit table
    might not exist yet, which can happen during migrations or initial deployments.

    Args:
        db: Database session
        audit_record: FlowDeletionAudit instance to save
        flow_id: Flow ID being deleted (for error context)
        operation_context: Context description for logging

    Returns:
        Audit record ID if successful, None if table doesn't exist
    """
    try:
        db.add(audit_record)
        await db.flush()  # Get the ID without committing yet
        audit_id = str(audit_record.id)

        logger.info(
            f"✅ [{operation_context}] Created deletion audit record {audit_id} for flow {flow_id}"
        )
        return audit_id

    except (ProgrammingError, OperationalError) as e:
        error_message = str(e).lower()

        # Check if the error is related to missing table
        if "flow_deletion_audit" in error_message and (
            "does not exist" in error_message
            or "relation" in error_message
            or "table" in error_message
        ):
            logger.warning(
                f"⚠️  [{operation_context}] flow_deletion_audit table not found - "
                f"skipping audit record creation for flow {flow_id}. "
                f"This is expected during initial migrations. Error: {e}"
            )
            # Rollback the failed operation to keep the session clean
            await db.rollback()
            return None
        else:
            # Re-raise if it's a different type of database error
            logger.error(
                f"❌ [{operation_context}] Unexpected database error creating audit record for flow {flow_id}: {e}"
            )
            raise

    except Exception as e:
        logger.error(
            f"❌ [{operation_context}] Unexpected error creating audit record for flow {flow_id}: {e}"
        )
        raise


def safely_create_audit_data(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    deletion_type: str,
    deletion_method: str,
    deleted_by: str,
    deletion_reason: str = None,
    data_deleted: Dict[str, Any] = None,
    deletion_impact: Dict[str, Any] = None,
    cleanup_summary: Dict[str, Any] = None,
    deletion_duration_ms: int = None,
) -> Optional[dict]:
    """
    Create audit data safely with validation.

    Returns None if required imports fail (table model not available).
    """
    try:
        from app.models.flow_deletion_audit import FlowDeletionAudit

        audit_record = FlowDeletionAudit.create_audit_record(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            deletion_type=deletion_type,
            deletion_method=deletion_method,
            deleted_by=deleted_by,
            deletion_reason=deletion_reason,
            data_deleted=data_deleted or {},
            deletion_impact=deletion_impact or {},
            cleanup_summary=cleanup_summary or {},
            deletion_duration_ms=deletion_duration_ms,
        )
        return audit_record

    except ImportError as e:
        logger.warning(
            f"⚠️  FlowDeletionAudit model not available: {e}. "
            f"Skipping audit record creation for flow {flow_id}"
        )
        return None
    except Exception as e:
        logger.error(f"❌ Error creating audit data for flow {flow_id}: {e}")
        return None


async def check_audit_table_exists(db: AsyncSession) -> bool:
    """
    Check if the flow_deletion_audit table exists in the database.

    Returns:
        True if table exists, False otherwise
    """
    try:
        from sqlalchemy import text

        result = await db.execute(
            text(
                """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'flow_deletion_audit'
            )
        """
            )
        )
        return bool(result.scalar())

    except Exception as e:
        logger.warning(f"Could not check if flow_deletion_audit table exists: {e}")
        return False
