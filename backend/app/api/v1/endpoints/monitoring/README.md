# Monitoring Module Documentation

## Overview

The monitoring module has been refactored from a single 1,115 line file into a modular structure organized by functional domains. This improves maintainability, readability, and allows for easier testing and extension.

## Module Structure

```
monitoring/
├── __init__.py              # Module exports
├── base.py                  # Shared dependencies and utilities
├── agent_monitoring.py      # Agent status, tasks, and registry management
├── health_metrics.py        # System health and performance metrics
├── crewai_flow_monitoring.py # CrewAI flow-specific monitoring
├── crew_monitoring.py       # Phase 2 crew system monitoring
└── error_monitoring.py      # Background task and error tracking
```

## Module Breakdown

### 1. Agent Monitoring (`agent_monitoring.py`)
**Lines of Code:** ~430
**Endpoints:**
- `GET /status` - Get current agent monitoring status
- `GET /tasks` - Get task execution history
- `GET /agents` - Get detailed information about all agents
- `GET /agents/by-phase/{phase}` - Get agents for a specific phase
- `POST /agents/{agent_id}/heartbeat` - Update agent heartbeat
- `GET /registry/export` - Export complete agent registry

### 2. Health & Metrics (`health_metrics.py`)
**Lines of Code:** ~95
**Endpoints:**
- `GET /health` - Get overall system health
- `GET /metrics` - Get detailed performance metrics

### 3. CrewAI Flow Monitoring (`crewai_flow_monitoring.py`)
**Lines of Code:** ~185
**Endpoints:**
- `GET /crewai-flows` - Get comprehensive CrewAI Flow monitoring data
- `GET /crewai-flows/{flow_id}` - Get details for a specific flow
- `GET /crewai-flows/{flow_id}/agent-tasks` - Get agent task information

### 4. Crew Monitoring (`crew_monitoring.py`)
**Lines of Code:** ~200
**Endpoints:**
- `GET /crews/list` - List available crew types
- `GET /crews/system/status` - Get crew system status
- `GET /crews/{crew_type}/status` - Get specific crew status
- `GET /crews/flows/active` - Get active discovery flows with crew info

### 5. Error Monitoring (`error_monitoring.py`)
**Lines of Code:** ~230
**Endpoints:**
- `GET /errors/background-tasks/active` - Get active background tasks
- `GET /errors/background-tasks/failed` - Get failed background tasks
- `GET /errors/background-tasks/{task_id}` - Get specific task status
- `GET /errors/summary` - Get error summary
- `POST /errors/test/{error_type}` - Trigger test error (non-production)

## Benefits of Modularization

1. **Improved Maintainability** - Each module has a clear, focused responsibility
2. **Better Organization** - Related functionality is grouped together
3. **Easier Testing** - Modules can be tested independently
4. **Reduced Complexity** - Smaller files are easier to understand and modify
5. **Better Collaboration** - Multiple developers can work on different modules without conflicts
6. **Extensibility** - New monitoring domains can be added as separate modules

## Backward Compatibility

The main `monitoring.py` file now acts as an aggregator that includes all sub-routers, maintaining the same API endpoints. No changes are required for existing clients or imports.
