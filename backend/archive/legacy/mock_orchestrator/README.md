# Mock Discovery Orchestrator - ARCHIVED

**Status**: Archived on 2025-07-05  
**Reason**: Mock implementation that created false success responses

## What was archived

- `unified_discovery_modular.py` - Main router that exposed mock endpoints
- `unified_discovery/` - Entire module including:
  - `services/discovery_orchestrator.py` - Mock orchestrator class
  - `routes/flow_routes.py` - Mock flow endpoints
  - `routes/status_routes.py` - Mock status endpoints
  - Various other mock service files

## Why it was removed

This mock orchestrator was creating **false success responses** that misled developers:

1. **Fake execution**: The `/unified-discovery/flow/execute` endpoint returned `{"status": "completed"}` without doing any real work
2. **No actual CrewAI**: It tried to import non-existent handlers and fell back to mock behavior
3. **Developer confusion**: Made it appear that flows were working when they weren't
4. **Redundant**: Real working endpoints exist at `/discovery/flow/` that use actual CrewAI flows

## What to use instead

Use the **real working endpoints** in `/api/v1/discovery/` which properly integrate with CrewAI flows:

- `POST /api/v1/discovery/flow/{flow_id}/resume` - Resume paused flows
- `GET /api/v1/discovery/flows/active` - Get active flows  
- `GET /api/v1/discovery/flows/{flow_id}/status` - Get flow status

These endpoints use the real `CrewAIFlowService` and `UnifiedDiscoveryFlow` implementations.

## Architecture lesson

**Always prefer real implementations over mocks in production code.** Mocks should only exist in test files, not in the main codebase where they can be mistaken for working functionality.