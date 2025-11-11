# Decommission Flow Implementation - Multi-Agent Orchestration Prompt

**Session Type**: Fresh Implementation Session
**Execution Mode**: Multi-Agent Delegation with Full Automation
**Target**: Complete Decommission Flow Implementation (v2.5.0)

---

## Context Setup

I need to implement the Decommission Flow following the complete specifications in:

1. **Solution Document**: `/docs/planning/DECOMMISSION_FLOW_SOLUTION.md` (v2.1 - APPROVED)
2. **Milestone Definition**: `/docs/planning/DECOMMISSION_FLOW_MILESTONE.md`
3. **GitHub Parent Issue**: #952 (Milestone Definition)
4. **GitHub Sub-Issues**: #930-951 (22 detailed implementation tasks)
5. **GitHub Milestone**: "Decommission Flow Implementation (v2.5.0)" (Milestone #23)

**Architecture Requirements**:
- ADR-027 (Universal FlowTypeConfig Pattern)
- ADR-025 (Child Flow Service Pattern)
- ADR-006 (MFO Two-Table Pattern)
- ADR-012 (Status Management Separation)
- ADR-024 (TenantMemoryManager - memory=False)

**Phase Names** (CRITICAL - Must Match FlowTypeConfig):
- `decommission_planning` (NOT "planning")
- `data_migration` (NOT "data_retention")
- `system_shutdown` (NOT "execution" or "validation")

---

## Pre-Implementation Checklist

Before starting, verify:

1. **Read All Documentation**:
   ```bash
   # Read solution document
   Read /docs/planning/DECOMMISSION_FLOW_SOLUTION.md

   # Read milestone definition
   Read /docs/planning/DECOMMISSION_FLOW_MILESTONE.md

   # Read all ADRs
   Read /docs/adr/027-universal-flow-type-config-pattern.md
   Read /docs/adr/025-collection-flow-child-service-migration.md
   Read /docs/adr/006-master-flow-orchestrator.md
   Read /docs/adr/012-flow-status-management-separation.md
   Read /docs/adr/024-tenant-memory-manager-architecture.md

   # Read coding guide
   Read /docs/analysis/Notes/coding-agent-guide.md
   Read /.claude/agent_instructions.md
   ```

2. **Check Current State**:
   ```bash
   # Verify on correct branch
   git branch --show-current
   # Should be main or create feature branch

   # Check git status
   git status

   # Verify milestone exists
   gh issue view 952

   # List all sub-issues
   gh issue list --milestone "Decommission Flow Implementation (v2.5.0)"
   ```

3. **Create Feature Branch**:
   ```bash
   git checkout -b feature/decommission-flow-v2.5.0
   git push -u origin feature/decommission-flow-v2.5.0
   ```

---

## Phase 0: Mock Preservation (Issue #930)

**Objective**: Rename existing Decommission → "Decom" to preserve wireframes

**Agent Delegation**:
```
Task tool with subagent_type: "nextjs-ui-architect"

Prompt:
"Implement Issue #930: Rename Existing Decommission Section to Decom

Read the issue details from GitHub:
gh issue view 930 --json body --jq '.body'

Requirements:
1. Update src/components/Sidebar.tsx:
   - Change label: 'Decommission' → 'Decom'
   - Change href: '/decommission/overview' → '/decom/overview'
   - Move section after FinOps, before Observability

2. Rename directory:
   mv src/pages/decommission/ src/pages/decom/

3. Update all internal links in Decom pages to use /decom/* routes

4. Create URL redirects in next.config.js or middleware.ts:
   /decommission/* → /decom/*

5. Test all navigation flows manually

After implementation, provide summary of:
- Files modified
- Changes made
- Testing performed
- Any issues encountered
"
```

**Validation**:
```
Task tool with subagent_type: "qa-playwright-tester"

Prompt:
"Validate Issue #930 implementation.

Test Requirements:
1. Navigate to /decom/overview via sidebar
2. Verify Decom appears below FinOps, above Observability
3. Test old /decommission/* URLs redirect to /decom/*
4. Verify no console errors
5. Verify mock data displays correctly

Create Playwright test at tests/e2e/decommission/mock-preservation.spec.ts

Provide test results and any failures found."
```

**Pre-Commit Preparation**:
```
Task tool with subagent_type: "sre-precommit-enforcer"

Prompt:
"Prepare Issue #930 changes for Git commit.

1. Run all pre-commit checks:
   cd backend && pre-commit run --all-files
   npm run lint
   npm run typecheck

2. Fix ALL violations (no --no-verify shortcuts)

3. If linting/complexity issues, use devsecops-linting-engineer agent

4. Provide summary of:
   - Pre-commit results
   - Fixes applied
   - Files ready for commit
"
```

**Commit & Push**:
```bash
# After all validations pass
git add .
git commit -m "feat(decommission): Rename Decommission section to Decom for mock preservation

- Update Sidebar.tsx to rename 'Decommission' → 'Decom'
- Move section after FinOps, before Observability
- Rename src/pages/decommission/ → src/pages/decom/
- Add URL redirects /decommission/* → /decom/*
- Update all internal links
- Add E2E test for navigation

Closes #930

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin feature/decommission-flow-v2.5.0

# Mark issue as complete
gh issue close 930 --comment "✅ Implemented and tested. Mock pages preserved at /decom/*"
```

---

## Phase 1: Database Foundation (Issues #931-933)

### Issue #931: Database Schema

**Agent Delegation**:
```
Task tool with subagent_type: "pgvector-data-architect"

Prompt:
"Implement Issue #931: Create Decommission Database Schema

Read full issue details:
gh issue view 931 --json body --jq '.body'

Read solution document Section 3:
Read /docs/planning/DECOMMISSION_FLOW_SOLUTION.md (lines 200-400)

Requirements:
1. Create backend/alembic/versions/120_create_decommission_tables.py

2. Create 6 tables in migration schema:
   - decommission_flows (child flow - ADR-006)
   - decommission_plans
   - data_retention_policies
   - archive_jobs
   - decommission_execution_logs
   - decommission_validation_checks

3. CRITICAL: Phase columns MUST match FlowTypeConfig:
   - decommission_planning_status (NOT planning_status)
   - data_migration_status (NOT data_retention_status)
   - system_shutdown_status (NOT execution_status)

4. Add CHECK constraints for valid phase/status values

5. Make migration idempotent with IF EXISTS/IF NOT EXISTS

6. Test locally:
   cd backend && alembic upgrade head

7. Verify tables created:
   docker exec -it migration_postgres psql -U postgres -d migration_db -c '\dt migration.decommission*'

Provide:
- Complete migration file
- Test results
- Verification queries
"
```

**Validation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Validate Issue #931 database migration.

1. Run migration on fresh database
2. Verify all 6 tables exist in migration schema
3. Check phase column names match FlowTypeConfig exactly
4. Verify CHECK constraints
5. Test idempotency (run migration twice)
6. Check indexes created

Provide validation report with any issues found."
```

**Pre-Commit**:
```
Task tool with subagent_type: "sre-precommit-enforcer"

Prompt:
"Prepare Issue #931 for commit.
Run pre-commit, fix all violations, validate Alembic migration syntax."
```

**Commit**:
```bash
git add backend/alembic/versions/120_create_decommission_tables.py
git commit -m "feat(db): Add decommission flow database schema (6 tables)

- Create decommission_flows table (ADR-006 two-table pattern)
- Add decommission_plans for per-system planning
- Add data_retention_policies for compliance
- Add archive_jobs for data archival tracking
- Add decommission_execution_logs for audit trail
- Add decommission_validation_checks for post-decommission validation

Phase columns match FlowTypeConfig per ADR-027:
- decommission_planning_status
- data_migration_status
- system_shutdown_status

Closes #931

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin feature/decommission-flow-v2.5.0
gh issue close 931 --comment "✅ Migration created and tested. All 6 tables in migration schema."
```

### Issue #932: SQLAlchemy Models

**Agent Delegation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Implement Issue #932: Create SQLAlchemy Models

Read issue: gh issue view 932 --json body --jq '.body'
Read solution: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md (Section 3.2)

Requirements:
1. Create backend/app/models/decommission_flow.py with 6 model classes
2. All inherit from Base
3. Define relationships with proper foreign keys
4. Add type hints on all attributes
5. Add __repr__() for debugging
6. Handle JSONB columns properly
7. Register in backend/app/models/__init__.py

8. Test:
   - Import models in Python REPL
   - Create instance: flow = DecommissionFlow(flow_id=uuid4(), status='initialized')
   - Verify __repr__ output

9. Run mypy: cd backend && mypy app/models/decommission_flow.py

Provide complete model file and test results."
```

**Validation & Modularization**:
```
Task tool with subagent_type: "devsecops-linting-engineer"

Prompt:
"Validate Issue #932 models.

1. Run mypy type checking
2. Check for security issues (SQL injection prevention)
3. Verify no circular imports
4. If file >400 lines, modularize per file length guidelines
5. Run pre-commit checks

Provide validation report."
```

**Commit**:
```bash
git add backend/app/models/decommission_flow.py backend/app/models/__init__.py
git commit -m "feat(models): Add SQLAlchemy models for decommission flow

- Add DecommissionFlow model (child flow, ADR-006)
- Add DecommissionPlan model
- Add DataRetentionPolicy model
- Add ArchiveJob model
- Add DecommissionExecutionLog model
- Add DecommissionValidationCheck model

All models include:
- Type hints and proper relationships
- __repr__ for debugging
- JSONB serialization
- Passes mypy type checking

Closes #932

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push
gh issue close 932 --comment "✅ Models created with full type hints and relationships."
```

### Issue #933: Repository Layer

**Agent Delegation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Implement Issue #933: Create DecommissionFlowRepository

Read issue: gh issue view 933 --json body --jq '.body'

Requirements:
1. Create backend/app/repositories/decommission_flow_repository.py
2. Implement all CRUD methods with multi-tenant scoping
3. All queries MUST include client_account_id AND engagement_id
4. Use async/await throughout
5. Add proper exception handling
6. Type hints and docstrings

7. Create unit tests: backend/tests/repositories/test_decommission_flow_repository.py
8. Run tests: cd backend && pytest tests/repositories/test_decommission_flow_repository.py -v

Pattern: backend/app/repositories/assessment_flow_repository.py

Provide complete implementation and test results."
```

**Validation**:
```
Task tool with subagent_type: "devsecops-linting-engineer"

Prompt:
"Validate Issue #933 repository implementation.

1. Run pytest with coverage
2. Verify multi-tenant scoping in ALL queries
3. Check for SQL injection risks
4. Run mypy type checking
5. Pre-commit validation

Provide test coverage report and any issues."
```

**Commit**:
```bash
git add backend/app/repositories/decommission_flow_repository.py \
        backend/tests/repositories/test_decommission_flow_repository.py

git commit -m "feat(repository): Add DecommissionFlowRepository with multi-tenant scoping

- Implement all CRUD operations
- Multi-tenant scoping on all queries (client_account_id + engagement_id)
- Async/await throughout
- Type hints and docstrings
- Unit tests with 100% coverage

Closes #933

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push
gh issue close 933 --comment "✅ Repository layer complete with unit tests."
```

---

## Phase 2: Backend API & MFO (Issues #934-936)

### Issue #934: MFO Integration Layer

**Agent Delegation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Implement Issue #934: MFO Integration Layer

Read issue: gh issue view 934 --json body --jq '.body'
Read ADR-006: /docs/adr/006-master-flow-orchestrator.md

Requirements:
1. Create backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py

2. Implement functions:
   - create_decommission_via_mfo() - Atomic master + child creation
   - get_decommission_status_via_mfo() - Returns child status (ADR-012)
   - update_decommission_phase_via_mfo() - Syncs master + child
   - resume_decommission_flow()

3. Use async with db.begin() for atomic transactions

4. Create integration tests:
   backend/tests/integration/test_decommission_mfo.py

5. Run tests: cd backend && pytest tests/integration/test_decommission_mfo.py -v

Pattern: backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py

Provide implementation and test results."
```

**Validation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Validate Issue #934 MFO integration.

1. Test atomic transactions (verify rollback on failure)
2. Test multi-tenant scoping
3. Verify ADR-012 compliance (child status returned)
4. Integration tests pass
5. Pre-commit validation

Provide validation report."
```

**Commit**:
```bash
git add backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py \
        backend/tests/integration/test_decommission_mfo.py

git commit -m "feat(mfo): Add MFO integration layer for decommission flow

- Implement create_decommission_via_mfo with atomic transactions
- Add get_decommission_status_via_mfo (returns child status per ADR-012)
- Add update_decommission_phase_via_mfo
- Add resume_decommission_flow
- Integration tests for all functions

Per ADR-006 two-table pattern
Per ADR-012 status management separation

Closes #934

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push
gh issue close 934 --comment "✅ MFO integration complete with atomic transactions."
```

### Issue #935: Flow Management Endpoints

**Agent Delegation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Implement Issue #935: Flow Management Endpoints

Read issue: gh issue view 935 --json body --jq '.body'

Requirements:
1. Create backend/app/api/v1/endpoints/decommission_flow/flow_management.py

2. Implement endpoints:
   - POST /api/v1/decommission-flow/initialize
   - GET /api/v1/decommission-flow/{flow_id}/status
   - POST /api/v1/decommission-flow/{flow_id}/resume
   - POST /api/v1/decommission-flow/{flow_id}/pause
   - POST /api/v1/decommission-flow/{flow_id}/cancel

3. All endpoints require authentication via get_current_user
4. Use background_tasks for agent execution
5. Register router in backend/app/api/router_registry.py

6. Integration tests: backend/tests/integration/test_decommission_endpoints.py

7. Test OpenAPI docs: http://localhost:8000/docs

Pattern: backend/app/api/v1/endpoints/assessment_flow/flow_management.py

Provide implementation and test results."
```

**Router Registration**:
```
After creating endpoints, update router_registry.py:

from app.api.v1.endpoints.decommission_flow import flow_management

app.include_router(
    flow_management.router,
    prefix="/api/v1/decommission-flow",
    tags=["decommission"]
)
```

**Validation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Validate Issue #935 endpoints.

1. Test all 5 endpoints via pytest
2. Verify OpenAPI docs generated correctly
3. Test authentication required
4. Test background tasks start
5. Pre-commit validation

Provide test results and OpenAPI screenshot."
```

**Commit**:
```bash
git add backend/app/api/v1/endpoints/decommission_flow/flow_management.py \
        backend/app/api/router_registry.py \
        backend/tests/integration/test_decommission_endpoints.py

git commit -m "feat(api): Add decommission flow management endpoints

- POST /initialize - Create new decommission flow
- GET /{flow_id}/status - Get flow status
- POST /{flow_id}/resume - Resume paused flow
- POST /{flow_id}/pause - Pause running flow
- POST /{flow_id}/cancel - Cancel flow
- Register router with /api/v1/decommission-flow prefix
- Integration tests for all endpoints

All endpoints require authentication
Background tasks start agent execution

Closes #935

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push
gh issue close 935 --comment "✅ Flow management endpoints complete with integration tests."
```

### Issue #936: Pydantic Schemas

**Agent Delegation**:
```
Task tool with subagent_type: "python-crewai-fastapi-expert"

Prompt:
"Implement Issue #936: Pydantic Schemas

Read issue: gh issue view 936 --json body --jq '.body'

Requirements:
1. Create backend/app/schemas/decommission_flow.py

2. Create schemas:
   - DecommissionFlowCreateRequest
   - DecommissionFlowResponse
   - DecommissionFlowStatusResponse
   - UpdatePhaseRequest
   - ResumeFlowRequest

3. CRITICAL: Use snake_case field naming:
   - decommission_planning (NOT decommissionPlanning)
   - data_migration (NOT dataMigration)
   - system_shutdown (NOT systemShutdown)

4. Add field validators for enums (status, phase)

5. Test schema validation with example data

Provide complete schemas and validation tests."
```

**Validation**:
```
Task tool with subagent_type: "devsecops-linting-engineer"

Prompt:
"Validate Issue #936 schemas.

1. Verify all field names are snake_case
2. Test enum validators reject invalid values
3. Run mypy type checking
4. Pre-commit validation

Provide validation report."
```

**Commit**:
```bash
git add backend/app/schemas/decommission_flow.py

git commit -m "feat(schemas): Add Pydantic schemas for decommission flow API

- DecommissionFlowCreateRequest
- DecommissionFlowResponse
- DecommissionFlowStatusResponse
- UpdatePhaseRequest
- ResumeFlowRequest

All schemas use snake_case per API conventions
Field validators for phase/status enums
Passes mypy type checking

Closes #936

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push
gh issue close 936 --comment "✅ Pydantic schemas complete with validation."
```

---

## Phase 3-6 Implementation Pattern

**For each remaining issue (#937-951), follow this pattern**:

1. **Delegate to Appropriate Agent**:
   - Backend: `python-crewai-fastapi-expert`
   - Frontend: `nextjs-ui-architect`
   - Testing: `qa-playwright-tester`
   - Pre-commit: `sre-precommit-enforcer`

2. **Agent Prompt Template**:
   ```
   Task tool with subagent_type: "<agent-type>"

   Prompt:
   "Implement Issue #<number>: <title>

   Read full issue details:
   gh issue view <number> --json body --jq '.body'

   Read solution document section:
   Read /docs/planning/DECOMMISSION_FLOW_SOLUTION.md (Section <X>)

   Requirements:
   [Copy from issue body]

   Pattern: <reference-file-path>

   Provide:
   - Complete implementation
   - Test results
   - Any issues encountered
   "
   ```

3. **Validation Pattern**:
   ```
   Task tool with subagent_type: "qa-playwright-tester" or "devsecops-linting-engineer"

   Prompt:
   "Validate Issue #<number> implementation.

   1. Run all tests
   2. Pre-commit checks
   3. Manual testing if applicable
   4. Provide validation report
   "
   ```

4. **Commit Pattern**:
   ```bash
   git add <files>
   git commit -m "<type>(<scope>): <description>

   <detailed-changes>

   Closes #<number>

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"

   git push
   gh issue close <number> --comment "✅ <summary>"
   ```

---

## Phase 3: Child Flow Service & Agents (Issues #937-939)

### Agents to Use:
- **#937** (Child Flow Service): `python-crewai-fastapi-expert`
- **#938** (Agent Pool): `python-crewai-fastapi-expert`
- **#939** (Crew Functions): `python-crewai-fastapi-expert`

**Key Requirements**:
- **memory=False** per ADR-024 (use TenantMemoryManager)
- Phase names match FlowTypeConfig
- No `crew_class` usage (deprecated per ADR-025)

---

## Phase 4: Frontend Implementation (Issues #940-946)

### Agents to Use:
- **#940** (API Service): `nextjs-ui-architect`
- **#941** (React Query Hooks): `nextjs-ui-architect`
- **#942-946** (UI Pages): `nextjs-ui-architect`

**Key Requirements**:
- snake_case field naming (decommission_planning, data_migration, system_shutdown)
- React Query polling: 5s active, 15s idle, stop when completed
- All data via hooks (no direct API calls)

---

## Phase 5: Integration & Testing (Issues #947-949)

### Agents to Use:
- **#947** (Assessment Integration): `python-crewai-fastapi-expert`
- **#948** (Wave Integration): `python-crewai-fastapi-expert`
- **#949** (E2E Testing): `qa-playwright-tester`

**Key Requirements**:
- Integration tests for 6R Retire → Decommission
- Integration tests for post-migration → Decommission
- Complete E2E test suite covering all 3 phases

---

## Phase 6: Documentation (Issues #950-951)

### Agents to Use:
- **#950** (API Docs): `docs-curator`
- **#951** (User Guide): `docs-curator`

**Key Requirements**:
- OpenAPI docs at /docs
- Postman collection exported
- User guide with screenshots
- Admin runbook for operations

---

## Final Steps: Pull Request Creation

### 1. Run Complete Validation Suite

**Full Test Suite**:
```
Task tool with subagent_type: "qa-playwright-tester"

Prompt:
"Run complete test validation for decommission flow.

1. Backend tests:
   cd backend && pytest tests/ -v --cov=app --cov-report=html

2. Frontend E2E tests:
   npm run test:e2e -- tests/e2e/decommission/

3. Linting:
   npm run lint
   npm run typecheck
   cd backend && ruff check .
   cd backend && mypy app/

4. Pre-commit (final check):
   cd backend && pre-commit run --all-files

5. Manual smoke test:
   - Initialize decommission flow
   - Navigate through all 3 phases
   - Export report

Provide comprehensive test report with:
- Test coverage percentage
- Number of passing/failing tests
- Any issues found
- Screenshots of smoke test
"
```

### 2. Code Review Preparation

**Generate PR Description**:
```
Task tool with subagent_type: "docs-curator"

Prompt:
"Generate comprehensive PR description for decommission flow implementation.

Read all closed issues #930-951:
for i in {930..951}; do gh issue view $i; done

Generate PR description with:

## Summary
Complete implementation of Decommission Flow v2.5.0

## Changes
### Phase 0: Preparation
- #930: Mock preservation

### Phase 1: Database Foundation
- #931: Database schema (6 tables)
- #932: SQLAlchemy models
- #933: Repository layer

### Phase 2: Backend API
- #934: MFO integration
- #935: Flow management endpoints
- #936: Pydantic schemas

### Phase 3: Agents
- #937: Child flow service (ADR-025)
- #938: Agent pool (7 agents, ADR-024)
- #939: Crew functions (3 phases)

### Phase 4: Frontend
- #940: API service layer
- #941: React Query hooks
- #942-946: UI pages (Overview, Planning, Data Migration, System Shutdown, Export)

### Phase 5: Integration & Testing
- #947: Assessment integration (6R Retire)
- #948: Wave execution integration (post-migration)
- #949: E2E testing (Playwright)

### Phase 6: Documentation
- #950: API documentation
- #951: User guide and runbook

## Architecture Compliance
- ✅ ADR-027: FlowTypeConfig pattern
- ✅ ADR-025: Child flow service pattern
- ✅ ADR-006: MFO two-table pattern
- ✅ ADR-012: Status management separation
- ✅ ADR-024: TenantMemoryManager (memory=False)

## Testing
- Backend test coverage: X%
- E2E tests: X passing
- Pre-commit: All checks pass

## Phase Names
All phase names match FlowTypeConfig:
- decommission_planning
- data_migration
- system_shutdown

## Closes Issues
Closes #952 (parent issue)
Closes #930, #931, #932, #933, #934, #935, #936, #937, #938, #939, #940, #941, #942, #943, #944, #945, #946, #947, #948, #949, #950, #951

## Screenshots
[Agent to generate screenshots of key features]

## Migration Notes
1. Run Alembic migration: `alembic upgrade head`
2. No breaking changes to existing flows
3. New /api/v1/decommission-flow/* endpoints

## Reviewers
@<team-members>

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
"
```

### 3. Create Pull Request

```bash
# Ensure all changes committed and pushed
git status
git push origin feature/decommission-flow-v2.5.0

# Create PR
gh pr create \
  --title "feat: Decommission Flow Implementation (v2.5.0)" \
  --body "$(cat pr_description.md)" \
  --base main \
  --head feature/decommission-flow-v2.5.0 \
  --milestone "Decommission Flow Implementation (v2.5.0)" \
  --label "feature,backend,frontend,testing,documentation"

# Get PR URL
PR_URL=$(gh pr view --json url --jq '.url')
echo "Pull Request created: $PR_URL"
```

### 4. Request Reviews

```bash
# Add reviewers
gh pr edit --add-reviewer <team-member-1>,<team-member-2>

# Add to project board
gh pr edit --add-project "AI Force Assess Roadmap"

# Comment on parent issue
gh issue comment 952 --body "🎉 Implementation complete! Pull request ready for review: $PR_URL

All 22 sub-issues completed and tested:
- ✅ Phase 0: Mock preservation
- ✅ Phase 1: Database foundation (3 issues)
- ✅ Phase 2: Backend API (3 issues)
- ✅ Phase 3: Agents (3 issues)
- ✅ Phase 4: Frontend (7 issues)
- ✅ Phase 5: Integration & Testing (3 issues)
- ✅ Phase 6: Documentation (2 issues)

Test coverage: X%
All pre-commit checks: ✅ PASS

🤖 Generated with Claude Code"
```

---

## Post-PR Actions

### Monitor CI/CD Pipeline
```bash
# Watch GitHub Actions
gh pr checks --watch

# If failures, delegate to appropriate agent to fix
```

### Address Review Comments
```
For each review comment:

Task tool with subagent_type: "<appropriate-agent>"

Prompt:
"Address PR review comment:

Comment: <review-comment-text>
File: <file-path>
Line: <line-number>

Make the requested changes, test, and push."
```

### Merge After Approval
```bash
# After all approvals and CI passes
gh pr merge --squash --delete-branch

# Update parent issue
gh issue comment 952 --body "✅ PR merged! Decommission Flow v2.5.0 is now in main branch.

Deployment: <deployment-url>
Documentation: /docs/user-guide/DECOMMISSION_FLOW.md

Thank you reviewers! 🎉"

# Close parent issue
gh issue close 952 --comment "✅ Milestone complete! All 22 sub-issues implemented, tested, and merged."
```

---

## Critical Reminders

### NEVER Do These Things:
❌ Use `--no-verify` to skip pre-commit
❌ Hardcode phase names other than FlowTypeConfig phases
❌ Use `memory=True` in CrewAI agents (violates ADR-024)
❌ Use `crew_class` in FlowTypeConfig (violates ADR-025)
❌ Skip multi-tenant scoping in queries
❌ Use camelCase for API fields (must be snake_case)
❌ Skip testing before committing
❌ Create commits without agent validation

### ALWAYS Do These Things:
✅ Read issue details from GitHub before implementing
✅ Delegate to appropriate CC agents
✅ Run all tests (pytest, E2E, linting)
✅ Validate with pre-commit before committing
✅ Use atomic commits (one issue per commit)
✅ Include proper commit messages with Co-Authored-By
✅ Close issues after validation
✅ Test in Docker environment
✅ Verify phase names match FlowTypeConfig
✅ Document all changes

---

## Agent Selection Guide

| Task Type | Agent | Example |
|-----------|-------|---------|
| Database schema/migrations | `pgvector-data-architect` | Alembic migrations |
| Backend Python/FastAPI | `python-crewai-fastapi-expert` | API endpoints, services |
| Frontend React/TypeScript | `nextjs-ui-architect` | UI pages, components |
| E2E testing | `qa-playwright-tester` | Playwright tests |
| Pre-commit validation | `sre-precommit-enforcer` | Linting, security |
| Linting/complexity | `devsecops-linting-engineer` | Code quality |
| Documentation | `docs-curator` | User guides, API docs |

---

## Success Criteria

Before creating PR, verify:

- [ ] All 22 issues closed (#930-951)
- [ ] All commits pushed to feature branch
- [ ] Backend test coverage >80%
- [ ] All E2E tests passing
- [ ] Pre-commit checks pass
- [ ] No hardcoded phase names (except FlowTypeConfig phases)
- [ ] All API fields use snake_case
- [ ] memory=False in all agents
- [ ] Multi-tenant scoping in all queries
- [ ] Documentation complete
- [ ] Manual smoke test passed

---

## Estimated Timeline

- **Phase 0**: 2-3 hours (1 issue)
- **Phase 1**: 1-2 days (3 issues)
- **Phase 2**: 1-2 days (3 issues)
- **Phase 3**: 2-3 days (3 issues)
- **Phase 4**: 3-4 days (7 issues)
- **Phase 5**: 2-3 days (3 issues)
- **Phase 6**: 1 day (2 issues)

**Total**: 10-17 days (2-3.5 weeks)

With proper agent delegation and parallel execution, can be accelerated significantly.

---

## Emergency Contacts

If stuck:
1. Check solution document: `/docs/planning/DECOMMISSION_FLOW_SOLUTION.md`
2. Check coding guide: `/docs/analysis/Notes/coding-agent-guide.md`
3. Check ADRs in `/docs/adr/`
4. Ask user for clarification

---

**END OF IMPLEMENTATION PROMPT**

This prompt should be used at the start of a fresh Claude Code session to implement the complete Decommission Flow with full multi-agent orchestration.
