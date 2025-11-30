# CRITICAL: Docker Container Management

## NEVER rebuild containers after code changes!

**Why:**
- Rebuilding (`docker-compose up --build`) creates new image layers
- Left uncleaned, this consumes disk space rapidly
- The user has repeated this instruction MANY times

## Correct approach after code changes:

```bash
# Just restart the container - code changes are picked up via volume mounts
docker restart migration_backend
docker restart migration_frontend
```

## When rebuild IS needed (rare):
- Only when Dockerfile changes
- Only when requirements.txt/package.json dependencies change
- Only when explicitly requested by user

## Remember:
- Backend Python code is mounted via volumes
- Frontend code is mounted via volumes
- Hot reload handles most changes automatically
- A simple restart is sufficient for code changes to take effect
