"""
Pydantic schemas for credential management
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.platform_credentials import (
    CredentialStatus,
    CredentialType,
    VaultProvider,
)


class CredentialBase(BaseModel):
    """Base credential schema"""

    credential_name: str = Field(..., min_length=1, max_length=255)
    credential_type: CredentialType
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CredentialCreate(CredentialBase):
    """Schema for creating credentials"""

    client_account_id: uuid.UUID
    platform_adapter_id: uuid.UUID
    credential_data: Dict[str, Any]
    vault_provider: Optional[VaultProvider] = VaultProvider.LOCAL

    @validator("credential_data")
    def validate_credential_data(cls, v, values):
        if not v:
            raise ValueError("Credential data cannot be empty")
        return v


class CredentialUpdate(BaseModel):
    """Schema for updating credentials"""

    credential_data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CredentialResponse(CredentialBase):
    """Schema for credential responses"""

    id: uuid.UUID
    client_account_id: uuid.UUID
    platform_adapter_id: uuid.UUID
    status: CredentialStatus
    vault_provider: VaultProvider
    last_rotated_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    validation_errors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    decrypted_data: Optional[
        Dict[str, Any]
    ] = None  # Only included when explicitly requested

    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class CredentialListResponse(BaseModel):
    """Schema for credential list responses"""

    credentials: List[CredentialResponse]
    total: int


class CredentialHealthReport(BaseModel):
    """Schema for credential health reports"""

    credential_id: uuid.UUID
    status: str
    health_score: int
    health_status: str
    issues: List[str]
    recommendations: List[str]


class CredentialRotationRequest(BaseModel):
    """Schema for credential rotation requests"""

    new_credential_data: Dict[str, Any]
    reason: str = Field(..., min_length=1)
    new_expires_at: Optional[datetime] = None


class CredentialPermissionRequest(BaseModel):
    """Schema for permission requests"""

    user_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    permission_type: str = Field(..., regex="^(read|write|delete|rotate|grant)$")
    expires_at: Optional[datetime] = None

    @validator("role")
    def validate_user_or_role(cls, v, values):
        if not v and not values.get("user_id"):
            raise ValueError("Either user_id or role must be specified")
        return v


class CredentialValidationResponse(BaseModel):
    """Schema for validation responses"""

    credential_id: uuid.UUID
    is_valid: bool
    error_message: Optional[str] = None
    validated_at: datetime


class CredentialAccessLog(BaseModel):
    """Schema for access log entries"""

    id: uuid.UUID
    credential_id: uuid.UUID
    accessed_by: uuid.UUID
    access_type: str
    access_purpose: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    accessed_at: datetime

    class Config:
        orm_mode = True


class CredentialRotationHistory(BaseModel):
    """Schema for rotation history entries"""

    id: uuid.UUID
    credential_id: uuid.UUID
    rotation_type: str
    old_expires_at: Optional[datetime] = None
    new_expires_at: Optional[datetime] = None
    rotation_reason: Optional[str] = None
    rotated_by: uuid.UUID
    success: bool
    error_message: Optional[str] = None
    rotated_at: datetime

    class Config:
        orm_mode = True


class LifecycleReport(BaseModel):
    """Schema for lifecycle reports"""

    report_date: str
    client_account_id: Optional[str] = None
    summary: Dict[str, Any]
    health_metrics: Dict[str, int]
    health_score: int
    recent_rotations: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class ComplianceReport(BaseModel):
    """Schema for compliance reports"""

    report_period: Dict[str, str]
    client_account_id: Optional[str] = None
    event_summary: Dict[str, int]
    total_events: int
    security_violations: int
    top_users: List[Dict[str, Any]]
    compliance_status: str
    generated_at: str


class SecurityEvent(BaseModel):
    """Schema for security events"""

    event_type: str
    event_category: str
    severity: str
    actor_user_id: str
    description: str
    details: Dict[str, Any]
    is_suspicious: bool
    requires_review: bool
    created_at: datetime

    class Config:
        orm_mode = True
