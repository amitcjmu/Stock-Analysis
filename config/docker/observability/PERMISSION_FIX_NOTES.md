# Azure VM Permission Fix - Observability Stack

## Issue Summary

**Problem**: Grafana observability stack worked perfectly on local Docker Desktop (Mac) but failed on Azure Linux VM with permission errors.

**Error**:
```
mkdir /loki/rules: permission denied
error initialising module: ruler-storage
```

---

## Root Cause

### Local Docker Desktop Behavior
- **File Sharing**: Uses osxfs (Mac) or wsl2 (Windows)
- **UID/GID Handling**: Automatically maps container UIDs to host user
- **Permissions**: Volumes accessible regardless of container user
- **Result**: Works without issues

### Azure Linux VM Behavior
- **File Sharing**: Native Linux filesystem (ext4)
- **UID/GID Handling**: Strict enforcement, no automatic mapping
- **Volume Ownership**: Docker volumes owned by root (UID 0)
- **Container Users**:
  - Loki runs as UID 10001 (non-root)
  - Tempo runs as UID 10001 (non-root)
  - Alloy runs as UID 472 (non-root)
- **Result**: Permission denied when containers try to create directories in volumes

---

## Fix Applied

### Docker Compose Changes

Added `user: "0"` directive to run containers as root:

```yaml
# Loki
loki:
  image: grafana/loki:3.2.0
  user: "0"  # ← Added
  volumes:
    - loki_data:/loki

# Tempo
tempo:
  image: grafana/tempo:2.6.0
  user: "0"  # ← Added
  volumes:
    - tempo_data:/var/tempo

# Alloy
alloy:
  image: grafana/alloy:v1.4.2
  user: "0"  # ← Added
  volumes:
    - alloy_data:/var/lib/alloy
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Why This Works

1. **Root Access**: Container runs as UID 0, can create any directory
2. **Volume Permissions**: Root can write to root-owned volumes
3. **Docker Socket**: Alloy needs root to access `/var/run/docker.sock`
4. **No Host Impact**: Container root ≠ host root (namespace isolation)

---

## Alternative Solutions (Not Chosen)

### Option 1: Pre-create Directories with Correct Ownership
```bash
# On host
docker volume create migration_loki_data
docker run --rm -v migration_loki_data:/data alpine sh -c "mkdir -p /data/rules && chown -R 10001:10001 /data"
```
**Why not chosen**: More complex, requires manual steps, breaks on volume recreation

### Option 2: Use Named User in Compose
```yaml
loki:
  user: "10001:10001"
  volumes:
    - loki_data:/loki
```
**Why not chosen**: Still requires pre-creating directories with correct ownership

### Option 3: Init Container Pattern
```yaml
loki-init:
  image: alpine
  command: sh -c "mkdir -p /loki/rules && chown -R 10001:10001 /loki"
  volumes:
    - loki_data:/loki

loki:
  depends_on:
    - loki-init
```
**Why not chosen**: Adds complexity, extra container, orchestration overhead

### Option 4: Custom Entrypoint Script
```bash
#!/bin/sh
mkdir -p /loki/rules
chown -R loki:loki /loki
exec /usr/bin/loki "$@"
```
**Why not chosen**: Requires custom Docker image, maintenance burden

---

## Security Considerations

### Is Running as Root Safe?

**YES** - for these reasons:

1. **Container Isolation**: Container root ≠ host root
   - Linux namespaces isolate container processes
   - Container root has no privileges on host
   - Can't escape container without kernel exploit

2. **Limited Attack Surface**:
   - Read-only config files (`:ro` mounts)
   - No shell access (minimal images)
   - No network access to sensitive services

3. **Grafana Security Best Practices**:
   - Grafana official images run as root by default
   - Prometheus runs as `nobody` (UID 65534) but still needs root for certain operations
   - Industry standard for observability stacks

4. **Azure VM Hardening**:
   - Container runtime (Docker) is already privileged
   - VM access controlled by Bastion host
   - Network security groups (NSG) restrict inbound traffic

### Better Than Alternatives?

**YES** - compared to:
- ❌ Disabling SELinux/AppArmor (actually reduces security)
- ❌ Chmod 777 on volumes (massive security hole)
- ❌ Running entire Docker daemon as non-root (breaks many features)

---

## Network Fix

### Original Issue
```
ERROR: Network migration_network declared as external, but could not be found
```

### Network Naming in Docker Compose

**Main Compose File** (`docker-compose.yml`):
```yaml
name: migration  # ← Project name

networks:
  migration_network:
    driver: bridge
```

**Docker's Naming Convention**:
- Format: `{project}_{network}`
- Result: `migration_migration_network`

**Observability Compose Fix**:
```yaml
networks:
  migration_network:
    external: true
    name: migration_migration_network  # ← Explicit name
```

---

## Deployment Commands

### Clean Deployment (Removes Old Volumes)
```bash
cd /home/achall/AIForce-Assess/config/docker

# Stop and remove old stack
docker-compose -f docker-compose.observability.yml down -v

# Deploy new stack with fixes
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify all containers running
docker ps | grep migration_

# Check logs for errors
docker logs migration_loki | tail -20
docker logs migration_tempo | tail -20
docker logs migration_alloy | tail -20
```

### Update Existing Deployment
```bash
cd /home/achall/AIForce-Assess/config/docker

# Pull latest changes
git pull origin main

# Recreate only observability containers
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d --force-recreate \
  migration_grafana migration_loki migration_tempo migration_prometheus migration_alloy

# Verify
docker ps | grep migration_
```

---

## Verification

### Check Container Users
```bash
# Verify Loki runs as root
docker exec migration_loki id
# Expected: uid=0(root) gid=0(root)

# Verify Tempo runs as root
docker exec migration_tempo id
# Expected: uid=0(root) gid=0(root)

# Verify Alloy runs as root
docker exec migration_alloy id
# Expected: uid=0(root) gid=0(root)
```

### Check Volume Permissions
```bash
# Check Loki volume
docker exec migration_loki ls -la /loki
# Should show directories owned by root

# Check Tempo volume
docker exec migration_tempo ls -la /var/tempo
# Should show directories owned by root

# Check no permission errors in logs
docker logs migration_loki 2>&1 | grep -i "permission denied"
# Should return nothing
```

---

## Future Improvements

### Phase 2: Non-Root Containers (Optional)

If security requirements mandate non-root containers:

1. **Add init containers** to pre-create directories
2. **Use security contexts** in Kubernetes (if migrating)
3. **Custom images** with proper entrypoint scripts
4. **Host volume mounts** with explicit chown on VM

**Trade-offs**:
- ✅ Slightly better security posture
- ❌ More complexity
- ❌ Harder to maintain
- ❌ Not necessary for enterprise Azure VM deployment

### Phase 3: Azure Files Integration (Optional)

For persistent storage across VM restarts:

1. Mount Azure Files as NFS volume
2. Set correct permissions on Azure Files share
3. Update volume drivers in compose file

**Trade-offs**:
- ✅ Data persists across VM replacements
- ❌ Higher cost (~$0.06/GB/month)
- ❌ Network latency for volume access
- ❌ Not necessary for 14-day retention

---

## References

- Docker UID/GID handling: https://docs.docker.com/engine/security/userns-remap/
- Grafana security best practices: https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/
- Loki configuration: https://grafana.com/docs/loki/latest/configuration/
- ADR-031: `/docs/adr/031-environment-based-observability-architecture.md`
- Issue #878: https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/878
