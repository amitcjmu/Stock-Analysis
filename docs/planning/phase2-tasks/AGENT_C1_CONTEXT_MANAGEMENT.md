# Phase 2 - Agent C1: Context Management & Multi-Tenant Infrastructure

## Context
You are part of Phase 2 remediation effort to transform the AI Force Migration Platform to proper CrewAI architecture. This is Track C focusing on implementing a robust context injection framework, enhancing multi-tenant isolation, and ensuring context flows seamlessly through all CrewAI components.

### Required Reading Before Starting
- `docs/planning/PHASE-2-REMEDIATION-PLAN.md` - Phase 2 objectives
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Existing context system
- `backend/app/core/context.py` - Current context implementation
- Python's `contextvars` documentation

### Current Context System
The platform already has a superior multi-tenant context system with:
- Multi-level isolation (Client Account → Engagement → User)
- Advanced middleware with security audit logging
- `ContextAwareRepository` pattern
- Row-level security (RLS) policies

### Phase 2 Goal
Enhance the existing context system to work seamlessly with CrewAI agents, tools, and flows. Implement automatic context injection using Python's `contextvars` to ensure multi-tenant isolation is maintained throughout the new CrewAI architecture.

## Your Specific Tasks

### 1. Enhance Context Framework with ContextVars
**File to update**: `backend/app/core/context.py`

```python
"""
Enhanced context management with automatic injection
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any, TypeVar, Callable
from functools import wraps
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# Context variable for request context
_request_context: ContextVar[Optional['RequestContext']] = ContextVar(
    'request_context',
    default=None
)

@dataclass
class RequestContext:
    """Enhanced request context with audit fields"""
    client_account_id: str
    engagement_id: str
    user_id: str
    request_id: str
    
    # Audit fields
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_version: Optional[str] = None
    
    # Feature flags
    feature_flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if context has permission for resource/action"""
        # TODO: Implement permission checking
        return True

# Context management functions
def set_request_context(context: RequestContext) -> None:
    """Set the current request context"""
    _request_context.set(context)
    logger.debug(f"Set context for client {context.client_account_id}")

def get_current_context() -> Optional[RequestContext]:
    """Get the current request context"""
    return _request_context.get()

def get_required_context() -> RequestContext:
    """Get context or raise if not available"""
    context = get_current_context()
    if not context:
        raise RuntimeError("No request context available")
    return context

def clear_request_context() -> None:
    """Clear the current request context"""
    _request_context.set(None)

# Decorators for context management
T = TypeVar('T')

def require_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures context is available"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_current_context()
        if not context:
            raise RuntimeError(f"Context required for {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def inject_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that injects context as first argument"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_required_context()
        return func(context, *args, **kwargs)
    return wrapper

def with_context(
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    **extra_fields
):
    """Decorator to run function with specific context"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                request_id=f"test-{func.__name__}",
                **extra_fields
            )
            
            # Set context
            token = _request_context.set(context)
            try:
                return await func(*args, **kwargs)
            finally:
                _request_context.reset(token)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                request_id=f"test-{func.__name__}",
                **extra_fields
            )
            
            # Set context
            token = _request_context.set(context)
            try:
                return func(*args, **kwargs)
            finally:
                _request_context.reset(token)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

# Context propagation for async tasks
class ContextTask:
    """Wrapper for asyncio tasks that preserves context"""
    
    @staticmethod
    def create_task(coro, *, name=None):
        """Create task that preserves current context"""
        context = get_current_context()
        
        async def wrapped():
            if context:
                set_request_context(context)
            try:
                return await coro
            finally:
                if context:
                    clear_request_context()
        
        import asyncio
        return asyncio.create_task(wrapped(), name=name)
```

### 2. Create Context-Aware Base Classes
**File to create**: `backend/app/core/context_aware.py`

```python
"""
Base classes for context-aware components
"""

from abc import ABC
from typing import Optional, Any, Dict
from app.core.context import get_required_context, RequestContext, require_context
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import logging

logger = logging.getLogger(__name__)

class ContextAwareService(ABC):
    """Base class for all context-aware services"""
    
    def __init__(self):
        """Initialize without context - context comes from ContextVar"""
        super().__init__()
    
    @property
    def context(self) -> RequestContext:
        """Get current context"""
        return get_required_context()
    
    @property
    def client_account_id(self) -> str:
        """Convenience property for client account ID"""
        return self.context.client_account_id
    
    @property
    def engagement_id(self) -> str:
        """Convenience property for engagement ID"""
        return self.context.engagement_id
    
    @property
    def user_id(self) -> str:
        """Convenience property for user ID"""
        return self.context.user_id
    
    def check_permission(self, resource: str, action: str) -> bool:
        """Check if current context has permission"""
        return self.context.has_permission(resource, action)
    
    def log_with_context(self, level: str, message: str, **extra):
        """Log with context information"""
        extra.update({
            'client_account_id': self.client_account_id,
            'engagement_id': self.engagement_id,
            'user_id': self.user_id,
            'request_id': self.context.request_id
        })
        getattr(logger, level)(message, extra=extra)

class ContextAwareTool(ContextAwareService):
    """Base class for context-aware CrewAI tools"""
    
    def __init__(self, **kwargs):
        """Initialize tool with context awareness"""
        super().__init__()
        # Tool-specific initialization
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @require_context
    def _run(self, *args, **kwargs):
        """Run tool with context validation"""
        self.log_with_context('info', f"Tool {self.__class__.__name__} executing")
        return self.run(*args, **kwargs)
    
    def run(self, *args, **kwargs):
        """Override in subclasses"""
        raise NotImplementedError

class ContextAwareRepository(ABC):
    """Enhanced base repository with automatic context filtering"""
    
    def __init__(self, db: AsyncSession, model_class: Any):
        """Initialize with database session and model"""
        self.db = db
        self.model_class = model_class
        self._context = None
    
    @property
    def context(self) -> RequestContext:
        """Get current context"""
        if not self._context:
            self._context = get_required_context()
        return self._context
    
    def apply_context_filter(self, query):
        """Apply context-based filtering to query"""
        # Apply client account filter
        if hasattr(self.model_class, 'client_account_id'):
            query = query.where(
                self.model_class.client_account_id == self.context.client_account_id
            )
        
        # Apply engagement filter if available
        if hasattr(self.model_class, 'engagement_id') and self.context.engagement_id:
            query = query.where(
                self.model_class.engagement_id == self.context.engagement_id
            )
        
        return query
    
    async def get_by_id(self, id: Any) -> Optional[Any]:
        """Get entity by ID with context filtering"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_all(self, limit: int = 100, offset: int = 0):
        """List all entities with context filtering"""
        query = select(self.model_class).limit(limit).offset(offset)
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def set_context_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set context fields on data before insert/update"""
        if hasattr(self.model_class, 'client_account_id'):
            data['client_account_id'] = self.context.client_account_id
        
        if hasattr(self.model_class, 'engagement_id'):
            data['engagement_id'] = self.context.engagement_id
        
        if hasattr(self.model_class, 'created_by'):
            data['created_by'] = self.context.user_id
        
        return data
```

### 3. Implement Context Middleware Enhancement
**File to update**: `backend/app/core/middleware/context_middleware.py`

```python
"""
Enhanced context middleware for automatic injection
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.context import set_request_context, clear_request_context, RequestContext
from app.core.auth import get_current_user_id
import uuid
import logging

logger = logging.getLogger(__name__)

class ContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically set request context.
    Integrates with ContextVars for automatic propagation.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract context from request
        try:
            # Get authentication info
            user_id = await get_current_user_id(request)
            if not user_id:
                return Response("Unauthorized", status_code=401)
            
            # Extract tenant info from headers or JWT
            client_account_id = request.headers.get('X-Client-Account-ID')
            engagement_id = request.headers.get('X-Engagement-ID')
            
            # Validate required fields
            if not client_account_id:
                return Response("Client Account ID required", status_code=400)
            
            # Create context
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id or client_account_id,  # Default to client if not specified
                user_id=user_id,
                request_id=str(uuid.uuid4()),
                ip_address=request.client.host,
                user_agent=request.headers.get('User-Agent'),
                api_version=request.url.path.split('/')[2] if len(request.url.path.split('/')) > 2 else 'v1'
            )
            
            # Set context for this request
            set_request_context(context)
            
            # Log request with context
            logger.info(
                f"Request {context.request_id}: {request.method} {request.url.path}",
                extra={
                    'client_account_id': context.client_account_id,
                    'user_id': context.user_id,
                    'ip_address': context.ip_address
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Add context headers to response
            response.headers['X-Request-ID'] = context.request_id
            
            return response
            
        except Exception as e:
            logger.error(f"Context middleware error: {e}")
            return Response("Internal error", status_code=500)
        
        finally:
            # Always clear context
            clear_request_context()
```

### 4. Create Database RLS Policies
**File to create**: `backend/migrations/add_row_level_security.py`

```python
"""
Add Row Level Security policies for multi-tenant isolation
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add RLS policies to all tenant-scoped tables"""
    
    # Enable RLS on tables
    tables_with_rls = [
        'data_imports',
        'raw_import_records', 
        'import_field_mappings',
        'assets',
        'applications',
        'dependencies',
        'crewai_flow_state_extensions'
    ]
    
    for table in tables_with_rls:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        
        # Create policy for client account isolation
        op.execute(f"""
            CREATE POLICY {table}_client_isolation ON {table}
            FOR ALL
            TO application_role
            USING (client_account_id = current_setting('app.client_account_id')::uuid)
            WITH CHECK (client_account_id = current_setting('app.client_account_id')::uuid);
        """)
        
        # Create policy for engagement isolation (if applicable)
        if table not in ['clients', 'engagements']:
            op.execute(f"""
                CREATE POLICY {table}_engagement_isolation ON {table}
                FOR ALL
                TO application_role
                USING (
                    engagement_id = current_setting('app.engagement_id', true)::uuid
                    OR current_setting('app.engagement_id', true) IS NULL
                );
            """)
    
    # Create function to set context in database session
    op.execute("""
        CREATE OR REPLACE FUNCTION set_tenant_context(
            p_client_account_id uuid,
            p_engagement_id uuid DEFAULT NULL
        ) RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.client_account_id', p_client_account_id::text, false);
            IF p_engagement_id IS NOT NULL THEN
                PERFORM set_config('app.engagement_id', p_engagement_id::text, false);
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade():
    """Remove RLS policies"""
    tables_with_rls = [
        'data_imports',
        'raw_import_records',
        'import_field_mappings',
        'assets',
        'applications',
        'dependencies',
        'crewai_flow_state_extensions'
    ]
    
    for table in tables_with_rls:
        op.execute(f"DROP POLICY IF EXISTS {table}_client_isolation ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_engagement_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP FUNCTION IF EXISTS set_tenant_context;")
```

### 5. Integrate Context with Database Sessions
**File to create**: `backend/app/core/database_context.py`

```python
"""
Context-aware database session management
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.context import get_current_context
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_context_db():
    """
    Get database session with context automatically set.
    Sets PostgreSQL session variables for RLS.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get current context
            context = get_current_context()
            if context:
                # Set context in PostgreSQL session
                await session.execute(
                    "SELECT set_tenant_context(:client_account_id, :engagement_id)",
                    {
                        "client_account_id": context.client_account_id,
                        "engagement_id": context.engagement_id
                    }
                )
                await session.commit()
                
                logger.debug(
                    f"Set database context for client {context.client_account_id}"
                )
            
            yield session
            
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# FastAPI dependency
async def get_db():
    """FastAPI dependency for context-aware database session"""
    async with get_context_db() as session:
        yield session
```

### 6. Create Context-Aware Tool Examples
**File to create**: `backend/app/services/tools/context_aware_tools.py`

```python
"""
Example context-aware tools for CrewAI agents
"""

from typing import Dict, Any, List
from app.core.context_aware import ContextAwareTool
from app.core.database_context import get_context_db
from sqlalchemy import select
from app.models import Asset, DataImport

class AssetSearchTool(ContextAwareTool):
    """Tool to search assets with automatic context filtering"""
    
    name: str = "asset_search"
    description: str = "Search for assets within the current tenant context"
    
    async def run(self, query: str) -> List[Dict[str, Any]]:
        """Search assets with automatic context filtering"""
        async with get_context_db() as db:
            # Query automatically filtered by RLS
            result = await db.execute(
                select(Asset).where(Asset.name.ilike(f"%{query}%"))
            )
            assets = result.scalars().all()
            
            self.log_with_context(
                'info',
                f"Found {len(assets)} assets matching '{query}'"
            )
            
            return [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type,
                    "status": asset.status
                }
                for asset in assets
            ]

class DataImportTool(ContextAwareTool):
    """Tool to access data imports with context"""
    
    name: str = "data_import_access"
    description: str = "Access data imports for the current context"
    
    async def run(self, import_id: str) -> Dict[str, Any]:
        """Get data import with context validation"""
        async with get_context_db() as db:
            result = await db.execute(
                select(DataImport).where(DataImport.id == import_id)
            )
            data_import = result.scalar_one_or_none()
            
            if not data_import:
                self.log_with_context(
                    'warning',
                    f"Data import {import_id} not found or access denied"
                )
                return {"error": "Import not found or access denied"}
            
            return {
                "id": str(data_import.id),
                "filename": data_import.filename,
                "status": data_import.status,
                "record_count": data_import.record_count
            }
```

## Success Criteria
- [ ] ContextVars implementation working
- [ ] Context flows through all async operations
- [ ] Context-aware base classes implemented
- [ ] Database RLS policies active
- [ ] Context automatically set in DB sessions
- [ ] Tools access only tenant data
- [ ] No context leakage between requests

## Interfaces with Other Agents
- **All agents** will use your context-aware base classes
- **Agent B1** needs context in flows
- **Agent D1** uses context-aware tools
- Share context patterns with all tracks

## Implementation Guidelines

### 1. Context Propagation Rules
- Always use ContextVars, never pass context explicitly
- Context must flow through async boundaries
- Clear context after request completion
- Handle missing context gracefully

### 2. Security First
- Never allow cross-tenant access
- Log all context-based filtering
- Fail closed (deny by default)
- Audit suspicious access patterns

### 3. Testing Approach
```python
@with_context(
    client_account_id="test-client",
    engagement_id="test-engagement",
    user_id="test-user"
)
async def test_context_isolation():
    # Test runs with context automatically set
```

## Commands to Run
```bash
# Run RLS migration
docker exec -it migration_backend alembic upgrade head

# Test context propagation
docker exec -it migration_backend python -m pytest tests/core/test_context.py -v

# Verify RLS policies
docker exec -it migration_backend psql -U postgres -d migration_db -c "\dp+"

# Test context isolation
docker exec -it migration_backend python -m tests.integration.test_context_isolation
```

## Definition of Done
- [ ] ContextVars integrated throughout
- [ ] Context-aware base classes created
- [ ] RLS policies implemented and tested
- [ ] Context flows through all operations
- [ ] Tools respect tenant boundaries
- [ ] No cross-tenant data leakage
- [ ] Unit tests >90% coverage
- [ ] Integration tests verify isolation
- [ ] PR created with title: "feat: [Phase2-C1] Context management infrastructure"

## Notes
- Preserve existing superior context system
- Focus on automatic propagation
- Test isolation thoroughly
- Consider performance impact of RLS
- Document context requirements clearly