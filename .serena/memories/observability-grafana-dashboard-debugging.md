# Grafana Dashboard Debugging - Observability Stack

**Last Updated**: 2025-12-04

## Problem: Dashboard Shows "No Data" Despite Working Backend

**Symptom**: Grafana dashboards appear broken but backend logs show data exists.

**Root Cause Pattern**: Default time ranges don't match actual data timestamps.

**Solution**:
```json
// In Grafana dashboard JSON (e.g., llm-costs.json):
"time": {
  "from": "now-30d",  // Was: "now-24h" - too narrow
  "to": "now"
}
```

**When to Check**:
- Dashboard shows "No Data" but database has records
- Check `SELECT MAX(created_at) FROM table` to find latest data timestamp
- Adjust time range to encompass actual data

---

## Problem: PostgreSQL RLS Blocking Grafana Queries (Added 2025-12-04)

**Symptom**: PostgreSQL queries return 0 rows for `grafana_readonly` user but full data for `postgres` user. Dashboard shows "No data" even with correct time ranges.

**Root Cause**: Row Level Security (RLS) is enabled on tables and `grafana_readonly` user lacks `BYPASSRLS` attribute.

**Verification**:
```sql
-- Check RLS status
SELECT relname, relrowsecurity FROM pg_class WHERE relname = 'crewai_flow_state_extensions';
-- If relrowsecurity = t, RLS is enabled

-- Check if grafana_readonly can bypass RLS
SELECT rolname, rolbypassrls FROM pg_roles WHERE rolname = 'grafana_readonly';
-- If rolbypassrls = f, user CANNOT bypass RLS

-- Test query as both users
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT COUNT(*) FROM migration.crewai_flow_state_extensions;"
-- Returns: 226 rows

sudo docker exec migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.crewai_flow_state_extensions;"
-- Returns: 0 rows (if BYPASSRLS is missing!)
```

**Fix**:
```bash
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "ALTER ROLE grafana_readonly BYPASSRLS;"
```

**Deployment Note**: Include in PostgreSQL user setup for all environments:
```sql
CREATE USER grafana_readonly WITH PASSWORD '<password>';
GRANT USAGE ON SCHEMA migration TO grafana_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA migration TO grafana_readonly;
ALTER ROLE grafana_readonly BYPASSRLS;  -- CRITICAL!
```

---

## Problem: PostgreSQL Password Empty in Grafana Container (Added 2025-12-04)

**Symptom**: Grafana cannot connect to PostgreSQL datasource. `POSTGRES_GRAFANA_PASSWORD` environment variable is empty inside container.

**Root Cause**: Docker Compose doesn't automatically load `.env.observability` file.

**Verification**:
```bash
docker exec migration_grafana printenv POSTGRES_GRAFANA_PASSWORD
# If empty, env file not loaded
```

**Fix**: Add `env_file` directive to `docker-compose.observability.yml`:
```yaml
services:
  grafana:
    image: grafana/grafana:10.2.0
    env_file:
      - .env.observability   # <-- Add this
    # ... rest of config
```

**Apply to all observability services**: grafana, loki, tempo, prometheus

**Alternative Fix** (runtime, doesn't persist):
```bash
sudo docker-compose -f docker-compose.observability.yml --env-file .env.observability up -d grafana
```

---

## Problem: PostgreSQL GROUP BY SQL Errors (Added 2025-12-04)

**Symptom**: Dashboard panel shows SQL error: `column "X" must appear in the GROUP BY clause or be used in an aggregate function`

**Root Cause**: PostgreSQL requires ALL non-aggregated columns in SELECT to be in GROUP BY clause. Dashboard JSON queries often miss columns.

**Example Error**:
```
column "agent_performance_daily.agent_name" must appear in the GROUP BY clause
```

**Fix Pattern**:
```sql
-- WRONG - agent_name selected but not grouped
SELECT
  date_trunc('hour', created_at) AS time,
  agent_name,
  AVG(avg_duration_seconds) AS duration_sec
FROM migration.agent_performance_daily
WHERE $__timeFilter(created_at)
GROUP BY 1    -- Only groups by time
ORDER BY 1;

-- CORRECT - all non-aggregated columns in GROUP BY
SELECT
  date_trunc('hour', created_at) AS time,
  agent_name,
  AVG(avg_duration_seconds) AS duration_sec
FROM migration.agent_performance_daily
WHERE $__timeFilter(created_at)
GROUP BY 1, agent_name    -- Groups by time AND agent_name
ORDER BY 1;
```

**Dashboard Files to Check**: `agent-health.json`, `agent-activity.json`

---

## Problem: Negative Flow Durations in Metrics

**Symptom**: `updated_at` timestamp BEFORE `created_at` causing impossible negative durations.

**Root Cause**: Child entity creation copying parent's old timestamps:
```python
# WRONG - Copies old timestamps from parent
child_flow = ChildFlow(
    created_at=parent_flow.created_at,  # Old time
    updated_at=parent_flow.updated_at   # Even older!
)
```

**Fix - Let SQLAlchemy Defaults Work**:
```python
# CORRECT - Omit timestamps, use database defaults
child_flow = ChildFlow(
    # created_at and updated_at omitted
    # SQLAlchemy model has server_default=func.now()
)
```

**When to Apply**: Any entity creation that derives from existing records.

---

## Problem: LiteLLM Callbacks Not Firing

**Symptom**: LLM calls execute but tracking callback never invoked.

**Root Cause**: Using deprecated `litellm.callbacks` instead of modern callback lists.

**Fix**:
```python
# WRONG - Legacy API
litellm.callbacks = [callback_instance]

# CORRECT - Modern API (LiteLLM 1.72+)
if not hasattr(litellm, 'success_callback') or litellm.success_callback is None:
    litellm.success_callback = []
litellm.success_callback.append(callback_instance)

if not hasattr(litellm, 'failure_callback') or litellm.failure_callback is None:
    litellm.failure_callback = []
litellm.failure_callback.append(callback_instance)
```

**Key Pattern**: Always APPEND to preserve existing callbacks (e.g., DeepInfra fixes).

---

## Grafana Pie Chart Field Naming

**Problem**: Pie chart only shows one category despite query returning multiple.

**Root Cause**: Grafana expects specific field names for pie chart data.

**Fix**:
```sql
-- WRONG - Generic names
SELECT flow_type, COUNT(*) AS count
FROM table GROUP BY flow_type;

-- CORRECT - Grafana-friendly names
SELECT
  flow_type AS metric,      -- Grafana recognizes "metric"
  COUNT(*)::float AS value  -- Grafana recognizes "value"
FROM table
GROUP BY flow_type
ORDER BY value DESC;
```

---

## Observability Stack Deployment Checklist

When deploying to a new environment (Azure, Staging, Prod):

### 1. PostgreSQL User Setup
```bash
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "
CREATE USER grafana_readonly WITH PASSWORD '<secure-password>';
GRANT USAGE ON SCHEMA migration TO grafana_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA migration TO grafana_readonly;
ALTER ROLE grafana_readonly BYPASSRLS;
"
```

### 2. Environment File
```bash
# Required variables in .env.observability:
GRAFANA_ADMIN_PASSWORD=<openssl rand -base64 32>
POSTGRES_GRAFANA_PASSWORD=<same-as-above>

# For Azure Front Door:
GF_LIVE_ALLOWED_ORIGINS=https://<your-domain>
GF_SECURITY_CSRF_TRUSTED_ORIGINS=https://<your-domain>
```

### 3. Start Stack
```bash
cd config/docker
sudo docker-compose -f docker-compose.observability.yml --env-file .env.observability up -d
```

### 4. Verify
```bash
# Check containers
sudo docker ps | grep migration_

# Verify password loaded
docker exec migration_grafana printenv POSTGRES_GRAFANA_PASSWORD

# Test grafana_readonly access
sudo docker exec migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.crewai_flow_state_extensions;"
# Should return actual count, NOT 0
```

---

## Search Keywords

grafana, observability, dashboard, no data, RLS, row level security, BYPASSRLS, grafana_readonly, env_file, GROUP BY, PostgreSQL, time range, alloy, loki, tempo, prometheus
