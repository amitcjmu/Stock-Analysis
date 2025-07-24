"""
Credential Lifecycle Management Service
Handles automatic rotation, expiration, and lifecycle policies
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.models.platform_credentials import (
    CredentialRotationHistory,
    CredentialStatus,
    CredentialType,
    PlatformCredential,
)
from app.services.credential_audit_service import AuditEventType, CredentialAuditService
from app.services.credential_service import CredentialService
from app.services.credential_validators import get_credential_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RotationPolicy(str, Enum):
    """Credential rotation policies"""

    FIXED_INTERVAL = "fixed_interval"
    ON_EXPIRY = "on_expiry"
    SECURITY_EVENT = "security_event"
    MANUAL_ONLY = "manual_only"


class LifecyclePolicy:
    """Credential lifecycle policy configuration"""

    def __init__(
        self,
        credential_type: CredentialType,
        rotation_policy: RotationPolicy = RotationPolicy.FIXED_INTERVAL,
        rotation_interval_days: int = 90,
        max_lifetime_days: int = 365,
        expiry_warning_days: int = 30,
        auto_rotate: bool = False,
        auto_disable_on_expiry: bool = True,
        validation_interval_hours: int = 24,
    ):
        self.credential_type = credential_type
        self.rotation_policy = rotation_policy
        self.rotation_interval_days = rotation_interval_days
        self.max_lifetime_days = max_lifetime_days
        self.expiry_warning_days = expiry_warning_days
        self.auto_rotate = auto_rotate
        self.auto_disable_on_expiry = auto_disable_on_expiry
        self.validation_interval_hours = validation_interval_hours


# Default lifecycle policies by credential type
DEFAULT_POLICIES = {
    CredentialType.API_KEY: LifecyclePolicy(
        credential_type=CredentialType.API_KEY,
        rotation_interval_days=90,
        max_lifetime_days=365,
        auto_rotate=False,
    ),
    CredentialType.OAUTH2: LifecyclePolicy(
        credential_type=CredentialType.OAUTH2,
        rotation_interval_days=180,
        max_lifetime_days=730,
        auto_rotate=True,
    ),
    CredentialType.BASIC_AUTH: LifecyclePolicy(
        credential_type=CredentialType.BASIC_AUTH,
        rotation_interval_days=60,
        max_lifetime_days=180,
        auto_rotate=False,
    ),
    CredentialType.SERVICE_ACCOUNT: LifecyclePolicy(
        credential_type=CredentialType.SERVICE_ACCOUNT,
        rotation_interval_days=365,
        max_lifetime_days=1095,
        auto_rotate=False,
    ),
    CredentialType.CERTIFICATE: LifecyclePolicy(
        credential_type=CredentialType.CERTIFICATE,
        rotation_policy=RotationPolicy.ON_EXPIRY,
        expiry_warning_days=60,
        auto_rotate=False,
    ),
    CredentialType.SSH_KEY: LifecyclePolicy(
        credential_type=CredentialType.SSH_KEY,
        rotation_interval_days=180,
        max_lifetime_days=730,
        auto_rotate=False,
    ),
    CredentialType.CUSTOM: LifecyclePolicy(
        credential_type=CredentialType.CUSTOM,
        rotation_policy=RotationPolicy.MANUAL_ONLY,
        auto_rotate=False,
    ),
}


class CredentialLifecycleService:
    """Service for managing credential lifecycle and rotation"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.credential_service = CredentialService(session)
        self.audit_service = CredentialAuditService(session)
        self.policies = DEFAULT_POLICIES.copy()

    async def check_credential_health(
        self, credential_id: uuid.UUID, system_user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Check health status of a credential

        Args:
            credential_id: Credential ID
            system_user_id: System user for operations

        Returns:
            Health status report
        """
        # Get credential
        credential, _ = await self.credential_service.get_credential(
            credential_id, system_user_id, decrypt_data=False
        )

        health_report = {
            "credential_id": str(credential_id),
            "status": credential.status.value,
            "health_score": 100,
            "issues": [],
            "recommendations": [],
        }

        # Check expiration
        if credential.expires_at:
            days_until_expiry = (credential.expires_at - datetime.utcnow()).days

            if days_until_expiry < 0:
                health_report["issues"].append("Credential has expired")
                health_report["health_score"] -= 50
                health_report["recommendations"].append("Rotate credential immediately")
            elif days_until_expiry < 30:
                health_report["issues"].append(
                    f"Credential expires in {days_until_expiry} days"
                )
                health_report["health_score"] -= 20
                health_report["recommendations"].append("Plan credential rotation")

        # Check rotation status
        policy = self.get_policy(credential.credential_type)
        if credential.last_rotated_at:
            days_since_rotation = (datetime.utcnow() - credential.last_rotated_at).days

            if days_since_rotation > policy.rotation_interval_days:
                health_report["issues"].append(
                    f"Credential not rotated for {days_since_rotation} days"
                )
                health_report["health_score"] -= 30
                health_report["recommendations"].append("Rotate credential per policy")
        else:
            # Never rotated
            days_since_creation = (datetime.utcnow() - credential.created_at).days
            if days_since_creation > policy.rotation_interval_days:
                health_report["issues"].append("Credential never rotated")
                health_report["health_score"] -= 30
                health_report["recommendations"].append(
                    "Perform initial credential rotation"
                )

        # Check validation status
        if credential.last_validated_at:
            hours_since_validation = (
                datetime.utcnow() - credential.last_validated_at
            ).total_seconds() / 3600

            if hours_since_validation > policy.validation_interval_hours:
                health_report["issues"].append("Credential validation overdue")
                health_report["health_score"] -= 10
                health_report["recommendations"].append("Validate credential")

        # Check for validation errors
        if credential.validation_errors:
            health_report["issues"].append("Credential has validation errors")
            health_report["health_score"] -= 40
            health_report["recommendations"].append(
                "Fix validation errors or rotate credential"
            )

        # Determine overall health status
        if health_report["health_score"] >= 80:
            health_report["health_status"] = "HEALTHY"
        elif health_report["health_score"] >= 60:
            health_report["health_status"] = "WARNING"
        elif health_report["health_score"] >= 40:
            health_report["health_status"] = "CRITICAL"
        else:
            health_report["health_status"] = "FAILED"

        return health_report

    async def process_lifecycle_policies(
        self, system_user_id: uuid.UUID, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Process lifecycle policies for all credentials

        Args:
            system_user_id: System user for operations
            dry_run: If True, only report what would be done

        Returns:
            Processing report
        """
        report = {
            "processed": 0,
            "rotations_needed": 0,
            "rotations_performed": 0,
            "expirations_handled": 0,
            "validations_performed": 0,
            "errors": [],
        }

        # Get all active credentials
        result = await self.session.execute(
            select(PlatformCredential).where(
                PlatformCredential.status == CredentialStatus.ACTIVE
            )
        )
        credentials = result.scalars().all()

        for credential in credentials:
            report["processed"] += 1

            try:
                # Check if rotation needed
                if await self._needs_rotation(credential):
                    report["rotations_needed"] += 1

                    if (
                        not dry_run
                        and self.get_policy(credential.credential_type).auto_rotate
                    ):
                        success = await self._auto_rotate_credential(
                            credential, system_user_id
                        )
                        if success:
                            report["rotations_performed"] += 1

                # Check expiration
                if await self._is_expiring_soon(credential):
                    if not dry_run:
                        await self._handle_expiring_credential(
                            credential, system_user_id
                        )
                    report["expirations_handled"] += 1

                # Validate if needed
                if await self._needs_validation(credential):
                    if not dry_run:
                        await self._validate_credential(credential, system_user_id)
                    report["validations_performed"] += 1

            except Exception as e:
                logger.error(f"Error processing credential {credential.id}: {e}")
                report["errors"].append(
                    {"credential_id": str(credential.id), "error": str(e)}
                )

        # Log summary
        await self.audit_service.log_credential_event(
            event_type=AuditEventType.CREDENTIAL_VALIDATED,
            user_id=system_user_id,
            severity="INFO",
            description="Lifecycle policy processing completed",
            details=report,
        )

        return report

    async def schedule_rotation(
        self,
        credential_id: uuid.UUID,
        rotation_date: datetime,
        reason: str,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Schedule a credential rotation

        Args:
            credential_id: Credential to rotate
            rotation_date: When to rotate
            reason: Reason for rotation
            user_id: User scheduling rotation

        Returns:
            Scheduling confirmation
        """
        # Get credential
        credential, _ = await self.credential_service.get_credential(
            credential_id, user_id, decrypt_data=False
        )

        # Update status to pending rotation
        credential.status = CredentialStatus.PENDING_ROTATION

        # Store rotation schedule in metadata
        credential.credential_metadata["scheduled_rotation"] = {
            "date": rotation_date.isoformat(),
            "reason": reason,
            "scheduled_by": str(user_id),
            "scheduled_at": datetime.utcnow().isoformat(),
        }

        await self.session.commit()

        # Log event
        await self.audit_service.log_credential_event(
            event_type=AuditEventType.CREDENTIAL_UPDATED,
            user_id=user_id,
            credential_id=credential_id,
            severity="INFO",
            description=f"Rotation scheduled for {rotation_date.date()}",
            details={"reason": reason},
        )

        return {
            "credential_id": str(credential_id),
            "rotation_scheduled": rotation_date.isoformat(),
            "status": "scheduled",
        }

    async def get_rotation_recommendations(
        self, client_account_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get rotation recommendations for credentials

        Args:
            client_account_id: Filter by client account

        Returns:
            List of rotation recommendations
        """
        recommendations = []

        # Build query
        query = select(PlatformCredential).where(
            PlatformCredential.status == CredentialStatus.ACTIVE
        )

        if client_account_id:
            query = query.where(
                PlatformCredential.client_account_id == client_account_id
            )

        result = await self.session.execute(query)
        credentials = result.scalars().all()

        for credential in credentials:
            self.get_policy(credential.credential_type)
            recommendation = None
            priority = "LOW"

            # Check various conditions
            if await self._needs_rotation(credential):
                if (
                    credential.expires_at
                    and credential.expires_at < datetime.utcnow() + timedelta(days=7)
                ):
                    recommendation = "URGENT: Rotate before expiration"
                    priority = "CRITICAL"
                else:
                    recommendation = "Rotate per policy schedule"
                    priority = "HIGH"

            elif await self._is_expiring_soon(credential):
                recommendation = "Plan rotation before expiration"
                priority = "MEDIUM"

            elif credential.validation_errors:
                recommendation = "Rotate due to validation errors"
                priority = "HIGH"

            if recommendation:
                recommendations.append(
                    {
                        "credential_id": str(credential.id),
                        "credential_name": credential.credential_name,
                        "credential_type": credential.credential_type.value,
                        "recommendation": recommendation,
                        "priority": priority,
                        "expires_at": (
                            credential.expires_at.isoformat()
                            if credential.expires_at
                            else None
                        ),
                        "last_rotated": (
                            credential.last_rotated_at.isoformat()
                            if credential.last_rotated_at
                            else None
                        ),
                    }
                )

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return recommendations

    async def generate_lifecycle_report(
        self, client_account_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive lifecycle report

        Args:
            client_account_id: Filter by client account

        Returns:
            Lifecycle report
        """
        # Build base query
        query = select(PlatformCredential)
        if client_account_id:
            query = query.where(
                PlatformCredential.client_account_id == client_account_id
            )

        result = await self.session.execute(query)
        credentials = result.scalars().all()

        # Analyze credentials
        total = len(credentials)
        by_status = {}
        by_type = {}
        expiring_soon = 0
        rotation_overdue = 0
        never_rotated = 0
        validation_errors = 0

        for credential in credentials:
            # Count by status
            status = credential.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            cred_type = credential.credential_type.value
            by_type[cred_type] = by_type.get(cred_type, 0) + 1

            # Check conditions
            if await self._is_expiring_soon(credential):
                expiring_soon += 1

            if await self._needs_rotation(credential):
                rotation_overdue += 1

            if not credential.last_rotated_at:
                never_rotated += 1

            if credential.validation_errors:
                validation_errors += 1

        # Get recent rotation history
        recent_rotations = await self.session.execute(
            select(CredentialRotationHistory)
            .where(
                CredentialRotationHistory.rotated_at
                >= datetime.utcnow() - timedelta(days=30)
            )
            .limit(10)
        )

        recent_rotation_list = [
            {
                "credential_id": str(rotation.credential_id),
                "rotation_type": rotation.rotation_type,
                "success": rotation.success,
                "rotated_at": rotation.rotated_at.isoformat(),
            }
            for rotation in recent_rotations.scalars()
        ]

        return {
            "report_date": datetime.utcnow().isoformat(),
            "client_account_id": str(client_account_id) if client_account_id else None,
            "summary": {
                "total_credentials": total,
                "by_status": by_status,
                "by_type": by_type,
            },
            "health_metrics": {
                "expiring_soon": expiring_soon,
                "rotation_overdue": rotation_overdue,
                "never_rotated": never_rotated,
                "validation_errors": validation_errors,
            },
            "health_score": self._calculate_health_score(
                total, expiring_soon, rotation_overdue, validation_errors
            ),
            "recent_rotations": recent_rotation_list,
            "recommendations": await self.get_rotation_recommendations(
                client_account_id
            ),
        }

    def get_policy(self, credential_type: CredentialType) -> LifecyclePolicy:
        """Get lifecycle policy for credential type"""
        return self.policies.get(
            credential_type, DEFAULT_POLICIES[CredentialType.CUSTOM]
        )

    def update_policy(
        self, credential_type: CredentialType, policy: LifecyclePolicy
    ) -> None:
        """Update lifecycle policy for credential type"""
        self.policies[credential_type] = policy

    async def _needs_rotation(self, credential: PlatformCredential) -> bool:
        """Check if credential needs rotation"""
        policy = self.get_policy(credential.credential_type)

        if policy.rotation_policy == RotationPolicy.MANUAL_ONLY:
            return False

        if policy.rotation_policy == RotationPolicy.ON_EXPIRY:
            if credential.expires_at:
                return credential.expires_at <= datetime.utcnow() + timedelta(
                    days=policy.expiry_warning_days
                )
            return False

        # Fixed interval policy
        if credential.last_rotated_at:
            days_since_rotation = (datetime.utcnow() - credential.last_rotated_at).days
        else:
            days_since_rotation = (datetime.utcnow() - credential.created_at).days

        return days_since_rotation >= policy.rotation_interval_days

    async def _is_expiring_soon(self, credential: PlatformCredential) -> bool:
        """Check if credential is expiring soon"""
        if not credential.expires_at:
            return False

        policy = self.get_policy(credential.credential_type)
        warning_date = datetime.utcnow() + timedelta(days=policy.expiry_warning_days)

        return credential.expires_at <= warning_date

    async def _needs_validation(self, credential: PlatformCredential) -> bool:
        """Check if credential needs validation"""
        policy = self.get_policy(credential.credential_type)

        if not credential.last_validated_at:
            return True

        hours_since_validation = (
            datetime.utcnow() - credential.last_validated_at
        ).total_seconds() / 3600
        return hours_since_validation >= policy.validation_interval_hours

    async def _auto_rotate_credential(
        self, credential: PlatformCredential, system_user_id: uuid.UUID
    ) -> bool:
        """Automatically rotate a credential"""
        try:
            # This would integrate with the platform adapter to generate new credentials
            # For now, we'll mark it as needing manual rotation
            credential.status = CredentialStatus.PENDING_ROTATION

            await self.audit_service.log_credential_event(
                event_type=AuditEventType.CREDENTIAL_ROTATED,
                user_id=system_user_id,
                credential_id=credential.id,
                severity="INFO",
                description="Auto-rotation triggered",
                details={"auto_rotate": True},
            )

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to auto-rotate credential {credential.id}: {e}")
            return False

    async def _handle_expiring_credential(
        self, credential: PlatformCredential, system_user_id: uuid.UUID
    ) -> None:
        """Handle an expiring credential"""
        policy = self.get_policy(credential.credential_type)

        if credential.expires_at and credential.expires_at <= datetime.utcnow():
            # Already expired
            if policy.auto_disable_on_expiry:
                credential.status = CredentialStatus.EXPIRED

                await self.audit_service.log_credential_event(
                    event_type=AuditEventType.CREDENTIAL_EXPIRED,
                    user_id=system_user_id,
                    credential_id=credential.id,
                    severity="WARNING",
                    description="Credential expired and disabled",
                )
        else:
            # Expiring soon - mark for rotation
            credential.status = CredentialStatus.PENDING_ROTATION

        await self.session.commit()

    async def _validate_credential(
        self, credential: PlatformCredential, system_user_id: uuid.UUID
    ) -> None:
        """Validate a credential"""
        try:
            # Get appropriate validator
            validator = get_credential_validator(credential.credential_type.value)

            # Decrypt and validate
            _, decrypted_data = await self.credential_service.get_credential(
                credential.id, system_user_id, decrypt_data=True, purpose="validation"
            )

            is_valid, error_message = await validator.validate(decrypted_data)

            # Update validation status
            credential.last_validated_at = datetime.utcnow()
            credential.validation_errors = (
                {"error": error_message} if not is_valid else None
            )

            await self.session.commit()

        except Exception as e:
            logger.error(f"Failed to validate credential {credential.id}: {e}")

    def _calculate_health_score(
        self, total: int, expiring: int, overdue: int, errors: int
    ) -> int:
        """Calculate overall health score"""
        if total == 0:
            return 100

        score = 100
        score -= (expiring / total) * 20
        score -= (overdue / total) * 30
        score -= (errors / total) * 40

        return max(0, int(score))
