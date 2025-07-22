"""
Credential Audit Service
Enhanced audit logging for credential-related security events
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_credentials import CredentialAccessLog
from app.models.security_audit import SecurityAuditLog

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of credential audit events"""
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"
    CREDENTIAL_READ = "CREDENTIAL_READ"
    CREDENTIAL_DECRYPTED = "CREDENTIAL_DECRYPTED"
    CREDENTIAL_UPDATED = "CREDENTIAL_UPDATED"
    CREDENTIAL_DELETED = "CREDENTIAL_DELETED"
    CREDENTIAL_ROTATED = "CREDENTIAL_ROTATED"
    CREDENTIAL_VALIDATED = "CREDENTIAL_VALIDATED"
    CREDENTIAL_EXPIRED = "CREDENTIAL_EXPIRED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    ACCESS_DENIED = "ACCESS_DENIED"
    SUSPICIOUS_ACCESS = "SUSPICIOUS_ACCESS"
    BULK_EXPORT = "BULK_EXPORT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class CredentialAuditService:
    """Service for comprehensive credential audit logging"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_credential_event(
        self,
        event_type: AuditEventType,
        user_id: uuid.UUID,
        credential_id: Optional[uuid.UUID] = None,
        client_account_id: Optional[uuid.UUID] = None,
        severity: str = "INFO",
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_suspicious: bool = False
    ) -> SecurityAuditLog:
        """
        Log a credential security event
        
        Args:
            event_type: Type of event
            user_id: User performing action
            credential_id: Affected credential
            client_account_id: Client account
            severity: Event severity
            description: Event description
            details: Additional details
            ip_address: Client IP
            user_agent: Client user agent
            is_suspicious: Mark as suspicious
            
        Returns:
            Created audit log
        """
        # Determine event category
        category_map = {
            AuditEventType.CREDENTIAL_CREATED: "CREDENTIAL_MANAGEMENT",
            AuditEventType.CREDENTIAL_READ: "CREDENTIAL_ACCESS",
            AuditEventType.CREDENTIAL_DECRYPTED: "CREDENTIAL_ACCESS",
            AuditEventType.CREDENTIAL_UPDATED: "CREDENTIAL_MANAGEMENT",
            AuditEventType.CREDENTIAL_DELETED: "CREDENTIAL_MANAGEMENT",
            AuditEventType.CREDENTIAL_ROTATED: "CREDENTIAL_LIFECYCLE",
            AuditEventType.CREDENTIAL_VALIDATED: "CREDENTIAL_VALIDATION",
            AuditEventType.CREDENTIAL_EXPIRED: "CREDENTIAL_LIFECYCLE",
            AuditEventType.PERMISSION_GRANTED: "ACCESS_CONTROL",
            AuditEventType.PERMISSION_REVOKED: "ACCESS_CONTROL",
            AuditEventType.ACCESS_DENIED: "SECURITY_VIOLATION",
            AuditEventType.SUSPICIOUS_ACCESS: "SECURITY_VIOLATION",
            AuditEventType.BULK_EXPORT: "DATA_EXPORT",
            AuditEventType.RATE_LIMIT_EXCEEDED: "SECURITY_VIOLATION"
        }
        
        event_category = category_map.get(event_type, "CREDENTIAL_OPERATION")
        
        # Enhance details with context
        enhanced_details = {
            "credential_id": str(credential_id) if credential_id else None,
            "client_account_id": str(client_account_id) if client_account_id else None,
            "timestamp": datetime.utcnow().isoformat(),
            **(details or {})
        }
        
        # Create audit log
        audit_log = SecurityAuditLog(
            event_type=event_type.value,
            event_category=event_category,
            severity=severity,
            actor_user_id=str(user_id),
            description=description or f"{event_type.value} by user {user_id}",
            details=enhanced_details,
            ip_address=ip_address,
            user_agent=user_agent,
            is_suspicious=is_suspicious,
            requires_review=is_suspicious or severity == "CRITICAL"
        )
        
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        
        # Log suspicious events
        if is_suspicious:
            logger.warning(
                f"SUSPICIOUS CREDENTIAL EVENT: {event_type.value} by user {user_id} "
                f"on credential {credential_id}"
            )
        
        return audit_log
    
    async def detect_suspicious_patterns(
        self,
        user_id: uuid.UUID,
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious access patterns for a user
        
        Args:
            user_id: User to check
            time_window_minutes: Time window to analyze
            
        Returns:
            List of suspicious patterns detected
        """
        suspicious_patterns = []
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Check for rapid credential access
        rapid_access = await self.session.execute(
            select(func.count(CredentialAccessLog.id))
            .where(
                and_(
                    CredentialAccessLog.accessed_by == user_id,
                    CredentialAccessLog.accessed_at >= cutoff_time,
                    CredentialAccessLog.access_type == "decrypt"
                )
            )
        )
        decrypt_count = rapid_access.scalar()
        
        if decrypt_count > 10:  # Threshold for suspicious
            suspicious_patterns.append({
                "pattern": "rapid_decryption",
                "count": decrypt_count,
                "threshold": 10,
                "severity": "HIGH"
            })
        
        # Check for failed access attempts
        failed_access = await self.session.execute(
            select(func.count(CredentialAccessLog.id))
            .where(
                and_(
                    CredentialAccessLog.accessed_by == user_id,
                    CredentialAccessLog.accessed_at >= cutoff_time,
                    CredentialAccessLog.success is False
                )
            )
        )
        failed_count = failed_access.scalar()
        
        if failed_count > 5:  # Threshold for suspicious
            suspicious_patterns.append({
                "pattern": "multiple_failures",
                "count": failed_count,
                "threshold": 5,
                "severity": "MEDIUM"
            })
        
        # Check for access outside normal hours (if applicable)
        # This would require user timezone information
        
        # Check for access to multiple client accounts
        client_access = await self.session.execute(
            select(func.count(func.distinct(SecurityAuditLog.details['client_account_id'])))
            .where(
                and_(
                    SecurityAuditLog.actor_user_id == str(user_id),
                    SecurityAuditLog.created_at >= cutoff_time,
                    SecurityAuditLog.event_category == "CREDENTIAL_ACCESS"
                )
            )
        )
        client_count = client_access.scalar()
        
        if client_count > 3:  # Threshold for suspicious
            suspicious_patterns.append({
                "pattern": "multi_client_access",
                "count": client_count,
                "threshold": 3,
                "severity": "MEDIUM"
            })
        
        # Log patterns if found
        if suspicious_patterns:
            await self.log_credential_event(
                event_type=AuditEventType.SUSPICIOUS_ACCESS,
                user_id=user_id,
                severity="WARNING",
                description=f"Detected {len(suspicious_patterns)} suspicious patterns",
                details={"patterns": suspicious_patterns},
                is_suspicious=True
            )
        
        return suspicious_patterns
    
    async def get_credential_access_history(
        self,
        credential_id: uuid.UUID,
        days: int = 30,
        include_failed: bool = True
    ) -> List[CredentialAccessLog]:
        """
        Get access history for a credential
        
        Args:
            credential_id: Credential ID
            days: Number of days to look back
            include_failed: Include failed attempts
            
        Returns:
            List of access logs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(CredentialAccessLog).where(
            and_(
                CredentialAccessLog.credential_id == credential_id,
                CredentialAccessLog.accessed_at >= cutoff_date
            )
        )
        
        if not include_failed:
            query = query.where(CredentialAccessLog.success is True)
        
        query = query.order_by(desc(CredentialAccessLog.accessed_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_credential_activity(
        self,
        user_id: uuid.UUID,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get credential activity summary for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Activity summary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get access counts by type
        access_stats = await self.session.execute(
            select(
                CredentialAccessLog.access_type,
                func.count(CredentialAccessLog.id).label('count')
            )
            .where(
                and_(
                    CredentialAccessLog.accessed_by == user_id,
                    CredentialAccessLog.accessed_at >= cutoff_date
                )
            )
            .group_by(CredentialAccessLog.access_type)
        )
        
        access_by_type = {row.access_type: row.count for row in access_stats}
        
        # Get security events
        security_events = await self.session.execute(
            select(func.count(SecurityAuditLog.id))
            .where(
                and_(
                    SecurityAuditLog.actor_user_id == str(user_id),
                    SecurityAuditLog.created_at >= cutoff_date,
                    SecurityAuditLog.event_category.in_([
                        "SECURITY_VIOLATION",
                        "UNAUTHORIZED_ACCESS"
                    ])
                )
            )
        )
        
        violation_count = security_events.scalar()
        
        # Check for suspicious patterns
        suspicious_patterns = await self.detect_suspicious_patterns(user_id)
        
        return {
            "user_id": str(user_id),
            "period_days": days,
            "access_summary": access_by_type,
            "total_accesses": sum(access_by_type.values()),
            "security_violations": violation_count,
            "suspicious_patterns": suspicious_patterns,
            "risk_level": self._calculate_risk_level(
                access_by_type,
                violation_count,
                len(suspicious_patterns)
            )
        }
    
    async def generate_compliance_report(
        self,
        client_account_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for credential access
        
        Args:
            client_account_id: Filter by client account
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report data
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build base query
        base_conditions = [
            SecurityAuditLog.created_at >= start_date,
            SecurityAuditLog.created_at <= end_date,
            SecurityAuditLog.event_category.in_([
                "CREDENTIAL_ACCESS",
                "CREDENTIAL_MANAGEMENT",
                "ACCESS_CONTROL",
                "SECURITY_VIOLATION"
            ])
        ]
        
        if client_account_id:
            base_conditions.append(
                SecurityAuditLog.details['client_account_id'].astext == str(client_account_id)
            )
        
        # Get event counts by category
        category_stats = await self.session.execute(
            select(
                SecurityAuditLog.event_category,
                func.count(SecurityAuditLog.id).label('count')
            )
            .where(and_(*base_conditions))
            .group_by(SecurityAuditLog.event_category)
        )
        
        events_by_category = {row.event_category: row.count for row in category_stats}
        
        # Get top users by activity
        user_stats = await self.session.execute(
            select(
                SecurityAuditLog.actor_user_id,
                func.count(SecurityAuditLog.id).label('count')
            )
            .where(and_(*base_conditions))
            .group_by(SecurityAuditLog.actor_user_id)
            .order_by(desc('count'))
            .limit(10)
        )
        
        top_users = [
            {"user_id": row.actor_user_id, "event_count": row.count}
            for row in user_stats
        ]
        
        # Get security violations
        violations = await self.session.execute(
            select(func.count(SecurityAuditLog.id))
            .where(
                and_(
                    *base_conditions,
                    SecurityAuditLog.event_category == "SECURITY_VIOLATION"
                )
            )
        )
        
        violation_count = violations.scalar()
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "client_account_id": str(client_account_id) if client_account_id else None,
            "event_summary": events_by_category,
            "total_events": sum(events_by_category.values()),
            "security_violations": violation_count,
            "top_users": top_users,
            "compliance_status": "PASS" if violation_count == 0 else "REVIEW_REQUIRED",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_risk_level(
        self,
        access_counts: Dict[str, int],
        violations: int,
        suspicious_patterns: int
    ) -> str:
        """
        Calculate risk level based on activity
        
        Args:
            access_counts: Access counts by type
            violations: Number of violations
            suspicious_patterns: Number of suspicious patterns
            
        Returns:
            Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        """
        risk_score = 0
        
        # Weight different factors
        risk_score += violations * 10
        risk_score += suspicious_patterns * 5
        risk_score += access_counts.get("decrypt", 0) * 0.5
        risk_score += access_counts.get("delete", 0) * 2
        
        if risk_score >= 50:
            return "CRITICAL"
        elif risk_score >= 30:
            return "HIGH"
        elif risk_score >= 10:
            return "MEDIUM"
        else:
            return "LOW"