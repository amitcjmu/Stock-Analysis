# Multi-Tenancy Implementation Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform implements comprehensive multi-tenancy using row-level security with `client_account_id` and `engagement_id` as isolation keys. This ensures complete data separation between tenants while maintaining efficient query performance and security.

## Core Multi-Tenancy Architecture

### Tenant Isolation Strategy

The platform uses a **Two-Level Isolation** approach:

1. **Client Level**: `client_account_id` (UUID) - Separates different organizations
2. **Engagement Level**: `engagement_id` (UUID) - Separates different projects within an organization

### RequestContext Pattern

All multi-tenant operations flow through the `RequestContext` data structure:

```python
@dataclass
class RequestContext:
    """Enhanced request context with audit fields"""
    
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None
    flow_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Audit fields
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_version: Optional[str] = None
    
    # Feature flags
    feature_flags: Optional[Dict[str, bool]] = None
```

## Implementation Patterns

### 1. Context Extraction and Injection

**From HTTP Headers:**
```python
def extract_context_from_request(request: Request) -> RequestContext:
    """Extract context from request headers with demo client fallback."""
    
    # Header precedence: X-Client-Account-Id > query params > demo fallback
    client_account_id = (
        request.headers.get("X-Client-Account-Id") or
        request.query_params.get("client_account_id") or
        DEMO_CLIENT_CONFIG["client_account_id"]
    )
    
    engagement_id = (
        request.headers.get("X-Engagement-Id") or
        request.query_params.get("engagement_id") or
        DEMO_CLIENT_CONFIG["engagement_id"]
    )
    
    return RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=request.headers.get("X-User-Id"),
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        api_version=request.headers.get("X-API-Version", "v1")
    )
```

**FastAPI Dependency Injection:**
```python
async def get_current_context(request: Request) -> RequestContext:
    """FastAPI dependency for extracting request context."""
    context = extract_context_from_request(request)
    _request_context.set(context)
    return context

# Usage in endpoints
@router.get("/flows/{flow_id}")
async def get_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    # Context is automatically available and contains tenant isolation
    pass
```

### 2. Database Query Filtering

**Automatic Tenant Filtering:**
All database queries automatically include tenant filters:

```python
class DiscoveryFlowRepository:
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def get_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow by ID with automatic tenant filtering."""
        query = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == self.context.client_account_id,
                DiscoveryFlow.engagement_id == self.context.engagement_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def save(self, flow: DiscoveryFlow) -> DiscoveryFlow:
        """Save flow with automatic tenant context injection."""
        if not flow.client_account_id:
            flow.client_account_id = self.context.client_account_id
        if not flow.engagement_id:
            flow.engagement_id = self.context.engagement_id
        
        self.db.add(flow)
        await self.db.commit()
        await self.db.refresh(flow)
        return flow
```

**Master-Child Table Pattern:**
The two-table state pattern maintains tenant isolation:

```python
class CrewAIFlowStateExtensions(Base):
    """Master table - source of truth for all flows."""
    __tablename__ = "crewai_flow_state_extensions"
    
    flow_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # ... other fields

class DiscoveryFlow(Base):
    """Child table - domain-specific data."""
    __tablename__ = "discovery_flows"
    
    flow_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # ... domain-specific fields
```

### 3. Service Layer Integration

**Context-Aware Services:**
```python
class CrewAIFlowServiceBase:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self._discovery_flow_service: Optional[DiscoveryFlowService] = None
    
    async def _get_discovery_flow_service(
        self, context: Dict[str, Any]
    ) -> DiscoveryFlowService:
        """Get discovery flow service with tenant context."""
        if not self._discovery_flow_service:
            # Create RequestContext from the context dict
            request_context = RequestContext(
                client_account_id=context.get("client_account_id"),
                engagement_id=context.get("engagement_id"),
                user_id=context.get("user_id"),
                flow_id=context.get("flow_id")
            )
            
            self._discovery_flow_service = DiscoveryFlowService(
                db=self.db,
                context=request_context
            )
        
        return self._discovery_flow_service
```

**Repository Pattern with Context:**
```python
class FlowStateRepository:
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def get_flow_state(self, flow_id: UUID) -> Optional[CrewAIFlowStateExtensions]:
        """Get flow state with tenant filtering."""
        query = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == flow_id,
                CrewAIFlowStateExtensions.client_account_id == self.context.client_account_id,
                CrewAIFlowStateExtensions.engagement_id == self.context.engagement_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

### 4. Cache Isolation

**Tenant-Scoped Cache Keys:**
```python
def get_tenant_cache_key(context: RequestContext, base_key: str) -> str:
    """Generate tenant-scoped cache key."""
    return f"{context.client_account_id}:{context.engagement_id}:{base_key}"

# Usage in cache operations
async def get_cached_flow_state(context: RequestContext, flow_id: str):
    cache_key = get_tenant_cache_key(context, f"flow_state:{flow_id}")
    return await redis_client.get(cache_key)

async def set_cached_flow_state(context: RequestContext, flow_id: str, state: dict):
    cache_key = get_tenant_cache_key(context, f"flow_state:{flow_id}")
    await redis_client.setex(cache_key, 300, json.dumps(state))
```

## Security Implementation

### Row-Level Security (RLS)

**Database Level Protection:**
```sql
-- Enable RLS on tenant tables
ALTER TABLE discovery_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE crewai_flow_state_extensions ENABLE ROW LEVEL SECURITY;

-- Create policies for tenant isolation
CREATE POLICY tenant_isolation_policy ON discovery_flows
    FOR ALL TO application_role
    USING (client_account_id = current_setting('app.current_client_account_id')::uuid);
```

**Application Level Enforcement:**
```python
async def set_tenant_context(db: AsyncSession, context: RequestContext):
    """Set tenant context for RLS enforcement."""
    await db.execute(
        text("SET app.current_client_account_id = :client_id"),
        {"client_id": context.client_account_id}
    )
    await db.execute(
        text("SET app.current_engagement_id = :engagement_id"),
        {"engagement_id": context.engagement_id}
    )
```

### API Security

**Tenant Validation Middleware:**
```python
class TenantValidationMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract context
        context = extract_context_from_request(request)
        
        # Validate tenant exists and user has access
        if not await validate_tenant_access(context):
            raise HTTPException(
                status_code=403,
                detail="Access denied to tenant resources"
            )
        
        # Continue with request
        response = await call_next(request)
        return response
```

## Agent Integration

### Tenant-Scoped Agent Pools

**Persistent Agent Architecture:**
```python
class TenantScopedAgentPool:
    """Manages CrewAI agents per tenant."""
    
    _pools: Dict[str, Dict[str, Agent]] = {}
    _pool_lock = threading.Lock()
    
    @classmethod
    def get_agent_pool(
        cls, 
        client_account_id: str, 
        engagement_id: str
    ) -> Dict[str, Agent]:
        """Get or create agent pool for tenant."""
        pool_key = f"{client_account_id}:{engagement_id}"
        
        with cls._pool_lock:
            if pool_key not in cls._pools:
                cls._pools[pool_key] = cls._create_agent_pool(
                    client_account_id, engagement_id
                )
            
            return cls._pools[pool_key]
    
    @classmethod
    def _create_agent_pool(
        cls, 
        client_account_id: str, 
        engagement_id: str
    ) -> Dict[str, Agent]:
        """Create new agent pool with tenant context."""
        memory_manager = ThreeTierMemoryManager(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        agents = {
            "discovery_agent": Agent(
                role="Discovery Specialist",
                goal="Discover and catalog cloud resources",
                backstory="Expert in cloud infrastructure discovery",
                memory=memory_manager.get_agent_memory("discovery"),
                tools=get_discovery_tools(client_account_id, engagement_id)
            ),
            # ... other agents
        }
        
        return agents
```

**Memory Isolation:**
```python
class ThreeTierMemoryManager:
    def __init__(self, client_account_id: str, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.memory_namespace = f"{client_account_id}:{engagement_id}"
    
    def get_agent_memory(self, agent_name: str):
        """Get tenant-scoped memory for agent."""
        return TenantScopedMemory(
            namespace=f"{self.memory_namespace}:{agent_name}",
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id
        )
```

## Testing Multi-Tenancy

### Isolation Tests

**Tenant Data Isolation:**
```python
@pytest.mark.asyncio
async def test_tenant_data_isolation():
    """Test that tenant data is properly isolated."""
    # Create flows for different tenants
    tenant_1_context = RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222"
    )
    
    tenant_2_context = RequestContext(
        client_account_id="33333333-3333-3333-3333-333333333333",
        engagement_id="44444444-4444-4444-4444-444444444444"
    )
    
    # Create flow for tenant 1
    repo_1 = DiscoveryFlowRepository(db, tenant_1_context)
    flow_1 = await repo_1.create_flow({"name": "Tenant 1 Flow"})
    
    # Try to access tenant 1's flow with tenant 2's context
    repo_2 = DiscoveryFlowRepository(db, tenant_2_context)
    result = await repo_2.get_by_id(flow_1.flow_id)
    
    # Should return None due to tenant isolation
    assert result is None
```

**Context Propagation Tests:**
```python
@pytest.mark.asyncio
async def test_context_propagation():
    """Test that context propagates through service layers."""
    context = RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222"
    )
    
    # Context should propagate through all layers
    service = CrewAIFlowService(db)
    result = await service.create_flow(context.to_dict())
    
    # Verify context was used in database operations
    assert result["client_account_id"] == context.client_account_id
    assert result["engagement_id"] == context.engagement_id
```

## Demo Client Configuration

The platform includes a demo client for development and testing:

```python
DEMO_CLIENT_CONFIG = {
    "client_account_id": "11111111-1111-1111-1111-111111111111",
    "client_name": "Demo Corporation",
    "engagement_id": "22222222-2222-2222-2222-222222222222",
    "engagement_name": "Demo Cloud Migration Project",
}
```

This provides a consistent fallback when headers are missing during development.

## Performance Considerations

### Index Strategy

**Multi-Column Indexes:**
```sql
-- Composite indexes for efficient tenant filtering
CREATE INDEX idx_discovery_flows_tenant_lookup 
ON discovery_flows (client_account_id, engagement_id, flow_id);

CREATE INDEX idx_crewai_flow_tenant_lookup 
ON crewai_flow_state_extensions (client_account_id, engagement_id, flow_id);
```

**Query Optimization:**
```python
# Always filter by tenant columns first (most selective)
query = select(DiscoveryFlow).where(
    and_(
        DiscoveryFlow.client_account_id == context.client_account_id,  # Most selective
        DiscoveryFlow.engagement_id == context.engagement_id,         # Secondary filter
        DiscoveryFlow.flow_id == flow_id                             # Final filter
    )
)
```

### Cache Efficiency

**Hierarchical Cache Keys:**
```python
# Efficient cache hierarchy
def get_cache_hierarchy(context: RequestContext, resource_type: str, resource_id: str):
    return [
        f"global:{resource_type}",                                    # Global cache
        f"client:{context.client_account_id}:{resource_type}",       # Client cache
        f"engagement:{context.engagement_id}:{resource_type}",       # Engagement cache
        f"resource:{context.engagement_id}:{resource_type}:{resource_id}"  # Resource cache
    ]
```

## Troubleshooting

### Common Issues

1. **Missing Tenant Context:**
   ```python
   # Check if context is properly set
   context = _request_context.get()
   if not context or not context.client_account_id:
       logger.error("Missing tenant context in request")
       raise HTTPException(status_code=400, detail="Tenant context required")
   ```

2. **Cross-Tenant Data Leaks:**
   ```python
   # Always verify queries include tenant filters
   def validate_query_has_tenant_filter(query_str: str, context: RequestContext):
       if context.client_account_id not in query_str:
           raise SecurityError("Query missing tenant filter")
   ```

3. **Cache Key Collisions:**
   ```python
   # Ensure cache keys are properly namespaced
   def safe_cache_key(context: RequestContext, key: str) -> str:
       if not context.client_account_id:
           raise ValueError("Cannot create cache key without tenant context")
       return f"{context.client_account_id}:{context.engagement_id}:{key}"
   ```

## Migration Strategies

### Adding Multi-Tenancy to Existing Tables

```python
# Alembic migration example
def upgrade():
    # Add tenant columns
    op.add_column('existing_table', sa.Column('client_account_id', UUID(), nullable=True))
    op.add_column('existing_table', sa.Column('engagement_id', UUID(), nullable=True))
    
    # Populate with demo values for existing data
    op.execute(f"""
        UPDATE existing_table 
        SET client_account_id = '{DEMO_CLIENT_CONFIG["client_account_id"]}',
            engagement_id = '{DEMO_CLIENT_CONFIG["engagement_id"]}'
        WHERE client_account_id IS NULL
    """)
    
    # Make columns non-nullable
    op.alter_column('existing_table', 'client_account_id', nullable=False)
    op.alter_column('existing_table', 'engagement_id', nullable=False)
    
    # Add indexes
    op.create_index('idx_existing_table_tenant', 'existing_table', 
                   ['client_account_id', 'engagement_id'])
```

This multi-tenancy implementation ensures complete data isolation while maintaining performance and security across all platform components.