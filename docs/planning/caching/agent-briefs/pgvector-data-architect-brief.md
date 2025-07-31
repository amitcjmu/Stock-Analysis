# Task Brief: pgvector-data-architect

## Mission
Design and implement the database architecture and Redis cache schema for the AI Force Migration Platform's caching solution, ensuring optimal performance, data integrity, and multi-tenant security.

## Context
The platform currently suffers from cache synchronization issues between frontend and backend. We're implementing a comprehensive Redis caching solution to replace the custom frontend cache and improve performance by 70-80%.

## Primary Objectives

### 1. Cache Schema Design (Week 1)
- Design Redis cache key strategies with versioning support
- Implement tenant isolation in cache keys
- Create cache metadata tracking tables in PostgreSQL
- Design cascade invalidation patterns

### 2. SQLAlchemy Models (Week 1)
- Create models for cache metadata tracking
- Implement cache audit logging tables
- Design cache performance metrics tables
- Add cache configuration management

### 3. Alembic Migrations (Week 1-2)
- Create idempotent migration scripts for cache tables
- Add indexes for cache lookup optimization
- Implement cache statistics aggregation tables

### 4. Cache Coherence Protocol (Week 2)
- Design and implement cache coherence strategies
- Create invalidation cascade patterns
- Implement distributed cache synchronization
- Design cache warming strategies

## Specific Deliverables

### Week 1 Deliverables
```python
# 1. Cache Key Strategy Implementation
# File: backend/app/constants/cache_keys.py
CACHE_VERSION = "v1"

class CacheKeys:
    @staticmethod
    def user_context(user_id: str) -> str:
        return f"{CACHE_VERSION}:user:context:{user_id}"
    
    @staticmethod
    def field_mappings(import_id: str) -> str:
        return f"{CACHE_VERSION}:field_mappings:{import_id}"
    
    # Add all other cache key patterns
```

```python
# 2. Cache Metadata Models
# File: backend/app/models/cache_metadata.py
class CacheMetadata(Base):
    __tablename__ = 'cache_metadata'
    __table_args__ = {'schema': 'migration'}
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String, unique=True, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    client_account_id = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
```

```python
# 3. Cache Coherence Manager
# File: backend/app/services/caching/coherence_manager.py
class CacheCoherenceManager:
    async def invalidate_cascade(self, entity_type: str, entity_id: str):
        """Implement cascade invalidation logic"""
        pass
```

### Week 2-3 Deliverables
- Complete cache invalidation patterns for all entity types
- Implement cache statistics aggregation
- Create cache warming strategies for predictable workflows
- Design multi-tenant cache isolation mechanisms

## Technical Requirements

### Security Requirements
- All cache keys must include tenant context (client_account_id)
- Implement field-level encryption for sensitive cached data
- Create audit trail for cache operations
- Ensure GDPR compliance for cached personal data

### Performance Requirements
- Cache operations must complete within 50ms
- Support for 10,000+ concurrent cache operations
- Implement cache size limits and eviction policies
- Monitor memory usage and alert on thresholds

### Integration Points
- Coordinate with python-crewai-fastapi-expert for API integration
- Work with devsecops-linting-engineer on security review
- Align with qa-playwright-tester on test scenarios

## Success Criteria
- Cache hit ratio > 80% for targeted endpoints
- Zero cache-related security vulnerabilities
- All migrations pass in both development and production
- Cache operations add < 10ms latency to requests

## Resources
- Redis documentation
- Existing codebase patterns in `backend/app/models/`
- Current database schema in `backend/alembic/versions/`
- Multi-tenant patterns in `ContextAwareRepository`

## Communication
- Daily updates to progress dashboard
- Coordinate with python-crewai-fastapi-expert on API integration
- Weekly sync with orchestrator on progress

## Timeline
- Week 1: Complete schema design and initial models
- Week 2: Implement coherence protocols and invalidation
- Week 3: Testing and optimization
- Ongoing: Support other teams with integration

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Immediate
**Priority**: Critical Path