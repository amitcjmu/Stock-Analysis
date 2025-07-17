# ADR-002: Consolidate APIs into Unified v3 Interface

## Status
Accepted

## Context
The AI Modernize Migration Platform has evolved multiple API versions and endpoints that create fragmentation:

### Current API Landscape
- **`/api/v1/unified-discovery/`** - Original unified approach with session-based operations
- **`/api/v1/discovery/`** - Legacy discovery endpoints with mixed patterns
- **`/api/v2/discovery-flows/`** - Partial v2 implementation with incomplete coverage
- **Various standalone endpoints** - Scattered utility endpoints

### Problems with Current State
1. **Developer Confusion**: Three different API patterns for similar operations
2. **Maintenance Burden**: Bug fixes and features need implementation across multiple APIs
3. **Inconsistent Patterns**: Different response formats, error handling, and authentication
4. **Client Integration Complexity**: Applications must handle multiple API versions
5. **Documentation Fragmentation**: Multiple API references to maintain
6. **Testing Overhead**: Each API version requires separate test suites

## Decision
We will consolidate all discovery flow operations into a **unified v3 API** with the following principles:

### API Design Principles
1. **RESTful Design**: Consistent HTTP methods and resource-based URLs
2. **Single Responsibility**: Each endpoint serves one clear purpose
3. **Standardized Responses**: Consistent success/error response formats
4. **Multi-tenant Context**: Built-in support for client account and engagement scoping
5. **Real-time Capabilities**: WebSocket support for live updates
6. **Comprehensive Coverage**: Complete CRUD operations for all resources

### API Structure
```
/api/v3/
├── discovery-flow/          # Flow lifecycle management
├── data-import/             # Data upload and validation
├── field-mapping/           # Field mapping with AI assistance
├── health                   # System health monitoring
├── metrics                  # Performance metrics
└── ws/                      # WebSocket endpoints
```

## Consequences

### Positive
- **Developer Experience**: Single, consistent API to learn and use
- **Reduced Maintenance**: One codebase for all discovery operations
- **Better Documentation**: Comprehensive, unified API reference
- **Improved Testing**: Single test suite with complete coverage
- **Enhanced Features**: Modern capabilities like real-time updates and standardized error handling
- **Migration Path**: Clear upgrade path from legacy APIs
- **Performance**: Optimized for current architecture patterns

### Negative
- **Breaking Changes**: Existing integrations need updates for new patterns
- **Migration Effort**: Applications using v1/v2 APIs need migration work
- **Temporary Complexity**: During transition, multiple API versions coexist
- **Learning Curve**: Teams need to adopt new API patterns

### Risks
- **Client Disruption**: Rapid migration could break existing integrations
- **Feature Gaps**: V3 API must support all existing functionality
- **Performance Regression**: New API patterns might introduce latency

## Implementation

### Phase 1: V3 API Development ✅ (Completed)
- **Core Router**: `/api/v3/router.py` with modular sub-routers
- **Discovery Flow API**: Complete CRUD operations with flow lifecycle management
- **Data Import API**: File upload, validation, and data processing
- **Field Mapping API**: AI-powered mapping suggestions and management
- **Schema Definitions**: Comprehensive Pydantic models for all operations
- **Error Handling**: Standardized error responses with detailed context
- **OpenAPI Integration**: Auto-generated documentation with examples

### Phase 2: Client Migration Support
```python
# Migration compatibility layer
@app.middleware("http")
async def api_compatibility_middleware(request: Request, call_next):
    # Detect legacy API usage
    if request.url.path.startswith("/api/v1/") or request.url.path.startswith("/api/v2/"):
        response = await call_next(request)
        response.headers["X-API-Deprecation-Warning"] = "This API version is deprecated. Please migrate to /api/v3/"
        return response
    return await call_next(request)
```

### Phase 3: Legacy API Deprecation
- **Deprecation Headers**: Add deprecation warnings to v1/v2 responses
- **Migration Tools**: Automated tools to help update client code
- **Documentation**: Clear migration guides with code examples
- **Timeline**: 6-month deprecation period with advance notice

## API Design Details

### Standardized Response Format
```json
{
  "success": true,
  "data": {
    // Response payload
  },
  "pagination": {  // For paginated responses
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "flow_id",
      "reason": "Invalid UUID format"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Multi-tenant Context
```http
POST /api/v3/discovery-flow/flows
Authorization: Bearer <token>
X-Client-Account-ID: <client_uuid>
X-Engagement-ID: <engagement_uuid>
Content-Type: application/json
```

## Migration Strategy

### Backward Compatibility Approach
1. **Parallel Operation**: V3 API runs alongside existing APIs during transition
2. **Feature Parity**: V3 API supports all functionality from previous versions
3. **Data Compatibility**: Shared database models ensure data consistency
4. **Response Mapping**: V1/V2 endpoints can proxy to V3 with response transformation

### Client Migration Tools
```bash
# API migration helper tool
python -m app.tools.api_migrator \
  --source-version v1 \
  --target-version v3 \
  --client-code-path ./src/api/ \
  --output-path ./src/api/v3/
```

### Migration Timeline
- **Month 1-2**: V3 API development and testing
- **Month 3**: Client migration tools and documentation
- **Month 4-6**: Gradual client migration with support
- **Month 7**: Begin v1/v2 deprecation warnings
- **Month 12**: Remove v1/v2 APIs (unless critical usage remains)

## Validation

### API Quality Metrics
- **Response Time**: <200ms for 95% of requests
- **Error Rate**: <1% for all endpoints
- **Documentation Coverage**: 100% of endpoints documented with examples
- **Schema Validation**: 100% of requests/responses validated
- **Test Coverage**: >90% code coverage for all v3 endpoints

### Migration Success Criteria
- **Client Adoption**: >80% of active clients migrated to v3
- **Performance**: V3 API performs better than or equal to legacy APIs
- **Feature Completeness**: V3 API supports all legacy functionality
- **Developer Satisfaction**: Positive feedback on API usability and documentation

## Alternatives Considered

### Alternative 1: Incremental v2 Enhancement
**Rejected** - Would perpetuate the fragmentation problem and not address fundamental design issues.

### Alternative 2: Keep All API Versions Indefinitely
**Rejected** - Unsustainable maintenance burden and prevents platform evolution.

### Alternative 3: Big Bang Migration (Force immediate adoption)
**Rejected** - Too disruptive to existing clients and high risk of breaking integrations.

## OpenAPI Specification

The V3 API includes comprehensive OpenAPI 3.0 specification:
- **Interactive Documentation**: Available at `/docs` and `/redoc`
- **Machine-readable Spec**: Available at `/api/v3/openapi-spec`
- **Code Generation**: Supports client SDK generation for multiple languages
- **Validation**: Request/response validation with detailed error messages

## Related ADRs
- [ADR-001](001-session-to-flow-migration.md) - Flow ID as primary identifier
- [ADR-003](003-postgresql-only-state-management.md) - State management architecture

## References
- V3 API Implementation: `backend/app/api/v3/`
- Migration Guide: `docs/api/v3/migration-guide.md`
- API Documentation: `docs/api/v3/README.md`
- Legacy API Analysis: `docs/planning/phase1-tasks/AGENT_B1_BACKEND_API_CONSOLIDATION.md`