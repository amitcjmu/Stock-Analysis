# Docker Observability Init Containers - Root Cause Analysis

## Issue Summary
Docker Desktop displayed error: "Cannot start Docker Compose application. Reason: compose [start] process 98923 exited with exit code 1 and WaitStatus 256, could not find alloy-init: not found"

## Investigation Findings

### What Actually Happened
1. **Init containers ARE working correctly** - they are NOT the problem
   - `loki-init`, `tempo-init`, `alloy-init` are designed to run once and exit
   - Their purpose: Fix volume permissions for Azure VM deployment
   - They successfully create directories and set ownership
   - They exit with status code 0 (success) as designed

2. **Observability stack WAS running** - but stopped 9 hours ago
   - All 5 containers (Grafana, Loki, Tempo, Prometheus, Alloy) were healthy
   - They stopped when Docker Desktop was closed/restarted
   - Containers remained in "Exited" state

3. **The ACTUAL problem** - Environment variable loading
   - docker-compose.observability.yml needs `.env.observability` file
   - Variables like `GRAFANA_ADMIN_PASSWORD` and `POSTGRES_GRAFANA_PASSWORD` required
   - Docker Compose wasn't loading the env file automatically

### Root Cause of Confusion
An AI agent previously claimed:
- "Init containers are not needed and can be removed" ❌ FALSE
- "All docker config for observability was changed" ❌ INCOMPLETE

**Reality:**
- Init containers ARE needed for proper volume permissions (especially on Azure VM)
- They work correctly - they're supposed to exit after setting up permissions
- The real issue was env file loading, not init container design

## Solution Implemented

### Step 1: Remove Stopped Containers
```bash
docker rm -f migration_grafana migration_alloy migration_loki migration_tempo migration_prometheus
```

### Step 2: Start with Environment File
```bash
docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d
```

### Result: ALL CONTAINERS HEALTHY ✅
```
migration_grafana      Up 19 seconds (healthy)
migration_alloy        Up 19 seconds (healthy)
migration_prometheus   Up 21 seconds (healthy)
migration_loki         Up 20 seconds (health: starting)
migration_tempo        Up 20 seconds (healthy)
```

## Secondary Issue: Alloy Docker Socket Permissions

### Error in Alloy Logs
```
level=error msg="Unable to refresh target groups"
err="permission denied while trying to connect to the Docker daemon socket"
```

### Root Cause
**macOS Docker Desktop Limitation:**
- Docker socket: `/var/run/docker.sock` → `/Users/chocka/.docker/run/docker.sock`
- Socket owned by: `chocka:staff` (not a numeric group ID)
- Alloy container runs as: `uid=472 gid=999` (alloy:docker)
- On macOS, Docker socket group mapping doesn't work like Linux

**On Linux (production):**
- Socket owned by: `root:docker` (gid typically 999 or specific docker group)
- Container user `472:999` can access socket via group membership
- Works correctly ✅

**On macOS (development):**
- Socket owned by user running Docker Desktop
- No group-based access control
- Container needs root access OR socket needs world-readable permissions

### Impact
- **Docker log collection disabled on macOS development**
- All other Alloy features work: OTLP traces/metrics, Prometheus remote write
- **Production deployment (Azure/Railway) unaffected** - Linux has proper group permissions

### Workarounds (Optional - for local dev only)

#### Option 1: Run Alloy as root (NOT RECOMMENDED - security risk)
```yaml
# docker-compose.observability.yml
alloy:
  user: "0:0"  # Run as root - DEVELOPMENT ONLY
```

#### Option 2: Use alternative log collection (RECOMMENDED for local dev)
```yaml
# Use Docker logging driver to send logs to Loki directly
# In docker-compose.yml, add to each service:
logging:
  driver: loki
  options:
    loki-url: "http://localhost:3100/loki/api/v1/push"
```

#### Option 3: Accept limited functionality on macOS
- Docker logs won't be collected automatically
- Manual log viewing: `docker logs <container>` or Docker Desktop UI
- Full observability works in production (Azure VM)

## Correct Understanding: Init Container Pattern

### Two-Table Pattern (ADR-012)
Init containers follow the same architectural principle as flow state management:

**Init Container (Setup Phase):**
- Run once at startup
- Fix permissions, create directories
- Exit with success status
- Dependency for main container

**Main Container (Operational Phase):**
- Starts after init container completes
- Uses volumes with correct permissions
- Runs continuously with restart policy

### Why This Pattern Exists
1. **Azure VM Requirements**: Volume directories need specific ownership (10001:10001 for Loki/Tempo, 472:472 for Alloy)
2. **Security Hardening**: Main containers run as non-root users
3. **Idempotency**: Init containers can run multiple times without issues
4. **Docker Compose Design**: `depends_on` with `condition: service_completed_successfully`

## What NOT to Do

❌ **Don't remove init containers** - they're required for production deployment
❌ **Don't assume they're broken** - exiting is their correct behavior
❌ **Don't add workarounds** - the pattern is working as designed
❌ **Don't confuse "exited" with "failed"** - check exit code (0 = success)

## Correct Startup Command

### For Development (macOS/Linux)
```bash
cd config/docker
docker-compose -f docker-compose.yml -f docker-compose.observability.yml --env-file .env.observability up -d
```

### For Production (Azure VM)
```bash
cd config/docker
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d
# Env vars loaded from /etc/environment or Azure App Service settings
```

## Monitoring Commands

### Check Container Status
```bash
docker ps | grep -E "migration_loki|migration_tempo|migration_prometheus|migration_alloy|migration_grafana"
```

### Check Init Container Completion
```bash
docker ps -a | grep -E "_init"
# Should show "Exited (0)" status
```

### Access Grafana UI
```bash
open http://localhost:9999
# Login: admin / <GRAFANA_ADMIN_PASSWORD from .env.observability>
```

### View Alloy UI
```bash
open http://localhost:12345
# Check pipeline status and target discovery
```

## Related Documentation
- ADR-031: Grafana Observability Stack Architecture
- `config/docker/docker-compose.observability.yml`: Container definitions
- `config/docker/.env.observability`: Environment configuration
- `config/docker/observability/alloy-config.alloy`: Telemetry collection pipeline

## Lessons Learned
1. **Don't trust AI claims without verification** - "init containers not needed" was false
2. **Understand container lifecycle** - exited != failed for one-time setup containers
3. **Check exit codes** - exit code 0 means success, not failure
4. **macOS Docker limitations** - socket permissions work differently than Linux
5. **Read the architecture** - init containers are documented in ADR-031 for good reason
