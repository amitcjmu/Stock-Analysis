# Railway Deployment: Dockerfile vs requirements.txt Confusion

**Date**: 2025-11-04
**Context**: Railway production crash with `ModuleNotFoundError: No module named 'apscheduler'`

## Problem

Adding dependency to `backend/requirements.txt` didn't fix Railway crash because Railway uses **different requirements file**.

**Error**:
```python
File "/app/app/services/agent_performance_aggregation_service.py", line 13
    from apscheduler.schedulers.background import BackgroundScheduler
ModuleNotFoundError: No module named 'apscheduler'
```

## Root Cause Investigation

1. **Railway configuration** (`config/deployment/railway.toml:2`):
   ```toml
   builder = "DOCKERFILE"  # NOT NIXPACKS
   ```

2. **This means**: `backend/railway.json` is **completely ignored**

3. **Dockerfile location** (`Dockerfile:25`):
   ```dockerfile
   COPY config/dependencies/requirements-docker.txt requirements.txt
   ```

4. **Not used by Railway**:
   - ❌ `backend/requirements.txt`
   - ❌ `backend/railway.json`

## Solution

Add missing dependency to **correct requirements file**:

```diff
# config/dependencies/requirements-docker.txt

# Async support
aiofiles>=23.0.0

+# Background task scheduling
+apscheduler==3.10.4
```

## Verification Commands

```bash
# Check Railway builder type
cat config/deployment/railway.toml | grep builder

# Find which requirements file Dockerfile uses
grep "COPY.*requirements" Dockerfile

# Verify dependency in correct file
grep apscheduler config/dependencies/requirements-docker.txt
```

## Common Mistake Pattern

When Railway uses **DOCKERFILE builder**:
- Ignore `railway.json` configuration entirely
- Find `COPY` command in Dockerfile to locate actual requirements file
- Update the file that Dockerfile copies, not local development files

## Files Modified

- `config/dependencies/requirements-docker.txt` (added apscheduler==3.10.4)

## Related Commits

- ✅ `9cdf44cd2` - Actual fix (requirements-docker.txt)
- ❌ `1402049ad` - Wrong file (railway.json) - reverted
- ❌ `ee556e306` - Wrong file (requirements.txt) - reverted

## Usage Pattern

**When**: Railway deployment fails with missing Python module
**Check**: `railway.toml` for builder type
**If DOCKERFILE**: Trace `COPY` commands to find actual requirements file
**Never**: Assume Railway uses project root requirements.txt
