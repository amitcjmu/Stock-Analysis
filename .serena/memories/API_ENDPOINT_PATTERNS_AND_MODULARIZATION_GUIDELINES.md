# API Endpoint Patterns and Modularization Guidelines

## Critical API Endpoint Mappings (As of August 2025)

### Master Flow Orchestrator (MFO) Endpoints
- **Backend Registration**: `/api/v1/master-flows/*` (NOT `/api/v1/flows/*`)
- **Key Endpoints**:
  - `GET /api/v1/master-flows/active` - Get active flows
  - `POST /api/v1/master-flows/{flowId}/resume` - Resume a flow
  - `DELETE /api/v1/master-flows/{flowId}` - Delete a flow

### Flow Processing Service
- **Backend Registration**: `/api/v1/flow-processing/*`
- **Key Endpoints**:
  - `POST /api/v1/flow-processing/continue/{flowId}` - Continue/monitor a flow

### Unified Discovery Service
- **Backend Registration**: `/api/v1/unified-discovery/*`
- **Key Endpoints**:
  - `GET /api/v1/unified-discovery/flow/{flowId}/status` - Get flow status
  - `POST /api/v1/unified-discovery/flow/{flowId}/execute` - Execute flow phase

### Collection Flow Service
- **Backend Registration**: `/api/v1/collection/*`
- **Key Endpoints**:
  - `GET /api/v1/collection/adaptive-questionnaires` - Get questionnaires
  - `GET /api/v1/collection/status` - Get collection status

## Root Cause Analysis (August 2025)

### What Happened
1. **August 14, 2025**: Master Flow State Enrichment (commit 99d0cc559) introduced MFO architecture
2. **August 17-20, 2025**: Major modularization effort split large files into smaller modules
3. **During Modularization**:
   - Backend router registrations were updated to new paths
   - Frontend services were NOT updated to match new paths
   - Result: Frontend calling old endpoints that no longer existed

### Breaking Changes During Modularization
- `/api/v1/flows/*` → `/api/v1/master-flows/*` (MFO endpoints)
- `/api/v1/flows/{flowId}/resume` → `/api/v1/flow-processing/continue/{flowId}`
- `/api/v1/flows/{flowId}/status` → `/api/v1/unified-discovery/flow/{flowId}/status`

## Prevention Guidelines

### 1. Pre-Modularization Checklist
Before ANY modularization or refactoring:
- [ ] Document all current API endpoints being used
- [ ] Search frontend for all API calls to affected endpoints
- [ ] Create a mapping of old paths to new paths
- [ ] Plan frontend updates alongside backend changes

### 2. During Modularization
- [ ] Update backend router registration
- [ ] Update corresponding frontend service files
- [ ] Update any API documentation
- [ ] Test ALL affected UI flows

### 3. Post-Modularization Verification
- [ ] Run full E2E tests with Playwright
- [ ] Check browser console for 404 errors
- [ ] Verify all major user flows work:
  - Discovery Dashboard navigation
  - Flow monitoring/continuation
  - Collection adaptive forms
  - Data import blocking
  - Attribute mapping

### 4. Critical Files to Check
When changing endpoints, ALWAYS update:
- **Backend**:
  - `backend/app/api/v1/router_registry.py`
  - `backend/app/api/v1/router_imports.py`
  - Individual endpoint files
- **Frontend**:
  - `src/services/api/masterFlowService.ts`
  - `src/services/api/discoveryService.ts`
  - `src/services/api/collectionService.ts`
  - Any component using direct API calls

### 5. Testing Commands
Always run after endpoint changes:
```bash
# Backend
docker-compose build backend
docker-compose up -d

# Frontend
npm run build
npm run type-check

# E2E Testing
npx playwright test
```

## Common Pitfalls to Avoid
1. **Never** change backend endpoints without updating frontend
2. **Never** assume endpoint paths from function names
3. **Always** check actual router registration, not just endpoint definitions
4. **Always** test UI flows after backend changes
5. **Never** rely on fallbacks to mask broken endpoints

## Emergency Recovery
If endpoints break in production:
1. Check `backend/app/api/v1/router_registry.py` for actual paths
2. Compare with frontend service files for mismatches
3. Update frontend to match backend registrations
4. Test all affected UI flows
5. Document the fix in this memory file
