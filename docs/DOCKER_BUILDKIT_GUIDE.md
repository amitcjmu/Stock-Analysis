# Docker BuildKit Guide

## Problem: "the --mount option requires BuildKit"

If you encounter this error when building the application locally:

```
Step 7/23 : RUN --mount=type=cache,target=/pip-cache ...
the --mount option requires BuildKit. Refer to https://docs.docker.com/go/buildkit/ to learn how to build images with BuildKit enabled
ERROR: Service 'backend' failed to build : Build failed
```

This means your Docker environment doesn't have BuildKit enabled, which is required for advanced Dockerfile features like cache mounts.

## Quick Solutions

### Option 1: Use Local Development Setup (Recommended for Quick Fix)

Use the local development Docker Compose file that doesn't require BuildKit:

```bash
# Instead of regular docker-compose up
docker-compose -f docker-compose.local.yml up --build
```

This uses `Dockerfile.backend.local` which provides the same functionality without BuildKit requirements.

### Option 2: Enable BuildKit (Recommended for Performance)

#### Temporary Enable (One-time)
```bash
DOCKER_BUILDKIT=1 docker-compose up --build
```

#### Enable for Current Shell Session
```bash
export DOCKER_BUILDKIT=1
docker-compose up --build
```

#### Permanently Enable BuildKit

**Docker Desktop (Mac/Windows):**
1. Open Docker Desktop
2. Go to Settings > Docker Engine
3. Add or modify the configuration:
```json
{
  "features": {
    "buildkit": true
  }
}
```
4. Click "Apply & Restart"

**Linux:**
Add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
export DOCKER_BUILDKIT=1
```

### Option 3: Use the Setup Helper Script

Run the automated setup helper:

```bash
./scripts/docker-setup.sh
```

This script will:
- Check if BuildKit is available
- Test BuildKit functionality
- Recommend the best build approach for your environment

## Why BuildKit?

The main `Dockerfile.backend` uses BuildKit for:
- **Cache Mounts**: Speeds up pip installs by caching packages between builds
- **Better Build Performance**: Multi-stage builds with optimized layer caching
- **Reduced Build Time**: Especially important in CI/CD environments

## File Comparison

| File | BuildKit Required | Use Case |
|------|------------------|----------|
| `Dockerfile.backend` | ✅ Yes | Production builds, CI/CD, performance-critical |
| `Dockerfile.backend.local` | ❌ No | Local development, older Docker versions |
| `docker-compose.yml` | ✅ Yes | Standard development with BuildKit |
| `docker-compose.local.yml` | ❌ No | Development without BuildKit |

## Troubleshooting

### Check Docker Version
```bash
docker version
```
BuildKit is supported in Docker 18.06+ and enabled by default in Docker Desktop.

### Check BuildKit Status
```bash
docker info | grep BuildKit
```

### Test BuildKit
```bash
# Create a simple test
echo 'FROM alpine:latest
RUN --mount=type=cache,target=/tmp echo "test"' | DOCKER_BUILDKIT=1 docker build -
```

### Still Having Issues?

1. **Update Docker**: Ensure you're using a recent version of Docker Desktop
2. **Restart Docker**: Sometimes a restart resolves BuildKit detection issues
3. **Use Local Version**: The `docker-compose.local.yml` always works as a fallback
4. **Check Permissions**: On Linux, ensure your user is in the `docker` group

## Performance Impact

| Approach | Build Time (Clean) | Build Time (Cached) | Disk Usage |
|----------|-------------------|---------------------|------------|
| With BuildKit | ~3-4 minutes | ~30-60 seconds | Optimized |
| Without BuildKit | ~4-5 minutes | ~2-3 minutes | Higher |

## Development Workflow

**For teams:**
- Use BuildKit-enabled setup for best performance
- Keep local versions as fallback for onboarding
- Document BuildKit setup in team docs

**For individual developers:**
- Try BuildKit first for better experience
- Fall back to local setup if issues arise
- Consider updating Docker if using old versions

## Environment Variables Reference

```bash
# Enable BuildKit for current command
DOCKER_BUILDKIT=1 docker-compose up

# Disable BuildKit explicitly
DOCKER_BUILDKIT=0 docker-compose up

# Check if BuildKit is enabled
docker info | grep -i buildkit
```