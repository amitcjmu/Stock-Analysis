"""
Audit logging endpoint for frontend-initiated audit events.
Handles terminal state action blocking and modal closure events.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel, Field
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

        logger.info(
            f"✅ Audit log created: {audit_data.action_type} - {audit_data.result} "
            f"(flow_id: {flow_id}, resource: {audit_data.resource_type})"
        )

        return {
            "status": "success",
            "message": "Audit event logged successfully",
            "audit_log_id": str(audit_log.id),
        }

    except Exception as e:
        logger.error(f"❌ Failed to log audit event: {e}", exc_info=True)
        # Don't raise - audit logging should not break the application
        # Return success with warning to prevent frontend errors
        return {
            "status": "warning",
            "message": f"Audit event logged with warnings: {str(e)}",
        }
