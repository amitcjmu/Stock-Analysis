# Rich Console Display Conflict Fix

## Problem
The error "Only one live display may be active at once" occurs when multiple Rich console Live displays try to run simultaneously. This happens in the CrewAI event handling system when processing TaskCompletedEvent.

## Root Cause
CrewAI and its agents may use Rich console internally for progress displays. When our event listeners also try to use Rich console or when multiple events fire concurrently, it creates conflicts.

## Solution

### 1. Console Manager
Created `console_manager.py` to centralize Rich console management:
- Singleton pattern ensures only one instance
- Thread-safe locking mechanism
- Disables Rich output during event processing

### 2. Rich Configuration
Created `rich_config.py` to globally configure Rich:
- Detects non-interactive environments (Docker, CI/CD)
- Sets TERM=dumb to disable Rich formatting
- Respects NO_COLOR standard

### 3. Event Handler Updates
Modified `discovery_flow_listener.py`:
- Disables Rich output at initialization
- Wraps TaskCompletedEvent handler with try/finally
- Temporarily disables Rich during event processing

### 4. Docker Configuration
Updated `Dockerfile.backend`:
- Sets DOCKER_CONTAINER=1 environment variable
- Enables PYTHONUNBUFFERED for better logging

## How It Works

1. **On Startup**: Rich is configured based on environment
2. **During Events**: Rich output is temporarily disabled
3. **After Events**: Rich output is re-enabled
4. **In Docker**: Rich is permanently disabled

## Testing
To verify the fix:
1. Run the backend in Docker
2. Trigger discovery flow with asset processing
3. Monitor logs for "EventBus Error" messages
4. Verify no "Only one live display" errors occur

## Environment Variables
- `DISABLE_RICH_OUTPUT=true`: Force disable Rich output
- `DOCKER_CONTAINER=1`: Indicates running in Docker
- `TERM=dumb`: Disables terminal formatting
- `NO_COLOR=1`: Standard for disabling colors