# API Endpoints Breakdown

Generated: 2025-08-20

## Summary Statistics
- **Total Endpoints**: 356
- **Total Categories**: 28
- **Average Endpoints per Category**: ~13

## Endpoints by Category

| Category | Count | Key Functionality |
|----------|-------|-------------------|
| **Authentication & User Management** | | |
| Authentication | 2 | Login, password management |
| User Management | 11 | Registration, approvals, user status |
| Admin User Management | 9 | Dashboard stats, active users, admin operations |
| | | |
| **Data Import & Processing** | | |
| Data Import Core | 10 | Import operations, processing control |
| Field Mapping | 24 | Field mapping configuration and management |
| Field Mapping Analysis | 3 | Re-analysis, generation of mappings |
| Field Mapping CRUD | 4 | Create, read, update, delete operations |
| Field Mapping Utilities | 4 | Validation, counting, cleanup |
| Import Storage | 7 | Storage operations for imports |
| Import Retrieval | 4 | Fetching import data and records |
| Asset Processing | 2 | Raw data to asset conversion |
| Critical Attributes | 1 | Critical attributes status |
| Clean API | 2 | Clean import operations |
| | | |
| **Administration** | | |
| Client Management | 9 | Client account management |
| Admin - Engagement Management | 7 | Engagement lifecycle management |
| Platform Admin | 5 | Platform-level administrative tasks |
| Security Monitoring | 5 | Security audit and monitoring |
| Flow Comparison | 5 | Flow comparison and analysis |
| | | |
| **Monitoring & Analytics** | | |
| Agent Monitoring | 6 | Agent status and task monitoring |
| Agent Performance | 3 | Performance metrics and analytics |
| CrewAI Flow Monitoring | 3 | CrewAI-specific flow monitoring |
| Error Monitoring | 5 | Background task and error tracking |
| Health & Metrics | 3 | System health and metrics |
| Analysis Queues | 9 | Queue management and processing |
| | | |
| **Business Operations** | | |
| FinOps | 6 | Financial operations and metrics |
| Master Flow Coordination | 11 | Master flow orchestration |
| AI Learning | 2 | Machine learning from mappings |
| | | |
| **Untagged/Misc** | | |
| Untagged | 194 | Various endpoints needing categorization |

## Most Active Categories

1. **Field Mapping** (35 total endpoints) - Core data transformation functionality
2. **Authentication & User Management** (22 endpoints) - User lifecycle management
3. **Data Import** (23 endpoints) - Data ingestion pipeline
4. **Administration** (31 endpoints) - Platform administration
5. **Monitoring** (26 endpoints) - System observability

## API Design Observations

### Strengths
- Clear RESTful design patterns
- Comprehensive CRUD operations for major entities
- Good separation of concerns between categories
- Strong monitoring and observability coverage

### Areas for Improvement
- **194 untagged endpoints** need proper categorization
- Some categories could be consolidated (e.g., multiple Field Mapping subcategories)
- Consider versioning strategy for future API evolution

## Recommended Actions

1. **Tag Classification**: Prioritize tagging the 194 untagged endpoints
2. **Documentation**: Generate OpenAPI documentation for each category
3. **Rate Limiting**: Implement rate limiting per category based on usage patterns
4. **Security**: Add authentication requirements documentation per endpoint
5. **Deprecation Strategy**: Plan for API evolution and deprecation notices

## API Coverage by Domain

```
Data Pipeline:     65 endpoints (18%)
Administration:    31 endpoints (9%)
Monitoring:        26 endpoints (7%)
Authentication:    22 endpoints (6%)
Business Logic:    19 endpoints (5%)
Untagged:         194 endpoints (55%)
```

## Route Migration Guide

### Assessment Flow Routes
The assessment flow endpoints have been reorganized for better modularity:

| Old Route | New Route | Notes |
|-----------|-----------|-------|
| `/api/v1/assessment-flow/*` | Split into multiple endpoints | See below |
| `/api/v1/assessment-flow/start` | `/api/v1/assessment-flow/flow-management/start` | Flow control |
| `/api/v1/assessment-flow/navigate` | `/api/v1/assessment-flow/flow-management/navigate` | Phase navigation |
| `/api/v1/assessment-flow/architecture` | `/api/v1/assessment-flow/architecture-standards/*` | Architecture endpoints |
| `/api/v1/assessment-flow/components` | `/api/v1/assessment-flow/component-analysis/*` | Component analysis |
| `/api/v1/assessment-flow/tech-debt` | `/api/v1/assessment-flow/tech-debt-analysis/*` | Tech debt endpoints |
| `/api/v1/assessment-flow/sixr` | `/api/v1/assessment-flow/sixr-decisions/*` | 6R decision endpoints |
| `/api/v1/assessment-flow/finalize` | `/api/v1/assessment-flow/finalization/*` | Finalization endpoints |

### Discovery Routes
Discovery endpoints have been unified under a single prefix:

| Old Route | New Route | Notes |
|-----------|-----------|-------|
| `/api/v1/discovery/*` | `/api/v1/unified-discovery/*` | All discovery operations |
| `/api/v1/agents/discovery/*` | `/api/v1/unified-discovery/agents/*` | Agent-specific operations |
| `/api/v1/discovery-flow/*` | `/api/v1/unified-discovery/flow/*` | Flow management |

### Deprecated Endpoints
The following endpoints are deprecated and will be removed in v2:

- `/api/v1/test-discovery/*` - Removed (was debug code with auth bypass)
- `/api/v3/*` - Archived (legacy database abstraction layer)
- WebSocket endpoints - Replaced with HTTP polling for Vercel/Railway compatibility

## CSP Configuration Requirements

For Swagger/ReDoc to work properly, ensure the Content Security Policy allows:

```python
# In security_headers middleware
CSP_EXCEPTIONS = [
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
    "/docs",
    "/redoc",
    "/openapi.json"
]
```

## Next Steps

1. Complete endpoint tagging for better organization
2. Create API client SDKs for common languages
3. Implement API versioning strategy
4. Add request/response examples to documentation
5. Create interactive API playground
6. Generate static ReDoc bundle for offline documentation
7. Add CI checks to enforce tag usage only at router inclusion
