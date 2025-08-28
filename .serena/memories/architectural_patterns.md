# Architectural Patterns and Decisions

## Core Architecture Principles

### 1. Multi-Tenant Isolation
- **Pattern**: Row-level security with client_account_id and engagement_id
- **Implementation**: Every query filtered by tenant context
- **Validation**: UUID type consistency throughout

### 2. Two-Table State Pattern
- **Master Table**: crewai_flow_state_extensions (source of truth)
- **Child Table**: discovery_flows (domain-specific)
- **Rationale**: Separation of concerns, atomic updates, audit trail
- **NOT over-engineering**: Required for enterprise resilience

### 3. Seven-Layer Architecture
```
1. API Layer (FastAPI routes)
2. Service Layer (business logic)
3. Repository Layer (data access)
4. Model Layer (SQLAlchemy/Pydantic)
5. Cache Layer (Redis/in-memory)
6. Queue Layer (async processing)
7. Integration Layer (external services)
```

## State Management Architecture

### Pydantic vs SQLAlchemy Models
- **Pydantic (BaseModel)**: Runtime validation, API contracts, serialization
- **SQLAlchemy (Base)**: Database persistence, ORM mapping
- **UnifiedDiscoveryFlowState**: Pydantic model, NOT a database table
- **Pattern**: Transform between layers for clean separation

### Flow State Lifecycle
```python
1. API receives request → Pydantic validation
2. Service processes → Business logic
3. Repository persists → SQLAlchemy models
4. Cache updates → Redis/memory
5. Response returns → Pydantic serialization
```

## Service Patterns

### Persistent Agent Architecture
- **Location**: backend/app/services/persistent_agents/
- **TenantScopedAgentPool**: DOES EXIST, manages agent lifecycle
- **Pattern**: Singleton per tenant with lazy initialization
- **Memory**: Enabled with DeepInfra embeddings patch

### CrewAI Integration Pattern
```python
# Service layer orchestration
service = CrewAIFlowService()
state = await service.process_flow(request)

# Repository layer persistence
repo = FlowStateRepository()
await repo.save_state(state)

# Cache layer optimization
cache = FlowStateCache()
await cache.set(key, state)
```

### Modularization Architecture
- **Single File → Package**: Preserve public API
- **Backward Compatibility**: Shim pattern with star imports
- **Module Organization**: Logical separation by responsibility
- **Import Strategy**: Avoid circular dependencies

## Database Patterns

### Migration Strategy
- **Tool**: Alembic with async support
- **Schema**: 'migration' schema, not 'public'
- **Idempotency**: Check before create/drop
- **Version Control**: Never drop alembic_version table

### Repository Pattern
```python
class BaseRepository:
    async def get_by_id(self, id: UUID) -> Optional[Model]:
        # Tenant filtering applied automatically
        pass

    async def save(self, entity: Model) -> Model:
        # Audit trail created automatically
        pass
```

### Transaction Management
```python
async with async_session() as session:
    async with session.begin():
        # All operations atomic
        await repo1.save(entity1)
        await repo2.save(entity2)
    # Auto-commit on success, rollback on failure
```

## Caching Architecture

### Multi-Level Cache Strategy
1. **L1**: In-memory LRU cache (fast, limited)
2. **L2**: Redis distributed cache (shared, persistent)
3. **L3**: Database cache tables (fallback, durable)

### Cache Invalidation Patterns
- **Time-based**: TTL expiration
- **Event-driven**: Pub/sub notifications
- **Dependency-based**: Graph invalidation
- **Pattern**: Cascade through levels

## Error Handling Patterns

### Graceful Degradation
```python
try:
    result = await primary_service.execute()
except ServiceUnavailable:
    result = await fallback_service.execute()
except Exception:
    result = get_placeholder_response()
```

### Retry Strategy
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_operation():
    pass
```

## Security Patterns

### Authentication & Authorization
- **JWT**: Token-based auth with refresh tokens
- **RBAC**: Role-based access control
- **Row-Level**: Tenant isolation at query level
- **API Keys**: Service-to-service authentication

### Data Protection
```python
# Encryption at rest
class EncryptedField(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        return encrypt(value)

    def process_result_value(self, value, dialect):
        return decrypt(value)
```

## Integration Patterns

### External Service Integration
```python
class AzureAdapter:
    async def discover_resources(self):
        # Retry logic
        # Circuit breaker
        # Rate limiting
        # Error transformation
        pass
```

### Message Queue Pattern
```python
# Producer
await queue.publish(
    topic="discovery.started",
    message={"flow_id": flow_id}
)

# Consumer
@queue.subscribe("discovery.*")
async def handle_discovery_event(message):
    pass
```

## Testing Architecture

### Test Pyramid
1. **Unit Tests**: 70% - Fast, isolated
2. **Integration Tests**: 20% - Service layer
3. **E2E Tests**: 10% - Full stack Docker

### Test Patterns
```python
# Fixtures for common setup
@pytest.fixture
async def test_client():
    async with AsyncClient(app=app) as client:
        yield client

# Mocking external services
@patch('app.services.azure_adapter.discover')
async def test_discovery(mock_discover):
    mock_discover.return_value = test_data
```

## Performance Patterns

### Async/Await Throughout
```python
# Bad: Blocking I/O
data = requests.get(url).json()

# Good: Non-blocking
async with httpx.AsyncClient() as client:
    response = await client.get(url)
    data = response.json()
```

### Batch Processing
```python
# Process in chunks to avoid memory issues
async def process_large_dataset(items):
    for chunk in chunked(items, 100):
        await process_chunk(chunk)
        await asyncio.sleep(0)  # Yield control
```

## Deployment Patterns

### Container Architecture
- **Frontend**: Next.js on Vercel
- **Backend**: FastAPI on Railway
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis with persistence
- **Queue**: RabbitMQ/Redis Streams

### Environment Configuration
```python
# Hierarchy: Railway ENV > .env file > defaults
if os.getenv("RAILWAY_ENVIRONMENT"):
    # Production settings
    load_from_railway()
else:
    # Local development
    load_dotenv()
```

## Critical Lessons

1. **DO NOT** dismiss patterns as over-engineering
2. **DO NOT** remove fallback mechanisms
3. **DO NOT** simplify away multi-tenant isolation
4. **DO NOT** combine separate concerns
5. **DO** respect existing architectural decisions
6. **DO** enhance rather than replace
7. **DO** maintain backward compatibility
8. **DO** preserve audit trails
