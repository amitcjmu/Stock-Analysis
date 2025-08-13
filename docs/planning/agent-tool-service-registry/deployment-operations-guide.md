# Service Registry Deployment and Operations Guide

## Overview

This guide provides operational procedures for deploying, monitoring, and maintaining the Service Registry architecture for CrewAI tools.

## Environment Configuration

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  migration_backend:
    build: ./backend
    environment:
      # Service Registry Feature Flag
      - USE_SERVICE_REGISTRY=${USE_SERVICE_REGISTRY:-false}
      
      # Metrics Collection (start disabled)
      - ENABLE_SERVICE_METRICS=${ENABLE_SERVICE_METRICS:-false}
      
      # Audit Configuration
      - AUDIT_TOOL_OPERATIONS=${AUDIT_TOOL_OPERATIONS:-true}
      
      # Session Management
      - ENFORCE_SESSION_OWNERSHIP=${ENFORCE_SESSION_OWNERSHIP:-true}
      
      # Database Configuration
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db
      
      # Multi-tenant Context
      - ENFORCE_TENANT_ISOLATION=${ENFORCE_TENANT_ISOLATION:-true}
    
    volumes:
      - ./backend:/app
    
    depends_on:
      - postgres
      - redis
```

### Railway Deployment

```bash
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./backend/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

# Environment variables set in Railway dashboard:
# USE_SERVICE_REGISTRY=true
# ENABLE_SERVICE_METRICS=false
# AUDIT_TOOL_OPERATIONS=true
# ENFORCE_SESSION_OWNERSHIP=true
# ENFORCE_TENANT_ISOLATION=true
```

### Vercel Configuration

```json
// vercel.json (if API routes exist)
{
  "env": {
    "USE_SERVICE_REGISTRY": "true",
    "ENABLE_SERVICE_METRICS": "false",
    "AUDIT_TOOL_OPERATIONS": "true"
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9",
      "maxDuration": 30
    }
  }
}
```

## Deployment Phases

### Phase 1: Initial Rollout (Week 1)

#### Pre-Deployment Checklist

- [ ] Database migrations applied
- [ ] Audit categories updated to include `TOOL_OPERATION`
- [ ] Feature flag set to `false` in all environments
- [ ] Monitoring dashboards configured
- [ ] Rollback procedure documented and tested

#### Deployment Steps

1. **Deploy with Flag Disabled**
   ```bash
   # Deploy code with feature flag off
   export USE_SERVICE_REGISTRY=false
   docker-compose up -d migration_backend
   ```

2. **Verify Legacy Operation**
   ```bash
   # Ensure existing tools still work
   curl -X POST http://localhost:8000/api/v1/discovery/flows \
     -H "Content-Type: application/json" \
     -d '{"test": "legacy_tools"}'
   ```

3. **Enable for Test Tenant**
   ```python
   # backend/app/core/feature_flags.py
   def is_service_registry_enabled(context: RequestContext) -> bool:
       """Gradual rollout by tenant"""
       test_tenants = ["test-client-id-1", "test-client-id-2"]
       
       if str(context.client_account_id) in test_tenants:
           return True
       
       return os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
   ```

4. **Monitor Test Tenants**
   ```sql
   -- Check audit logs for test tenants
   SELECT 
       COUNT(*) as operations,
       category,
       level,
       DATE(created_at) as date
   FROM audit_logs
   WHERE category = 'TOOL_OPERATION'
     AND context->>'client_account_id' IN ('test-client-id-1', 'test-client-id-2')
   GROUP BY category, level, date
   ORDER BY date DESC;
   ```

### Phase 2: Gradual Rollout (Week 2-3)

#### Progressive Enablement

```python
# backend/app/core/feature_flags.py
from datetime import datetime
import random

def is_service_registry_enabled(context: RequestContext) -> bool:
    """Progressive rollout strategy"""
    
    # Override for specific environments
    if os.getenv("FORCE_SERVICE_REGISTRY") == "true":
        return True
    
    # Rollout percentage (increase gradually)
    rollout_percentage = int(os.getenv("SERVICE_REGISTRY_ROLLOUT_PCT", "0"))
    
    # Consistent hashing for tenant (same tenant always gets same result)
    tenant_hash = hash(str(context.client_account_id))
    tenant_bucket = abs(tenant_hash) % 100
    
    return tenant_bucket < rollout_percentage
```

#### Rollout Schedule

| Day | Percentage | Action |
|-----|------------|--------|
| 1 | 0% | Deploy code, verify no impact |
| 2 | 5% | Enable for 5% of tenants |
| 3 | 10% | Monitor metrics, check errors |
| 4 | 25% | Quarter of traffic |
| 5 | 50% | Half of traffic |
| 6 | 75% | Majority of traffic |
| 7 | 100% | Full rollout |

### Phase 3: Full Production (Week 4)

#### Final Cutover

1. **Enable Globally**
   ```bash
   # Set in all environments
   export USE_SERVICE_REGISTRY=true
   export ENABLE_SERVICE_METRICS=true
   ```

2. **Remove Legacy Code** (After 1 week stable)
   ```python
   # Remove legacy tool implementations
   # Update imports to require service registry
   # Remove feature flag checks
   ```

## Monitoring and Observability

### Key Metrics

#### Service Registry Health

```sql
-- Service operation metrics
CREATE OR REPLACE VIEW service_metrics_hourly AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    service_name,
    operation,
    COUNT(*) as total_calls,
    AVG(duration_ms) as avg_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM service_operations
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), service_name, operation
ORDER BY hour DESC, service_name, operation;
```

#### Tool Operation Audit

```sql
-- Tool operation audit trail
CREATE OR REPLACE VIEW tool_operations_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    context->>'tool_name' as tool_name,
    context->>'agent_name' as agent_name,
    level,
    COUNT(*) as operation_count,
    AVG((context->>'duration_ms')::FLOAT) as avg_duration_ms,
    SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as error_count
FROM audit_logs
WHERE category = 'TOOL_OPERATION'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), 
         context->>'tool_name',
         context->>'agent_name',
         level
ORDER BY hour DESC;
```

### Monitoring Dashboards

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Service Registry Operations",
    "panels": [
      {
        "title": "Service Call Rate",
        "targets": [{
          "expr": "rate(service_operations_total[5m])"
        }]
      },
      {
        "title": "Service Latency P95",
        "targets": [{
          "expr": "histogram_quantile(0.95, service_operation_duration_seconds)"
        }]
      },
      {
        "title": "Tool Operation Errors",
        "targets": [{
          "expr": "sum(rate(tool_operations_errors_total[5m])) by (tool_name)"
        }]
      },
      {
        "title": "Session Ownership Violations",
        "targets": [{
          "expr": "sum(session_ownership_violations_total)"
        }]
      }
    ]
  }
}
```

### Alert Configuration

```yaml
# prometheus/alerts.yml
groups:
  - name: service_registry
    rules:
      - alert: HighServiceErrorRate
        expr: |
          sum(rate(service_operations_total{success="false"}[5m])) 
          / sum(rate(service_operations_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "Service error rate above 5%"
          
      - alert: ServiceLatencyHigh
        expr: |
          histogram_quantile(0.99, service_operation_duration_seconds) > 1.0
        for: 10m
        annotations:
          summary: "P99 latency above 1 second"
          
      - alert: SessionOwnershipViolation
        expr: |
          increase(session_ownership_violations_total[1h]) > 0
        annotations:
          summary: "Tool created own database session"
          severity: critical
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Tools Still Using AsyncSessionLocal

**Symptoms:**
- Errors about session ownership
- Audit logs show gaps
- Multi-tenant context missing

**Diagnosis:**
```bash
# Check for violations
grep -r "AsyncSessionLocal" backend/app/services/crewai_flows/tools/
grep -r "from app.core.database import AsyncSessionLocal" backend/app/services/
```

**Resolution:**
1. Identify violating tools
2. Refactor to use service registry
3. Add to CI guards

#### Issue: Service Registry Performance Impact

**Symptoms:**
- Latency increase > 10%
- Memory usage growth
- Slow service instantiation

**Diagnosis:**
```sql
-- Check service operation latency
SELECT 
    service_name,
    operation,
    AVG(duration_ms) as avg_ms,
    MAX(duration_ms) as max_ms,
    COUNT(*) as call_count
FROM service_operations
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY service_name, operation
ORDER BY avg_ms DESC;
```

**Resolution:**
1. Enable service caching in registry
2. Optimize service initialization
3. Consider connection pooling

#### Issue: Transaction Boundary Violations

**Symptoms:**
- Services committing transactions
- Deadlocks or lock timeouts
- Inconsistent data state

**Diagnosis:**
```bash
# Check for commit calls in services
grep -r "\.commit\(" backend/app/services/ --exclude-dir=tests
```

**Resolution:**
1. Remove commit() from services
2. Use flush() for ID generation
3. Let orchestrator manage transactions

### Emergency Procedures

#### Full Rollback

```bash
#!/bin/bash
# emergency-rollback.sh

echo "🚨 Initiating emergency rollback..."

# 1. Disable feature flag immediately
export USE_SERVICE_REGISTRY=false

# 2. Restart all services
docker-compose restart migration_backend

# 3. Verify rollback
curl http://localhost:8000/health

# 4. Check error rates
curl http://localhost:8000/api/v1/monitoring/agents/metrics

echo "✅ Rollback complete"
```

#### Partial Disable

```python
# backend/app/core/circuit_breaker.py
class ServiceRegistryCircuitBreaker:
    """Emergency circuit breaker for service registry"""
    
    def __init__(self):
        self.error_count = 0
        self.threshold = 100
        self.is_open = False
    
    def record_error(self):
        self.error_count += 1
        if self.error_count > self.threshold:
            self.is_open = True
            logger.critical("Service registry circuit breaker OPEN")
    
    def should_use_legacy(self) -> bool:
        return self.is_open or os.getenv("FORCE_LEGACY_TOOLS") == "true"
```

## Performance Tuning

### Service Registry Optimization

```python
# backend/app/services/service_registry_optimized.py
class OptimizedServiceRegistry(ServiceRegistry):
    """Performance-optimized registry"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        self._service_pool = {}  # Pre-warm common services
        self._metrics_buffer = []  # Batch metrics
    
    async def prewarm_services(self, service_classes: List[Type]):
        """Pre-instantiate commonly used services"""
        for service_class in service_classes:
            await self.get_service(service_class)
    
    async def flush_metrics(self):
        """Batch write metrics to avoid blocking"""
        if self._metrics_buffer:
            # Async write to metrics store
            asyncio.create_task(self._write_metrics_batch())
```

### Connection Pooling

```python
# backend/app/core/database.py
from sqlalchemy.pool import NullPool, QueuePool

def get_engine_with_pooling():
    """Optimized connection pooling for service registry"""
    return create_async_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,  # Increase for service registry
        max_overflow=40,
        pool_timeout=30,
        pool_pre_ping=True,  # Verify connections
        echo_pool=True  # Debug pool usage
    )
```

## Maintenance Procedures

### Weekly Tasks

- [ ] Review service operation metrics
- [ ] Check for session ownership violations
- [ ] Analyze tool operation audit logs
- [ ] Update rollout percentage if gradual
- [ ] Review error rates and alerts

### Monthly Tasks

- [ ] Performance baseline comparison
- [ ] Service consolidation review
- [ ] Legacy code removal planning
- [ ] Security audit of multi-tenant isolation
- [ ] Update documentation

### Quarterly Tasks

- [ ] Full architecture review
- [ ] Service boundary assessment
- [ ] Performance optimization sprint
- [ ] Disaster recovery drill
- [ ] Team training on service patterns

## Appendix

### A. Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| USE_SERVICE_REGISTRY | false | Enable service registry for tools |
| ENABLE_SERVICE_METRICS | false | Collect service operation metrics |
| AUDIT_TOOL_OPERATIONS | true | Audit all tool operations |
| ENFORCE_SESSION_OWNERSHIP | true | Prevent tools from creating sessions |
| ENFORCE_TENANT_ISOLATION | true | Strict multi-tenant context enforcement |
| SERVICE_REGISTRY_ROLLOUT_PCT | 0 | Percentage rollout (0-100) |
| FORCE_LEGACY_TOOLS | false | Emergency override to legacy |
| SERVICE_POOL_SIZE | 20 | Connection pool size |
| SERVICE_CACHE_TTL | 3600 | Service instance cache TTL (seconds) |

### B. SQL Migrations

```sql
-- V1: Add audit category for tools
ALTER TYPE audit_category ADD VALUE 'TOOL_OPERATION';

-- V2: Service operations metrics table
CREATE TABLE IF NOT EXISTS service_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    duration_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    flow_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_service_ops_created (created_at DESC),
    INDEX idx_service_ops_tenant (client_account_id, engagement_id),
    INDEX idx_service_ops_service (service_name, operation)
);

-- V3: Idempotency keys table (if needed)
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key_hash VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',
    
    INDEX idx_idempotency_expires (expires_at)
);
```

### C. Monitoring Queries

```sql
-- Daily health check
WITH metrics AS (
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as total_operations,
        AVG(duration_ms) as avg_duration,
        SUM(CASE WHEN success THEN 0 ELSE 1 END) as failures
    FROM service_operations
    WHERE created_at > NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
)
SELECT 
    date,
    total_operations,
    ROUND(avg_duration::numeric, 2) as avg_duration_ms,
    failures,
    ROUND((failures::FLOAT / total_operations * 100)::numeric, 2) as error_rate_pct
FROM metrics
ORDER BY date DESC;

-- Tenant isolation verification
SELECT 
    client_account_id,
    COUNT(DISTINCT engagement_id) as engagements,
    COUNT(*) as operations,
    COUNT(DISTINCT service_name) as services_used
FROM service_operations
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY client_account_id
ORDER BY operations DESC;
```

---

*Last Updated: 2025-01-13*
*Version: 1.0*
*Status: Production Ready*
*Contact: Platform Team*