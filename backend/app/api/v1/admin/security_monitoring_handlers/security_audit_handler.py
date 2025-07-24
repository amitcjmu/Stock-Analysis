"""
Security Monitoring Handler - Platform Admin Security Audit Dashboard
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Import security audit service
try:
    from app.services.security_audit_service import SecurityAuditService

    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    SecurityAuditService = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/security", tags=["security-monitoring"])


# Pydantic models
class SecurityEventResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    actor_user_id: str
    target_user_id: Optional[str]
    description: str
    details: Optional[Dict[str, Any]]
    created_at: str
    is_suspicious: bool
    requires_review: bool


class SecuritySummaryResponse(BaseModel):
    total_events: int
    critical_events: int
    suspicious_events: int
    admin_accesses: int
    role_changes: int
    recent_events: List[SecurityEventResponse]


class PlatformAdminChangesResponse(BaseModel):
    id: str
    actor_user_id: str
    target_user_id: str
    old_role: Optional[str]
    new_role: str
    created_at: str
    ip_address: Optional[str]
    requires_review: bool


# Dependency to verify platform admin access
async def verify_platform_admin_access(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Verify that the current user is a platform administrator."""
    try:
        from app.models.rbac import UserRole
        from sqlalchemy import and_, select

        # Check if user has platform_admin role
        query = select(UserRole).where(
            and_(
                UserRole.user_id == context.user_id,
                UserRole.role_type == "platform_admin",
                UserRole.is_active is True,
            )
        )
        result = await db.execute(query)
        is_platform_admin = result.scalar_one_or_none() is not None

        if not is_platform_admin:
            raise HTTPException(
                status_code=403,
                detail="Platform administrator access required for security monitoring",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying platform admin access: {e}")
        raise HTTPException(status_code=500, detail="Access verification failed")


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    hours: int = Query(24, description="Hours to look back for events"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_platform_admin_access),
):
    """Get recent security events for monitoring."""
    if not AUDIT_AVAILABLE:
        return []

    try:
        audit_service = SecurityAuditService(db)
        events = await audit_service.get_security_events(
            event_type=event_type, hours=hours
        )

        # Filter by severity if specified
        if severity:
            events = [e for e in events if e.get("severity") == severity.upper()]

        return [SecurityEventResponse(**event) for event in events]

    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve security events"
        )


@router.get("/summary", response_model=SecuritySummaryResponse)
async def get_security_summary(
    hours: int = Query(24, description="Hours to look back for summary"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_platform_admin_access),
):
    """Get security summary dashboard data."""
    if not AUDIT_AVAILABLE:
        return SecuritySummaryResponse(
            total_events=0,
            critical_events=0,
            suspicious_events=0,
            admin_accesses=0,
            role_changes=0,
            recent_events=[],
        )

    try:
        audit_service = SecurityAuditService(db)

        # Get all events
        all_events = await audit_service.get_security_events(hours=hours)

        # Calculate summary statistics
        total_events = len(all_events)
        critical_events = len(
            [e for e in all_events if e.get("severity") == "CRITICAL"]
        )
        suspicious_events = len([e for e in all_events if e.get("is_suspicious")])
        admin_accesses = len(
            [e for e in all_events if e.get("event_type") == "ADMIN_ACCESS"]
        )
        role_changes = len(
            [e for e in all_events if e.get("event_type") == "ROLE_CHANGE"]
        )

        # Get recent critical events
        recent_critical = [
            e for e in all_events if e.get("severity") in ["CRITICAL", "WARNING"]
        ][:10]

        return SecuritySummaryResponse(
            total_events=total_events,
            critical_events=critical_events,
            suspicious_events=suspicious_events,
            admin_accesses=admin_accesses,
            role_changes=role_changes,
            recent_events=[SecurityEventResponse(**event) for event in recent_critical],
        )

    except Exception as e:
        logger.error(f"Failed to get security summary: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve security summary"
        )


@router.get("/admin-changes", response_model=List[PlatformAdminChangesResponse])
async def get_platform_admin_changes(
    days: int = Query(30, description="Days to look back for admin role changes"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_platform_admin_access),
):
    """Get all platform admin role changes in the specified period."""
    if not AUDIT_AVAILABLE:
        return []

    try:
        audit_service = SecurityAuditService(db)
        changes = await audit_service.get_platform_admin_changes(days=days)

        return [PlatformAdminChangesResponse(**change) for change in changes]

    except Exception as e:
        logger.error(f"Failed to get platform admin changes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin changes")


@router.get("/user-activity/{user_id}")
async def get_user_security_activity(
    user_id: str,
    hours: int = Query(24, description="Hours to look back for user activity"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_platform_admin_access),
):
    """Get security activity for a specific user."""
    if not AUDIT_AVAILABLE:
        return {
            "events": [],
            "summary": {"total": 0, "admin_accesses": 0, "role_changes": 0},
        }

    try:
        audit_service = SecurityAuditService(db)
        events = await audit_service.get_security_events(user_id=user_id, hours=hours)

        # Calculate user-specific summary
        admin_accesses = len(
            [e for e in events if e.get("event_type") == "ADMIN_ACCESS"]
        )
        role_changes = len([e for e in events if e.get("event_type") == "ROLE_CHANGE"])

        return {
            "user_id": user_id,
            "events": [SecurityEventResponse(**event) for event in events],
            "summary": {
                "total": len(events),
                "admin_accesses": admin_accesses,
                "role_changes": role_changes,
                "has_suspicious_activity": any(e.get("is_suspicious") for e in events),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get user security activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user activity")


@router.get("/health")
async def security_monitoring_health():
    """Health check for security monitoring system."""
    return {
        "status": "healthy",
        "audit_system_available": AUDIT_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "event_logging": AUDIT_AVAILABLE,
            "admin_monitoring": True,
            "role_change_tracking": AUDIT_AVAILABLE,
            "suspicious_activity_detection": AUDIT_AVAILABLE,
        },
    }
