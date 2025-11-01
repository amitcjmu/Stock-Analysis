# Grafana Observability Stack - Deployment Checklist

**Architecture**: ADR-031
**Environments**: Local Dev, Azure Dev, Railway Prod

## Pre-Deployment Verification

### Infrastructure Readiness

- [ ] Docker Compose v2.0+ installed
- [ ] Docker Engine running
- [ ] `migration_network` Docker network exists
  ```bash
  docker network inspect migration_network
  ```
- [ ] Disk space available (>50GB recommended)
  ```bash
  df -h /path/to/observability/data
  ```

### Configuration Files

- [ ] `.env.observability` created from template
  ```bash
  cp config/docker/.env.observability.template config/docker/.env.observability
  ```
- [ ] Grafana admin password generated (20+ chars)
  ```bash
  openssl rand -base64 32
  ```
- [ ] Postgres Grafana user password generated
  ```bash
  openssl rand -base64 32
  ```
- [ ] All environment variables set in `.env.observability`:
  - `GRAFANA_ADMIN_PASSWORD`
  - `POSTGRES_GRAFANA_PASSWORD`
  - `GF_SERVER_PROTOCOL` (http for local, https for production)
  - `GF_SERVER_ROOT_URL`
  - `GF_SERVER_DOMAIN`
  - Retention days (LOKI_RETENTION_DAYS, TEMPO_RETENTION_DAYS, PROMETHEUS_RETENTION_DAYS)

## Local Development Deployment

### Prerequisites

- [ ] Backend and frontend containers running
  ```bash
  docker ps | grep -E "migration_backend|migration_frontend|migration_postgres"
  ```

### Deployment Steps

- [ ] PostgreSQL read-only user created
  ```bash
  docker exec -i migration_postgres psql -U postgres -d migration_db < config/docker/observability/create-grafana-user.sql
  ```

- [ ] Start observability stack
  ```bash
  cd config/docker
  docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d
  ```

- [ ] Verify all 5 containers running
  ```bash
  docker ps | grep -E "grafana|loki|tempo|prometheus|alloy"
  ```

- [ ] Verify health checks passing
  ```bash
  docker ps --filter "health=healthy" | grep -E "grafana|loki|tempo|prometheus|alloy"
  ```

### Post-Deployment Verification

- [ ] Grafana accessible at http://localhost:9999
  ```bash
  curl -s http://localhost:9999/api/health | jq .
  ```

- [ ] Login works with admin credentials
- [ ] All 4 datasources connected:
  - Loki ✅
  - Tempo ✅
  - Prometheus ✅
  - PostgreSQL ✅

- [ ] All 4 dashboards load without errors:
  - Application Logs ✅
  - LLM Usage Costs ✅
  - MFO Flow Lifecycle ✅
  - Agent Health ✅

- [ ] Logs flowing to Loki
  ```bash
  curl -s "http://localhost:3100/loki/api/v1/query_range?query=%7Bcontainer%3D%22migration_backend%22%7D&start=$(date -u -d '5 minutes ago' +%s)000000000&end=$(date -u +%s)000000000" | jq '.data.result | length'
  ```

## Azure Dev Deployment

### Prerequisites

- [ ] SSH access to Azure VM via Bastion
  - Azure Portal → CNCoE-Ubuntu → Connect → Bastion

- [ ] Azure NSG rule created for port 9999
  - Port: 9999
  - Protocol: TCP
  - Source: <office-public-ip> (or Any)
  - Priority: 310
  - Name: Allow-Grafana-9999
  - Action: Allow

- [ ] SSL certificates obtained (if using HTTPS)
  - Option A: External TLS termination (nginx/Traefik/App Gateway) **[RECOMMENDED]**
  - Option B: Grafana native HTTPS (place certs in `observability/ssl/`)
  ```bash
  # Verify certificates
  openssl x509 -in observability/ssl/grafana.crt -text -noout
  openssl rsa -noout -modulus -in observability/ssl/grafana.key | openssl md5
  ```

### Deployment Steps

- [ ] Copy observability configs to Azure VM
  ```bash
  # Via git pull or SCP
  git pull origin feat/grafana-observability-stack
  ```

- [ ] Edit `.env.observability` for Azure
  ```bash
  nano config/docker/.env.observability
  ```
  - Set `GRAFANA_ADMIN_PASSWORD`
  - Set `POSTGRES_GRAFANA_PASSWORD`
  - For HTTPS (native): Set `GF_SERVER_PROTOCOL=https`, `GF_SERVER_ROOT_URL=https://aiforceasses.cloudsmarthcl.com:9999`
  - For HTTPS (external TLS): Set `GF_SERVER_PROTOCOL=http`, `GF_SERVER_ROOT_URL=https://aiforceasses.cloudsmarthcl.com:9999`

- [ ] Create PostgreSQL read-only user
  ```bash
  docker exec -i migration_postgres psql -U postgres -d migration_db < config/docker/observability/create-grafana-user.sql
  ```

- [ ] Deploy observability stack
  ```bash
  cd config/docker
  docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d
  ```

- [ ] Verify all 5 containers running
  ```bash
  docker ps | grep -E "grafana|loki|tempo|prometheus|alloy"
  ```

### Post-Deployment Verification

- [ ] Grafana accessible at https://aiforceasses.cloudsmarthcl.com:9999
  ```bash
  curl -k -s https://aiforceasses.cloudsmarthcl.com:9999/api/health | jq .
  ```

- [ ] SSL certificate valid (if using native HTTPS)
  ```bash
  openssl s_client -connect aiforceasses.cloudsmarthcl.com:9999 -showcerts
  ```

- [ ] Login works with admin credentials
- [ ] All 4 datasources connected
- [ ] All 4 dashboards load without errors
- [ ] Logs flowing from all containers:
  - migration_backend
  - migration_frontend
  - migration_postgres
  - migration_redis

- [ ] LLM Usage Costs dashboard shows data from `llm_usage_logs`
- [ ] MFO Flow Lifecycle dashboard shows master and child flows
- [ ] Agent Health dashboard shows 17 agents

### Security Verification

- [ ] NSG rule enforced (test from non-allowlisted IP if restricted)
  ```bash
  # From external IP - should fail if IP-restricted
  curl --connect-timeout 5 https://aiforceasses.cloudsmarthcl.com:9999/api/health
  ```

- [ ] HTTPS enforced (HTTP redirects or blocked)
- [ ] Anonymous access disabled
- [ ] Strong password set (20+ chars)
- [ ] PostgreSQL user has read-only access
  ```bash
  docker exec -it migration_postgres psql -U grafana_readonly -d migration_db -c "INSERT INTO migration.llm_usage_logs (model_name) VALUES ('test');"
  # Should fail with: ERROR: permission denied for table llm_usage_logs
  ```

- [ ] Password stored in Azure Key Vault (if available)
  ```bash
  az keyvault secret show --vault-name <vault> --name grafana-admin-password
  ```

## Railway Prod Deployment (Optional)

**Note**: Railway has built-in logs. This deployment adds rich dashboards for LLM costs, MFO flows, and agent performance.

### Prerequisites

- [ ] Railway project created
- [ ] Database deployed (PostgreSQL with pgvector)
- [ ] Backend/frontend services deployed

### Decision Point

- [ ] **Option A**: Self-hosted (5 services) - $40-300/month
  - All components (Grafana, Loki, Tempo, Prometheus, Alloy) on Railway
  - GitHub OAuth recommended
  - Complete control

- [ ] **Option B**: Grafana Cloud - $5-70/month
  - Only Alloy on Railway
  - Grafana Cloud free tier (50GB logs, 50GB traces, 10K metrics)
  - Less management overhead

### Deployment Steps (Option A - Self-Hosted)

- [ ] Add Railway services:
  - migration_grafana (public)
  - migration_loki (private)
  - migration_tempo (private)
  - migration_prometheus (private)
  - migration_alloy (private)

- [ ] Configure GitHub OAuth in Railway
  ```bash
  # Railway environment variables
  GF_AUTH_GITHUB_ENABLED=true
  GF_AUTH_GITHUB_CLIENT_ID=<from-github-app>
  GF_AUTH_GITHUB_CLIENT_SECRET=<from-github-app>
  GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS=YourGitHubOrg
  ```

- [ ] Deploy observability stack
  ```bash
  railway up -d
  ```

- [ ] Verify HTTPS (Railway provides automatic HTTPS)

### Post-Deployment Verification

- [ ] Grafana accessible via Railway public URL
- [ ] OAuth login works
- [ ] HTTP-only operation verified (no WebSocket errors)
- [ ] Loki/Tempo/Prometheus private (not publicly accessible)
- [ ] Cost within budget (<$150/month for medium usage)

## Post-Deployment Operations

### Monitoring Setup

- [ ] Add disk usage alerts (cron job)
  ```bash
  crontab -e
  # Add: 0 * * * * df -h /path/to/observability/data | awk '{if(NR>1 && $5+0 > 80) print "Observability disk usage: " $5}' | mail -s "Disk Alert" ops@company.com
  ```

- [ ] Configure Grafana alerting (optional)
  - High disk usage (>80%)
  - High LLM costs (>$X per day)
  - Agent failure rate (>10%)

### Documentation

- [ ] Update team wiki with:
  - Grafana URL
  - Admin password location (Azure Key Vault or password manager)
  - Dashboard links
  - Access request procedure

- [ ] Add to runbook:
  - Password rotation procedure (every 90 days)
  - Backup procedure (dashboard export)
  - Scaling guidelines (adjust retention if disk full)

### Password Management

- [ ] Document password rotation date (90 days from now)
  ```bash
  echo "Next rotation: $(date -d '+90 days' +%Y-%m-%d)" >> /path/to/runbook
  ```

- [ ] Add calendar reminder for password rotation

## Rollback Procedure

If issues occur during deployment:

```bash
# Stop observability stack
docker-compose -f docker-compose.observability.yml down

# Remove volumes (if needed)
docker volume prune

# Restore previous state
git checkout main
```

## Common Issues

### Issue: Grafana Won't Start

**Symptoms**: Container exits immediately

**Diagnosis**:
```bash
docker logs migration_grafana
```

**Fixes**:
- Port 9999 already in use: `lsof -i :9999` and kill process
- Permission error: `docker exec migration_grafana chown -R grafana:grafana /var/lib/grafana`
- SSL certificate error: Verify cert files or disable HTTPS (`GF_SERVER_PROTOCOL=http`)

### Issue: Dashboards Show "No Data"

**Symptoms**: Empty panels in dashboards

**Diagnosis**:
```bash
# Check PostgreSQL connectivity
docker exec -it migration_postgres psql -U grafana_readonly -d migration_db -c "SELECT COUNT(*) FROM migration.llm_usage_logs;"

# Check Loki receiving logs
curl http://localhost:3100/ready

# Check Alloy forwarding
docker logs migration_alloy
```

**Fixes**:
- PostgreSQL user missing: Run `create-grafana-user.sql`
- No data in tables: Generate test data or wait for agent execution
- Loki not receiving logs: Check Alloy configuration and Docker socket access

### Issue: High Disk Usage

**Symptoms**: Disk space warnings, slow queries

**Diagnosis**:
```bash
du -sh config/docker/observability/data/*
```

**Fixes**:
- Reduce retention periods in `.env.observability`
- Restart affected services: `docker-compose -f docker-compose.observability.yml restart`
- Clean old data: `docker exec migration_loki rm -rf /loki/chunks/*`

## Success Criteria

Deployment is successful when:

- ✅ All 5 containers running and healthy
- ✅ Grafana accessible via web browser
- ✅ Admin login works
- ✅ All 4 datasources connected
- ✅ All 4 dashboards display data
- ✅ Logs flowing from application containers
- ✅ LLM costs tracked in dashboard
- ✅ MFO flows visible in dashboard
- ✅ Agent health metrics displayed
- ✅ HTTPS enabled (production) or HTTP working (local)
- ✅ NSG/firewall rules configured (Azure)
- ✅ Passwords stored securely
- ✅ Documentation updated

## References

- **ADR-031**: Architecture decision record
- **Issue #878**: Implementation tracking
- **README.md**: Comprehensive documentation
- **CLAUDE.md (lines 96-156)**: LLM tracking requirements

## Support Contacts

- **DevOps Team**: For Azure infrastructure issues
- **Database Team**: For PostgreSQL access issues
- **Security Team**: For NSG/firewall changes
- **Engineering Lead**: For architectural questions
