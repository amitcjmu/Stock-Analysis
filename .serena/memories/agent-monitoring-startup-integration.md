# Agent Monitoring Startup Integration Pattern

## Problem: Background Services Not Starting

**Symptom**: Database tables for monitoring exist but remain empty (0 rows).

**Root Cause**: Service initialization function exists but never called at app startup.

**Solution Pattern**:

### 1. Add Startup Hook in lifecycle.py

```python
# In app/app_setup/lifecycle.py

# Add import at top
from app.core.agent_monitoring_startup import (
    initialize_agent_monitoring,
    shutdown_agent_monitoring,
)

# In lifespan() function, AFTER database initialization:
try:
    logger.info("🔧 Initializing agent monitoring...")
    initialize_agent_monitoring()
    logger.info("✅ Agent monitoring initialized successfully")
except Exception as e:  # pragma: no cover
    # Don't fail startup if monitoring fails - log and continue
    logger.error(f"⚠️ Failed to initialize agent monitoring: {e}", exc_info=True)

# In shutdown section, BEFORE app exit:
try:
    logger.info("🛑 Shutting down agent monitoring...")
    shutdown_agent_monitoring()
    logger.info("✅ Agent monitoring shut down successfully")
except Exception as e:  # pragma: no cover
    logger.warning("⚠️ Failed to shut down agent monitoring: %s", e)
```

### 2. Verify in Startup Logs

```bash
# Check Docker logs after restart
docker logs migration_backend --tail=50 | grep -E "(Agent monitoring|✅|❌)"

# Should see:
# ✅ Agent monitor started successfully
# ✅ Agent performance aggregation service started successfully
# 🔍 Agent monitoring services initialized:
#    - Real-time task monitoring: ACTIVE
#    - Database persistence: ACTIVE
```

### 3. Key Patterns

**Non-Blocking Initialization**:
- Always wrap in try/except
- Log errors but don't crash app startup
- Monitoring is observability, not core functionality

**Graceful Shutdown**:
- Call shutdown in reverse order of initialization
- Handle shutdown failures gracefully
- Use `logger.warning()` for shutdown issues (not `error`)

**Order Matters**:
```
1. Database initialization
2. Master Flow Orchestrator
3. Agent monitoring ← Add here
4. Feature flags
5. LiteLLM setup
```

---

## When to Apply This Pattern

**Use Cases**:
- Background schedulers (APScheduler)
- Monitoring/observability services
- Health check endpoints
- Background worker threads
- Cache warming

**Don't Use For**:
- Database connections (already in lifecycle)
- Critical services (should block startup on failure)
- Request handlers (registered via FastAPI routers)
