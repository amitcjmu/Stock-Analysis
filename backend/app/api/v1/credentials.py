"""
Credential Management API Endpoints
Provides secure CRUD operations for platform credentials
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.platform_credentials import CredentialStatus, CredentialType, VaultProvider
from app.services.credential_service import CredentialService
from app.services.credential_audit_service import CredentialAuditService, AuditEventType
from app.services.credential_lifecycle_service import CredentialLifecycleService
from app.services.credential_validators import get_credential_validator
from app.middleware.credential_access_control import CredentialAccessControl
from app.schemas.credential_schemas import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialListResponse,
    CredentialHealthReport,
    CredentialRotationRequest,
    CredentialPermissionRequest,
    CredentialValidationResponse,
    LifecycleReport
)

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.post("/", response_model=CredentialResponse)
async def create_credential(
    request: Request,
    credential_data: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new platform credential"""
    # Check client account access
    await CredentialAccessControl.check_client_account_access(
        request,
        credential_data.client_account_id,
        db
    )
    
    service = CredentialService(db)
    audit_service = CredentialAuditService(db)
    
    try:
        # Create credential
        credential = await service.create_credential(
            client_account_id=credential_data.client_account_id,
            platform_adapter_id=credential_data.platform_adapter_id,
            credential_name=credential_data.credential_name,
            credential_type=credential_data.credential_type,
            credential_data=credential_data.credential_data,
            user_id=current_user.id,
            expires_at=credential_data.expires_at,
            vault_provider=credential_data.vault_provider or VaultProvider.LOCAL,
            metadata=credential_data.metadata
        )
        
        # Log success
        await audit_service.log_credential_event(
            event_type=AuditEventType.CREDENTIAL_CREATED,
            user_id=current_user.id,
            credential_id=credential.id,
            client_account_id=credential_data.client_account_id,
            severity="INFO",
            description=f"Created credential {credential.credential_name}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return CredentialResponse.from_orm(credential)
        
    except Exception as e:
        # Log failure
        await audit_service.log_credential_event(
            event_type=AuditEventType.CREDENTIAL_CREATED,
            user_id=current_user.id,
            client_account_id=credential_data.client_account_id,
            severity="ERROR",
            description=f"Failed to create credential: {str(e)}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            is_suspicious=True
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    request: Request,
    credential_id: uuid.UUID,
    decrypt: bool = Query(False, description="Decrypt credential data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a credential by ID"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "decrypt" if decrypt else "read",
        db
    )
    
    service = CredentialService(db)
    
    try:
        credential, decrypted_data = await service.get_credential(
            credential_id,
            current_user.id,
            decrypt_data=decrypt,
            purpose="api_access"
        )
        
        response = CredentialResponse.from_orm(credential)
        if decrypt and decrypted_data:
            response.decrypted_data = decrypted_data
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    request: Request,
    credential_id: uuid.UUID,
    update_data: CredentialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a credential"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "write",
        db
    )
    
    service = CredentialService(db)
    
    try:
        credential = await service.update_credential(
            credential_id,
            current_user.id,
            credential_data=update_data.credential_data,
            expires_at=update_data.expires_at,
            metadata=update_data.metadata
        )
        
        return CredentialResponse.from_orm(credential)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{credential_id}")
async def delete_credential(
    request: Request,
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (revoke) a credential"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "delete",
        db
    )
    
    service = CredentialService(db)
    
    try:
        await service.delete_credential(credential_id, current_user.id)
        return {"status": "success", "message": "Credential revoked"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{credential_id}/validate", response_model=CredentialValidationResponse)
async def validate_credential(
    request: Request,
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a credential"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "read",
        db
    )
    
    service = CredentialService(db)
    
    try:
        # Get credential
        credential, decrypted_data = await service.get_credential(
            credential_id,
            current_user.id,
            decrypt_data=True,
            purpose="validation"
        )
        
        # Get validator
        validator = get_credential_validator(credential.credential_type.value)
        
        # Validate
        is_valid, error_message = await validator.validate(decrypted_data)
        
        # Update validation status
        credential.last_validated_at = datetime.utcnow()
        credential.validation_errors = {"error": error_message} if not is_valid else None
        
        await db.commit()
        
        return CredentialValidationResponse(
            credential_id=credential_id,
            is_valid=is_valid,
            error_message=error_message,
            validated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{credential_id}/rotate", response_model=CredentialResponse)
async def rotate_credential(
    request: Request,
    credential_id: uuid.UUID,
    rotation_data: CredentialRotationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rotate a credential"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "rotate",
        db
    )
    
    service = CredentialService(db)
    
    try:
        credential = await service.rotate_credential(
            credential_id,
            current_user.id,
            new_credential_data=rotation_data.new_credential_data,
            rotation_reason=rotation_data.reason,
            new_expires_at=rotation_data.new_expires_at
        )
        
        return CredentialResponse.from_orm(credential)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=CredentialListResponse)
async def list_credentials(
    request: Request,
    client_account_id: Optional[uuid.UUID] = Query(None),
    platform_adapter_id: Optional[uuid.UUID] = Query(None),
    status: Optional[CredentialStatus] = Query(None),
    include_expired: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List credentials accessible to the user"""
    service = CredentialService(db)
    
    credentials = await service.list_credentials(
        user_id=current_user.id,
        client_account_id=client_account_id,
        platform_adapter_id=platform_adapter_id,
        status=status,
        include_expired=include_expired
    )
    
    return CredentialListResponse(
        credentials=[CredentialResponse.from_orm(c) for c in credentials],
        total=len(credentials)
    )


@router.get("/{credential_id}/health", response_model=CredentialHealthReport)
async def get_credential_health(
    request: Request,
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health status of a credential"""
    # Check access
    await CredentialAccessControl.check_credential_access(
        request,
        credential_id,
        "read",
        db
    )
    
    lifecycle_service = CredentialLifecycleService(db)
    
    health_report = await lifecycle_service.check_credential_health(
        credential_id,
        current_user.id
    )
    
    return CredentialHealthReport(**health_report)


@router.post("/{credential_id}/permissions", response_model=Dict[str, Any])
async def grant_permission(
    request: Request,
    credential_id: uuid.UUID,
    permission_data: CredentialPermissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grant permission to access a credential"""
    # Check if user can grant permissions
    if not CredentialAccessControl.can_grant_permission(
        current_user.role,
        permission_data.permission_type
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to grant this permission"
        )
    
    service = CredentialService(db)
    
    try:
        permission = await service.grant_permission(
            credential_id,
            current_user.id,
            target_user_id=permission_data.user_id,
            target_role=permission_data.role,
            permission_type=permission_data.permission_type,
            expires_at=permission_data.expires_at
        )
        
        return {
            "status": "success",
            "permission_id": str(permission.id),
            "message": "Permission granted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/lifecycle/report", response_model=LifecycleReport)
async def get_lifecycle_report(
    request: Request,
    client_account_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get credential lifecycle report"""
    # Check if user has access to view reports
    if current_user.role not in ["platform_admin", "client_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to view lifecycle reports"
        )
    
    lifecycle_service = CredentialLifecycleService(db)
    
    report = await lifecycle_service.generate_lifecycle_report(client_account_id)
    
    return LifecycleReport(**report)


@router.get("/lifecycle/recommendations", response_model=List[Dict[str, Any]])
async def get_rotation_recommendations(
    request: Request,
    client_account_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get credential rotation recommendations"""
    lifecycle_service = CredentialLifecycleService(db)
    
    recommendations = await lifecycle_service.get_rotation_recommendations(
        client_account_id
    )
    
    return recommendations


@router.post("/lifecycle/process")
async def process_lifecycle_policies(
    request: Request,
    dry_run: bool = Query(True, description="Run without making changes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process lifecycle policies for all credentials"""
    # Only platform admins can run lifecycle processing
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform admins can process lifecycle policies"
        )
    
    lifecycle_service = CredentialLifecycleService(db)
    
    report = await lifecycle_service.process_lifecycle_policies(
        current_user.id,
        dry_run=dry_run
    )
    
    return report