# Database Seeding Scripts

This directory contains database seeding scripts for the AI Modernize Migration Platform.

## Agent 2: Core Data Engineer

These scripts were created by Agent 2 to seed foundational data including users, RBAC roles, discovery flows, and data imports.

## Files

### Core Scripts
- `constants.py` - Shared constants and hardcoded IDs for consistency across all seeding
- `01_core_entities.py` - Seeds client account, engagement, users with RBAC setup
- `02_discovery_flows.py` - Seeds 5 discovery flows in various states
- `03_data_imports.py` - Seeds 3 data imports (CSV, JSON, Excel)
- `run_seeding.py` - Main orchestrator that runs all scripts in order

### Generated Files
- `SCHEMA_READY.md` - Indicates database schema is ready (created by Agent 1)
- `FLOW_IDS.json` - Exported flow IDs for reference
- `SEEDED_IDS.json` - Complete list of all seeded entity IDs for Agent 3

## Running the Seeds

### Option 1: Run All Seeds
```bash
cd backend
python seeding/run_seeding.py
```

### Option 2: Run Individual Scripts
```bash
cd backend
python seeding/01_core_entities.py
python seeding/02_discovery_flows.py
python seeding/03_data_imports.py
```

## Seeded Data

### Client & Engagement
- **Client**: DemoCorp International (ID: 11111111-1111-1111-1111-111111111111)
- **Engagement**: Cloud Migration Assessment 2024 (ID: 22222222-2222-2222-2222-222222222222)

### Users (4 total)
1. **demo@democorp.com** - Engagement Manager (full permissions)
2. **analyst@democorp.com** - Analyst (read/write, import data)
3. **viewer@democorp.com** - Viewer (read-only access)
4. **client.admin@democorp.com** - Client Admin (admin console access)

Default password for all users: `DemoPassword123!`

### Discovery Flows (5 total)
1. **Completed Flow** - 100% complete, assessment ready
2. **Field Mapping Flow** - 45% progress, at field mapping phase
3. **Asset Inventory Flow** - 65% progress, building inventory
4. **Failed Import Flow** - Failed at 15%, data quality issues
5. **Just Started Flow** - 5% progress, initialization phase

### Data Imports (3 total)
1. **server_inventory.csv** - 150 servers, completed
2. **application_catalog.json** - 75 applications, processing
3. **app_dependencies.xlsx** - 200 dependencies, completed

## Key Features

### Multi-Tenant Support
- All data is properly scoped to client account and engagement
- User access is controlled through RBAC with client/engagement isolation

### RBAC Implementation
- UserProfile with approval workflow
- UserRole with granular permissions
- ClientAccess for client-level permissions
- EngagementAccess for engagement-level permissions

### Agent Learning Configuration
- Learning scope: engagement
- Memory isolation: client_account level
- Agent preferences configured per client

## Notes

- All timestamps use `2024-01-01 10:00:00 UTC` as base
- IDs are hardcoded UUIDs for consistency
- Sample data is generated programmatically
- Failed rows include example validation errors
- CrewAI flow states include realistic metrics and outputs
