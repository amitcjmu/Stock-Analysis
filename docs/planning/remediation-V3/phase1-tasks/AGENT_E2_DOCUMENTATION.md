# Phase 1 - Agent E2: Documentation & Architecture Records

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track E (Documentation) of Phase 1, focusing on documenting all changes, creating architecture decision records, and ensuring knowledge transfer.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- All other agent task files to understand what's being built
- Existing documentation structure in `docs/`

### Phase 1 Goal
Create comprehensive documentation for all Phase 1 changes, including API documentation, architecture decisions, deployment guides, and troubleshooting resources. Your documentation ensures future maintainability and knowledge transfer.

## Your Specific Tasks

### 1. Document V3 API Endpoints
**File to create**: `docs/api/v3/README.md`

```markdown
# Discovery Flow API v3

## Overview
The v3 API consolidates all discovery flow operations into a unified, RESTful interface. This document describes all endpoints, request/response formats, and usage examples.

## Base URL
```
https://api.platform.com/api/v3
```

## Authentication
All requests require Bearer token authentication:
```
Authorization: Bearer <token>
```

## Endpoints

### Discovery Flow Management

#### Create Flow
Creates a new discovery flow.

**Endpoint:** `POST /discovery-flow/flows`

**Request:**
```json
{
  "name": "Q4 2024 Migration",
  "description": "Quarterly migration assessment",
  "client_account_id": "uuid",
  "engagement_id": "uuid",
  "metadata": {
    "source": "manual",
    "tags": ["quarterly", "assessment"]
  }
}
```

**Response:**
```json
{
  "flow_id": "uuid",
  "name": "Q4 2024 Migration",
  "status": "initializing",
  "current_phase": null,
  "progress_percentage": 0,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  "phases_completed": [],
  "metadata": {}
}
```

[Continue with all endpoints...]
```

### 2. Create Architecture Decision Records
**Files to create in**: `docs/adr/`

#### ADR-001: Session to Flow ID Migration
```markdown
# ADR-001: Migrate from Session ID to Flow ID

## Status
Accepted

## Context
The platform currently uses two different identification systems:
- Session IDs (format: `disc_session_*`) for user sessions
- Flow IDs (UUID v4) for CrewAI flows

This dual system causes confusion, synchronization issues, and complicates the codebase.

## Decision
We will migrate to use Flow ID as the single identifier throughout the system.

## Consequences
### Positive
- Single source of truth for identification
- Simplified codebase
- Better alignment with CrewAI patterns
- Easier debugging and tracing

### Negative
- Migration effort required
- Temporary backward compatibility needed
- Risk of breaking existing integrations

### Mitigation
- Backward compatibility layer during transition
- Feature flags for gradual rollout
- Comprehensive testing
```

#### ADR-002: API Consolidation Strategy
```markdown
# ADR-002: Consolidate APIs into v3

## Status
Accepted

## Context
Current API landscape:
- `/api/v1/unified-discovery/` - Original unified approach
- `/api/v1/discovery/` - Legacy discovery endpoints
- `/api/v2/discovery-flows/` - Partial v2 implementation

This fragmentation causes:
- Developer confusion
- Maintenance burden
- Inconsistent patterns

[Continue...]
```

### 3. Update Deployment Documentation
**File to update**: `docs/deployment/README.md`

Add Phase 1 specific deployment steps:
```markdown
## Phase 1 Deployment Guide

### Prerequisites
- Docker 24.0+
- PostgreSQL 15+
- Node.js 18+
- Python 3.11+

### Migration Steps

#### 1. Database Migration
Before deploying Phase 1 changes, run the session-to-flow migration:

```bash
# Backup database
docker exec -it migration_db pg_dump -U postgres migration_db > backup_$(date +%Y%m%d).sql

# Run migration
docker exec -it migration_backend alembic upgrade head

# Verify migration
docker exec -it migration_backend python -m app.verify_migration
```

#### 2. Feature Flags
Enable Phase 1 features gradually:

```env
# .env.production
ENABLE_FLOW_ID_PRIMARY=true
USE_POSTGRES_ONLY_STATE=true
API_V3_ENABLED=true
```

[Continue with deployment steps...]
```

### 4. Create Troubleshooting Guide
**File to create**: `docs/troubleshooting/phase1-common-issues.md`

```markdown
# Phase 1 Common Issues & Solutions

## Field Mapping Issues

### Problem: Dropdown doesn't close when clicking outside
**Symptoms:**
- Clicking outside dropdown doesn't close it
- Multiple dropdowns can be open simultaneously

**Solution:**
1. Verify `dropdown-container` class is present
2. Check event listeners are properly attached
3. Clear browser cache and reload

**Code to check:**
```typescript
// Should see this in FieldMappingsTab.tsx
useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    // Implementation
  };
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, []);
```

### Problem: 500 Error on Approve/Reject
**Symptoms:**
- API returns 500 error
- Console shows "Mapping not found"

**Solution:**
1. Verify using database mapping IDs, not temporary IDs
2. Check data_import_id is being used, not flow_id
3. Verify user has correct permissions

[Continue with more issues...]
```

### 5. API Migration Guide
**File to create**: `docs/api/v3/migration-guide.md`

```markdown
# Migrating to API v3

This guide helps you migrate from v1/v2 APIs to the new consolidated v3 API.

## Overview of Changes

### URL Structure
| Old | New |
|-----|-----|
| `/api/v1/unified-discovery/flow/initialize` | `/api/v3/discovery-flow/flows` |
| `/api/v1/discovery/session/{id}/status` | `/api/v3/discovery-flow/flows/{id}/status` |
| `/api/v2/discovery-flows/flows/active` | `/api/v3/discovery-flow/flows?status=active` |

### Parameter Changes
- `session_id` → `flow_id` everywhere
- Consistent parameter names across endpoints
- Standardized error responses

## Migration Examples

### Creating a Flow
**Before (v1):**
```javascript
const response = await fetch('/api/v1/unified-discovery/flow/initialize', {
  method: 'POST',
  body: JSON.stringify({
    session_name: 'My Session',
    client_id: clientId
  })
});
```

**After (v3):**
```javascript
const response = await fetch('/api/v3/discovery-flow/flows', {
  method: 'POST',
  body: JSON.stringify({
    name: 'My Flow',
    client_account_id: clientId,
    engagement_id: engagementId
  })
});
```

[Continue with more examples...]
```

### 6. Update CLAUDE.md
**File to update**: `CLAUDE.md`

Add Phase 1 specific information:
```markdown
## Phase 1 Changes (January 2024)

### Key Architecture Changes
1. **Flow ID Primary**: All systems now use flow_id instead of session_id
2. **API v3**: New consolidated API at `/api/v3/`
3. **PostgreSQL-Only State**: Removed SQLite dual persistence
4. **Field Mapping Fixes**: Stabilized approve/reject functionality

### New Commands
```bash
# Run session-to-flow migration
docker exec -it migration_backend python -m app.services.migration.session_to_flow

# Validate all flow states
docker exec -it migration_backend python -m app.core.flow_state_validator --check-all

# Test v3 API endpoints
docker exec -it migration_backend python -m pytest tests/api/v3/ -v
```

### Breaking Changes
- Session ID no longer supported in new APIs
- Some v1 endpoints deprecated (see X-API-Deprecation-Warning headers)
```

## Success Criteria
- [ ] Complete API v3 documentation with examples
- [ ] All ADRs created for major decisions
- [ ] Deployment guide updated with Phase 1 steps
- [ ] Troubleshooting guide covers common issues
- [ ] Migration guide helps developers update code
- [ ] CLAUDE.md updated for AI assistants
- [ ] All documentation reviewed for accuracy

## Documentation Standards

### Markdown Guidelines
- Use proper heading hierarchy
- Include code examples with syntax highlighting
- Add diagrams where helpful (Mermaid supported)
- Keep line length under 100 characters
- Use tables for comparisons

### Code Examples
- Always include language identifier
- Show both request and response
- Include error cases
- Use realistic data

### Structure
```
docs/
├── api/
│   └── v3/
│       ├── README.md          # Complete API reference
│       ├── migration-guide.md  # Migration from v1/v2
│       └── examples/          # Code examples
├── adr/
│   ├── README.md             # Index of all ADRs
│   ├── 001-session-to-flow.md
│   ├── 002-api-consolidation.md
│   └── 003-state-management.md
├── troubleshooting/
│   ├── phase1-common-issues.md
│   └── debugging-guide.md
└── deployment/
    ├── phase1-deployment.md
    └── rollback-procedures.md
```

## Commands to Run
```bash
# Validate markdown formatting
docker exec -it migration_backend markdownlint docs/

# Generate API documentation from OpenAPI
docker exec -it migration_backend python -m app.api.v3.generate_docs

# Check for broken links
docker exec -it migration_backend linkchecker docs/
```

## Definition of Done
- [ ] All v3 API endpoints documented
- [ ] ADRs created for all major decisions
- [ ] Deployment guide includes Phase 1 procedures
- [ ] Troubleshooting guide addresses known issues
- [ ] Migration guide with code examples
- [ ] Documentation reviewed by other agents
- [ ] PR created with title: "docs: [Phase1-E2] Phase 1 documentation"

## Coordination Notes
- Review code changes from all other agents
- Verify examples match actual implementation
- Get API details from Agent B1
- Understand migration process from Agent A1
- Document fixes from Agent D1
- Include test information from Agent E1

## Writing Tips
1. **Be Specific**: Avoid vague descriptions
2. **Show Don't Tell**: Use examples liberally
3. **Consider the Reader**: Write for developers new to the project
4. **Stay Current**: Update docs as code changes
5. **Be Concise**: Get to the point quickly
6. **Test Your Examples**: Ensure code samples actually work

## Notes
- Documentation is a living document
- Focus on clarity over completeness
- Include diagrams where they add value
- Keep troubleshooting guide practical
- Link between related documents