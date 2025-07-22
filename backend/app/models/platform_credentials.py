"""
Platform Credentials Models - Secure storage for platform integration credentials
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CredentialStatus(str, PyEnum):
    """Credential status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_ROTATION = "pending_rotation"


class CredentialType(str, PyEnum):
    """Credential type enumeration"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    SERVICE_ACCOUNT = "service_account"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    CUSTOM = "custom"


class VaultProvider(str, PyEnum):
    """Vault provider enumeration"""
    LOCAL = "local"
    AWS_KMS = "aws_kms"
    AZURE_KEYVAULT = "azure_keyvault"
    GCP_KMS = "gcp_kms"
    HASHICORP_VAULT = "hashicorp_vault"


class PlatformCredential(Base):
    """
    Secure storage for platform integration credentials with encryption
    """
    
    __tablename__ = "platform_credentials"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    platform_adapter_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform_adapters.id"), nullable=False, index=True)
    
    # Credential Information
    credential_name = Column(String(255), nullable=False)
    credential_type = Column(
        ENUM(CredentialType, name="credentialtype", create_type=False),
        nullable=False,
        index=True
    )
    
    # Vault Information
    vault_provider = Column(
        ENUM(VaultProvider, name="vaultprovider", create_type=False),
        nullable=False,
        default=VaultProvider.LOCAL
    )
    vault_reference = Column(String(500), nullable=True)  # External vault key/path
    
    # Encrypted Data
    encrypted_data = Column(Text, nullable=False)  # Base64 encoded encrypted data
    encryption_metadata = Column(JSONB, nullable=False, default={})  # IV, algorithm, etc.
    
    # Metadata
    credential_metadata = Column(JSONB, nullable=False, default={})  # Additional info
    
    # Status and Lifecycle
    status = Column(
        ENUM(CredentialStatus, name="credentialstatus", create_type=False),
        nullable=False,
        default=CredentialStatus.ACTIVE,
        index=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_errors = Column(JSONB, nullable=True)
    
    # Audit Fields
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    access_logs = relationship("CredentialAccessLog", back_populates="credential", cascade="all, delete-orphan")
    rotation_history = relationship("CredentialRotationHistory", back_populates="credential", cascade="all, delete-orphan")
    permissions = relationship("CredentialPermission", back_populates="credential", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_account_id', 'platform_adapter_id', 'credential_name', name='_client_platform_credential_uc'),
    )
    
    def __repr__(self):
        return f"<PlatformCredential(name='{self.credential_name}', type='{self.credential_type}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if credential is active and not expired"""
        if self.status != CredentialStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def needs_rotation(self) -> bool:
        """Check if credential needs rotation"""
        if self.status == CredentialStatus.PENDING_ROTATION:
            return True
        # Add custom logic for rotation policies
        return False


class CredentialAccessLog(Base):
    """
    Audit log for credential access events
    """
    
    __tablename__ = "credential_access_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    credential_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    accessed_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Access Information
    access_type = Column(String(50), nullable=False, index=True)  # read, decrypt, validate, etc.
    access_purpose = Column(Text, nullable=True)
    collection_flow_id = Column(PostgresUUID(as_uuid=True), ForeignKey("collection_flows.id", ondelete="SET NULL"), nullable=True)
    
    # Request Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Additional Data
    access_metadata = Column("metadata", JSONB, nullable=False, default={})
    
    # Timestamp
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    credential = relationship("PlatformCredential", back_populates="access_logs")
    
    def __repr__(self):
        return f"<CredentialAccessLog(credential_id='{self.credential_id}', type='{self.access_type}', success={self.success})>"


class CredentialRotationHistory(Base):
    """
    History of credential rotations
    """
    
    __tablename__ = "credential_rotation_history"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    credential_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rotation Information
    rotation_type = Column(String(50), nullable=False, index=True)  # manual, automatic, forced
    old_expires_at = Column(DateTime(timezone=True), nullable=True)
    new_expires_at = Column(DateTime(timezone=True), nullable=True)
    rotation_reason = Column(Text, nullable=True)
    
    # Who performed the rotation
    rotated_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Result
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Additional Data
    rotation_metadata = Column("metadata", JSONB, nullable=False, default={})
    
    # Timestamp
    rotated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    credential = relationship("PlatformCredential", back_populates="rotation_history")
    
    def __repr__(self):
        return f"<CredentialRotationHistory(credential_id='{self.credential_id}', type='{self.rotation_type}', success={self.success})>"


class CredentialPermission(Base):
    """
    Fine-grained permissions for credential access
    """
    
    __tablename__ = "credential_permissions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    credential_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Permission target (user or role)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    role = Column(String(50), nullable=True, index=True)
    
    # Permission details
    permission_type = Column(String(50), nullable=False, index=True)  # read, write, delete, rotate
    granted_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Data
    permission_metadata = Column("metadata", JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    credential = relationship("PlatformCredential", back_populates="permissions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('(user_id IS NOT NULL) OR (role IS NOT NULL)', name='user_or_role'),
    )
    
    def __repr__(self):
        target = f"user={self.user_id}" if self.user_id else f"role={self.role}"
        return f"<CredentialPermission(credential_id='{self.credential_id}', {target}, type='{self.permission_type}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if permission is still active"""
        if self.revoked_at:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True