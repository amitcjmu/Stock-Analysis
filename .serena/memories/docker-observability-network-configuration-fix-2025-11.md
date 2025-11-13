# Docker Observability Stack Network Configuration Fix

**Date**: 2025-11-04
**Context**: Docker Compose observability stack containers on wrong network after fresh setup

## Problem

After Docker prune, observability init containers created on `migration_default` network instead of `migration_migration_network`:

```bash
# Wrong network assignment
migration_loki_init    → migration_default
migration_tempo_init   → migration_default
migration_alloy_init   → migration_default
```

**Root Cause**: `docker-compose.observability.yml` used `external: true` without explicit network name mapping.

## Solution

Add explicit network name to external network definition:

```yaml
networks:
  migration_network:
    name: migration_migration_network  # ← ADD THIS
    external: true
```

Add network specification to all init containers:

```yaml
loki-init:
  image: alpine:3.19
  volumes:
    - ./observability/data/loki:/loki
  networks:
    - migration_network  # ← ADD THIS
  restart: "no"
```

## Files Modified

- `config/docker/docker-compose.observability.yml` (lines 250-253, 82-95, 123-137, 194-208)

## Verification

```bash
docker ps -a --format "table {{.Names}}\t{{.Networks}}"
# All containers should show: migration_migration_network
```

## Usage Pattern

**When**: Multi-file Docker Compose with external networks
**Apply**: Always explicitly name external networks when using `external: true`
**Avoid**: Relying on Docker's default network name inference

## Related Fix

Commit: `cbc43319c` - Fix Docker network configuration and init containers
