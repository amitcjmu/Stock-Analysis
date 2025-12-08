# Grafana Observability Stack - Deployment Guide

**URGENT**: Fix for network error shown in screenshot

## Errors Fixed

### Error 1: Network Not Found
```
ERROR: Network migration_network declared as external, but could not be found.
```
**Fixed**: Network now correctly references `migration_migration_network` (created by main compose)

### Error 2: Loki Permission Denied (Azure VMs)
```
mkdir /loki/rules: permission denied
error initialising module: ruler-storage
```
**Root Cause**: Docker volume permissions differ on Azure Linux VMs vs local Docker Desktop
**Fixed**: Run Loki/Tempo/Alloy as root user (`user: "0"`) to handle volume permissions

## Solution: New Tier B Stack

I've created a **NEW** `docker-compose.observability.yml` following ADR-031:
- **5 containers** (not 7+): Grafana + Loki + Tempo + Prometheus + Alloy
- **Replaces Jaeger** with Tempo (as requested)
- **Replaces OpenLIT** stack (heavy footprint)
- **Network fixed**: Shared network with main stack

---

## 🚀 Deploy Now (Azure Dev)

### Step 1: Update Password
```bash
cd /home/achall/AIForce-Assess/config/docker

# Edit .env.observability (already exists with password)
# Verify GRAFANA_ADMIN_PASSWORD is set
grep GRAFANA_ADMIN_PASSWORD .env.observability
```

### Step 2: Create Read-Only PostgreSQL User
```bash
docker exec -it migration_postgres psql -U postgres -d migration_db

# Run this SQL:
CREATE USER grafana_readonly WITH PASSWORD 'j5lpi8zAu1e99UdGH3CI6JDoLsV9Rq49WoExtmxaggs=';
GRANT CONNECT ON DATABASE migration_db TO grafana_readonly;
GRANT USAGE ON SCHEMA migration TO grafana_readonly;
GRANT SELECT ON migration.llm_usage_logs TO grafana_readonly;
GRANT SELECT ON migration.crewai_flow_state_extensions TO grafana_readonly;
GRANT SELECT ON migration.discovery_flows TO grafana_readonly;
GRANT SELECT ON migration.assessment_flows TO grafana_readonly;
GRANT SELECT ON migration.collection_flows TO grafana_readonly;
GRANT SELECT ON migration.agent_discovered_patterns TO grafana_readonly;
GRANT SELECT ON migration.agent_performance_analytics TO grafana_readonly;
\q
```

### Step 3: Deploy Observability Stack
```bash
# Stop old stack (to avoid port conflicts)
docker-compose -f docker-compose.observability.yml down

# Deploy new Tier B stack WITH main stack
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify all containers running
docker ps | grep migration_
```

**Expected containers**:
- `migration_grafana` (port 9999)
- `migration_loki` (port 3100)
- `migration_tempo` (port 3200, 4317, 4318)
- `migration_prometheus` (port 9090)
- `migration_alloy` (port 12345)
- `migration_backend` (existing)
- `migration_frontend` (existing)
- `migration_postgres` (existing)
- `migration_redis` (existing)

### Step 4: Verify Deployment
```bash
# Check Grafana is healthy
docker logs migration_grafana | tail -20

# Check Loki is ready
curl http://localhost:3100/ready

# Check Tempo is ready
curl http://localhost:3200/ready

# Check Prometheus is healthy
curl http://localhost:9090/-/healthy
```

### Step 5: Access Grafana
**URL**: https://aiforceassessgrafana.cloudsmarthcl.com/
**Login**: admin / `<GRAFANA_ADMIN_PASSWORD from .env.observability>`

**⚠️ IMPORTANT**: Access is via dedicated subdomain with Azure Front Door/App Gateway handling TLS termination.

### Step 6: Verify Datasources
In Grafana:
1. Go to **Connections** → **Datasources**
2. Verify 4 datasources loaded:
   - ✅ Loki (http://loki:3100)
   - ✅ Tempo (http://tempo:3200)
   - ✅ Prometheus (http://prometheus:9090)
   - ✅ PostgreSQL (postgres:5432, user: grafana_readonly)
3. Click **Test** on each datasource

---

## 📊 What You Get

### Immediate (Phase 1 - NOW)
- **Grafana Web UI** on port 9999 (instead of CLI `docker logs`)
- **Log Aggregation** (Loki) - search/filter logs from all containers
- **Metrics UI** (Prometheus) - system health, container stats
- **Distributed Tracing** (Tempo) - trace requests across services
- **Unified Collection** (Alloy) - automatic log/metric/trace collection

### Next Steps (Phase 2 - Issue #878)
- **LLM Cost Dashboard** - track spending by model/provider/tenant
- **MFO Flow Dashboard** - visualize workflow lifecycle and phases
- **Agent Health Dashboard** - monitor all 17 CrewAI agents
- **Application Logs Dashboard** - advanced log filtering and analysis

---

## 🔧 Troubleshooting

### Why Did Old Stack Work Locally But Not on Azure?

**Local Docker Desktop (Mac/Windows)**:
- Runs containers with permissive file sharing (osxfs/wsl2)
- Auto-fixes UID/GID mismatches
- Volumes owned by local user, accessible to containers

**Azure Linux VM**:
- Strict UID/GID enforcement
- Volume mounted with root ownership (UID 0)
- Containers run as non-root (Loki uses UID 10001)
- Permission denied when creating `/loki/rules` directory

**Fix Applied**:
- Added `user: "0"` to Loki, Tempo, Alloy services
- Containers run as root and can write to volumes
- Alternative: Pre-create directories with correct ownership (more complex)

### Still Getting Network Error?
```bash
# Network should be created automatically when running both files
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify network exists
docker network ls | grep migration
# Should show: migration_migration_network

# If missing, create manually
docker network create migration_migration_network --driver bridge
```

### Loki Permission Errors (mkdir /loki/rules: permission denied)
```bash
# This is fixed in the new compose file with user: "0"
# If you still see this error:

# Option 1: Verify user directive is in compose file
grep "user:" docker-compose.observability.yml
# Should show: user: "0" for loki, tempo, alloy

# Option 2: Recreate containers
docker-compose -f docker-compose.yml -f docker-compose.observability.yml down
docker volume rm migration_loki_data migration_tempo_data migration_alloy_data
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Option 3: Manual permission fix (if still needed)
docker exec -it migration_loki sh -c "chown -R 10001:10001 /loki"
```

### Grafana Won't Start
```bash
# Check password is set
grep GRAFANA_ADMIN_PASSWORD .env.observability

# Check logs
docker logs migration_grafana -f
```

### Can't Access PostgreSQL from Grafana
```bash
# Verify read-only user exists
docker exec -it migration_postgres psql -U postgres -d migration_db -c "\du"

# Test connection
docker exec -it migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.llm_usage_logs;"
```

### Port 9999 Not Accessible
1. Check NSG rule exists in Azure Portal
2. Verify Grafana is listening: `docker exec migration_grafana netstat -tlnp | grep 3000`
3. Check firewall on VM: `sudo ufw status`

---

## 📝 What Changed

### Replaced
- ❌ OpenLIT dashboard + DB + Redis (heavy, separate ecosystem)
- ❌ Jaeger (old tracing)
- ❌ Separate Promtail and OTel Collector

### New Stack
- ✅ Grafana (single UI for everything)
- ✅ Loki (log aggregation, 14-day retention)
- ✅ Tempo (distributed tracing, 7-day retention) - **replaces Jaeger**
- ✅ Prometheus (metrics TSDB, 14-day retention)
- ✅ Alloy (unified collector) - **replaces Promtail + OTel Collector**

### Benefits
- **Fewer containers**: 5 instead of 7+
- **Modern stack**: Grafana ecosystem with Tempo (not Jaeger)
- **HTTP-only**: Railway compatible (no WebSocket requirements)
- **Integrated**: LLM tracking, MFO flows, agent analytics in one UI
- **Enterprise ready**: Local auth, TLS support, read-only DB access

---

## 📖 References

- **ADR-031**: `/docs/adr/031-environment-based-observability-architecture.md`
- **Issue #878**: https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/878
- **Detailed README**: `/config/docker/observability/README.md`
- **Dashboard Guide**: `/config/docker/observability/grafana/dashboards/README.md`

---

## ✅ Success Criteria

After deployment, you should be able to:
- [ ] Access Grafana at https://aiforceassessgrafana.cloudsmarthcl.com/
- [ ] Login with admin credentials
- [ ] See 4 datasources configured (Loki, Tempo, Prometheus, PostgreSQL)
- [ ] Query logs from backend/frontend containers in Explore → Loki
- [ ] View metrics in Explore → Prometheus
- [ ] Query LLM usage from PostgreSQL datasource

---

**Need help?** Check `/config/docker/observability/README.md` for detailed troubleshooting.
