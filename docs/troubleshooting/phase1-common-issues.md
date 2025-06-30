# Phase 1 Common Issues & Solutions

## Overview
This guide addresses common issues encountered after Phase 1 deployment, including field mapping problems, API migration issues, state management failures, and performance concerns.

## Quick Diagnosis Commands

### System Health Check
```bash
# Run comprehensive health check
curl -s http://localhost:8000/health | jq '.'
curl -s http://localhost:8000/api/v3/health | jq '.'

# Check database connectivity
docker exec migration_backend python -c "
from app.core.database import AsyncSessionLocal
import asyncio
async def check():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute('SELECT 1')
        print('✅ Database: OK')
    except Exception as e:
        print(f'❌ Database: {e}')
asyncio.run(check())
"

# Check feature flags
docker exec migration_backend python -c "
import os
flags = {
    'ENABLE_FLOW_ID_PRIMARY': os.getenv('ENABLE_FLOW_ID_PRIMARY', 'false'),
    'USE_POSTGRES_ONLY_STATE': os.getenv('USE_POSTGRES_ONLY_STATE', 'false'),
    'API_V3_ENABLED': os.getenv('API_V3_ENABLED', 'false')
}
for flag, value in flags.items():
    print(f'{flag}: {value}')
"
```

## Field Mapping Issues

### Problem: Dropdown doesn't close when clicking outside
**Symptoms:**
- Clicking outside dropdown doesn't close it
- Multiple dropdowns can be open simultaneously
- Poor user experience with dropdown interactions

**Root Cause:**
Event listeners not properly attached or dropdown container classes missing.

**Solution:**
1. Verify `dropdown-container` class is present in the DOM:
```typescript
// Check in browser console
document.querySelectorAll('.dropdown-container').length
```

2. Check event listeners are properly attached:
```typescript
// Should see this in FieldMappingsTab.tsx
useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as Element;
    if (!target.closest('.dropdown-container')) {
      setOpenDropdowns(new Set());
    }
  };
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, []);
```

3. Clear browser cache and reload the page
4. If issue persists, check console for JavaScript errors

**Verification:**
```bash
# Check if field mapping component is properly loaded
curl -s http://localhost:3000/_next/static/chunks/pages/discovery/attribute-mapping.js | head -10
```

### Problem: 500 Error on Approve/Reject
**Symptoms:**
- API returns 500 Internal Server Error
- Console shows "Mapping not found"
- Field mapping operations fail

**Root Cause:**
Using temporary frontend IDs instead of database mapping IDs, or incorrect foreign key relationships.

**Solution:**
1. Verify using database mapping IDs:
```python
# Check backend logs for the error
docker logs migration_backend | grep "FieldMapping" | tail -10

# Verify mapping ID format being sent
# Should be source field name, not UUID
```

2. Check data_import_id is being used correctly:
```bash
# Verify data import exists
docker exec migration_db psql -U postgres -d migration_db -c "
SELECT id, flow_id, client_account_id, status 
FROM data_imports 
WHERE id = 'your-data-import-id';
"
```

3. Verify user permissions:
```bash
# Check user context in backend logs
docker logs migration_backend | grep "RequestContext" | tail -5
```

4. Check field mapping exists with correct relationships:
```sql
-- Run in database
SELECT fm.id, fm.source_field, fm.target_field, fm.status, di.id as data_import_id
FROM field_mappings fm
JOIN data_imports di ON fm.data_import_id = di.id
WHERE di.flow_id = 'your-flow-id'
AND fm.source_field = 'your-source-field';
```

**Fix Implementation:**
```python
# Correct approach in backend
async def approve_mapping(data_import_id: UUID, source_field: str):
    # Use source_field as stable identifier, not temporary frontend ID
    mapping = await session.execute(
        select(FieldMapping).where(
            FieldMapping.data_import_id == data_import_id,
            FieldMapping.source_field == source_field
        )
    )
    # Rest of implementation...
```

### Problem: Field mappings not saving
**Symptoms:**
- Changes to field mappings don't persist
- Mappings revert to previous state on page reload
- No success feedback after save

**Root Cause:**
Database transaction not committed or validation errors preventing save.

**Solution:**
1. Check database transaction logs:
```bash
docker exec migration_db psql -U postgres -d migration_db -c "
SELECT pg_stat_get_db_xact_commit(oid) as commits,
       pg_stat_get_db_xact_rollback(oid) as rollbacks
FROM pg_database WHERE datname = 'migration_db';
"
```

2. Verify field mapping validation:
```python
# Check validation errors in backend
docker exec migration_backend python -c "
from app.core.flow_state_validator import FlowStateValidator
validator = FlowStateValidator()
# Test with sample mapping data
"
```

3. Check for foreign key constraint violations:
```bash
docker logs migration_backend | grep "IntegrityError" | tail -5
```

## API Migration Issues

### Problem: API v3 endpoints not found (404)
**Symptoms:**
- Requests to `/api/v3/*` return 404
- API v3 not listed in OpenAPI docs
- Health check fails on v3 endpoints

**Root Cause:**
API v3 router not properly registered or feature flag disabled.

**Solution:**
1. Check if API v3 is enabled:
```bash
docker exec migration_backend python -c "
import os
print(f'API_V3_ENABLED: {os.getenv(\"API_V3_ENABLED\", \"false\")}')
"
```

2. Verify v3 router registration:
```python
# Check in main.py
docker exec migration_backend python -c "
from main import app
v3_routes = [route for route in app.routes if '/api/v3' in str(route.path_regex)]
print(f'V3 routes registered: {len(v3_routes)}')
"
```

3. Enable API v3 if disabled:
```bash
docker exec migration_backend sh -c 'echo "API_V3_ENABLED=true" >> .env'
docker restart migration_backend
```

4. Check FastAPI route mounting:
```python
# Verify router is mounted correctly
docker exec migration_backend python -c "
from app.api.v3.router import v3_router
print(f'V3 router prefix: {v3_router.prefix}')
print(f'V3 router routes: {len(v3_router.routes)}')
"
```

### Problem: API v3 authentication failures
**Symptoms:**
- 401 Unauthorized responses
- "Missing client context" errors
- Authentication works on v1/v2 but not v3

**Root Cause:**
v3 API requires additional headers for multi-tenant context.

**Solution:**
1. Include required headers:
```bash
# Correct API v3 request format
curl -H "Authorization: Bearer your-token" \
     -H "X-Client-Account-ID: your-client-id" \
     -H "X-Engagement-ID: your-engagement-id" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v3/discovery-flow/flows
```

2. Verify token is valid:
```bash
# Check token validation
docker exec migration_backend python -c "
from app.core.security import verify_token
token = 'your-token-here'
try:
    payload = verify_token(token)
    print(f'Token valid: {payload}')
except Exception as e:
    print(f'Token invalid: {e}')
"
```

3. Check client account and engagement exist:
```sql
-- Verify in database
SELECT id, name, active FROM client_accounts WHERE id = 'your-client-id';
SELECT id, name, status FROM engagements WHERE id = 'your-engagement-id';
```

### Problem: API v3 response format differences
**Symptoms:**
- Frontend expects different response format
- Missing fields in API v3 responses
- JavaScript errors due to response format

**Root Cause:**
API v3 uses standardized response format different from v1/v2.

**Solution:**
1. Update frontend to handle v3 response format:
```typescript
// v1/v2 response format
{
  "flow_id": "...",
  "status": "...",
  // Direct fields
}

// v3 response format
{
  "success": true,
  "data": {
    "flow_id": "...",
    "status": "...",
    // Fields wrapped in 'data'
  }
}

// Update frontend code
const response = await fetch('/api/v3/discovery-flow/flows');
const result = await response.json();
if (result.success) {
  const flowData = result.data; // Access data wrapper
} else {
  console.error(result.error);
}
```

2. Use migration helper for gradual transition:
```typescript
// Helper function for API response normalization
function normalizeApiResponse(response: any, apiVersion: 'v1' | 'v3') {
  if (apiVersion === 'v3') {
    return response.success ? response.data : null;
  }
  return response; // v1 format
}
```

## State Management Issues

### Problem: PostgreSQL state management failures
**Symptoms:**
- "ConcurrentModificationError" in logs
- Flow state not persisting
- State validation errors

**Root Cause:**
Optimistic locking conflicts or database connectivity issues.

**Solution:**
1. Check database connection pool:
```bash
# Check active connections
docker exec migration_db psql -U postgres -d migration_db -c "
SELECT count(*) as active_connections,
       max_conn.setting as max_connections
FROM pg_stat_activity, pg_settings max_conn
WHERE max_conn.name = 'max_connections'
GROUP BY max_conn.setting;
"
```

2. Monitor for concurrent modifications:
```python
# Check for version conflicts
docker exec migration_backend python -c "
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
import asyncio

async def check_versions():
    context = RequestContext(
        client_account_id='test',
        engagement_id='test',
        user_id='test'
    )
    async with AsyncSessionLocal() as db:
        store = PostgresFlowStateStore(db, context)
        versions = await store.get_flow_versions('your-flow-id')
        print(f'Flow versions: {len(versions)}')
        for v in versions[-3:]:  # Last 3 versions
            print(f'  Version {v[\"version\"]}: {v[\"created_at\"]}')

asyncio.run(check_versions())
"
```

3. Validate state structure:
```python
# Check state validation
docker exec migration_backend python -c "
from app.core.flow_state_validator import FlowStateValidator
validator = FlowStateValidator()

# Test with actual flow state
sample_state = {
    'flow_id': 'test-flow',
    'current_phase': 'initialization',
    'client_account_id': 'test-client',
    'phase_completion': {'initialization': False}
}

result = validator.validate_complete_state(sample_state)
print(f'Validation result: {result}')
"
```

### Problem: SQLite to PostgreSQL migration incomplete
**Symptoms:**
- Some flow states missing after migration
- "Flow not found" errors for existing flows
- Inconsistent state between SQLite and PostgreSQL

**Root Cause:**
Migration script didn't complete successfully or some flows were skipped.

**Solution:**
1. Check migration status:
```bash
docker exec migration_backend python -c "
from app.services.crewai_flows.persistence.state_migrator import StateMigrator
from app.core.database import AsyncSessionLocal
import asyncio

async def check_migration():
    async with AsyncSessionLocal() as db:
        migrator = StateMigrator(db)
        report = await migrator.generate_migration_report()
        print(f'Migration report: {report}')

asyncio.run(check_migration())
"
```

2. Retry failed migrations:
```bash
docker exec migration_backend python -m app.services.crewai_flows.persistence.state_migrator \
  --retry-failed \
  --verbose
```

3. Manually migrate specific flows:
```bash
docker exec migration_backend python -c "
from app.services.crewai_flows.persistence.state_migrator import StateMigrator
from app.core.database import AsyncSessionLocal
import asyncio

async def migrate_specific_flow():
    async with AsyncSessionLocal() as db:
        migrator = StateMigrator(db)
        # Replace with actual flow ID
        result = await migrator.migrate_single_flow('your-flow-id')
        print(f'Migration result: {result}')

asyncio.run(migrate_specific_flow())
"
```

## Session to Flow ID Migration Issues

### Problem: Session ID to Flow ID mapping failures
**Symptoms:**
- "Session not found" errors
- Broken links using session IDs
- Frontend components showing empty data

**Root Cause:**
Session to Flow ID migration incomplete or mapping table not properly populated.

**Solution:**
1. Check mapping table status:
```sql
-- Check session_flow_mapping table
SELECT COUNT(*) as total_mappings FROM session_flow_mapping;
SELECT COUNT(*) as sessions_with_flow_id FROM sessions WHERE flow_id IS NOT NULL;
```

2. Verify specific session mapping:
```bash
docker exec migration_backend python -c "
from app.services.migration.session_to_flow_migrator import SessionToFlowMigrator
from app.core.database import AsyncSessionLocal
import asyncio

async def check_session():
    async with AsyncSessionLocal() as db:
        migrator = SessionToFlowMigrator(db)
        # Replace with actual session ID
        flow_id = await migrator.get_flow_id_for_session('disc_session_123')
        print(f'Flow ID for session: {flow_id}')

asyncio.run(check_session())
"
```

3. Regenerate missing mappings:
```bash
docker exec migration_backend python -m app.services.migration.session_to_flow_migrator \
  --regenerate-mappings \
  --session-id="disc_session_123"
```

### Problem: Frontend still using session IDs
**Symptoms:**
- API calls using old session ID format
- React hooks expecting session IDs
- Routing issues with session-based URLs

**Root Cause:**
Frontend not updated to use Flow ID or backward compatibility not working.

**Solution:**
1. Check if frontend is using Flow ID:
```typescript
// In browser console, check current hook usage
// Should see flow_id, not session_id
console.log(window.localStorage.getItem('current_flow_id'));
console.log(window.localStorage.getItem('session_id')); // Should be null
```

2. Update React hooks to use Flow ID:
```typescript
// Update useUnifiedDiscoveryFlow hook
const { flowId, status, progress } = useUnifiedDiscoveryFlow({
  flowId: flowId, // Not sessionId
  enableRealTimeUpdates: true
});
```

3. Enable backward compatibility temporarily:
```bash
docker exec migration_backend sh -c 'echo "BACKWARD_COMPATIBILITY_MODE=true" >> .env'
docker restart migration_backend
```

## Performance Issues

### Problem: Slow API v3 response times
**Symptoms:**
- API v3 requests taking >2 seconds
- Timeout errors on large datasets
- Poor user experience

**Root Cause:**
Database queries not optimized for new schema or missing indexes.

**Solution:**
1. Check database query performance:
```sql
-- Enable query logging temporarily
SET log_min_duration_statement = 100;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%flow_id%'
ORDER BY mean_time DESC
LIMIT 10;
```

2. Add missing indexes:
```sql
-- Create performance indexes for Phase 1
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_flow_id_active 
ON sessions(flow_id) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_imports_flow_id_status 
ON data_imports(flow_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_field_mappings_data_import_source 
ON field_mappings(data_import_id, source_field);

-- Analyze tables
ANALYZE sessions;
ANALYZE data_imports;
ANALYZE field_mappings;
```

3. Check connection pool settings:
```python
# Verify connection pool configuration
docker exec migration_backend python -c "
from app.core.database import engine
pool = engine.pool
print(f'Pool size: {pool.size()}')
print(f'Pool checked out: {pool.checkedout()}')
print(f'Pool overflow: {pool.overflow()}')
"
```

### Problem: High memory usage after Phase 1
**Symptoms:**
- Container memory usage >2GB
- Out of memory errors
- Slower response times

**Root Cause:**
State management keeping too many flow states in memory or memory leaks.

**Solution:**
1. Check memory usage patterns:
```bash
# Monitor memory usage
docker stats migration_backend --no-stream

# Check Python memory usage
docker exec migration_backend python -c "
import psutil
import os
process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f'RSS: {memory_info.rss / 1024 / 1024:.2f} MB')
print(f'VMS: {memory_info.vms / 1024 / 1024:.2f} MB')
"
```

2. Configure memory cleanup:
```bash
# Enable state cleanup
docker exec migration_backend sh -c 'echo "FLOW_STATE_CLEANUP_HOURS=24" >> .env'
docker restart migration_backend
```

3. Optimize database connections:
```python
# Reduce connection pool size if needed
docker exec migration_backend python -c "
import os
os.environ['DATABASE_POOL_SIZE'] = '10'
os.environ['DATABASE_MAX_OVERFLOW'] = '20'
print('Database pool optimized')
"
```

## Frontend Issues

### Problem: React components not updating with flow data
**Symptoms:**
- Empty or stale data in UI components
- Loading states never completing
- Components not re-rendering with new data

**Root Cause:**
Hooks not properly configured for Flow ID or WebSocket connections failing.

**Solution:**
1. Check WebSocket connection:
```typescript
// In browser console
if (window.WebSocket) {
  console.log('WebSocket supported');
  // Check if connection is active
  console.log('Active WebSocket connections:', navigator.onLine);
} else {
  console.log('WebSocket not supported');
}
```

2. Verify hook configuration:
```typescript
// Ensure useUnifiedDiscoveryFlow is properly configured
const { flowId, data, isLoading, error } = useUnifiedDiscoveryFlow({
  flowId: props.flowId, // Ensure flowId is passed correctly
  enableRealTimeUpdates: true,
  pollInterval: 5000 // Fallback polling
});

console.log('Hook state:', { flowId, data, isLoading, error });
```

3. Check API endpoint connectivity:
```bash
# Test from frontend container
curl -f http://backend:8000/api/v3/discovery-flow/flows/test-flow-id/status
```

### Problem: Field mapping UI not updating after approve/reject
**Symptoms:**
- Buttons remain in loading state
- Status doesn't change after approve/reject
- No success/error feedback

**Root Cause:**
Optimistic updates not working correctly or state not syncing.

**Solution:**
1. Check component state management:
```typescript
// Verify state updates in React DevTools
// Look for proper state transitions:
// pending -> loading -> approved/rejected

// Check if error handling is working
const handleApprove = async (mappingId) => {
  try {
    setLoadingStates(prev => ({ ...prev, [mappingId]: true }));
    await api.approveMapping(flowId, mappingId);
    // Verify this success path executes
    console.log('Approve successful for:', mappingId);
  } catch (error) {
    console.error('Approve failed:', error);
    // Check if error handling executes
  } finally {
    setLoadingStates(prev => ({ ...prev, [mappingId]: false }));
  }
};
```

2. Verify API response format:
```typescript
// Check network tab in browser dev tools
// API v3 responses should be:
{
  "success": true,
  "data": {
    "mapping_id": "...",
    "status": "approved"
  }
}
```

## Monitoring and Debugging

### Enable Debug Logging
```bash
# Enable detailed logging for troubleshooting
docker exec migration_backend sh -c 'echo "LOG_LEVEL=DEBUG" >> .env'
docker restart migration_backend

# Follow logs for specific issues
docker logs -f migration_backend | grep -E "(ERROR|WARNING|Field|Flow|State)"
```

### Database Debugging
```sql
-- Check database locks
SELECT pid, mode, locktype, relation::regclass, page, tuple, transactionid
FROM pg_locks
WHERE NOT granted;

-- Check active queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state = 'active';
```

### Performance Monitoring
```bash
# Check API response times
curl -w "Time: %{time_total}s\n" -o /dev/null -s http://localhost:8000/api/v3/health

# Monitor resource usage
docker stats migration_backend --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
```

## Getting Additional Help

### Log Collection for Support
```bash
# Collect comprehensive logs for support
mkdir -p /tmp/phase1-debug
docker logs migration_backend > /tmp/phase1-debug/backend.log 2>&1
docker logs migration_db > /tmp/phase1-debug/database.log 2>&1
docker exec migration_backend python -c "
from app.core.database import AsyncSessionLocal
import asyncio
async def health_check():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute('SELECT version()')
            print(f'Database version: {result.scalar()}')
    except Exception as e:
        print(f'Database error: {e}')
asyncio.run(health_check())
" > /tmp/phase1-debug/db-health.log

tar -czf phase1-debug-$(date +%Y%m%d_%H%M%S).tar.gz -C /tmp phase1-debug/
```

### Emergency Contacts
- **Phase 1 Support**: phase1-support@company.com
- **On-call Engineer**: +1-555-PHASE1
- **Database Emergency**: +1-555-DATABASE
- **Platform Team**: platform-team@company.com

### Escalation Procedures
1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Collect debug logs and contact Phase 1 support
3. **Level 3**: If critical issue affecting users, contact on-call engineer
4. **Level 4**: Consider emergency rollback (see deployment guide)