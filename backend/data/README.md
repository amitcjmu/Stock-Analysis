# Runtime Data Directory

This directory contains **runtime-generated data** that should NOT be committed to Git.

## Overview

All files in this directory are automatically generated during application runtime and are specific to each environment (development, staging, production). They are excluded from version control via `.gitignore` (`backend/data/**`).

## Files (Auto-Generated at Runtime)

### Agent Persistence Files
- **`agent_insights.json`** - Agent learnings and insights accumulated during discovery/collection flows
  - Size: ~1-10MB depending on usage
  - Contains: Flow-specific insights, confidence scores, recommendations
  - Purpose: Persist agent knowledge across restarts

- **`agent_memory.json`** - CrewAI agent memory state
  - Size: ~5-15MB
  - Contains: Agent conversation history, context, decisions
  - Purpose: Enable agents to remember past interactions

- **`agent_questions.json`** - Pending agent questions requiring user input
  - Size: ~10-100KB
  - Contains: Clarification questions, confidence levels, context
  - Purpose: Agent-user interaction queue

- **`agent_context.json`** - Cross-page and flow context
  - Size: ~1-5KB
  - Contains: Shared context across UI pages
  - Purpose: Maintain state during multi-page workflows

- **`agent_learning_experiences.json`** - Historical learning patterns
  - Size: ~1-5KB
  - Contains: Pattern recognition data, feedback loops
  - Purpose: Improve agent accuracy over time

### Application State Files
- **`field_mappings.json`** - Discovered field mappings during data import
  - Size: ~1-5KB
  - Contains: Source→Target field mapping cache
  - Purpose: Speed up repeated import operations

## Initialization

All files are created automatically when the application starts:
- Empty files (`{}`) are initialized if missing
- Files grow as agents execute tasks
- No manual setup required

## Docker/Production Deployment

**IMPORTANT**: In production, mount this directory as a persistent volume to preserve agent learnings across container restarts:

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - agent_data:/app/backend/data

volumes:
  agent_data:
    driver: local
```

### Railway Deployment
Railway automatically creates persistent volumes. Ensure the `backend/data` directory is writable:
```dockerfile
# Dockerfile
RUN mkdir -p /app/backend/data && chmod 755 /app/backend/data
```

## Cleanup/Maintenance

### Local Development
```bash
# Clear all runtime data (fresh start)
rm backend/data/*.json

# Clear specific agent memory
rm backend/data/agent_memory.json
```

### Production
Implement rotation policy for large files:
- Archive `agent_insights.json` when > 50MB
- Implement TTL for old insights (e.g., 90 days)
- Monitor disk usage via observability tools

## Why Not in Git?

These files should **never** be committed because:
1. **Size**: Can grow to 10-100MB, bloating repository
2. **Environment-specific**: Each environment has different flow IDs, tenant IDs
3. **Merge conflicts**: Different developers/environments generate conflicting data
4. **Security**: May contain customer-specific insights (PII concerns)
5. **CI/CD churn**: Each deployment generates new data → unnecessary commits

## Troubleshooting

### "Permission denied" errors
```bash
chmod 755 backend/data
chmod 644 backend/data/*.json
```

### Agent not remembering past actions
Check if `agent_memory.json` exists and is readable:
```bash
ls -lh backend/data/agent_memory.json
# Should show file with size > 0
```

### Large disk usage
```bash
du -sh backend/data/
# If > 100MB, consider cleanup or archival
```

## Related Documentation
- Agent UI Bridge: `app/services/agent_ui_bridge.py`
- Storage Manager: `app/services/agent_ui_bridge_handlers/storage_manager.py`
- ADR-024: TenantMemoryManager Architecture
