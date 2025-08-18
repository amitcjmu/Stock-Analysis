# API Patterns Implementation Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform implements a comprehensive FastAPI-based REST API following enterprise patterns including handler/service/repository layers, async operations, multi-tenant authentication, and modular routing architecture.

## API Architecture Layers

### Seven-Layer API Architecture

The platform follows a seven-layer architecture for enterprise resilience:

```
1. Router Layer     → FastAPI route definitions and parameter validation
2. Handler Layer    → Request processing and response formatting  
3. Service Layer    → Business logic and orchestration
4. Repository Layer → Data access and persistence
5. Model Layer      → SQLAlchemy models and Pydantic schemas
6. Cache Layer      → Redis caching and optimization
7. Integration Layer → External service integration
```

## Core API Patterns

### 1. Router Structure and Modularization

**Main Router Pattern:**
```python
# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import (
    assets,
    asset_inventory,
    assessments,
    auth,
    flow_management,
    unified_discovery
)

api_router = APIRouter()

# Include all endpoint routers with proper prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(asset_inventory.router, prefix="/asset-inventory", tags=["asset-inventory"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(flow_management.router, prefix="/flows", tags=["flow-management"])
api_router.include_router(unified_discovery.router, prefix="/discovery", tags=["discovery"])
```

**Modular Endpoint Structure:**
```python
# app/api/v1/endpoints/asset_inventory/__init__.py
from fastapi import APIRouter

from .analysis import router as analysis_router
from .audit import router as audit_router
from .crud import router as crud_router
from .intelligence import router as intelligence_router
from .pagination import router as pagination_router

# Create main router that combines all sub-routers
router = APIRouter(tags=["Asset Inventory"])

# Include all sub-routers
router.include_router(intelligence_router)
router.include_router(audit_router)
router.include_router(crud_router)
router.include_router(pagination_router)
router.include_router(analysis_router)
```

### 2. Standard Endpoint Pattern

**Complete CRUD Endpoint Example:**
```python
# app/api/v1/endpoints/asset_inventory/crud.py
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context, get_user_id
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset_schemas import AssetCreate, AssetResponse, AssetUpdate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Asset CRUD"])

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get single asset with tenant isolation."""
    repo = AssetRepository(db, context.client_account_id)
    asset = await repo.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    user_id: str = Depends(get_user_id),
):
    """Create new asset with automatic tenant context."""
    repo = AssetRepository(db, context.client_account_id)
    new_asset = await repo.create_asset(asset, user_id, context.engagement_id)
    return new_asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset: AssetUpdate,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Update existing asset with tenant validation."""
    repo = AssetRepository(db, context.client_account_id)
    updated_asset = await repo.update_asset(
        asset_id, 
        asset.dict(exclude_unset=True)
    )
    if not updated_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return updated_asset

@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Delete asset with tenant validation."""
    repo = AssetRepository(db, context.client_account_id)
    success = await repo.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None
```

### 3. Dependency Injection Pattern

**Standard Dependencies:**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User

# Standard dependency pattern for all endpoints
async def standard_endpoint(
    # Path parameters
    resource_id: str,
    # Query parameters
    include_details: bool = Query(True, description="Include detailed information"),
    # Dependencies
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Standard endpoint with all common dependencies."""
    pass
```

**Custom Dependencies:**
```python
from typing import Optional

async def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
) -> Dict[str, Any]:
    """Reusable pagination parameters."""
    return {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

async def get_filter_params(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    status: Optional[str] = Query(None, description="Filter by status")
) -> Dict[str, Any]:
    """Reusable filter parameters."""
    return {
        "asset_type": asset_type,
        "environment": environment,
        "status": status
    }

# Usage in endpoints
@router.get("/assets")
async def list_assets(
    pagination: Dict[str, Any] = Depends(get_pagination_params),
    filters: Dict[str, Any] = Depends(get_filter_params),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """List assets with pagination and filtering."""
    repo = AssetRepository(db, context.client_account_id)
    return await repo.list_assets(pagination, filters)
```

## Authentication and Authorization

### 1. JWT Authentication Pattern

**Authentication Service:**
```python
# app/services/auth_services/jwt_service.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.config import settings

class JWTService:
    """JWT token management service."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
```

**Authentication Dependencies:**
```python
# app/api/v1/auth/auth_utils.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db=Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify JWT token
        jwt_service = JWTService()
        payload = jwt_service.verify_token(token)
        
        if payload is None:
            raise credentials_exception

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Get user from database
        user_id = UUID(user_id_str)
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.user_associations))
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise credentials_exception

        return user

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### 2. Role-Based Access Control (RBAC)

**Permission Checking:**
```python
from enum import Enum
from typing import List

class Permission(Enum):
    READ_ASSETS = "read:assets"
    WRITE_ASSETS = "write:assets"
    DELETE_ASSETS = "delete:assets"
    ADMIN_ACCESS = "admin:access"
    FLOW_EXECUTE = "flow:execute"
    AGENT_MANAGE = "agent:manage"

class Role(Enum):
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ_ASSETS],
    Role.CONTRIBUTOR: [Permission.READ_ASSETS, Permission.WRITE_ASSETS, Permission.FLOW_EXECUTE],
    Role.ADMIN: [Permission.READ_ASSETS, Permission.WRITE_ASSETS, Permission.DELETE_ASSETS, Permission.FLOW_EXECUTE, Permission.AGENT_MANAGE],
    Role.SUPER_ADMIN: [perm for perm in Permission]  # All permissions
}

def require_permission(required_permission: Permission):
    """Decorator for requiring specific permissions."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = get_user_permissions(current_user)
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}"
            )
        return current_user
    return permission_checker

def get_user_permissions(user: User) -> List[Permission]:
    """Get all permissions for a user based on their roles."""
    permissions = set()
    for association in user.user_associations:
        role = Role(association.role)
        permissions.update(ROLE_PERMISSIONS.get(role, []))
    return list(permissions)

# Usage in endpoints
@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(require_permission(Permission.DELETE_ASSETS)),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Delete asset - requires delete permission."""
    repo = AssetRepository(db, context.client_account_id)
    success = await repo.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset deleted successfully"}
```

## Async Patterns

### 1. Async Service Integration

**Async Service Layer:**
```python
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class AssetIntelligenceService:
    """Service for asset intelligence operations."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def analyze_assets_batch(
        self, 
        asset_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze multiple assets concurrently."""
        
        # Split into batches for concurrent processing
        batch_size = 10
        batches = [asset_ids[i:i + batch_size] for i in range(0, len(asset_ids), batch_size)]
        
        # Process batches concurrently
        tasks = [
            self._analyze_asset_batch(batch) 
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_results = {}
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch analysis failed: {result}")
                continue
            all_results.update(result)
        
        return all_results
    
    async def _analyze_asset_batch(
        self, 
        asset_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze a single batch of assets."""
        
        # Get assets from repository
        repo = AssetRepository(self.db, self.context.client_account_id)
        assets = await repo.get_assets_by_ids(asset_ids)
        
        # Process each asset concurrently
        tasks = [
            self._analyze_single_asset(asset)
            for asset in assets
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        batch_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Asset analysis failed for {assets[i].id}: {result}")
                continue
            batch_results[str(assets[i].id)] = result
        
        return batch_results
    
    async def _analyze_single_asset(self, asset) -> Dict[str, Any]:
        """Analyze a single asset using AI agents."""
        
        # Run CPU-intensive analysis in thread pool
        loop = asyncio.get_event_loop()
        analysis_result = await loop.run_in_executor(
            self.executor,
            self._cpu_intensive_analysis,
            asset
        )
        
        return analysis_result
    
    def _cpu_intensive_analysis(self, asset) -> Dict[str, Any]:
        """CPU-intensive analysis that runs in thread pool."""
        # Simulate analysis work
        return {
            "complexity_score": 85,
            "migration_readiness": "high",
            "dependencies": [],
            "recommendations": []
        }
```

**Async Endpoint Pattern:**
```python
@router.post("/assets/analyze-batch")
async def analyze_assets_batch(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user)
):
    """Analyze multiple assets with async processing."""
    
    try:
        # Validate request
        if len(request.asset_ids) > 100:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 100 assets per batch"
            )
        
        # Start analysis service
        service = AssetIntelligenceService(db, context)
        
        if request.async_processing:
            # Process in background
            task_id = str(uuid.uuid4())
            background_tasks.add_task(
                service.analyze_assets_batch,
                request.asset_ids
            )
            
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Analysis started in background"
            }
        else:
            # Process synchronously
            results = await service.analyze_assets_batch(request.asset_ids)
            
            return {
                "status": "completed",
                "results": results,
                "analyzed_count": len(results)
            }
    
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Please try again."
        )
```

### 2. WebSocket Integration

**Real-time Updates Pattern:**
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {client_id}: {e}")
    
    async def broadcast_to_tenant(
        self, 
        message: str, 
        client_account_id: str,
        engagement_id: str
    ):
        """Broadcast message to all connections for a tenant."""
        tenant_key = f"{client_account_id}:{engagement_id}"
        await self.send_personal_message(message, tenant_key)

manager = ConnectionManager()

@router.websocket("/ws/flow-updates/{client_account_id}/{engagement_id}")
async def websocket_flow_updates(
    websocket: WebSocket,
    client_account_id: str,
    engagement_id: str
):
    """WebSocket endpoint for real-time flow updates."""
    tenant_key = f"{client_account_id}:{engagement_id}"
    await manager.connect(websocket, tenant_key)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_key)
        logger.info(f"WebSocket disconnected for tenant: {tenant_key}")

# Send updates from services
async def notify_flow_update(
    flow_id: str,
    update_data: Dict[str, Any],
    client_account_id: str,
    engagement_id: str
):
    """Send flow update to connected clients."""
    message = {
        "type": "flow_update",
        "flow_id": flow_id,
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_tenant(
        json.dumps(message),
        client_account_id,
        engagement_id
    )
```

## Error Handling

### 1. Structured Error Responses

**Exception Handlers:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

class APIError(Exception):
    """Base API error class."""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class ValidationError(APIError):
    """Validation error."""
    def __init__(self, message: str, field_errors: List[Dict[str, Any]] = None):
        super().__init__(message, 400, {"field_errors": field_errors or []})

class NotFoundError(APIError):
    """Resource not found error."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} not found: {identifier}", 404)

class PermissionError(APIError):
    """Permission denied error."""
    def __init__(self, action: str, resource: str):
        super().__init__(f"Permission denied for {action} on {resource}", 403)

# Global exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation failed",
                "status_code": 422,
                "details": {"field_errors": field_errors},
                "path": str(request.url),
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### 2. Error Context and Logging

**Structured Error Logging:**
```python
import structlog
from app.core.context import get_current_context_optional

logger = structlog.get_logger(__name__)

def log_api_error(
    error: Exception,
    request: Request,
    context: Optional[RequestContext] = None
):
    """Log API errors with context."""
    
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "request_path": str(request.url),
        "request_method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "request_id": getattr(request.state, "request_id", None)
    }
    
    if context:
        error_context.update({
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "user_id": context.user_id
        })
    
    logger.error("API error occurred", **error_context)

# Usage in endpoints
@router.post("/assets/{asset_id}/analyze")
async def analyze_asset(
    asset_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Analyze asset with comprehensive error handling."""
    try:
        repo = AssetRepository(db, context.client_account_id)
        asset = await repo.get_asset_by_id(asset_id)
        
        if not asset:
            raise NotFoundError("Asset", asset_id)
        
        # Perform analysis
        analysis_service = AssetAnalysisService(db, context)
        result = await analysis_service.analyze_asset(asset)
        
        return {"asset_id": asset_id, "analysis": result}
        
    except APIError:
        # Re-raise custom API errors
        raise
    except Exception as e:
        # Log unexpected errors with context
        log_api_error(e, request, context)
        raise APIError("Analysis failed due to internal error", 500)
```

## Request/Response Patterns

### 1. Pydantic Models

**Request/Response Schemas:**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MIGRATING = "migrating"
    DECOMMISSIONED = "decommissioned"

class AssetCreate(BaseModel):
    """Schema for creating new assets."""
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    asset_type: str = Field(..., description="Type of asset")
    environment: str = Field(..., description="Environment (dev, staging, prod)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Asset attributes")
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Asset name cannot be empty')
        return v.strip()
    
    @validator('environment')
    def environment_must_be_valid(cls, v):
        valid_environments = ['dev', 'staging', 'prod', 'test']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v

class AssetUpdate(BaseModel):
    """Schema for updating assets."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[AssetStatus] = None
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class AssetResponse(BaseModel):
    """Schema for asset responses."""
    id: str
    name: str
    asset_type: str
    environment: str
    status: AssetStatus
    attributes: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    client_account_id: str
    engagement_id: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
```

### 2. Response Formatting

**Consistent Response Structure:**
```python
from typing import TypeVar, Generic, Optional
from pydantic.generics import GenericModel

T = TypeVar('T')

class APIResponse(GenericModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginationMetadata(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool

def success_response(
    data: T, 
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> APIResponse[T]:
    """Create success response."""
    return APIResponse(
        success=True,
        data=data,
        message=message,
        metadata=metadata
    )

def error_response(
    message: str,
    errors: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> APIResponse[None]:
    """Create error response."""
    return APIResponse(
        success=False,
        message=message,
        errors=errors or [],
        metadata=metadata
    )

# Usage in endpoints
@router.get("/assets", response_model=APIResponse[List[AssetResponse]])
async def list_assets(
    pagination: Dict[str, Any] = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """List assets with standardized response."""
    repo = AssetRepository(db, context.client_account_id)
    assets, total = await repo.list_assets_paginated(pagination)
    
    # Calculate pagination metadata
    pages = (total + pagination["page_size"] - 1) // pagination["page_size"]
    pagination_meta = PaginationMetadata(
        total=total,
        page=pagination["page"],
        page_size=pagination["page_size"],
        pages=pages,
        has_next=pagination["page"] < pages,
        has_prev=pagination["page"] > 1
    )
    
    return success_response(
        data=assets,
        message=f"Retrieved {len(assets)} assets",
        metadata={"pagination": pagination_meta.dict()}
    )
```

## Performance Optimization

### 1. Caching Patterns

**Response Caching:**
```python
from functools import wraps
import json
import hashlib

def cache_response(ttl: int = 300):
    """Decorator for caching endpoint responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context for cache key
            context = kwargs.get('context')
            if not context:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, context, args, kwargs)
            
            # Try to get from cache
            redis_cache = get_redis_cache()
            cached_result = await redis_cache.get(cache_key)
            
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

def _generate_cache_key(func_name: str, context: RequestContext, args, kwargs) -> str:
    """Generate cache key for function call."""
    key_data = {
        "function": func_name,
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        "args": str(args),
        "kwargs": {k: v for k, v in kwargs.items() if k not in ['db', 'context']}
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return f"api_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

# Usage
@router.get("/assets/{asset_id}/analysis")
@cache_response(ttl=600)  # Cache for 10 minutes
async def get_asset_analysis(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get asset analysis with caching."""
    repo = AssetRepository(db, context.client_account_id)
    analysis = await repo.get_asset_analysis(asset_id)
    return success_response(analysis)
```

### 2. Query Optimization

**Efficient Database Queries:**
```python
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_, or_, func

class OptimizedAssetRepository:
    """Repository with optimized query patterns."""
    
    async def get_assets_with_dependencies(
        self, 
        asset_ids: List[str]
    ) -> List[Asset]:
        """Get assets with their dependencies in single query."""
        
        query = select(Asset).where(
            and_(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id
            )
        ).options(
            selectinload(Asset.dependencies),
            selectinload(Asset.dependent_assets),
            joinedload(Asset.environment_config)
        )
        
        result = await self.db.execute(query)
        return result.unique().scalars().all()
    
    async def get_asset_summary_stats(self) -> Dict[str, Any]:
        """Get asset statistics with efficient aggregation."""
        
        stats_query = select(
            func.count(Asset.id).label('total_assets'),
            func.count(Asset.id).filter(Asset.status == 'active').label('active_assets'),
            func.count(Asset.id).filter(Asset.status == 'migrating').label('migrating_assets'),
            func.count(distinct(Asset.asset_type)).label('asset_types'),
            func.count(distinct(Asset.environment)).label('environments')
        ).where(
            Asset.client_account_id == self.client_account_id
        )
        
        result = await self.db.execute(stats_query)
        row = result.first()
        
        return {
            'total_assets': row.total_assets,
            'active_assets': row.active_assets,
            'migrating_assets': row.migrating_assets,
            'asset_types': row.asset_types,
            'environments': row.environments
        }
```

This comprehensive API patterns guide provides enterprise-grade patterns for building scalable, secure, and maintainable REST APIs in the AI Modernize Migration Platform.