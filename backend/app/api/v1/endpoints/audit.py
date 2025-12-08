"""
Audit logging endpoint for frontend-initiated audit events.
Handles terminal state action blocking and modal closure events.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import get_db
from app.core.dependencies import get_current_context_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit")


class AuditLogRequest(BaseModel):
    """Request model for audit log entries."""

    action_type: str = Field(..., description="Type of action being logged")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    result: str = Field(
        ..., description="Result of the action (blocked, denied, closed)"
    )
    reason: str = Field(..., description="Human-readable reason for the outcome")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context details"
    )


@router.post("/log")
async def log_audit_event(
    request: Request,
    audit_data: AuditLogRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Log an audit event from the frontend.

    Used for tracking terminal state action blocking and modal closure events
    for troubleshooting and compliance requirements.
    """
    try:
        from app.models.rbac.audit_models import AccessAuditLog

        # Validate user_id is present (required for audit trail)
        if not context.user_id:
            logger.error(
                "Audit log creation failed: user_id is required but missing from context",
                extra={
                    "action_type": audit_data.action_type,
                    "resource_type": audit_data.resource_type,
                    "ip_address": (
                        context.ip_address or request.client.host
                        if request.client
                        else None
                    ),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "AUDIT_AUTHENTICATION_ERROR",
                    "message": "User authentication required for audit logging",
                    "details": (
                        "User context is required to create an audit log entry. "
                        "Please ensure you are authenticated."
                    ),
                },
            )

        # Extract flow_id from details if present
        flow_id = audit_data.details.get("flow_id") if audit_data.details else None

        # Extract client_account_id with proper fallback to context
        # Use context value if key is missing, None, or empty string
        client_account_id = (audit_data.details or {}).get(
            "client_account_id"
        ) or context.client_account_id

        # Extract engagement_id with proper fallback to context
        # Use context value if key is missing, None, or empty string
        engagement_id = (audit_data.details or {}).get(
            "engagement_id"
        ) or context.engagement_id

        # Create audit log entry
        audit_log = AccessAuditLog(
            user_id=context.user_id,
            action_type=audit_data.action_type,
            resource_type=audit_data.resource_type,
            resource_id=audit_data.resource_id or flow_id or "unknown",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            result=audit_data.result,
            reason=audit_data.reason,
            details=audit_data.details or {},
            ip_address=(
                context.ip_address or request.client.host if request.client else None
            ),
            user_agent=context.user_agent or request.headers.get("user-agent"),
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        # Use structured logging to prevent log injection
        logger.info(
            "Audit log created successfully",
            extra={
                "action_type": audit_data.action_type,
                "result": audit_data.result,
                "flow_id": flow_id,
                "resource_type": audit_data.resource_type,
                "resource_id": audit_data.resource_id,
                "audit_log_id": str(audit_log.id),
                "user_id": str(context.user_id) if context.user_id else None,
            },
        )

        return {
            "status": "success",
            "message": "Audit event logged successfully",
            "audit_log_id": str(audit_log.id),
        }

    except ValidationError as e:
        # Validation errors (e.g., invalid data format)
        logger.error(
            "Audit log validation error",
            exc_info=True,
            extra={
                "action_type": audit_data.action_type if audit_data else None,
                "resource_type": audit_data.resource_type if audit_data else None,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "AUDIT_VALIDATION_ERROR",
                "message": "Invalid audit log data",
                "details": str(e),
            },
        )
    except SQLAlchemyError as e:
        # Database errors (connection, constraint violations, etc.)
        logger.error(
            "Audit log database error",
            exc_info=True,
            extra={
                "action_type": audit_data.action_type if audit_data else None,
                "resource_type": audit_data.resource_type if audit_data else None,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        # Rollback the transaction
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "AUDIT_DATABASE_ERROR",
                "message": "Failed to persist audit log to database",
                "details": "Database operation failed. Please try again or contact support if the issue persists.",
            },
        )
    except Exception as e:
        # Other unexpected errors
        logger.error(
            "Failed to log audit event",
            exc_info=True,
            extra={
                "action_type": audit_data.action_type if audit_data else None,
                "resource_type": audit_data.resource_type if audit_data else None,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        # Rollback the transaction if it's still active
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "AUDIT_LOG_ERROR",
                "message": "Failed to log audit event",
                "details": "An unexpected error occurred while logging the audit event.",
            },
        )
