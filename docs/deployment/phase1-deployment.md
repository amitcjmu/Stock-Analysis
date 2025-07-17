# Phase 1 Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying Phase 1 improvements to the AI Modernize Migration Platform, including session-to-flow migration, API v3 consolidation, PostgreSQL-only state management, and field mapping fixes.

## Phase 1 Changes Summary

### Key Architectural Changes
1. **Flow ID Primary**: All systems now use `flow_id` instead of `session_id`
2. **API v3**: New consolidated API at `/api/v3/`
3. **PostgreSQL-Only State**: Removed SQLite dual persistence
4. **Field Mapping Fixes**: Stabilized approve/reject functionality
5. **Enhanced State Management**: Validation, recovery, and atomic operations

### Breaking Changes
- Session ID no longer supported in new APIs
- Some v1 endpoints deprecated (see X-API-Deprecation-Warning headers)
- CrewAI flows no longer use `@persist()` decorator
- Field mapping interface behavior changes

## Prerequisites

### System Requirements
```yaml
# Minimum requirements for Phase 1
Backend:
  CPU: 4 cores (8 cores recommended)
  Memory: 8GB (16GB recommended)
  Storage: 100GB SSD
  
Database:
  PostgreSQL: 15+
  Memory: 4GB (8GB recommended)
  Storage: 200GB SSD with backup capability
  
Frontend:
  Node.js: 18+
  Memory: 2GB (4GB recommended)
  CDN: Recommended for global distribution
```

### Software Prerequisites
```bash
# Required software versions
Docker: 24.0+
PostgreSQL: 15+
Node.js: 18+
Python: 3.11+
```

## Pre-Deployment Steps

### 1. Backup Current System
```bash
# Create complete system backup
./deployment/backup/create_full_backup.sh

# Backup database specifically
docker exec migration_db pg_dump -U postgres migration_db > backup_pre_phase1_$(date +%Y%m%d_%H%M%S).sql

# Backup application data
docker cp migration_backend:/app/data ./backup_data_$(date +%Y%m%d_%H%M%S)
```

### 2. Verify Database Schema
```bash
# Check current database schema version
docker exec migration_db psql -U postgres -d migration_db -c "SELECT version FROM alembic_version;"

# Verify critical tables exist
docker exec migration_db psql -U postgres -d migration_db -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('sessions', 'data_imports', 'field_mappings', 'crewai_flow_state_extensions');
"
```

### 3. Environment Configuration
```bash
# Phase 1 environment variables
# Add to .env.production
echo "
# Phase 1 Feature Flags
ENABLE_FLOW_ID_PRIMARY=true
USE_POSTGRES_ONLY_STATE=true
API_V3_ENABLED=true

# State Management Configuration
FLOW_STATE_VALIDATION_ENABLED=true
FLOW_STATE_RECOVERY_ENABLED=true
FLOW_STATE_CLEANUP_HOURS=72

# Migration Settings
SESSION_TO_FLOW_MIGRATION_ENABLED=true
BACKWARD_COMPATIBILITY_MODE=true
" >> .env.production
```

## Migration Procedures

### 1. Database Migration
```bash
# Run Alembic migrations for Phase 1 schema changes
echo "Running database migrations..."
docker exec migration_backend alembic upgrade head

# Verify migration success
docker exec migration_backend alembic current

# Check for any migration warnings
docker exec migration_db psql -U postgres -d migration_db -c "
SELECT schemaname, tablename, attname, typename 
FROM pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
JOIN pg_catalog.pg_type t ON a.atttypid = t.oid
WHERE n.nspname = 'public' 
AND c.relname IN ('sessions', 'data_imports', 'field_mappings')
AND a.attname LIKE '%flow_id%';
"
```

### 2. Session-to-Flow Migration
```bash
# Run the session-to-flow migration
echo "Starting session-to-flow migration..."
docker exec migration_backend python -m app.services.migration.session_to_flow_migrator \
  --migrate-all \
  --verify-integrity \
  --create-mapping-table

# Verify migration results
docker exec migration_backend python -c "
from app.services.migration.session_to_flow_migrator import SessionToFlowMigrator
from app.core.database import AsyncSessionLocal

async def verify():
    async with AsyncSessionLocal() as db:
        migrator = SessionToFlowMigrator(db)
        report = await migrator.generate_migration_report()
        print('Migration Report:')
        print(f'  Total sessions: {report[\"total_sessions\"]}')
        print(f'  Migrated sessions: {report[\"migrated_sessions\"]}')
        print(f'  Active flows: {report[\"active_flows\"]}')
        print(f'  Integrity check: {report[\"integrity_valid\"]}')

import asyncio
asyncio.run(verify())
"
```

### 3. State Management Migration
```bash
# Migrate CrewAI flows to PostgreSQL-only state management
echo "Migrating CrewAI flow state to PostgreSQL..."
docker exec migration_backend python -m app.services.crewai_flows.persistence.state_migrator \
  --migrate-active-flows \
  --verify-data-integrity \
  --cleanup-sqlite-after-verification

# Validate state management
docker exec migration_backend python -m app.core.flow_state_validator --check-all
```

### 4. API v3 Activation
```bash
# Enable API v3 endpoints
echo "Activating API v3..."
docker exec migration_backend python -c "
import os
os.environ['API_V3_ENABLED'] = 'true'
print('API v3 enabled')
"

# Test v3 endpoints
curl -H "Content-Type: application/json" \
     -H "X-Client-Account-ID: test-client" \
     -H "X-Engagement-ID: test-engagement" \
     http://localhost:8000/api/v3/health

# Verify all v3 endpoints are responding
docker exec migration_backend python -c "
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

endpoints = ['/api/v3/', '/api/v3/health', '/api/v3/metrics']
for endpoint in endpoints:
    response = client.get(endpoint)
    print(f'{endpoint}: {response.status_code}')
"
```

## Deployment Steps

### 1. Backend Deployment
```bash
# Build and deploy backend with Phase 1 changes
echo "Deploying backend with Phase 1 improvements..."

# Pull latest changes
git pull origin main

# Build Docker image with Phase 1 code
docker build -f backend/Dockerfile.production -t migration_backend:phase1 backend/

# Stop current backend
docker stop migration_backend

# Start new backend with Phase 1 features
docker run -d \
  --name migration_backend_phase1 \
  --env-file .env.production \
  -p 8000:8000 \
  -v ./data:/app/data \
  migration_backend:phase1

# Verify deployment
sleep 30
curl -f http://localhost:8000/health
```

### 2. Frontend Deployment
```bash
# Deploy frontend with Phase 1 UI improvements
echo "Deploying frontend with Phase 1 improvements..."

# Update environment variables for production
export NEXT_PUBLIC_API_URL="https://your-backend-api.com/api/v3"
export NEXT_PUBLIC_FLOW_ID_PRIMARY="true"
export NEXT_PUBLIC_PHASE1_FEATURES="true"

# Build production frontend
npm run build

# Deploy to Vercel (or your preferred platform)
vercel --prod

# Verify frontend deployment
curl -f https://your-frontend.vercel.app
```

### 3. Database Optimization
```bash
# Optimize database for Phase 1 performance
echo "Optimizing database for Phase 1..."

# Create Phase 1 specific indexes
docker exec migration_db psql -U postgres -d migration_db -f - << 'EOF'
-- Flow ID indexes for improved performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_flow_id 
ON sessions(flow_id) WHERE flow_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_imports_flow_id 
ON data_imports(flow_id) WHERE flow_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_field_mappings_data_import_source 
ON field_mappings(data_import_id, source_field);

-- State management indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crewai_flow_state_flow_id_version 
ON crewai_flow_state_extensions(flow_id, version DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crewai_flow_state_created_at 
ON crewai_flow_state_extensions(created_at DESC);

-- Analyze tables for query optimization
ANALYZE sessions;
ANALYZE data_imports;
ANALYZE field_mappings;
ANALYZE crewai_flow_state_extensions;
EOF
```

## Post-Deployment Verification

### 1. System Health Checks
```bash
# Comprehensive health check
echo "Running Phase 1 health checks..."

# API health check
HEALTH_CHECK=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$HEALTH_CHECK" = "healthy" ]; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed: $HEALTH_CHECK"
    exit 1
fi

# Database connectivity
DB_CHECK=$(docker exec migration_backend python -c "
from app.core.database import AsyncSessionLocal
import asyncio

async def check():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute('SELECT 1')
            return 'OK'
    except Exception as e:
        return f'ERROR: {e}'

print(asyncio.run(check()))
")

if [ "$DB_CHECK" = "OK" ]; then
    echo "✅ Database connectivity verified"
else
    echo "❌ Database connectivity failed: $DB_CHECK"
fi

# State management check
STATE_CHECK=$(docker exec migration_backend python -c "
from app.core.flow_state_validator import FlowStateValidator
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

try:
    validator = FlowStateValidator()
    print('State management system: OK')
except Exception as e:
    print(f'State management error: {e}')
")

echo "State management: $STATE_CHECK"
```

### 2. Feature Validation
```bash
# Test Phase 1 features
echo "Validating Phase 1 features..."

# Test API v3 endpoints
V3_TEST=$(curl -s -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "X-Client-Account-ID: test-client" \
    -H "X-Engagement-ID: test-engagement" \
    http://localhost:8000/api/v3/discovery-flow/flows)

if [[ $V3_TEST == *"200"* ]] || [[ $V3_TEST == *"422"* ]]; then
    echo "✅ API v3 endpoints responding"
else
    echo "❌ API v3 endpoints not responding: $V3_TEST"
fi

# Test flow ID migration
FLOW_ID_TEST=$(docker exec migration_backend python -c "
from app.services.migration.session_to_flow_migrator import SessionToFlowMigrator
from app.core.database import AsyncSessionLocal
import asyncio

async def test():
    async with AsyncSessionLocal() as db:
        migrator = SessionToFlowMigrator(db)
        count = await migrator.count_migrated_sessions()
        return count

result = asyncio.run(test())
print(f'Migrated sessions: {result}')
")

echo "Migration status: $FLOW_ID_TEST"

# Test PostgreSQL-only state management
STATE_TEST=$(docker exec migration_backend python -c "
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
import asyncio

async def test():
    try:
        context = RequestContext(
            client_account_id='test-client',
            engagement_id='test-engagement',
            user_id='test-user'
        )
        async with AsyncSessionLocal() as db:
            store = PostgresFlowStateStore(db, context)
            # Test basic operations
            test_state = {
                'flow_id': 'test-flow',
                'current_phase': 'initialization',
                'client_account_id': 'test-client'
            }
            await store.save_state('test-flow', test_state, 'initialization')
            loaded = await store.load_state('test-flow')
            return 'OK' if loaded else 'FAILED'
    except Exception as e:
        return f'ERROR: {e}'

print(asyncio.run(test()))
")

echo "PostgreSQL state management: $STATE_TEST"
```

### 3. Performance Validation
```bash
# Performance benchmarks for Phase 1
echo "Running performance validation..."

# API response time test
API_RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8000/api/v3/health)
echo "API v3 response time: ${API_RESPONSE_TIME}s"

# Database query performance
DB_PERFORMANCE=$(docker exec migration_db psql -U postgres -d migration_db -c "
\timing on
SELECT COUNT(*) FROM sessions WHERE flow_id IS NOT NULL;
SELECT COUNT(*) FROM data_imports WHERE flow_id IS NOT NULL;
" | grep "Time:")

echo "Database performance:"
echo "$DB_PERFORMANCE"

# Memory usage check
MEMORY_USAGE=$(docker stats migration_backend --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}")
echo "Resource usage:"
echo "$MEMORY_USAGE"
```

## Monitoring and Alerts

### 1. Phase 1 Specific Monitoring
```bash
# Set up Phase 1 monitoring
echo "Configuring Phase 1 monitoring..."

# Add Prometheus metrics for new features
cat >> deployment/monitoring/prometheus.yml << 'EOF'
  - job_name: 'phase1-metrics'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/v3/metrics'
    scrape_interval: 30s
EOF

# Restart Prometheus to pick up new config
docker restart prometheus
```

### 2. Alert Configuration
```yaml
# deployment/monitoring/phase1_alerts.yml
groups:
  - name: phase1_alerts
    rules:
      - alert: FlowIDMigrationIssues
        expr: migration_failed_sessions > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Session to Flow ID migration issues detected"
          description: "{{ $value }} sessions failed to migrate to Flow ID"
      
      - alert: APIv3HighErrorRate
        expr: rate(http_requests_total{path=~"/api/v3/.*",status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on API v3 endpoints"
          description: "API v3 error rate is {{ $value }} requests/second"
      
      - alert: PostgreSQLStateManagementFailures
        expr: rate(postgresql_state_operations_failed_total[5m]) > 0.05
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL state management failures"
          description: "PostgreSQL state operations failing at {{ $value }} operations/second"
```

## Rollback Procedures

### 1. Emergency Rollback Plan
```bash
#!/bin/bash
# Emergency rollback script for Phase 1
echo "⚠️  Starting Phase 1 emergency rollback..."

# 1. Stop current services
docker stop migration_backend_phase1
docker stop migration_frontend_phase1

# 2. Restore previous backend
docker start migration_backend_pre_phase1

# 3. Restore database to pre-Phase 1 state
docker exec migration_db psql -U postgres -d migration_db < backup_pre_phase1_*.sql

# 4. Revert environment variables
cp .env.production.backup .env.production

# 5. Restart services with previous configuration
docker restart migration_backend_pre_phase1

# 6. Verify rollback
sleep 30
curl -f http://localhost:8000/health

echo "✅ Emergency rollback completed"
```

### 2. Partial Rollback Options
```bash
# Disable specific Phase 1 features without full rollback
echo "Performing selective feature rollback..."

# Disable API v3
docker exec migration_backend python -c "
import os
os.environ['API_V3_ENABLED'] = 'false'
print('API v3 disabled')
"

# Revert to session ID mode
docker exec migration_backend python -c "
import os
os.environ['ENABLE_FLOW_ID_PRIMARY'] = 'false'
print('Reverted to session ID mode')
"

# Disable PostgreSQL-only state (revert to hybrid)
docker exec migration_backend python -c "
import os
os.environ['USE_POSTGRES_ONLY_STATE'] = 'false'
print('Reverted to hybrid state management')
"
```

## Troubleshooting

### Common Issues

#### 1. Migration Failures
```bash
# Check migration status
docker exec migration_backend python -c "
from app.services.migration.session_to_flow_migrator import SessionToFlowMigrator
from app.core.database import AsyncSessionLocal
import asyncio

async def check():
    async with AsyncSessionLocal() as db:
        migrator = SessionToFlowMigrator(db)
        failed = await migrator.get_failed_migrations()
        print(f'Failed migrations: {len(failed)}')
        for failure in failed[:5]:  # Show first 5
            print(f'  Session {failure[\"session_id\"]}: {failure[\"error\"]}')

asyncio.run(check())
"

# Fix common migration issues
docker exec migration_backend python -m app.services.migration.session_to_flow_migrator \
  --retry-failed \
  --fix-orphaned-data
```

#### 2. API v3 Issues
```bash
# Check API v3 registration
docker exec migration_backend python -c "
from main import app
v3_routes = [route for route in app.routes if '/api/v3' in str(route.path_regex)]
print(f'V3 routes registered: {len(v3_routes)}')
for route in v3_routes[:5]:
    print(f'  {route.methods} {route.path}')
"

# Test specific v3 endpoints
curl -v -H "Content-Type: application/json" \
       -H "X-Client-Account-ID: test" \
       -H "X-Engagement-ID: test" \
       http://localhost:8000/api/v3/
```

#### 3. State Management Issues
```bash
# Validate state management configuration
docker exec migration_backend python -c "
from app.core.flow_state_validator import FlowStateValidator
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

try:
    validator = FlowStateValidator()
    print('✅ State validator initialized')
    
    # Test validation
    test_state = {
        'flow_id': 'test',
        'current_phase': 'initialization',
        'client_account_id': 'test'
    }
    result = validator.validate_complete_state(test_state)
    print(f'✅ Validation test: {result[\"valid\"]}')
    
except Exception as e:
    print(f'❌ State management error: {e}')
"
```

## Success Criteria

### Phase 1 Deployment is Successful When:
- [ ] All database migrations completed without errors
- [ ] Session-to-flow migration completed with >95% success rate
- [ ] API v3 endpoints responding correctly
- [ ] PostgreSQL-only state management operational
- [ ] Field mapping UI improvements working correctly
- [ ] No critical performance regressions
- [ ] All monitoring alerts configured
- [ ] Backup and rollback procedures tested

### Performance Targets:
- API v3 response time: <200ms for 95% of requests
- Database query performance: No regression from pre-Phase 1
- Memory usage: Within 10% of pre-Phase 1 baseline
- Migration downtime: <5 minutes

## Support Contacts

### Phase 1 Deployment Team:
- **Architecture**: Team Lead (architecture@company.com)
- **Database**: DBA Team (dba@company.com)  
- **DevOps**: Platform Team (devops@company.com)
- **Monitoring**: SRE Team (sre@company.com)

### Emergency Contacts:
- **On-call Engineer**: +1-555-ONCALL
- **Platform Lead**: +1-555-PLATFORM
- **Database Emergency**: +1-555-DATABASE