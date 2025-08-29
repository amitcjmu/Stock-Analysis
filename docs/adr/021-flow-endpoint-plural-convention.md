# ADR-021: Flow Endpoint Plural Convention Consolidation

## Status
Accepted

## Context
The codebase has evolved to have inconsistent endpoint patterns for flow resources, mixing singular (`/flow/`) and plural (`/flows/`) conventions. This inconsistency has resulted in:

1. **Duplicate Functionality**: Two separate modules (`flow_management.py` and `unified_discovery/flow_handlers.py`) handle similar flow operations with overlapping endpoints
2. **Routing Confusion**: The `flow_management.py` module is mounted at `/unified-discovery/flow` (singular) while `flow_handlers.py` uses mixed singular/plural patterns
3. **Frontend 404 Errors**: The frontend expects singular endpoints in some places but the backend provides plural, causing failures in the Discovery Dashboard
4. **Maintenance Burden**: Developers must remember which endpoints use singular vs plural forms
5. **API Surface Bloat**: Multiple endpoints doing the same thing with different paths

The root cause was uncoordinated modularization where different teams/phases created their own flow management endpoints without establishing a consistent convention.

## Decision
We will consolidate all flow resource endpoints to use the **plural `/flows/` convention** consistently across the entire codebase. This includes:

1. **Merge Duplicate Modules**: Consolidate `flow_management.py` functionality into `unified_discovery/flow_handlers.py`, keeping the richer implementation
2. **Standardize Endpoints**: All flow resource operations will use `/flows/{flow_id}/` pattern:
   - `/flows/initialize` (not `/flow/initialize`)
   - `/flows/{flow_id}/status` (not `/flow/{flow_id}/status`)
   - `/flows/{flow_id}/execute` (not `/flow/{flow_id}/execute`)
   - `/flows/health` (not `/flow/health`)
3. **Remove Singular Router Mount**: Eliminate the `/unified-discovery/flow` prefix mount from `router_registry.py`
4. **Frontend Centralization**: Create a single source of truth for endpoint definitions in the frontend services
5. **No Redirects**: Since we control all code, we'll do a clean cutover without backward compatibility redirects to avoid code sprawl

**Exception**: Action endpoints that aren't REST resources (like `/flow-processing/continue`) may use different patterns as they represent operations, not resources.

## Consequences

### Positive
- **Eliminates Confusion**: Single, consistent pattern for all flow resources
- **Reduces Errors**: No more 404s from endpoint mismatches
- **Improves Maintainability**: Developers don't need to remember exceptions
- **Cleaner Architecture**: Single module handles all flow operations
- **Better API Design**: Follows REST conventions (plural for collections/resources)
- **Simplified Mental Model**: All flow resources under `/flows/`

### Negative
- **Migration Effort**: Requires updating ~17 frontend files and multiple backend modules
- **Testing Required**: All flow operations need verification after changes
- **No Gradual Migration**: Clean cutover means all changes must work immediately

### Risks
- **Missed Endpoints**: Some singular endpoints might be overlooked
  - **Mitigation**: Comprehensive grep searches and CI validation script
- **Runtime Failures**: Frontend might still call old endpoints
  - **Mitigation**: Update frontend first in the branch, test thoroughly
- **Third-party Integrations**: External systems might use old endpoints
  - **Mitigation**: We confirmed no external API consumers exist

## Implementation

### Phase 1: Frontend Updates (30 minutes)
1. Create centralized endpoint constants in `masterFlowService.ts`
2. Update all 17 files using singular `/flow/` to use plural `/flows/`
3. Ensure no hardcoded singular paths remain

### Phase 2: Backend Consolidation (45 minutes)
1. Merge `flow_management.py` into `unified_discovery/flow_handlers.py`:
   - Keep the richer `get_flow_status` implementation
   - Add pause, resume, retry, delete operations
2. Remove `flow_management.py` file
3. Remove flow_management router registration from `router_registry.py`
4. Update all remaining singular endpoints:
   - `/flow/initialize` → `/flows/initialize`
   - `/flow/{id}/import-data` → `/flows/{id}/import-data`
   - `/flow/{id}/agent-insights` → `/flows/{id}/agent-insights`
   - `/flow/health` → `/flows/health`

### Phase 3: Validation (15 minutes)
1. Add CI validation script to prevent new singular endpoints
2. Run comprehensive endpoint tests
3. Verify Discovery Dashboard functionality

### Timeline
- Single PR completion: ~1.5 hours
- No phased rollout needed
- Clean cutover approach

## Alternatives Considered

### Alternative 1: Keep Both Patterns with Redirects
- **Description**: Maintain both singular and plural with 308 redirects
- **Rejected Because**: Adds code sprawl, maintains confusion, requires later cleanup

### Alternative 2: Standardize on Singular
- **Description**: Change all endpoints to use `/flow/` (singular)
- **Rejected Because**: 
  - Plural is more common in the codebase (43 backend, most other modules)
  - Plural follows REST conventions for resources
  - Migration mappings expect plural

### Alternative 3: Gradual Migration
- **Description**: Migrate endpoints incrementally over multiple PRs
- **Rejected Because**: 
  - Prolongs the confusion period
  - Risk of incomplete migration
  - More total effort

### Alternative 4: Different Patterns by Context
- **Description**: Use singular for single operations, plural for collections
- **Rejected Because**: 
  - Adds complexity
  - Requires developers to think about each case
  - No clear benefit over consistent plural

## Related ADRs
- **ADR-006**: Master Flow Orchestrator - Defines flow orchestration patterns
- **ADR-007**: Comprehensive Modularization Architecture - Led to the modular structure that caused this issue
- **ADR-011**: Flow-Based Architecture Evolution - Establishes flows as core concept
- **ADR-012**: Flow Status Management Separation - Related to flow state handling

## References
- [REST Resource Naming Guide](https://restfulapi.net/resource-naming/)
- Git commits showing evolution of duplicate modules
- Discovery Dashboard error logs showing 404s from endpoint mismatches