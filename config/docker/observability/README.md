# Grafana Observability Stack

**Architecture**: ADR-031
**Status**: Phase 1 & 2 Complete (Infrastructure + Dashboards)
**Tier**: B (Full Stack - Logs, Metrics, Traces)

## Overview

This directory contains the complete Grafana observability stack for the AI Modernize Migration Platform. It replaces the OpenLIT-based stack (7+ containers) with a modern, efficient 5-container solution.

### Technology Stack

1. **Grafana** - Web UI, datasource configuration, dashboards (Port 9999)
2. **Loki** - Log aggregation and storage (14-day retention)
3. **Tempo** - Distributed tracing (7-day retention, replaces Jaeger)
4. **Prometheus** - Metrics TSDB (14-day retention)
5. **Alloy** - Unified collector (replaces Promtail + OTel Collector)

## Quick Start

### Local Development (Optional)

```bash
# 1. Copy environment template
cp config/docker/.env.observability.template config/docker/.env.observability

# 2. Generate strong password
openssl rand -base64 32

# 3. Edit .env.observability
#    - Set GRAFANA_ADMIN_PASSWORD
#    - Set POSTGRES_GRAFANA_PASSWORD
#    - Keep OTEL_SDK_DISABLED=true (Phase 4 only)

# 4. Create Postgres read-only user
docker exec -i migration_postgres psql -U postgres -d migration_db < config/docker/observability/create-grafana-user.sql

# 5. Start observability stack
cd config/docker
docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d

# 6. Access Grafana
open http://localhost:9999
# Login: admin / <GRAFANA_ADMIN_PASSWORD>

# 7. View dashboards
#    - Application Logs (Loki)
#    - LLM Usage Costs (PostgreSQL)
#    - MFO Flow Lifecycle (PostgreSQL)
#    - Agent Health (PostgreSQL + Prometheus)
```

### Azure Dev Environment (PRIMARY)

**Prerequisites**:
- Azure VM (Ubuntu) with Docker Compose
- Browser-based Bastion access (Azure Portal SSH)
- NSG rule for port 9999 (IP-restricted recommended)
- SSL certificates for HTTPS

```bash
# 1. SSH into Azure VM via Bastion
#    Azure Portal → CNCoE-Ubuntu → Connect → Bastion

# 2. Copy observability configs to VM
#    (SCP or git pull to /path/to/migrate-ui-orchestrator)

# 3. Generate and configure secrets
openssl rand -base64 32  # For Grafana admin password
openssl rand -base64 32  # For Postgres Grafana user

# 4. Edit .env.observability
nano config/docker/.env.observability
#    - Set GRAFANA_ADMIN_PASSWORD
#    - Set POSTGRES_GRAFANA_PASSWORD
#    - Set AZURE_AD_* vars if available

# 5. Create Postgres read-only user
docker exec -i migration_postgres psql -U postgres -d migration_db < config/docker/observability/create-grafana-user.sql

# 6. Deploy observability stack
cd config/docker
docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d

# 7. Verify all 5 containers running
docker ps | grep -E "grafana|loki|tempo|prometheus|alloy"

# 8. Access Grafana
#    https://aiforceasses.cloudsmarthcl.com:9999
#    Login: admin / <GRAFANA_ADMIN_PASSWORD>

# 9. Configure Azure NSG (if not already done)
#    Add inbound rule:
#      - Port: 9999
#      - Protocol: TCP
#      - Source: <office-public-ip> (or Any)
#      - Priority: 310
#      - Name: Allow-Grafana-9999
```

## Directory Structure

```
observability/
├── README.md                          # This file
├── docker-compose.observability.yml   # 5 services definition
├── .env.observability.template        # Environment template
├── alloy-config.yaml                  # Alloy collector config
├── loki-config.yaml                   # Loki retention + storage
├── tempo-config.yaml                  # Tempo retention + HTTP-only
├── prometheus.yml                     # Prometheus scrape config
├── create-grafana-user.sql            # Read-only Postgres user
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yaml       # Loki, Tempo, Prometheus, PostgreSQL
│   │   └── dashboards/
│   │       └── dashboards.yaml        # Auto-load dashboards
│   └── dashboards/
│       ├── app-logs.json              # Application logs (Loki)
│       ├── llm-costs.json             # LLM usage costs (PostgreSQL)
│       ├── mfo-flows.json             # MFO flow lifecycle (PostgreSQL)
│       └── agent-health.json          # Agent health (PostgreSQL + Prometheus)
├── data/                              # Runtime data (gitignored)
│   ├── .gitkeep
│   ├── grafana/                       # Grafana SQLite DB
│   ├── loki/                          # Log storage
│   ├── tempo/                         # Trace storage
│   ├── prometheus/                    # Metrics TSDB
│   └── alloy/                         # Alloy state
└── ssl/                               # SSL certificates (gitignored)
    ├── grafana.crt
    └── grafana.key
```

## Dashboards

### 1. Application Logs (Loki)
- **Purpose**: View logs from all containers with filtering
- **Datasource**: Loki
- **Panels**:
  - Log rate by container
  - All application logs (with search)
  - Error logs (ERROR|EXCEPTION|CRITICAL|FATAL)
- **Variables**:
  - Container selector (multi-select)
  - Search filter (text box)

### 2. LLM Usage Costs (PostgreSQL)
- **Purpose**: Track LLM costs per CLAUDE.md mandatory requirement
- **Datasource**: PostgreSQL (`migration.llm_usage_logs`)
- **Panels**:
  - Cost by model over time
  - Total cost gauge
  - Cost by provider (pie chart)
  - Top 100 expensive LLM calls (table)
  - Calls by feature context
- **Integration**: Links to `/finops/llm-costs` frontend UI

### 3. MFO Flow Lifecycle (PostgreSQL)
- **Purpose**: Monitor Master Flow Orchestrator (ADR-006)
- **Datasource**: PostgreSQL (`crewai_flow_state_extensions` + child flows)
- **Panels**:
  - Master flows by status (running/paused/completed)
  - Flows by type (discovery/assessment/collection)
  - Average flow duration
  - Child flow phase progression (table)
  - Flow creation rate by type

### 4. Agent Health (PostgreSQL + Prometheus)
- **Purpose**: Monitor 17 CrewAI agents across 9 phases
- **Datasource**: PostgreSQL (`agent_performance_analytics`) + Prometheus (Phase 4)
- **Panels**:
  - Agent performance summary (table)
  - Task execution over time
  - Task distribution by phase (pie chart)
  - Agent average duration
  - Agent success rate (%)
- **Integration**: Links to `/api/v1/observability/health` API

## Configuration Details

### Retention Policies

| Component | Default Retention | Configurable Via | Storage Estimate |
|-----------|------------------|------------------|------------------|
| Loki | 14 days | `LOKI_RETENTION_DAYS` | ~14GB |
| Tempo | 7 days | `TEMPO_RETENTION_DAYS` | ~1.4GB |
| Prometheus | 14 days | `PROMETHEUS_RETENTION_DAYS` | ~28GB |
| **Total** | - | - | **~45GB** |

### Ports

| Service | Port | Purpose |
|---------|------|---------|
| Grafana | 9999 | Web UI (HTTPS in production) |
| Loki | 3100 | HTTP API (internal) |
| Tempo | 3200, 4317, 4318 | HTTP API, OTLP gRPC/HTTP |
| Prometheus | 9090 | HTTP API (internal) |
| Alloy | 12345, 4317, 4318 | HTTP, OTLP gRPC/HTTP |

### Security Configuration

#### Azure Dev Environment
- **Authentication**: Local admin (GitHub OAuth blocked by enterprise firewall)
- **Password**: 20+ chars, stored in Azure Key Vault (if available)
- **Rotation**: Every 90 days
- **Network**: NSG rule port 9999, IP-restricted to office IP
- **TLS**: HTTPS mandatory (terminate at nginx/Traefik/App Gateway)
- **Database Access**: Read-only `grafana_readonly` user (NOT superuser)

#### Railway Prod (Optional)
- **Authentication**: GitHub OAuth (recommended)
- **Network**: Grafana public, others private
- **TLS**: HTTPS by default (Railway)
- **Database Access**: Same read-only user pattern

#### Local Dev
- **Authentication**: Local admin from `.env.local` (NOT committed)
- **Network**: localhost:9999
- **TLS**: Optional (HTTP acceptable for local)

### High Cardinality Warning

Per ADR-031 line 156:
- **DO NOT** add `client_account_id` or `engagement_id` to every Prometheus metric
- Use these labels sparingly for critical metrics only
- For per-tenant analytics, use SQL dashboards querying PostgreSQL
- This prevents Prometheus cardinality explosion

## Phase 4: Backend OTel Instrumentation (Optional)

**Status**: Pending implementation
**Purpose**: Enable distributed tracing and agent performance metrics

### Prerequisites
- Phase 1 & 2 complete (infrastructure + dashboards)
- Tempo running and accepting traces
- Prometheus receiving metrics from Alloy

### Implementation Steps

See issue #878 for full implementation plan. Key files to modify:
- `backend/app/services/child_flow_services/*` (phase execution)
- `backend/app/services/crewai_flows/executors/*` (agent run boundaries)
- `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` (agent checkout)
- `backend/app/services/crewai_flows/memory/tenant_memory_manager.py` (vector search)

Metrics to add:
```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Agent execution metrics
agent_runs_total = meter.create_counter(
    "agent.runs.total",
    description="Total agent runs",
    unit="1"
)

agent_duration = meter.create_histogram(
    "agent.phase.duration_ms",
    description="Agent phase execution duration",
    unit="ms"
)

# TenantMemoryManager metrics
tenant_memory_search_total = meter.create_counter(
    "tenant_memory.search.total",
    description="Total memory searches",
    unit="1"
)
```

## Troubleshooting

### Grafana Won't Start
```bash
# Check logs
docker logs migration_grafana

# Common issues:
# 1. Port 9999 already in use
sudo lsof -i :9999
# Kill process or change port in docker-compose.observability.yml

# 2. Permission error on /var/lib/grafana
docker exec migration_grafana chown -R grafana:grafana /var/lib/grafana
```

### Dashboards Show "No Data"
```bash
# 1. Check datasource connectivity
docker exec migration_grafana grafana-cli admin data-sources list

# 2. Verify Postgres user
docker exec -it migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.llm_usage_logs;"

# 3. Check Loki receiving logs
curl http://localhost:3100/ready

# 4. Verify Alloy forwarding
docker logs migration_alloy
```

### High Disk Usage
```bash
# Check data volume sizes
du -sh config/docker/observability/data/*

# Reduce retention periods in .env.observability:
LOKI_RETENTION_DAYS=7
TEMPO_RETENTION_DAYS=3
PROMETHEUS_RETENTION_DAYS=7

# Restart affected services
docker-compose -f docker-compose.observability.yml restart
```

## Operational Procedures

### Password Rotation (Every 90 Days)

```bash
# 1. Generate new passwords
openssl rand -base64 32  # Grafana
openssl rand -base64 32  # Postgres Grafana user

# 2. Update Grafana admin password
docker exec -it migration_grafana grafana-cli admin reset-admin-password <NEW_PASSWORD>

# 3. Update Postgres user password
docker exec -it migration_postgres psql -U postgres -d migration_db -c "ALTER USER grafana_readonly WITH PASSWORD '<NEW_PASSWORD>';"

# 4. Update .env.observability
nano config/docker/.env.observability

# 5. Restart Grafana
docker-compose -f docker-compose.observability.yml restart grafana
```

### Backup Dashboards

```bash
# Export all dashboards
docker exec migration_grafana grafana-cli admin export-all > dashboards-backup-$(date +%Y%m%d).json

# Store in secure location (Azure Blob Storage, S3, etc.)
```

### Monitoring Disk Usage

```bash
# Add to crontab for alerts at 80% usage
crontab -e

# Add line:
0 * * * * df -h /path/to/observability/data | awk '{if(NR>1 && $5+0 > 80) print "Observability disk usage: " $5}' | mail -s "Disk Alert" ops@company.com
```

## References

### Documentation
- **ADR-031**: Architecture decision record
- **Issue #878**: Implementation plan and tracking
- **CLAUDE.md (lines 96-156)**: LLM tracking requirements

### API Endpoints
- **Observability API**: `/api/v1/observability/health`
- **LLM Costs UI**: `/finops/llm-costs`

### Related ADRs
- **ADR-006**: Master Flow Orchestrator
- **ADR-010**: Docker-First Development
- **ADR-012**: Flow Status Management Separation
- **ADR-024**: TenantMemoryManager Architecture

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review ADR-031 for architectural context
3. Check issue #878 for implementation status
4. Contact DevOps team for Azure-specific issues
