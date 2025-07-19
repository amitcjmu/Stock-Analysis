"""
Platform Credential Service
Handles secure storage, retrieval, and management of platform credentials
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import logging

from app.models.platform_credentials import (
    PlatformCredential, 
    CredentialAccessLog, 
    CredentialRotationHistory,
    CredentialPermission,
    CredentialStatus,
    CredentialType,
    VaultProvider
)
from app.models.security_audit import SecurityAuditLog
from app.utils.encryption_utils import encrypt_credential, decrypt_credential, generate_secure_token
from app.utils.security_utils import InputSanitizer
from app.core.exceptions import NotFoundException, ValidationException, PermissionDeniedException

logger = logging.getLogger(__name__)


class CredentialService:
    """Service for managing platform credentials securely"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_credential(
        self,
        client_account_id: uuid.UUID,
        platform_adapter_id: uuid.UUID,
        credential_name: str,
        credential_type: CredentialType,
        credential_data: Dict[str, Any],
        user_id: uuid.UUID,
        expires_at: Optional[datetime] = None,
        vault_provider: VaultProvider = VaultProvider.LOCAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformCredential:
        """
        Create a new platform credential with encryption
        
        Args:
            client_account_id: Client account ID
            platform_adapter_id: Platform adapter ID
            credential_name: Name of the credential
            credential_type: Type of credential
            credential_data: Credential data to encrypt
            user_id: User creating the credential
            expires_at: Optional expiration date
            vault_provider: Vault provider to use
            metadata: Additional metadata
            
        Returns:
            Created credential
        """
        try:
            # Sanitize inputs
            credential_name = InputSanitizer.sanitize_string(credential_name)
            
            # Validate credential data based on type
            self._validate_credential_data(credential_type, credential_data)
            
            # Encrypt the credential data
            encrypted_data, encryption_metadata = encrypt_credential(
                credential_data, 
                credential_type.value
            )
            
            # Create credential record
            credential = PlatformCredential(
                client_account_id=client_account_id,
                platform_adapter_id=platform_adapter_id,
                credential_name=credential_name,
                credential_type=credential_type,
                vault_provider=vault_provider,
                encrypted_data=encrypted_data,
                encryption_metadata=encryption_metadata,
                credential_metadata=metadata or {},
                expires_at=expires_at,
                created_by=user_id,
                status=CredentialStatus.ACTIVE
            )
            
            self.session.add(credential)
            
            # Create audit log
            audit_log = SecurityAuditLog.create_admin_access_event(
                user_id=str(user_id),
                endpoint="credential_create",
                details={
                    "credential_id": str(credential.id),
                    "credential_type": credential_type.value,
                    "client_account_id": str(client_account_id),
                    "platform_adapter_id": str(platform_adapter_id)
                }
            )
            self.session.add(audit_log)
            
            await self.session.commit()
            await self.session.refresh(credential)
            
            logger.info(f"Created credential {credential.id} for client {client_account_id}")
            return credential
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create credential: {e}")
            raise
    
    async def get_credential(
        self,
        credential_id: uuid.UUID,
        user_id: uuid.UUID,
        decrypt_data: bool = False,
        purpose: Optional[str] = None
    ) -> Tuple[PlatformCredential, Optional[Dict[str, Any]]]:
        """
        Get a credential by ID with optional decryption
        
        Args:
            credential_id: Credential ID
            user_id: User accessing the credential
            decrypt_data: Whether to decrypt the credential data
            purpose: Purpose of access
            
        Returns:
            Tuple of (credential, decrypted_data)
        """
        # Get credential
        result = await self.session.execute(
            select(PlatformCredential)
            .where(PlatformCredential.id == credential_id)
            .options(selectinload(PlatformCredential.permissions))
        )
        credential = result.scalar_one_or_none()
        
        if not credential:
            raise NotFoundException(f"Credential {credential_id} not found")
        
        # Check permissions
        if not await self._check_permission(credential, user_id, "read"):
            raise PermissionDeniedException("No permission to access this credential")
        
        decrypted_data = None
        
        # Log access
        access_log = CredentialAccessLog(
            credential_id=credential_id,
            accessed_by=user_id,
            access_type="read" if not decrypt_data else "decrypt",
            access_purpose=purpose,
            success=True
        )
        self.session.add(access_log)
        
        # Decrypt if requested
        if decrypt_data:
            try:
                decrypted_data = decrypt_credential(
                    credential.encrypted_data,
                    credential.encryption_metadata,
                    credential.credential_type.value
                )
            except Exception as e:
                access_log.success = False
                access_log.error_message = str(e)
                logger.error(f"Failed to decrypt credential {credential_id}: {e}")
                raise ValidationException("Failed to decrypt credential")
        
        await self.session.commit()
        
        return credential, decrypted_data
    
    async def update_credential(
        self,
        credential_id: uuid.UUID,
        user_id: uuid.UUID,
        credential_data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformCredential:
        """
        Update a credential
        
        Args:
            credential_id: Credential ID
            user_id: User updating the credential
            credential_data: New credential data (will be encrypted)
            expires_at: New expiration date
            metadata: New metadata
            
        Returns:
            Updated credential
        """
        # Get credential
        credential, _ = await self.get_credential(credential_id, user_id)
        
        # Check write permission
        if not await self._check_permission(credential, user_id, "write"):
            raise PermissionDeniedException("No permission to update this credential")
        
        # Update credential data if provided
        if credential_data:
            # Validate new data
            self._validate_credential_data(credential.credential_type, credential_data)
            
            # Encrypt new data
            encrypted_data, encryption_metadata = encrypt_credential(
                credential_data,
                credential.credential_type.value
            )
            
            credential.encrypted_data = encrypted_data
            credential.encryption_metadata = encryption_metadata
            credential.last_rotated_at = datetime.utcnow()
        
        # Update other fields
        if expires_at is not None:
            credential.expires_at = expires_at
        
        if metadata is not None:
            credential.credential_metadata = metadata
        
        credential.updated_by = user_id
        credential.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = SecurityAuditLog.create_admin_access_event(
            user_id=str(user_id),
            endpoint="credential_update",
            details={
                "credential_id": str(credential_id),
                "updated_fields": {
                    "data": credential_data is not None,
                    "expires_at": expires_at is not None,
                    "metadata": metadata is not None
                }
            }
        )
        self.session.add(audit_log)
        
        await self.session.commit()
        await self.session.refresh(credential)
        
        return credential
    
    async def validate_credential(
        self,
        credential_id: uuid.UUID,
        user_id: uuid.UUID,
        platform_adapter: Any
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a credential against its platform
        
        Args:
            credential_id: Credential ID
            user_id: User validating the credential
            platform_adapter: Platform adapter instance
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        # Get and decrypt credential
        credential, decrypted_data = await self.get_credential(
            credential_id, 
            user_id, 
            decrypt_data=True,
            purpose="validation"
        )
        
        # Check if credential is expired
        if credential.expires_at and credential.expires_at < datetime.utcnow():
            validation_errors = {"expired": "Credential has expired"}
            is_valid = False
        else:
            # Validate with platform adapter
            try:
                is_valid = await platform_adapter.validate_credential(
                    credential.credential_type.value,
                    decrypted_data
                )
                validation_errors = None if is_valid else {"invalid": "Credential validation failed"}
            except Exception as e:
                is_valid = False
                validation_errors = {"error": str(e)}
        
        # Update validation status
        credential.last_validated_at = datetime.utcnow()
        credential.validation_errors = validation_errors
        
        if not is_valid and credential.status == CredentialStatus.ACTIVE:
            credential.status = CredentialStatus.EXPIRED if "expired" in (validation_errors or {}) else CredentialStatus.REVOKED
        
        await self.session.commit()
        
        return is_valid, validation_errors
    
    async def rotate_credential(
        self,
        credential_id: uuid.UUID,
        user_id: uuid.UUID,
        new_credential_data: Dict[str, Any],
        rotation_reason: str,
        new_expires_at: Optional[datetime] = None
    ) -> PlatformCredential:
        """
        Rotate a credential
        
        Args:
            credential_id: Credential ID
            user_id: User rotating the credential
            new_credential_data: New credential data
            rotation_reason: Reason for rotation
            new_expires_at: New expiration date
            
        Returns:
            Rotated credential
        """
        # Get credential
        credential, _ = await self.get_credential(credential_id, user_id)
        
        # Check rotate permission
        if not await self._check_permission(credential, user_id, "rotate"):
            raise PermissionDeniedException("No permission to rotate this credential")
        
        # Store old expiration
        old_expires_at = credential.expires_at
        
        try:
            # Update credential
            credential = await self.update_credential(
                credential_id,
                user_id,
                credential_data=new_credential_data,
                expires_at=new_expires_at
            )
            
            # Create rotation history
            rotation_history = CredentialRotationHistory(
                credential_id=credential_id,
                rotation_type="manual",
                old_expires_at=old_expires_at,
                new_expires_at=new_expires_at,
                rotation_reason=rotation_reason,
                rotated_by=user_id,
                success=True
            )
            self.session.add(rotation_history)
            
            # Update status
            credential.status = CredentialStatus.ACTIVE
            credential.last_rotated_at = datetime.utcnow()
            
            await self.session.commit()
            
            logger.info(f"Successfully rotated credential {credential_id}")
            return credential
            
        except Exception as e:
            # Log failed rotation
            rotation_history = CredentialRotationHistory(
                credential_id=credential_id,
                rotation_type="manual",
                rotation_reason=rotation_reason,
                rotated_by=user_id,
                success=False,
                error_message=str(e)
            )
            self.session.add(rotation_history)
            await self.session.commit()
            
            logger.error(f"Failed to rotate credential {credential_id}: {e}")
            raise
    
    async def delete_credential(
        self,
        credential_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """
        Delete a credential (soft delete by revoking)
        
        Args:
            credential_id: Credential ID
            user_id: User deleting the credential
        """
        # Get credential
        credential, _ = await self.get_credential(credential_id, user_id)
        
        # Check delete permission
        if not await self._check_permission(credential, user_id, "delete"):
            raise PermissionDeniedException("No permission to delete this credential")
        
        # Revoke credential
        credential.status = CredentialStatus.REVOKED
        credential.updated_by = user_id
        credential.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = SecurityAuditLog.create_admin_access_event(
            user_id=str(user_id),
            endpoint="credential_delete",
            details={
                "credential_id": str(credential_id)
            }
        )
        self.session.add(audit_log)
        
        await self.session.commit()
        
        logger.info(f"Revoked credential {credential_id}")
    
    async def grant_permission(
        self,
        credential_id: uuid.UUID,
        granting_user_id: uuid.UUID,
        target_user_id: Optional[uuid.UUID] = None,
        target_role: Optional[str] = None,
        permission_type: str = "read",
        expires_at: Optional[datetime] = None
    ) -> CredentialPermission:
        """
        Grant permission to access a credential
        
        Args:
            credential_id: Credential ID
            granting_user_id: User granting permission
            target_user_id: User to grant permission to
            target_role: Role to grant permission to
            permission_type: Type of permission
            expires_at: Permission expiration
            
        Returns:
            Created permission
        """
        if not target_user_id and not target_role:
            raise ValidationException("Either user_id or role must be specified")
        
        # Check if granting user has permission to grant
        credential, _ = await self.get_credential(credential_id, granting_user_id)
        
        # Create permission
        permission = CredentialPermission(
            credential_id=credential_id,
            user_id=target_user_id,
            role=target_role,
            permission_type=permission_type,
            granted_by=granting_user_id,
            expires_at=expires_at
        )
        
        self.session.add(permission)
        
        # Create audit log
        target = f"user {target_user_id}" if target_user_id else f"role {target_role}"
        audit_log = SecurityAuditLog.create_admin_access_event(
            user_id=str(granting_user_id),
            endpoint="credential_grant_permission",
            details={
                "credential_id": str(credential_id),
                "target": target,
                "permission_type": permission_type
            }
        )
        self.session.add(audit_log)
        
        await self.session.commit()
        await self.session.refresh(permission)
        
        return permission
    
    async def revoke_permission(
        self,
        permission_id: uuid.UUID,
        revoking_user_id: uuid.UUID
    ) -> None:
        """
        Revoke a credential permission
        
        Args:
            permission_id: Permission ID
            revoking_user_id: User revoking permission
        """
        # Get permission
        result = await self.session.execute(
            select(CredentialPermission)
            .where(CredentialPermission.id == permission_id)
            .options(selectinload(CredentialPermission.credential))
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise NotFoundException(f"Permission {permission_id} not found")
        
        # Revoke permission
        permission.revoked_at = datetime.utcnow()
        permission.revoked_by = revoking_user_id
        
        await self.session.commit()
        
        logger.info(f"Revoked permission {permission_id}")
    
    async def list_credentials(
        self,
        user_id: uuid.UUID,
        client_account_id: Optional[uuid.UUID] = None,
        platform_adapter_id: Optional[uuid.UUID] = None,
        status: Optional[CredentialStatus] = None,
        include_expired: bool = False
    ) -> List[PlatformCredential]:
        """
        List credentials accessible to a user
        
        Args:
            user_id: User requesting credentials
            client_account_id: Filter by client account
            platform_adapter_id: Filter by platform adapter
            status: Filter by status
            include_expired: Include expired credentials
            
        Returns:
            List of accessible credentials
        """
        query = select(PlatformCredential).options(
            selectinload(PlatformCredential.permissions)
        )
        
        # Apply filters
        if client_account_id:
            query = query.where(PlatformCredential.client_account_id == client_account_id)
        
        if platform_adapter_id:
            query = query.where(PlatformCredential.platform_adapter_id == platform_adapter_id)
        
        if status:
            query = query.where(PlatformCredential.status == status)
        
        if not include_expired:
            query = query.where(
                or_(
                    PlatformCredential.expires_at.is_(None),
                    PlatformCredential.expires_at > datetime.utcnow()
                )
            )
        
        result = await self.session.execute(query)
        credentials = result.scalars().all()
        
        # Filter by permissions
        accessible_credentials = []
        for credential in credentials:
            if await self._check_permission(credential, user_id, "read"):
                accessible_credentials.append(credential)
        
        return accessible_credentials
    
    async def get_expiring_credentials(
        self,
        days_before_expiry: int = 30
    ) -> List[PlatformCredential]:
        """
        Get credentials expiring soon
        
        Args:
            days_before_expiry: Days before expiry to check
            
        Returns:
            List of expiring credentials
        """
        expiry_date = datetime.utcnow() + timedelta(days=days_before_expiry)
        
        result = await self.session.execute(
            select(PlatformCredential)
            .where(
                and_(
                    PlatformCredential.expires_at.isnot(None),
                    PlatformCredential.expires_at <= expiry_date,
                    PlatformCredential.status == CredentialStatus.ACTIVE
                )
            )
        )
        
        return result.scalars().all()
    
    async def _check_permission(
        self,
        credential: PlatformCredential,
        user_id: uuid.UUID,
        permission_type: str
    ) -> bool:
        """
        Check if user has permission to access credential
        
        Args:
            credential: Credential to check
            user_id: User ID
            permission_type: Type of permission
            
        Returns:
            True if user has permission
        """
        # Owner always has permission
        if credential.created_by == user_id:
            return True
        
        # Check direct user permissions
        for permission in credential.permissions:
            if (permission.user_id == user_id and 
                permission.permission_type == permission_type and
                permission.is_active):
                return True
        
        # TODO: Check role-based permissions when user roles are available
        
        return False
    
    def _validate_credential_data(
        self,
        credential_type: CredentialType,
        credential_data: Dict[str, Any]
    ) -> None:
        """
        Validate credential data based on type
        
        Args:
            credential_type: Type of credential
            credential_data: Credential data
            
        Raises:
            ValidationException: If data is invalid
        """
        required_fields = {
            CredentialType.API_KEY: ["api_key"],
            CredentialType.BASIC_AUTH: ["username", "password"],
            CredentialType.OAUTH2: ["client_id", "client_secret"],
            CredentialType.SERVICE_ACCOUNT: ["account_data"],
            CredentialType.CERTIFICATE: ["certificate", "private_key"],
            CredentialType.SSH_KEY: ["private_key"],
            CredentialType.CUSTOM: []  # No specific validation
        }
        
        fields = required_fields.get(credential_type, [])
        missing_fields = [f for f in fields if f not in credential_data]
        
        if missing_fields:
            raise ValidationException(
                f"Missing required fields for {credential_type.value}: {', '.join(missing_fields)}"
            )