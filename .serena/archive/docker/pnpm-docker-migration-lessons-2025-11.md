# pnpm Docker Migration - Why It Failed (November 2025)

## Summary
Attempted migration from npm to pnpm for Docker builds was cancelled (PR #1137, Issues #1127-#1134) after discovering it provided **no benefits and doubled disk usage**.

## Key Findings

### What pnpm DOES NOT Improve in Docker

| Claim | Reality |
|-------|---------|
| Smaller images | ❌ Same size (~4GB) - pnpm hardlink dedup doesn't work inside Docker layers |
| Faster builds | ❌ Only with BuildKit cache preserved; clearing cache = same speed |
| Less disk space | ❌ **DOUBLED** from 12GB → 23GB (BuildKit cache adds 12.9GB) |

### Why pnpm's Benefits Don't Apply to Docker

```
pnpm benefit: Hardlink deduplication across projects
             ↓
Docker reality: Each image layer is a tarball - no cross-layer dedup
             ↓
Result: node_modules is fully copied regardless of package manager
```

### BuildKit Cache Mount Reality

```dockerfile
# This looks helpful but...
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
```

**Problems:**
1. `docker system prune -af --volumes` clears BuildKit cache
2. Without cache, pnpm downloads everything again (same as npm)
3. BuildKit cache itself uses ~12GB of disk space
4. Only helps on REPEAT builds with identical dependencies

## The "Antipattern" Was Actually a Feature

### Original npm Setup (KEEP THIS):
```yaml
frontend:
  volumes:
    - ../../package.json:/app/package.json
    - ../../package-lock.json:/app/package-lock.json
    - frontend_node_modules:/app/node_modules
  command: sh -c "npm install --legacy-peer-deps && npm run dev"
```

**Why this is BETTER for development:**
- Add/change dependency → Just restart container (2-3 min)
- No image rebuild needed for package.json changes
- HMR works for source code changes
- Total disk: ~12GB

### pnpm "Optimized" Setup (DON'T USE):
```yaml
frontend:
  # Dependencies baked at build time - NO package.json mount
  command: ["pnpm", "run", "dev"]
```

**Why this is WORSE:**
- Add/change dependency → Must rebuild entire image (5+ min)
- Image rebuild required for ANY package.json change
- Total disk: ~23GB+ (with BuildKit cache)

## When pnpm Migration WOULD Help

✅ **CI/CD pipelines** with persistent cache infrastructure
✅ **Monorepos** where pnpm workspace dedup matters
✅ **Production builds** with multi-stage Dockerfiles
❌ **Local development** with frequent dependency changes

## Commands Reference

### Check Docker disk usage:
```bash
docker system df
```

### Clean everything EXCEPT BuildKit cache:
```bash
docker image prune -af
docker container prune -f
docker volume prune -f
docker buildx prune --keep-storage=2GB -f
```

### Clean EVERYTHING (resets to slow builds):
```bash
docker system prune -af --volumes
docker buildx prune -af
```

## Related Issues (All Closed)
- PR #1137 - Main migration PR
- #1127 - Milestone definition
- #1128-#1134 - Sub-tasks

## Conclusion

**Keep the npm-based Docker setup.** The runtime `npm install` pattern enables rapid iteration on dependency changes without full rebuilds. pnpm's benefits (hardlink dedup) don't apply inside Docker image layers.
