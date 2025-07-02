# Agent Instruction Cards

## Instructions for Kicking Off Each Agent

Copy and paste these instructions to each agent to begin their work.

---

## Agent 1: Database Schema Specialist

### Your Mission
You are the Database Schema Specialist for the AI Force Migration Platform database reset project. Your goal is to create a clean database schema that properly aligns with our SQLAlchemy models and supports our multi-tenant agent-based system.

### Context
- The platform uses PostgreSQL with multi-tenant isolation
- We need fields like `learning_scope`, `memory_isolation_level`, and `assessment_ready` for the agent system
- All `is_mock` fields should be removed (we use multi-tenancy instead)
- The database and models were previously misaligned

### Your Tasks
1. **Backup current database** (~/backend/backups/)
2. **Reset the database** completely 
3. **Review and fix models** in backend/app/models/ if needed
4. **Create a single clean migration** that includes all tables with correct schemas
5. **Apply and validate** the migration
6. **Create SCHEMA_READY.md** when complete

### Key Requirements
- DiscoveryFlow table MUST have: learning_scope, memory_isolation_level, assessment_ready, phase_state, agent_state
- DataImport table MUST have: source_system, error_message, error_details, failed_records
- NO is_mock fields anywhere
- All foreign keys and indexes properly defined

### Resources
- Model alignment findings: docs/db/MODEL_DATABASE_ALIGNMENT_FINDINGS.md
- Full execution plan: docs/db/DATABASE_RESET_AGENT_EXECUTION_PLAN.md

### Deliverable
Create `backend/seeding/SCHEMA_READY.md` with:
- Timestamp of completion
- List of all tables created
- Any notes for the seeding team
- Confirmation that schema matches models

### Success Criteria
- Clean database with no legacy tables
- All models can be imported without errors
- Schema validation passes
- Migration is replayable

Begin with TASK 1.1 from the execution plan. Update STATUS.txt as you progress.

---

## Agent 2: Core Data Engineer

### Your Mission
You are the Core Data Engineer responsible for seeding all foundational data including users, RBAC roles, discovery flows, and data imports. Your work enables the platform to demonstrate multi-tenant capabilities with proper access control.

### Context
- Platform uses RBAC with roles: ENGAGEMENT_MANAGER, ANALYST, VIEWER, CLIENT_ADMIN
- Discovery flows have states: complete, in-progress, failed
- Multi-tenant isolation via client_account_id and engagement_id
- Agent learning system requires learning_scope and memory_isolation_level

### Prerequisites
- Wait for Agent 1 to create `backend/seeding/SCHEMA_READY.md`
- Ensure database schema is ready

### Your Tasks
1. **Create seeding infrastructure** with shared constants
2. **Seed client account and engagement** (use hardcoded demo IDs)
3. **Create 4 users** with different RBAC roles and access levels
4. **Seed 5 discovery flows** in various states
5. **Create 3 data imports** (CSV, JSON, Excel)
6. **Generate SEEDED_IDS.json** for Agent 3

### Key Data Points
```python
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

Users:
- demo@democorp.com (ENGAGEMENT_MANAGER)
- analyst@democorp.com (ANALYST)  
- viewer@democorp.com (VIEWER)
- client.admin@democorp.com (CLIENT_ADMIN)

Flows:
- 1 complete (assessment_ready=True)
- 1 at field mapping
- 1 at asset inventory
- 1 failed at import
- 1 just started
```

### Resources
- RBAC model: backend/app/models/rbac.py
- Execution plan: docs/db/DATABASE_RESET_AGENT_EXECUTION_PLAN.md

### Deliverables
1. `constants.py` - Shared IDs for all agents
2. `01_core_entities.py` - Users and accounts
3. `02_discovery_flows.py` - 5 flows
4. `03_data_imports.py` - 3 imports
5. `SEEDED_IDS.json` - Flow and import IDs for Agent 3

Begin with TASK 2.1 from the execution plan. Share constants.py immediately after creation.

---

## Agent 3: Asset Data Specialist

### Your Mission
You are the Asset Data Specialist responsible for creating a realistic asset inventory with dependencies, migration planning data, and field mappings. Your work enables the platform to demonstrate asset discovery and migration planning capabilities.

### Context
- Target: 60 assets total (10 apps, 35 servers, 10 databases, 5 network)
- Assets need dependencies for relationship visualization
- 6R strategies and migration waves for planning demos
- Field mappings show the AI-assisted mapping process

### Prerequisites
- Wait for Agent 2 to create `SEEDED_IDS.json`
- Import `constants.py` from Agent 2
- Understand the discovery flow IDs

### Your Tasks
1. **Create raw import records** (150-200 total across 3 imports)
2. **Create field mappings** (10-15 per import, varied confidence)
3. **Seed 60 assets** with realistic metadata
4. **Define dependencies** between assets
5. **Assign migration waves** and 6R strategies

### Asset Distribution
```
Applications (10):
- CustomerPortal (Java web)
- FinanceSystem (.NET)
- HRManagement (Python)
- InventoryERP (Legacy)
- 6 other business apps

Servers (35):
- 20 Linux (RHEL/Ubuntu)
- 15 Windows (2016/2019/2022)

Databases (10):
- 4 Oracle (production)
- 3 SQL Server
- 3 PostgreSQL (dev)

Network (5):
- 2 Load balancers
- 3 Firewalls
```

### Resources
- Asset model: backend/app/models/asset.py
- Execution plan: docs/db/DATABASE_RESET_AGENT_EXECUTION_PLAN.md

### Deliverables
1. `04_raw_import_records.py` - Import data
2. `05_field_mappings.py` - AI-suggested mappings
3. `06_assets.py` - 60 assets
4. `07_dependencies.py` - Relationships
5. `08_migration_planning.py` - Waves and strategies

Begin with TASK 3.1. Ensure assets are properly distributed across discovery flows.

---

## Agent 4: QA & Validation Engineer (Optional)

### Your Mission
You are the QA & Validation Engineer responsible for ensuring all seeded data is correct, relationships are valid, and the UI displays data properly for demo users.

### Context
- Multi-tenant system requiring isolation validation
- 4 different user roles to test
- Complex relationships between entities
- UI must show data on all pages

### Prerequisites
- Can begin test script creation immediately
- Full validation requires Agents 2 & 3 to complete

### Your Tasks
1. **Create validation scripts** to check data integrity
2. **Write test queries** for common operations
3. **Create UI validation checklist**
4. **Execute full validation** once seeding complete
5. **Document any issues** found

### Validation Points
- Record counts match expectations
- Foreign keys all valid
- No orphaned records
- Multi-tenant isolation working
- Each user role sees appropriate data
- All UI pages populated
- Performance acceptable

### Test Scenarios
1. Login as each user type
2. Navigate all major pages
3. Verify data visibility
4. Check permission boundaries
5. Test search/filter functions

### Resources
- Demo data reference: docs/db/DEMO_DATA_REFERENCE.md
- Execution plan: docs/db/DATABASE_RESET_AGENT_EXECUTION_PLAN.md

### Deliverables
1. `validate_seeding.py` - Automated checks
2. `test_queries.sql` - Manual verification
3. `UI_VALIDATION.md` - Checklist with results
4. `VALIDATION_REPORT.md` - Final summary

Begin with creating validation scripts. You can prepare while others seed data.

---

## Coordination Instructions

### Starting the Agents

1. **Launch Agent 1 immediately**:
   ```bash
   # Share the Agent 1 instruction card
   # Agent begins database reset
   ```

2. **Prepare Agents 2 & 3**:
   ```bash
   # Share their instruction cards
   # They can review plans while waiting
   # Agent 2 watches for SCHEMA_READY.md
   # Agent 3 watches for SEEDED_IDS.json
   ```

3. **Optional Agent 4**:
   ```bash
   # Can start immediately on test prep
   # Begin creating validation framework
   ```

### Monitoring Progress

Create a simple monitoring loop:
```bash
# In main terminal
watch -n 60 "cat backend/seeding/shared/STATUS.txt | tail -20"
```

### Communication Protocol

Each agent should:
1. Update STATUS.txt when starting/completing tasks
2. Create required handoff files
3. Alert via Slack/Teams when blocked
4. Commit frequently with clear messages

### Expected Timeline

- Agent 1: 4-5 hours
- Agent 2: 3-4 hours (can start ~4 hours in)
- Agent 3: 3-4 hours (can start ~5 hours in)  
- Agent 4: 2-3 hours (validation after ~8 hours)
- **Total: 8-10 hours with parallel execution**

### Emergency Handling

If an agent encounters blockers:
1. Document the issue in STATUS.txt
2. Try the documented workaround
3. Escalate if blocked > 30 minutes
4. Consider reassigning tasks if needed