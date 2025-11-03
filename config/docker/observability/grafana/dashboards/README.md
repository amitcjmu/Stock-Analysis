# Grafana Dashboards

This directory contains dashboard JSON files for automatic provisioning.

## Phase 2 Implementation (Issue #878)

Create the following dashboard JSON files:

### 1. app-logs.json
**Purpose**: Application log viewing and filtering
**Datasource**: Loki
**Panels**:
- Log stream with search
- Log volume time series
- Error rate chart
- Top errors table

**Example LogQL queries**:
```
{container="migration_backend"} |= "ERROR"
{container=~"migration_.*"} | json | level="error"
{service="backend"} | json | client_account_id="1"
```

### 2. llm-costs.json
**Purpose**: LLM usage cost tracking and forecasting
**Datasource**: PostgreSQL
**Panels**:
- Cost by model/provider over time (time series)
- Token consumption by tenant (table)
- Top 10 expensive calls (bar chart)
- Cost forecasting (prediction)
- Link to `/finops/llm-costs` frontend UI

**Example SQL queries** (from ADR-031):
```sql
-- Cost by model/provider
SELECT
  date_trunc('day', created_at) AS time,
  model_name,
  provider,
  feature_context,
  client_account_id,
  engagement_id,
  SUM(total_cost_usd) AS cost_usd,
  SUM(input_tokens) AS input_tokens,
  SUM(output_tokens) AS output_tokens
FROM migration.llm_usage_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY 1,2,3,4,5,6
ORDER BY cost_usd DESC;
```

### 3. mfo-flows.json
**Purpose**: Master Flow Orchestrator lifecycle tracking
**Datasource**: PostgreSQL
**Panels**:
- Master flows by status (pie chart)
- Flow duration histogram
- Child phase progression (stacked bar)
- Error rate by flow type (time series)
- Per-tenant flow counts (table)

**Example SQL queries** (from ADR-031):
```sql
-- Master flows by status
SELECT
  flow_status,
  COUNT(*) AS count,
  AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/60) AS avg_duration_minutes
FROM migration.crewai_flow_state_extensions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY flow_status
ORDER BY count DESC;

-- Child phase progression
SELECT
  'discovery' AS flow_type,
  current_phase,
  client_account_id,
  engagement_id,
  COUNT(*) AS count
FROM migration.discovery_flows
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1,2,3,4
UNION ALL
SELECT
  'assessment',
  current_phase,
  client_account_id,
  engagement_id,
  COUNT(*)
FROM migration.assessment_flows
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1,2,3,4
ORDER BY flow_type, count DESC;
```

### 4. agent-health.json
**Purpose**: Agent performance and health monitoring
**Datasource**: PostgreSQL + Prometheus (Phase 4)
**Panels**:
- Agent success/failure rates (gauge)
- Agent execution duration (histogram)
- TenantMemoryManager search performance (time series)
- Pattern count by tenant (table)
- Agent registry status (stat)

**Example SQL queries** (from ADR-031):
```sql
-- Pattern count by tenant
SELECT
  client_account_id,
  engagement_id,
  pattern_type,
  COUNT(*) AS pattern_count
FROM migration.agent_discovered_patterns
GROUP BY 1,2,3
ORDER BY pattern_count DESC;

-- pgvector index usage (optional)
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%agent_discovered_patterns%'
  AND query LIKE '%<->%'  -- pgvector similarity operator
ORDER BY total_exec_time DESC
LIMIT 10;
```

## Creating Dashboards

### Option 1: Grafana UI (Recommended for initial setup)
1. Access Grafana: http://localhost:9999 (or Azure URL)
2. Login with admin credentials from `.env.observability`
3. Create → Dashboard → Add visualization
4. Select datasource (Loki/PostgreSQL/Prometheus)
5. Write query and configure panel
6. Save dashboard
7. Share → Export → Save to file
8. Copy JSON to this directory (`dashboards/app-logs.json`)
9. Restart Grafana: `docker-compose restart grafana`

### Option 2: Copy from Templates
Dashboard templates will be provided in Phase 2 implementation.

### Option 3: Grafonnet (Code-based)
Use Jsonnet library for dashboard-as-code:
```bash
# Install grafonnet
git clone https://github.com/grafana/grafonnet

# Write dashboard.jsonnet
local grafonnet = import 'grafonnet/grafana.libsonnet';
local dashboard = grafonnet.dashboard;

# Generate JSON
jsonnet -J grafonnet dashboard.jsonnet > app-logs.json
```

## Dashboard Variables

Create template variables for filtering:
- `$client_account_id`: Filter by tenant
- `$engagement_id`: Filter by engagement
- `$time_range`: Time range selector
- `$container`: Filter logs by container
- `$agent`: Filter by agent name

## Best Practices

1. **Use datasource UIDs**: Reference datasources by UID (e.g., `"datasource": {"uid": "postgres"}`)
2. **Add documentation**: Use text panels to explain metrics
3. **Set appropriate refresh**: Use 30s-5m refresh for dashboards
4. **Use variables**: Make dashboards filterable by tenant
5. **Add links**: Link related dashboards (Logs → Traces → Metrics)
6. **Export regularly**: Version control dashboard JSON in git

## Testing Dashboards

1. Verify SQL queries return data:
   ```bash
   docker exec -it migration_postgres psql -U postgres -d migration_db
   # Run SQL queries from examples above
   ```

2. Check Grafana logs for errors:
   ```bash
   docker logs migration_grafana -f
   ```

3. Test dashboard with real data:
   - Trigger LLM calls (use `/finops/llm-costs` UI)
   - Create test flows (use MFO API)
   - Check agent execution (use agent registry API)

## Troubleshooting

**Dashboard not appearing**:
- Check JSON syntax with `jq . dashboard.json`
- Restart Grafana: `docker-compose restart grafana`
- Check Grafana logs: `docker logs migration_grafana`

**Query errors**:
- Verify datasource connection in Grafana UI
- Test SQL in psql/Postgres client
- Check read-only user permissions

**Slow queries**:
- Add indexes to frequently queried columns
- Limit time range with `$__timeFilter(created_at)`
- Use aggregation instead of raw data

## References

- ADR-031: Lines 336-407 (Phase 2 implementation plan)
- Issue #878: Grafana Stack Observability Implementation
- Grafana docs: https://grafana.com/docs/grafana/latest/dashboards/
