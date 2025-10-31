# ADR-031: Enterprise Observability Architecture with Grafana Stack

## Status
Proposed (2025-10-30)

Supersedes: `config/docker/docker-compose.observability.yml` (OpenLIT-based stack), Jaeger usage (replaced by Tempo)
Related: ADR-006 (Master Flow Orchestrator), ADR-010 (Docker-First Development), ADR-012 (Flow Status Management Separation), ADR-024 (TenantMemoryManager), ADR-025 (Child Flow Service Migration)

## Context

### Problem Statement

The AI Modernize Migration Platform operates in an **enterprise-isolated Azure environment** with strict firewall controls and manual deployment processes. Current observability is severely limited:

1. **Azure Dev Environment (PRIMARY USE CASE)**
   - Azure VMs (Ubuntu) with Docker Compose deployment
   - Browser-based Bastion host (Azure Portal SSH)
   - CLI-only log access (`docker logs` via Bastion SSH)
   - Multiple containers (backend, frontend, postgres, redis)
   - DNS: `aiforceasses.cloudsmarthcl.com` (with port-based services)
   - **Enterprise firewall**: Blocks outbound to github.com, public OAuth providers
   - **Manual deployment**: Code copied via Bastion, no GitHub Actions
   - **Need**: Web UI for log aggregation, metrics, and traces accessible via DNS

2. **Railway Production Environment (OPTIONAL)**
   - Built-in log streaming in Railway UI
   - Real-time log search and filtering
   - 7-day retention included
   - Multi-container log aggregation
   - **Need**: Rich dashboards for LLM cost tracking, MFO flow lifecycle, agent performance (beyond basic logs)

3. **Local Development Environment (OPTIONAL)**
   - Easy Docker log access (`docker logs -f`)
   - Developers comfortable with CLI
   - **Need**: Optional web UI matching production stack for testing

### Current State

- Existing `docker-compose.observability.yml` uses OpenLIT stack (7+ containers)
- Heavy footprint: OpenLIT + Postgres + Redis + Jaeger + Prometheus + Grafana + OTel Collector
- Designed for production monitoring (not enterprise-isolated environments)
- Not environment-aware (same stack everywhere)
- No integration with existing LLM tracking (`llm_usage_logs` table)
- No MFO flow lifecycle dashboards (ADR-006, ADR-012)
- No TenantMemoryManager metrics (ADR-024)
- Uses Jaeger (project requested Tempo instead)

### Key Insights

1. **Azure dev environment is enterprise-isolated**:
   - Enterprise firewall blocks GitHub OAuth, external SaaS services
   - Manual deployment only (no CI/CD from GitHub Actions)
   - Browser-based Bastion access (SSH via Azure Portal)
   - DNS + port-based access pattern (`:9999` for Grafana)

2. **Existing monitoring infrastructure must be integrated**:
   - LLM usage tracking: `migration.llm_usage_logs` table (MANDATORY - CLAUDE.md)
   - Agent registry: 17 agents tracked in `agent_registry/managers/observability.py`
   - MFO flow lifecycle: `crewai_flow_state_extensions` + child flow tables (ADR-006, ADR-012)
   - TenantMemoryManager: `agent_discovered_patterns` (ADR-024)

3. **Railway production benefits from rich dashboards**:
   - Built-in logs are good for basic troubleshooting
   - Grafana dashboards provide value for cost analytics, agent performance, flow tracking
   - Optional deployment (not required, but valuable)

## Decision

**We will deploy Tier B observability stack (5 containers: Grafana + Loki + Tempo + Prometheus + Alloy)** with environment-based configuration and enterprise security constraints.

### Specific Architecture by Environment

#### Azure Dev (PRIMARY - REQUIRED)
```yaml
Stack: Grafana + Loki + Tempo + Prometheus + Alloy (5 containers - Tier B)
Purpose: Full observability (logs, metrics, traces) with web UI
Deployment: Docker Compose on Azure Ubuntu VM (manual deployment)
Access:
  - DNS: https://aiforceasses.cloudsmarthcl.com:9999
  - Bastion: Browser-based SSH via Azure Portal
  - NSG Rule: Port 9999 inbound (IP-restricted recommended)
Authentication:
  - Local admin auth (GitHub OAuth blocked by enterprise firewall)
  - Strong password (20+ chars, rotated every 90 days)
  - Azure AD integration (future enhancement if available)
Cost: Minimal (containers on existing VM, no new infrastructure)
```

#### Railway Prod (OPTIONAL - VALUABLE)
```yaml
Stack: Same Tier B stack (5 containers) OR Grafana Cloud (1 container)
Purpose: Rich dashboards for LLM costs, agent performance, flow tracking
Deployment: Docker Compose on Railway (if self-hosted) or Grafana Cloud
Access:
  - Self-hosted: Private Railway services, only Grafana public with OAuth
  - Grafana Cloud: Alloy on Railway, remote write to Grafana Cloud
Authentication:
  - GitHub OAuth (recommended for Railway - no firewall constraints)
  - Or local admin with strong password
Cost:
  - Self-hosted: ~$40-$300/month (5 services + volumes)
  - Grafana Cloud: ~$0-$20/month (free tier or low usage)
Decision: Defer to implementation phase based on cost/compliance
```

#### Local Dev (OPTIONAL - TESTING)
```yaml
Stack: Same Tier B stack (mirrors production)
Purpose: Test observability configs before Azure/Railway deployment
Deployment: docker-compose --profile observability up -d
Access: http://localhost:9999
Authentication: Local admin (password from .env.local, NOT committed to git)
Cost: $0 (local resources)
```

### Technology Stack (Tier B - Full Stack)

**Components**:
1. **Grafana** - Web UI, datasource configuration, dashboards
2. **Loki** - Log aggregation and storage (14-day retention, compaction enabled)
3. **Tempo** - Distributed tracing (7-day retention, HTTP-only queries) - **Replaces Jaeger**
4. **Prometheus** - Metrics TSDB (14-day retention)
5. **Alloy** - Unified collector (replaces Promtail + OTel Collector)

**Why This Stack**:
- Modern Grafana ecosystem (single vendor, tight integration)
- Replaces 7+ OpenLIT containers with 5 efficient containers
- Tempo instead of Jaeger (as requested)
- Alloy replaces both Promtail and OTel Collector (simplification)
- No external dependencies (ChromaDB, OpenLIT DB/Redis)
- HTTP-only operation (no WebSockets - Railway compatible)

**Configuration Details**:

- **Alloy**:
  - Docker log pipeline: Parses JSON logs, maps keys to labels (`client_account_id`, `engagement_id`, `flow_id`, `agent`, `phase`, `status`)
  - Redacts sensitive fields (passwords, API keys) before forwarding to Loki
  - OTLP receiver (4317/4318) routes traces → Tempo, metrics → Prometheus
  - Optional: Postgres/Redis integrations (Azure dev only, not Railway)

- **Loki**:
  - 14-day retention with compaction
  - Log redaction to avoid PII/secrets ingestion
  - Filesystem storage (Azure dev VM disk, Railway persistent volume)

- **Tempo**:
  - 7-day retention
  - HTTP query mode only (no WebSockets)
  - Disable Grafana live tail/streaming features

- **Prometheus**:
  - 14-day retention via `--storage.tsdb.retention.time=14d`
  - Scrape targets:
    - Azure dev: Can scrape Postgres/Redis metrics on VM
    - Railway: Use Railway native metrics (no scraping)
  - High cardinality warning: Limit tenant labels in metrics; use SQL dashboards for per-tenant analytics

**Removed**:
- OpenLIT dashboard + DB + Redis (heavy, separate ecosystem)
- Jaeger (replaced by Tempo)
- Separate Promtail and OTel Collector (replaced by Alloy)

### Integration with Existing Systems

#### LLM Usage Tracking (MANDATORY - CLAUDE.md lines 96-156)
- **Backend tracking**: LiteLLM callback at `app/services/litellm_tracking_callback.py`
  - Auto-tracks all CrewAI + direct LLM calls
  - Logs to `migration.llm_usage_logs` table
- **Frontend UI**: `/finops/llm-costs` dashboard (existing)
- **Grafana integration**:
  - Datasource: PostgreSQL (`migration_db`) - **read-only user required**
  - Query `migration.llm_usage_logs` directly
  - Dashboard panels:
    - Cost by model/provider/feature over time
    - Tokens by client_account_id and engagement_id
    - Top 10 most expensive LLM calls
    - Usage trends and cost forecasting
    - Panel linking to `/finops/llm-costs` frontend UI
  - SQL example:
    ```sql
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
  - Correlation with agent execution metrics (via Prometheus)
- **Why this matters**: MANDATORY per CLAUDE.md - all LLM calls MUST be tracked

#### Agent Registry Observability
- **Existing infrastructure**:
  - API: `/api/v1/observability/health` (`backend/app/api/v1/endpoints/observability.py`)
  - Manager: `backend/app/services/agent_registry/managers/observability.py`
  - 17 agents tracked across 9 phases (see README.md)
- **Grafana integration**:
  - Query backend API for agent health status
  - Display agent performance from `migration.agent_performance_analytics`
  - Dashboard: Agent Health Monitor (real-time task tracking)

#### MFO Flow Lifecycle (ADR-006, ADR-012)
- **Two-table pattern** (ADR-012):
  - Master: `migration.crewai_flow_state_extensions` (lifecycle: running/paused/completed)
  - Children: `discovery_flows`, `assessment_flows`, `collection_flows` (operational state)
- **Dashboard panels with SQL**:
  - **Master flows by status**:
    ```sql
    SELECT
      flow_status,
      COUNT(*) AS count,
      AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/60) AS avg_duration_minutes
    FROM migration.crewai_flow_state_extensions
    WHERE created_at > NOW() - INTERVAL '7 days'
    GROUP BY flow_status
    ORDER BY count DESC;
    ```
  - **Child phase progression by flow type**:
    ```sql
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
  - **Flow lifecycle duration** (creation → completion)
  - **Error rates by flow type** (discovery vs assessment vs collection)
  - **Per-tenant flow analytics** (client_account_id, engagement_id filters)

#### TenantMemoryManager (ADR-024)
- **Architecture**: TenantMemoryManager replaces CrewAI memory (disabled per ADR-024)
  - Uses PostgreSQL + pgvector (not ChromaDB)
  - Multi-tenant isolation (client_account_id, engagement_id scoping)
  - Storage: `migration.agent_discovered_patterns`
- **Metrics to implement** (Phase 4):
  - Add in `backend/app/services/crewai_flows/memory/tenant_memory_manager.py`:
    ```python
    # In retrieve_similar_patterns()
    tenant_memory_search_total = meter.create_counter(
        "tenant_memory.search.total",
        description="Total memory searches"
    )
    tenant_memory_search_duration = meter.create_histogram(
        "tenant_memory.search.duration_ms",
        description="Memory search latency"
    )
    tenant_memory_patterns_retrieved = meter.create_counter(
        "tenant_memory.patterns.retrieved",
        description="Patterns retrieved per search"
    )
    ```
  - Labels: `client_account_id`, `engagement_id`, `scope` (engagement/client/global)
- **Dashboard panels**:
  - **Pattern count by tenant**:
    ```sql
    SELECT
      client_account_id,
      engagement_id,
      pattern_type,
      COUNT(*) AS pattern_count
    FROM migration.agent_discovered_patterns
    GROUP BY 1,2,3
    ORDER BY pattern_count DESC;
    ```
  - **pgvector index usage** (optional, requires pg_stat_statements):
    ```sql
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
  - **Memory retrieval performance** (from Prometheus metrics)

## Consequences

### Positive
- **Azure Dev**: Web UI for logs/metrics/traces (solves CLI-only access pain)
- **Enterprise Compatible**: Local auth works within firewall constraints
- **Full Stack**: Tier B provides comprehensive observability (not just logs)
- **Integrated Monitoring**: LLM tracking, MFO flows, agent performance in one UI
- **Modern Stack**: Grafana ecosystem with Tempo (not Jaeger), Alloy (not Promtail + OTel)
- **Reduced Containers**: 5 containers (vs 7+ OpenLIT stack)
- **HTTP-Only**: Works on Railway (no WebSocket requirements)
- **Flexible Deployment**: Same stack across local, Azure, Railway

### Negative
- **Manual Deployment**: No CI/CD from GitHub (enterprise firewall limitation)
- **Local Auth Only**: No SSO integration initially (GitHub OAuth blocked)
- **Manual User Management**: Grafana users created manually (until Azure AD integration)
- **Password Rotation**: Requires manual process (no automated rotation)
- **OTel Instrumentation**: Requires code changes in agent execution paths
- **Railway Cost**: $40-$300/month if self-hosting (vs Grafana Cloud)

### Risks
- **Password Compromise**: Single admin password for Grafana
  - Mitigation: Strong password (20+ chars), NSG IP allowlist, 90-day rotation
- **Storage Growth**: Loki/Tempo/Prometheus volume exhaustion
  - Mitigation: Monitor disk usage, conservative retention policies, alerts at 80%
- **Enterprise Firewall Changes**: Outbound restrictions may block image pulls
  - Mitigation: Use Azure Container Registry (ACR) for image mirroring
- **No CI/CD**: Manual deployment increases human error risk
  - Mitigation: Document deployment procedures, consider Azure DevOps Pipelines
- **Azure AD Integration Failure**: May not be available within firewall
  - Mitigation: Test connectivity to Azure AD endpoints first

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)

**Docker Compose**:
- [ ] Create `docker-compose.observability.yml` (5 services: Grafana, Loki, Tempo, Prometheus, Alloy)
- [ ] Configure environment variables (.env.observability)
- [ ] Set Grafana port to 9999 (not 3001)
- [ ] Configure local admin auth (no GitHub OAuth due to firewall)
- [ ] Add to `migration_network`

**Configuration Files**:
- [ ] `config/docker/observability/alloy-config.yaml` (Docker logs → Loki, OTLP → Tempo/Prometheus)
- [ ] `config/docker/observability/loki-config.yaml` (14-day retention, compaction)
- [ ] `config/docker/observability/tempo-config.yaml` (7-day retention)
- [ ] `config/docker/observability/prometheus.yml` (14-day retention, scrape config)

**Grafana Provisioning**:
- [ ] `config/docker/observability/grafana/provisioning/datasources/loki.yaml`
- [ ] `config/docker/observability/grafana/provisioning/datasources/tempo.yaml`
- [ ] `config/docker/observability/grafana/provisioning/datasources/prometheus.yaml`
- [ ] `config/docker/observability/grafana/provisioning/datasources/postgres.yaml` (for LLM/MFO queries)

### Phase 2: Dashboard Creation (Week 2)

**Priority 1 Dashboards**:
- [ ] Application Logs (Loki queries, error filtering, container selection)
- [ ] LLM Usage Costs (PostgreSQL datasource, queries `llm_usage_logs`)
- [ ] MFO Flow Lifecycle (PostgreSQL datasource, master + child flows)
- [ ] Agent Health (PostgreSQL datasource, 17 agents from registry)

**Dashboard Files**:
- [ ] `config/docker/observability/grafana/dashboards/app-logs.json`
- [ ] `config/docker/observability/grafana/dashboards/llm-costs.json`
- [ ] `config/docker/observability/grafana/dashboards/mfo-flows.json`
- [ ] `config/docker/observability/grafana/dashboards/agent-health.json`

### Phase 3: Azure Deployment (Week 3)

**Azure NSG**:
- [ ] Add inbound rule: Port 9999, protocol TCP (IP-restricted to office IP recommended)
- [ ] Document NSG rule configuration

**VM Deployment**:
- [ ] SSH into Ubuntu VM via Azure Bastion
- [ ] Copy observability configs to VM
- [ ] Deploy: `docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d`
- [ ] Verify all 5 containers running
- [ ] Test access: `https://aiforceasses.cloudsmarthcl.com:9999`

**Security**:
- [ ] Generate strong Grafana admin password (20+ chars)
- [ ] Store password in Azure Key Vault (if available)
- [ ] Document password rotation policy (90 days)
- [ ] Test login and verify access restrictions

### Phase 4: Backend Instrumentation (Week 4 - Required for Metrics/Traces)

**OTel Integration**:
- [ ] Enable OTel in backend: Set `OTEL_SDK_DISABLED=false`
- [ ] Configure OTLP endpoints: `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://alloy:4318`
- [ ] Add `opentelemetry-instrument` to uvicorn startup
- [ ] Verify traces appear in Tempo

**Agent Metrics** (instrumentation points):
- [ ] `backend/app/services/child_flow_services/*` (phase execution)
- [ ] `backend/app/services/crewai_flows/executors/*` (agent run boundaries)
- [ ] `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` (agent checkout)

**Metrics to Add**:
- [ ] `agent_runs_total{agent, phase, outcome, client_account_id, engagement_id}`
- [ ] `agent_duration_ms` histogram with tenant labels
- [ ] TenantMemoryManager vector search counters/histograms

### Phase 5: Railway Deployment (Future - Optional)

**Decision Point**: Self-hosted vs Grafana Cloud
- [ ] Analyze log volumes and cost estimates
- [ ] Choose: Self-hosted (5 services) OR Grafana Cloud (Alloy only)
- [ ] If self-hosted: Deploy same stack with GitHub OAuth
- [ ] If Grafana Cloud: Configure Alloy remote write

## Alternatives Considered

### 1. OpenLIT Stack (Current) ❌
- **Why rejected**:
  - Heavy footprint (7+ containers: OpenLIT + DB + Redis + Jaeger + Prometheus + Grafana + OTel)
  - Separate ecosystem (not integrated with existing LLM/MFO/agent tracking)
  - Uses Jaeger (project requested Tempo)
  - No integration with CLAUDE.md mandatory LLM tracking
- **Migration**: Remove entirely, replace with Grafana stack

### 2. GitHub OAuth for Grafana ❌
- **Why rejected**: Enterprise firewall blocks outbound to github.com
- **Technical barrier**: OAuth callback requires github.com access
- **Alternative**: Local admin auth OR Azure AD (if available within firewall)

### 3. Logs-Only Stack (3 containers: Grafana + Loki + Alloy) ❌
- **Why rejected**: Project requested Tier B (full stack with metrics + traces)
- **Missing value**: No agent performance metrics, no distributed tracing
- **Decision**: Deploy full Tier B from start

### 4. GitHub Actions Deployment ❌
- **Why rejected**: Enterprise firewall blocks outbound to github.com
- **Technical barrier**: GitHub Actions runner needs internet access
- **Alternative**: Manual deployment OR Azure DevOps Pipelines (within firewall)

### 5. Grafana Cloud (Managed Service) ⚠️
- **Why NOT chosen for Azure dev**:
  - External SaaS requires firewall rule changes
  - Data leaves enterprise network (compliance risk)
- **Valid for Railway**: Consider in Phase 5 (if compliance allows)
- **Benefits**: No container management, automatic scaling, free tier
- **Tradeoffs**: Vendor lock-in, data egress, subscription cost

### 6. Azure Monitor + Log Analytics (Azure-Native) ⚠️
- **Why NOT chosen**:
  - Tightly couples to Azure (not portable to Railway/local)
  - Cost per GB ingestion (can be expensive)
  - Steep learning curve (Azure-specific query language)
  - Doesn't solve Railway observability needs
- **Valid use case**: If Azure is long-term dev platform only

## Cost Analysis

### Azure Dev (VM-Based Deployment)
```yaml
Infrastructure: Existing Ubuntu VM (no new compute)
Containers: 5 services on existing VM
Storage:
  - Loki: 14d × 1GB/day ≈ 14GB
  - Tempo: 7d × 200MB/day ≈ 1.4GB
  - Prometheus: 14d × 2GB/day ≈ 28GB
  - Total: ~45GB additional disk (Azure managed disk cost: ~$5-10/month)

Total Incremental Cost: ~$5-10/month (storage only)
Note: No new VM cost (containers on existing CNCoE-Ubuntu VM)
```

### Railway Prod (Self-Hosted Option)
```yaml
Services: 5 containers (Grafana, Loki, Tempo, Prometheus, Alloy)
Cost Estimate:
  - 5 services on starter plans: ~$25-100/month
  - Persistent volumes (45GB): ~$15-25/month
  - Total: ~$40-125/month (low usage) to ~$150-300/month (higher usage)

Assumptions:
  - Logs: 0.5-1.5 GB/day
  - Traces: 0.1-0.3 GB/day
  - Metrics: 5-15M samples/day
```

### Railway Prod (Grafana Cloud Option)
```yaml
Services: 1 container (Alloy only)
Cost Estimate:
  - Railway Alloy service: ~$5-20/month
  - Grafana Cloud free tier: $0/month (50GB logs, 50GB traces, 10K metrics)
  - OR Grafana Cloud paid: ~$20-50/month (if exceeds free tier)
  - Total: ~$5-70/month

Decision: Defer to Phase 5 based on actual usage
```

### Cost Comparison
```yaml
OpenLIT Stack (Current): 7+ containers + DB + Redis = High complexity
Grafana Stack (Proposed): 5 containers = Lower complexity

Azure Dev: ~$5-10/month incremental (storage only)
Railway Prod (if deployed): $40-300/month (self-hosted) OR $5-70/month (Grafana Cloud)
```

## Success Criteria

### Azure Dev
- [ ] Developers access logs via Grafana web UI at `https://aiforceasses.cloudsmarthcl.com:9999`
- [ ] All 4 containers (backend, frontend, postgres, redis) visible in Loki dashboard
- [ ] Error log filtering works (`ERROR|CRITICAL|Exception` regex)
- [ ] LLM usage dashboard shows cost by model/provider/tenant
- [ ] MFO flow lifecycle dashboard shows master + child flows with SQL queries
- [ ] Agent health dashboard shows all 17 agents
- [ ] **Access secured via local admin auth** (Azure AD future enhancement)
- [ ] **HTTPS enabled** (TLS terminated at nginx/App Gateway)
- [ ] Grafana uses read-only Postgres user (no superuser)

### Railway Prod (If Deployed)
- [ ] Grafana with GitHub OAuth reachable
- [ ] Dashboards render LLM/MFO/Agent panels
- [ ] **HTTP-only verified** (no WebSocket errors, live tail disabled)
- [ ] Loki/Tempo/Prometheus private (only Grafana public)
- [ ] Cost within expected range ($40-300/month self-hosted OR $5-70/month Grafana Cloud)

### Local Dev
- [ ] Optional observability stack starts with `docker-compose --profile observability up`
- [ ] Password from `.env.local`, NOT committed to git
- [ ] Developers comfortable with `docker logs` continue using CLI

## Security Requirements

### Azure Dev (Enterprise Firewall Constraints)
- **Authentication**:
  - Local admin auth (GitHub OAuth blocked by firewall)
  - Strong password: 20+ characters, mixed case/numbers/symbols
  - Password rotation: Every 90 days
  - Secret delivery: Pull from Azure Key Vault (if available) OR secure password manager
  - Future: Azure AD integration (if accessible within firewall)
- **Network**:
  - Azure NSG rule: Port 9999 inbound
  - Recommended: IP allowlist (office public IP only)
  - Alternative: Allow from Any (requires stronger password policy)
  - DNS: `https://aiforceasses.cloudsmarthcl.com:9999`
- **TLS**:
  - **HTTPS MANDATORY** (not optional)
  - Terminate TLS at nginx/Traefik reverse proxy OR Azure App Gateway
  - Use existing SSL certificate for `aiforceasses.cloudsmarthcl.com`
  - Do NOT run Grafana over plain HTTP in production
- **RBAC**:
  - Initial: Single admin account for SRE/engineering only
  - No tenant users in Grafana (admin-only access model)
  - Future options:
    - Manual user creation (Admin/Editor/Viewer roles)
    - Azure AD SSO (Phase 2 enhancement)
    - Grafana organizations for per-tenant isolation (if needed)
    - Label-based query restrictions (Grafana Enterprise feature)
- **Database Access**:
  - **Create read-only PostgreSQL user for Grafana**:
    ```sql
    CREATE USER grafana_readonly WITH PASSWORD '<strong-password>';
    GRANT CONNECT ON DATABASE migration_db TO grafana_readonly;
    GRANT USAGE ON SCHEMA migration TO grafana_readonly;
    GRANT SELECT ON migration.llm_usage_logs TO grafana_readonly;
    GRANT SELECT ON migration.crewai_flow_state_extensions TO grafana_readonly;
    GRANT SELECT ON migration.discovery_flows TO grafana_readonly;
    GRANT SELECT ON migration.assessment_flows TO grafana_readonly;
    GRANT SELECT ON migration.collection_flows TO grafana_readonly;
    GRANT SELECT ON migration.agent_discovered_patterns TO grafana_readonly;
    GRANT SELECT ON migration.agent_performance_analytics TO grafana_readonly;
    -- Optionally pg_stat_statements (if enabled)
    GRANT SELECT ON pg_stat_statements TO grafana_readonly;
    ```
  - **NO superuser access** for Grafana datasource
- **Access Control**:
  - Layer 1: Bastion host (browser-based SSH)
  - Layer 2: NSG (port 9999 + IP filtering)
  - Layer 3: TLS (HTTPS mandatory)
  - Layer 4: Grafana admin password

### Railway Prod (If Deployed)
- **Authentication**:
  - GitHub OAuth (recommended - no firewall constraints)
  - Organization restrictions (allowed orgs only)
  - Disable anonymous signup
- **Network**:
  - Loki/Tempo/Prometheus: Private Railway services (no public routes)
  - Grafana: Public with OAuth
  - Alloy: Private (OTLP endpoints internal only)
- **TLS**: HTTPS by default (Railway)
- **RBAC**:
  - Admin-only access for SRE/engineering
  - Per-user access via GitHub OAuth
  - Admin/Editor/Viewer roles
  - Optional: Grafana organizations for multi-tenant isolation (if per-tenant access needed)
- **Secret Management**:
  - Use Railway project variables for passwords
  - Rotate quarterly
- **Database Access**:
  - Same read-only user pattern as Azure dev
  - NO superuser access for Grafana datasource

## Environment Configuration

### Azure Dev (.env.observability)
```bash
# Grafana Authentication (Local Admin)
GRAFANA_ADMIN_PASSWORD=<GENERATE_STRONG_PASSWORD_20_CHARS>
# Generate with: openssl rand -base64 32

# Azure AD Integration (Optional - Phase 2)
AZURE_AD_ENABLED=false
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_AUTH_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize
AZURE_AD_TOKEN_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token

# PostgreSQL (for LLM/MFO dashboards)
POSTGRES_PASSWORD=<from-existing-.env>

# Retention Policies
LOKI_RETENTION_DAYS=14
TEMPO_RETENTION_DAYS=7
PROMETHEUS_RETENTION_DAYS=14
```

### Railway Prod (.env.railway - If Deployed)
```bash
# GitHub OAuth (Recommended)
GF_AUTH_GITHUB_ENABLED=true
GF_AUTH_GITHUB_CLIENT_ID=<from-railway-vars>
GF_AUTH_GITHUB_CLIENT_SECRET=<from-railway-vars>
GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS=YourGitHubOrg

# OR Local Admin (If OAuth not desired)
GRAFANA_ADMIN_PASSWORD=<strong-password>

# Backend OTel (Enable traces/metrics)
OTEL_SDK_DISABLED=false
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://alloy:4318
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://alloy:4318
```

### Local Dev (.env.local - Optional)
```bash
# Local testing only - DO NOT commit this file
GRAFANA_ADMIN_PASSWORD=<strong-password-for-local-dev>
# Generate with: openssl rand -base64 20

# Postgres read-only user (same as Azure/Railway)
POSTGRES_GRAFANA_USER=grafana_readonly
POSTGRES_GRAFANA_PASSWORD=<from-local-postgres>

# Reduced retention for local dev
LOKI_RETENTION_DAYS=7
TEMPO_RETENTION_DAYS=3
PROMETHEUS_RETENTION_DAYS=7

# Enable with: docker-compose --profile observability up
```

## References

### Related ADRs
- **ADR-010**: Docker-First Development Mandate
- **ADR-024**: TenantMemoryManager Architecture (PostgreSQL + pgvector)

### Documentation
- `config/docker/docker-compose.observability.azure.yml` - Azure dev stack
- `config/docker/observability/alloy-config.yaml` - Alloy configuration
- `config/docker/observability/loki-config.yaml` - Loki retention policies
- `config/docker/observability/grafana/provisioning/` - Datasources + dashboards

### Implementation
- `backend/app/services/litellm_tracking_callback.py` - LLM usage tracking
- `backend/app/api/v1/endpoints/observability.py` - Observability API
- `backend/app/services/agent_registry/` - Agent health monitoring

## Decision Rationale

After comprehensive analysis considering enterprise constraints:

1. **Enterprise firewall requires local auth** - GitHub OAuth blocked, manual deployment only
2. **Tier B provides comprehensive value** - Not just logs, but metrics/traces for LLM costs, agent performance, MFO flows
3. **Azure dev is primary use case** - CLI-only access is poor DX, DNS + port access (`:9999`) is standard pattern
4. **Integration with existing tracking is critical** - LLM usage logs (MANDATORY per CLAUDE.md), MFO flows (ADR-006), TenantMemoryManager (ADR-024)
5. **Grafana stack over OpenLIT** - Modern (Tempo not Jaeger, Alloy not Promtail+OTel), integrated, fewer containers (5 vs 7+)
6. **Railway deployment is optional but valuable** - Built-in logs sufficient for troubleshooting, but dashboards add value for analytics
7. **HTTP-only operation required** - Railway has no WebSocket support, Grafana stack works without them

**Therefore, deploying Tier B Grafana stack with local auth to Azure dev (required) and optionally Railway prod (valuable) is the optimal solution.**

## Approval

- [ ] Engineering Lead Review
- [ ] DevOps Team Review
- [ ] Azure Cost Approval
- [ ] Security Review (OAuth, networking)

---

**Date**: 2025-10-30
**Author**: Claude Code (CC)
**Reviewers**: TBD
