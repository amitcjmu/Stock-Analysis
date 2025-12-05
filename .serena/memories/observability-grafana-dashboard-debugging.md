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

**IMPORTANT**: BYPASSRLS is NOT persistent across container restarts. Must be reapplied after PostgreSQL container restarts.

---

## CRITICAL: "origin not allowed" 403 Error (Added 2025-12-04)

**Symptom**: Grafana shows "origin not allowed" with 403 status. Dashboards fail to load data.

**Root Cause**: Docker Compose variable substitution happens at PARSE TIME, not runtime.

The docker-compose.observability.yml has:
```yaml
environment:
  - GF_SERVER_ROOT_URL=${GF_SERVER_ROOT_URL:-http://localhost:9999}
  - GF_SERVER_DOMAIN=${GF_SERVER_DOMAIN:-localhost}
```

The `${VAR:-default}` syntax uses shell environment variables at docker-compose parse time. Even with `env_file:` directive, those variables are only loaded INTO the container, NOT available for docker-compose substitution.

**Verification**:
```bash
# Check container env (will show WRONG values)
sudo docker exec migration_grafana printenv | grep GF_SERVER
# Shows: GF_SERVER_ROOT_URL=http://localhost:9999 (WRONG!)
# Shows: GF_SERVER_DOMAIN=localhost (WRONG!)

# Check .env.observability file (has CORRECT values)
cat .env.observability | grep GF_SERVER
# Shows: GF_SERVER_ROOT_URL=https://aiforceassessgrafana.cloudsmarthcl.com/
# Shows: GF_SERVER_DOMAIN=aiforceassessgrafana.cloudsmarthcl.com
```

**Fix**: Use `--env-file` flag to load variables for docker-compose substitution:
```bash
cd ~/AIForce-Assess/config/docker
sudo docker compose --env-file .env.observability -f docker-compose.observability.yml up -d --force-recreate grafana
```

**After Fix - Verify**:
```bash
sudo docker exec migration_grafana printenv | grep GF_SERVER
# Should show:
# GF_SERVER_ROOT_URL=https://aiforceassessgrafana.cloudsmarthcl.com/
# GF_SERVER_DOMAIN=aiforceassessgrafana.cloudsmarthcl.com
```

---

## Problem: PostgreSQL GROUP BY SQL Errors

**Symptom**: Dashboard panel shows SQL error: `column "X" must appear in the GROUP BY clause or be used in an aggregate function`

**Root Cause**: PostgreSQL requires ALL non-aggregated columns in SELECT to be in GROUP BY clause.

**Fix Pattern**:
```sql
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

---

## CORRECT Observability Stack Startup Procedure (Azure)

### Complete Startup Command
```bash
cd ~/AIForce-Assess/config/docker

# Start ALL observability services with correct env file
sudo docker compose --env-file .env.observability -f docker-compose.observability.yml up -d

# Apply BYPASSRLS (required after every PostgreSQL restart)
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "ALTER ROLE grafana_readonly BYPASSRLS;"

# Verify Grafana environment
sudo docker exec migration_grafana printenv | grep GF_SERVER
# Should show Azure domain, NOT localhost
```

### Why --env-file is REQUIRED

1. `env_file:` in docker-compose.yml → loads vars INTO container (runtime)
2. `${VAR:-default}` in environment section → needs vars at PARSE TIME
3. `--env-file` flag → loads vars for docker-compose substitution (parse time)

Without `--env-file`, Grafana gets `localhost` defaults instead of Azure domain values.

### After Restart Checklist
1. [ ] Start observability stack with `--env-file` flag
2. [ ] Apply BYPASSRLS to grafana_readonly user
3. [ ] Verify GF_SERVER_* env vars are correct (not localhost)
4. [ ] Test dashboard loads with data

---

## Available Grafana Dashboards (Updated 2025-12-05)

| Dashboard | UID | Description |
|-----------|-----|-------------|
| **LLM Usage Costs** | `llm-costs` | Cost by model/provider, total cost gauge, top expensive calls |
| **MFO Flow Lifecycle** | `mfo-flows` | Master flows by status, child phase progression, flow creation rate |
| **Agent Health** | `agent-health` | Agent performance summary, task execution, success rates |
| **Agent Activity** | `agent-activity` | Agent calls over time, token usage, response times |
| **Agent Task History** | `agent-task-history` | **NEW** - Detailed per-task execution, agent breakdown within flows |
| **Feature Usage Analytics** | `feature-usage` | **NEW** - Feature usage over time, flow type distribution |
| **Distributed Tracing** | `distributed-tracing` | **NEW** - Tempo traces, service graph, latency analysis |
| **System Alerts & Health** | `system-alerts` | **NEW** - Health metrics with thresholds, alert status |
| **CrewAI Flow Execution** | `crewai-flows` | Flows by type, tokens per flow type |
| **App Logs Enhanced** | `app-logs-enhanced` | Loki-based logs with agent decisions, errors, phase transitions |
| **App Logs** | `app-logs` | Basic container log view |

### Dashboard Data Sources

- **PostgreSQL** (`postgres`): `llm_usage_logs`, `agent_task_history`, `agent_performance_daily`, `crewai_flow_state_extensions`, child flow tables
- **Loki** (`Loki`): Container logs with labels (container, level, flow_id, agent, phase)
- **Tempo** (`Tempo`): Distributed traces (requires backend OTel instrumentation)

---

## Search Keywords

grafana, observability, dashboard, no data, RLS, row level security, BYPASSRLS, grafana_readonly, env_file, --env-file, GROUP BY, PostgreSQL, time range, origin not allowed, 403, localhost, azure, docker-compose, agent task history, feature usage, distributed tracing, system alerts
