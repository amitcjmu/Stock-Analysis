# Grafana Observability Stack (Tier B)

**ADR-031**: Enterprise Observability Architecture
**Issue #878**: Implementation tracking

## Architecture

**5 Containers**:
1. **Grafana** (port 9999) - Web UI, dashboards, datasource configuration
2. **Loki** (port 3100) - Log aggregation, 14-day retention
3. **Tempo** (port 3200) - Distributed tracing, 7-day retention (replaces Jaeger)
4. **Prometheus** (port 9090) - Metrics TSDB, 14-day retention
5. **Alloy** (port 12345) - Unified collector (replaces Promtail + OTel Collector)

**Supersedes**: OpenLIT stack (7+ containers), Jaeger tracing

## Quick Start

### Prerequisites

1. **Generate strong Grafana admin password**:
   ```bash
   openssl rand -base64 32
   ```

2. **Copy environment file** (if it doesn't exist):
   ```bash
   cd config/docker
   cp .env.observability.template .env.observability
   # Edit .env.observability and set GRAFANA_ADMIN_PASSWORD
   ```

3. **Create read-only PostgreSQL user**:
   ```bash
   docker exec -it migration_postgres psql -U postgres -d migration_db
   ```

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
   GRANT SELECT ON pg_stat_statements TO grafana_readonly;
   ```

   Update `.env.observability`:
   ```bash
   POSTGRES_GRAFANA_PASSWORD=<strong-password>
   ```

### Deployment

#### Local Development
```bash
cd config/docker

# Start main stack + observability stack together
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify all containers running
docker ps | grep migration

# Access Grafana
open http://localhost:9999
# Login: admin / <GRAFANA_ADMIN_PASSWORD from .env.observability>
```

#### Azure Dev (Manual Deployment)
```bash
# SSH into Azure VM via Bastion (browser-based)
# https://portal.azure.com → CNCoE-Ubuntu → Connect → Bastion

# Navigate to project directory
cd /home/achall/AIForce-Assess/config/docker

# Ensure .env.observability exists with strong password
# (Copy from secure password manager or Azure Key Vault)

# Deploy observability stack
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify deployment
docker ps | grep migration
docker logs migration_grafana -f

# Access Grafana
# https://aiforceasses.cloudsmarthcl.com:9999
# (Requires NSG rule for port 9999 - see ADR-031 Phase 3)
```

#### Railway Prod (Optional - Future)
See ADR-031 Phase 5 for Railway deployment options:
- **Self-hosted**: Same 5-container stack (~$40-300/month)
- **Grafana Cloud**: Alloy only + remote write (~$5-70/month)

## Configuration Files

### Core Configs
- `alloy-config.alloy` - Docker log collection, OTLP receiver, log redaction
- `loki-config.yaml` - 14-day retention, compaction, filesystem storage
- `tempo-config.yaml` - 7-day retention, HTTP-only queries (no WebSockets)
- `prometheus.yml` - 14-day retention, scrape targets, remote write

### Grafana Provisioning
- `grafana/provisioning/datasources/datasources.yml` - Auto-configure Loki, Tempo, Prometheus, PostgreSQL
- `grafana/provisioning/dashboards/dashboards.yml` - Auto-load dashboard JSON files
- `grafana/dashboards/*.json` - Dashboard definitions (Phase 2 - see README in dashboards/)

## Accessing Services

### Grafana Web UI
- **Local**: http://localhost:9999
- **Azure**: https://aiforceasses.cloudsmarthcl.com:9999
- **Login**: admin / `<GRAFANA_ADMIN_PASSWORD>`

### Prometheus UI (Optional)
- **Local**: http://localhost:9090
- Use for ad-hoc metric queries and troubleshooting

### Alloy UI (Optional)
- **Local**: http://localhost:12345
- Shows pipeline health and metrics

## Dashboards (Phase 2)

Create these dashboards in `grafana/dashboards/`:

1. **app-logs.json** - Loki log aggregation with filtering
2. **llm-costs.json** - LLM usage cost tracking (PostgreSQL queries)
3. **mfo-flows.json** - Master Flow Orchestrator lifecycle (PostgreSQL queries)
4. **agent-health.json** - Agent performance analytics (PostgreSQL + Prometheus)

See `grafana/dashboards/README.md` for SQL queries and examples.

## Troubleshooting

### Network Error: "migration_network declared as external, but could not be found"
**Solution**: Run both compose files together (creates shared network)
```bash
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```

If running observability stack standalone (not recommended):
```bash
# Create network manually first
docker network create migration_migration_network --driver bridge

# Then start observability stack
docker-compose -f docker-compose.observability.yml up -d
```

### Grafana Won't Start
**Check password set**:
```bash
grep GRAFANA_ADMIN_PASSWORD config/docker/.env.observability
```

**Check logs**:
```bash
docker logs migration_grafana -f
```

### Can't Query PostgreSQL
**Verify read-only user exists**:
```bash
docker exec -it migration_postgres psql -U postgres -d migration_db -c "\du"
# Should show grafana_readonly user
```

**Test connection**:
```bash
docker exec -it migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.llm_usage_logs;"
```

### Loki/Tempo Not Receiving Data
**Check Alloy pipeline**:
```bash
docker logs migration_alloy -f
# Look for errors in log processing
```

**Verify containers on same network**:
```bash
docker network inspect migration_migration_network
# All migration_* containers should be listed
```

### High Disk Usage
**Check volume sizes**:
```bash
docker system df -v | grep migration
```

**Loki data**:
```bash
docker exec migration_loki du -sh /loki
# Should be ~14GB (14 days × 1GB/day)
```

**Prometheus data**:
```bash
docker exec migration_prometheus du -sh /prometheus
# Should be ~28GB (14 days × 2GB/day)
```

## Maintenance

### Rotate Grafana Password (Every 90 Days)
```bash
# Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update .env.observability
sed -i "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=${NEW_PASSWORD}/" .env.observability

# Restart Grafana
docker-compose restart grafana

# Store in Azure Key Vault (if available)
```

### Cleanup Old Data
Data cleanup is automatic via retention policies:
- **Loki**: 14 days (compactor runs every 10 minutes)
- **Tempo**: 7 days (compactor runs every 30 minutes)
- **Prometheus**: 14 days (automatic TSDB cleanup)

### Backup Dashboards
```bash
# Export all dashboards
docker exec migration_grafana grafana-cli admin export-dashboard \
  --output /var/lib/grafana/dashboards/backup

# Copy to host
docker cp migration_grafana:/var/lib/grafana/dashboards/backup ./dashboards-backup-$(date +%Y%m%d)
```

### Monitor Disk Usage
```bash
# Set up alert at 80% disk usage
# In Azure Portal: VM → Monitoring → Alerts
# Threshold: Disk usage > 80%
# Action: Email SRE team
```

## Security

### Authentication
- **Local/Azure Dev**: Local admin auth (GitHub OAuth blocked by firewall)
- **Railway Prod**: GitHub OAuth (recommended) OR local admin
- **Password**: 20+ characters, rotated every 90 days

### Network Security (Azure)
- **NSG Rule**: Port 9999 inbound
- **Recommended**: IP allowlist (office public IP only)
- **TLS**: HTTPS mandatory (terminate at nginx/App Gateway)

### Database Access
- **Grafana**: Uses read-only user (`grafana_readonly`)
- **NO superuser access** for Grafana datasource
- **Permissions**: SELECT only on specific tables (see ADR-031)

### Secrets Management
- **Local**: `.env.observability` (NOT committed to git)
- **Azure**: Pull from Azure Key Vault (if available)
- **Railway**: Use Railway project variables

## Cost Estimates

### Azure Dev (VM-Based)
- **Infrastructure**: Existing Ubuntu VM (no new compute)
- **Storage**: ~45GB additional disk
- **Cost**: ~$5-10/month (storage only)

### Railway Prod (If Deployed)
- **Self-hosted**: ~$40-300/month (5 services + volumes)
- **Grafana Cloud**: ~$5-70/month (Alloy + remote write)
- **Decision**: Defer to Phase 5 (see ADR-031)

## References

- **ADR-031**: Full architecture documentation
- **Issue #878**: Implementation plan (60+ tasks across 5 phases)
- **CLAUDE.md**: Integration with LLM tracking (MANDATORY)
- **Grafana Docs**: https://grafana.com/docs/
- **Alloy Docs**: https://grafana.com/docs/alloy/
