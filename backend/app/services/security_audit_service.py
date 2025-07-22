"""
Security Audit Service - Comprehensive security event tracking and monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.models.security_audit import RoleChangeApproval, SecurityAuditLog
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    SecurityAuditLog = RoleChangeApproval = None

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("security_audit")


class SecurityAuditService:
    """
    Comprehensive security audit and monitoring service.
    Tracks all security-sensitive operations and privilege changes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_available = AUDIT_AVAILABLE
    
    async def log_role_change(self, actor_user_id: str, target_user_id: str, 
                            old_role: str, new_role: str, 
                            ip_address: str = None, user_agent: str = None) -> bool:
        """Log a role change event with security analysis."""
        if not self.is_available:
            audit_logger.warning(f"Role change not audited - models unavailable: {old_role} -> {new_role}")
            return True
        
        try:
            # Create audit log entry
            audit_entry = SecurityAuditLog.create_role_change_event(
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                old_role=old_role,
                new_role=new_role,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(audit_entry)
            await self.db.flush()  # Test if the table exists
            
            # If this is a privilege escalation to platform_admin, require additional logging
            if new_role == "platform_admin":
                audit_logger.critical(
                    f"PLATFORM_ADMIN_GRANTED: Actor {actor_user_id} granted platform_admin to {target_user_id}"
                )
                
                # Check if this is suspicious (multiple admin creations)
                await self._check_suspicious_admin_creation(actor_user_id)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            # Log warning instead of error - audit failure shouldn't block operations
            audit_logger.warning(
                f"Failed to log role change audit (table may not exist): {old_role} -> {new_role} "
                f"for user {target_user_id} by {actor_user_id}. Error: {str(e)}"
            )
            await self.db.rollback()
            # Return True - audit failure shouldn't block the actual operation
            return True
    
    async def log_admin_access(self, user_id: str, endpoint: str, 
                             ip_address: str = None, user_agent: str = None) -> bool:
        """Log admin endpoint access."""
        if not self.is_available:
            return True
        
        try:
            audit_entry = SecurityAuditLog.create_admin_access_event(
                user_id=user_id,
                endpoint=endpoint,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(audit_entry)
            await self.db.commit()
            return True
            
        except Exception as e:
            # Log warning instead of error - audit failure shouldn't block operations
            audit_logger.warning(
                f"Failed to log admin access audit (table may not exist): {endpoint} "
                f"for user {user_id}. Error: {str(e)}"
            )
            await self.db.rollback()
            # Return True - audit failure shouldn't block the actual operation
            return True
    
    async def log_security_violation(self, user_id: str, violation_type: str, 
                                   details: Dict[str, Any] = None,
                                   ip_address: str = None, user_agent: str = None) -> bool:
        """Log security violation events."""
        if not self.is_available:
            audit_logger.critical(f"SECURITY_VIOLATION not audited: {violation_type} by {user_id}")
            return True
        
        try:
            audit_entry = SecurityAuditLog.create_security_violation_event(
                user_id=user_id,
                violation_type=violation_type,
                ip_address=ip_address,
                user_agent=user_agent,
                **(details or {})
            )
            
            self.db.add(audit_entry)
            await self.db.commit()
            
            audit_logger.critical(f"SECURITY_VIOLATION: {violation_type} by {user_id} - {details}")
            return True
            
        except Exception as e:
            # Log warning but still log the critical security violation to file logs
            audit_logger.warning(
                f"Failed to log security violation audit (table may not exist): {violation_type} "
                f"for user {user_id}. Error: {str(e)}"
            )
            # Still log the critical violation to file logs even if DB fails
            audit_logger.critical(f"SECURITY_VIOLATION: {violation_type} by {user_id} - {details}")
            await self.db.rollback()
            # Return True - audit failure shouldn't block the actual operation
            return True
    
    async def _check_suspicious_admin_creation(self, actor_user_id: str) -> None:
        """Check for suspicious patterns in admin role creation."""
        if not self.is_available:
            return
        
        try:
            # Check how many platform_admin roles this user has created in the last 24 hours
            since = datetime.utcnow() - timedelta(hours=24)
            
            query = select(func.count(SecurityAuditLog.id)).where(
                and_(
                    SecurityAuditLog.actor_user_id == actor_user_id,
                    SecurityAuditLog.event_type == "ROLE_CHANGE",
                    SecurityAuditLog.details.op("->>")(text("new_role")) == "platform_admin",
                    SecurityAuditLog.created_at >= since
                )
            )
            
            result = await self.db.execute(query)
            admin_creations_today = result.scalar() or 0
            
            if admin_creations_today > 1:  # More than 1 admin creation in 24h is suspicious
                await self.log_security_violation(
                    user_id=actor_user_id,
                    violation_type="SUSPICIOUS_ADMIN_CREATION_PATTERN",
                    details={
                        "admin_creations_24h": admin_creations_today,
                        "threshold_exceeded": True
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to check suspicious admin creation: {e}")
    
    async def get_security_events(self, user_id: str = None, 
                                event_type: str = None, 
                                hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security events for monitoring."""
        if not self.is_available:
            return []
        
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(SecurityAuditLog).where(
                SecurityAuditLog.created_at >= since
            )
            
            if user_id:
                query = query.where(SecurityAuditLog.actor_user_id == user_id)
            
            if event_type:
                query = query.where(SecurityAuditLog.event_type == event_type)
            
            query = query.order_by(desc(SecurityAuditLog.created_at)).limit(100)
            
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            return [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "actor_user_id": event.actor_user_id,
                    "target_user_id": event.target_user_id,
                    "description": event.description,
                    "details": event.details,
                    "created_at": event.created_at.isoformat(),
                    "is_suspicious": event.is_suspicious,
                    "requires_review": event.requires_review
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []
    
    async def get_platform_admin_changes(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get all platform admin role changes in the specified period."""
        if not self.is_available:
            return []
        
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            query = select(SecurityAuditLog).where(
                and_(
                    SecurityAuditLog.event_type == "ROLE_CHANGE",
                    SecurityAuditLog.details.op("->>")(text("new_role")) == "platform_admin",
                    SecurityAuditLog.created_at >= since
                )
            ).order_by(desc(SecurityAuditLog.created_at))
            
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            return [
                {
                    "id": str(event.id),
                    "actor_user_id": event.actor_user_id,
                    "target_user_id": event.target_user_id,
                    "old_role": event.details.get("old_role"),
                    "new_role": event.details.get("new_role"),
                    "created_at": event.created_at.isoformat(),
                    "ip_address": event.ip_address,
                    "requires_review": event.requires_review
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Failed to get platform admin changes: {e}")
            return [] 