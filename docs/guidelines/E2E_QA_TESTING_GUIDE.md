# E2E QA Testing Guide for AI Force Assess Migration Platform

**Version**: 1.1
**Last Updated**: November 30, 2025
**Purpose**: Tool-agnostic guide for QA testing agents

---

## Related Documentation

This guide focuses on **how to test** the platform. For detailed implementation and architecture information, see:

| Flow | Implementation Guide |
|------|---------------------|
| Discovery | `/docs/e2e-flows/01_Discovery/00_Discovery_Flow_Complete_Guide.md` |
| Collection | `/docs/e2e-flows/02_Collection/00_Collection_Flow_Complete_Guide.md` |
| Assessment | `/docs/e2e-flows/03_Assess/00_Assessment_Flow_Complete_Guide.md` |
| Plan | `/docs/e2e-flows/04_Plan/00_Planning_Flow_Complete_Guide.md` |
| Decommission | `/docs/e2e-flows/05_Decommission/00_Decommission_Flow_Complete_Guide.md` |

---

## Table of Contents

1. [Overview](#overview)
2. [Test Environment](#test-environment)
3. [Flow Dependencies](#flow-dependencies)
4. [Testing Workflow by Flow](#testing-workflow-by-flow)
5. [Test Data Requirements](#test-data-requirements)
6. [Known Issues and Workarounds](#known-issues-and-workarounds)
7. [Bug Reporting Guidelines](#bug-reporting-guidelines)
8. [Success Criteria](#success-criteria)

---

## Overview

The AI Force Assess Migration Platform is a cloud migration assessment tool with four main flows that must be tested in sequence:

```
Discovery → Collection → Assessment → Plan
```

| Flow | Purpose | Key Output |
|------|---------|------------|
| **Discovery** | Import CMDB data, validate, map attributes | Assets in inventory |
| **Collection** | Analyze data gaps, generate questionnaires | Filled questionnaires |
| **Assessment** | Run AI-powered 6R analysis | Migration recommendations |
| **Plan** | Create migration waves and timelines | Migration roadmap |

---

## Test Environment

### Application URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `http://localhost:8081` | User interface |
| Backend API | `http://localhost:8000` | REST API |
| API Docs | `http://localhost:8000/docs` | Swagger UI |
| Database | `localhost:5433` | PostgreSQL |

### Verify Environment

```bash
# Check Docker containers
docker ps | grep migration

# Expected containers:
# - migration_backend
# - migration_frontend
# - migration_postgres

# Check backend health
curl http://localhost:8000/api/health

# Check frontend
curl -I http://localhost:8081
```

### Database Access

```bash
docker exec -it migration_postgres psql -U postgres -d migration_db
```

---

## Flow Dependencies

### Critical: Sequential Testing Required

Flows MUST be tested in order due to data dependencies:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Discovery  │────▶│ Collection  │────▶│ Assessment  │────▶│    Plan     │
│             │     │             │     │             │     │             │
│ Creates:    │     │ Requires:   │     │ Requires:   │     │ Requires:   │
│ - Assets    │     │ - Assets    │     │ - Canon Apps│     │ - 6R Recs   │
│ - Canon Apps│     │ Creates:    │     │ Creates:    │     │ Creates:    │
│             │     │ - Gap Data  │     │ - 6R Recs   │     │ - Waves     │
│             │     │ - Questions │     │             │     │ - Timeline  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### MFO Two-Table Pattern (Critical Architecture)

All flows use the Master Flow Orchestrator (MFO) with two types of IDs:

| ID Type | Table | Purpose |
|---------|-------|---------|
| **Master Flow ID** | `crewai_flow_state_extensions` | Internal MFO routing |
| **Child Flow ID** | `assessment_flows`, `discovery_flows`, etc. | User-facing identifier |

**Important**: URL paths use child flow IDs, but MFO methods use master flow IDs internally.

---

## Testing Workflow by Flow

### 1. Discovery Flow

**Purpose**: Import and validate infrastructure data from CMDB

#### Steps

1. **Navigate to Discovery**
   - URL: `http://localhost:8081`
   - Click "Discovery" in sidebar
   - Select "Data Import" or "Overview"

2. **Start New Discovery**
   - Click "New Discovery" or "Start Discovery"
   - Upload CMDB CSV file
   - Wait for file validation

3. **Data Validation Phase**
   - Verify row counts match uploaded data
   - Check for validation errors (red indicators)
   - All green checkmarks = success

4. **Attribute Mapping Phase**
   - Map source columns to target schema
   - Required mappings:
     - `hostname` → Server Name
     - `ip_address` → IP Address
     - `os` → Operating System
     - `application_name` → Application
   - Click "Approve Mappings"

5. **Inventory Processing Phase**
   - Wait for processing to complete
   - Verify assets appear in inventory table

#### Success Criteria
- [ ] File upload succeeds
- [ ] Validation shows green checkmarks
- [ ] Mappings approved successfully
- [ ] Assets visible in inventory
- [ ] Canonical applications created

#### Common Issues
- **Stuck at "Processing"**: Check backend logs for errors
- **CheckViolationError**: Run `alembic upgrade head` (Bug #1167 fix)

---

### 2. Collection Flow

**Purpose**: Analyze data gaps and collect missing information

**Prerequisites**: Discovery completed with assets in inventory

#### Steps

1. **Navigate to Collection**
   - Click "Collection" in sidebar
   - Select "Overview"

2. **Start New Collection**
   - Click "Start New Collection"
   - Select assets to include (checkboxes)
   - Click "Start Collection"

3. **Gap Analysis Phase**
   - Wait for AI to analyze data gaps
   - Review gap categories:
     - Critical (red)
     - High (orange)
     - Medium (yellow)
     - Low (green)

4. **Questionnaire Generation Phase**
   - Click "Continue" after gap analysis
   - Verify questions organized by section
   - Typical sections: Application Details, Infrastructure, Security, Dependencies

5. **Fill Questionnaire (Optional)**
   - Answer questions for each asset
   - Click "Save" or "Submit"

#### Success Criteria
- [ ] Gap analysis completes with counts
- [ ] Questionnaire generated for selected assets
- [ ] Auto-progression works between phases
- [ ] Can save/submit questionnaire answers

---

### 3. Assessment Flow

**Purpose**: Run AI-powered assessments and generate 6R recommendations

**Prerequisites**: Collection completed OR canonical applications exist

#### Steps

1. **Navigate to Assessment**
   - Click "Assess" in sidebar
   - Select "Overview" or "Treatment"

2. **Start New Assessment**
   - Click "New Assessment"
   - Select applications from list
   - Click "Start Assessment"

3. **Phase Progression** (6 phases, auto-progresses)

| Phase | Name | Progress | What It Does |
|-------|------|----------|--------------|
| 1 | Architecture Standards | 0% → 16% | Cloud readiness evaluation |
| 2 | Migration Complexity | 16% → 33% | Technical complexity scoring |
| 3 | Dependency Analysis | 33% → 50% | Application dependencies |
| 4 | Technical Debt | 50% → 66% | Tech debt quantification |
| 5 | Risk Assessment | 66% → 83% | Migration risk evaluation |
| 6 | 6R Recommendations | 83% → 100% | Strategy generation |

4. **Verify 6R Recommendations**
   - Each application should have ONE strategy:
     - **Rehost**: Lift and shift
     - **Replatform**: Minor optimizations
     - **Refactor**: Code changes for cloud
     - **Rearchitect**: Significant redesign
     - **Replace**: SaaS replacement
     - **Retire**: Decommission

#### Success Criteria
- [ ] All 6 phases complete
- [ ] Progress reaches 100%
- [ ] Each application has 6R recommendation
- [ ] Confidence scores present (0-1)
- [ ] Reasoning provided for each recommendation

#### Common Issues
- **Phase 6 fails for all apps**: Was Bug #1168 (FK constraint) - fixed in migration 142
- **Large batches (50+ apps)**: May cause JSON truncation - test with smaller batches

---

### 4. Plan Flow

**Purpose**: Create migration waves, timelines, and roadmaps

**Prerequisites**: Assessment completed with 6R recommendations

#### Steps

1. **Navigate to Plan**
   - Click "Plan" in sidebar
   - Select "Overview" or "Wave Planning"

2. **Review Wave Planning**
   - Check applications grouped by recommendation
   - Verify wave assignments
   - Test drag-and-drop reordering

3. **Review Timeline**
   - Navigate to "Timeline" tab
   - Check Gantt chart view
   - Toggle Day/Week/Month views

4. **Review Roadmap**
   - Navigate to "Roadmap" tab
   - Check wave details
   - Verify resource allocation

#### Success Criteria
- [ ] Waves display correctly
- [ ] Timeline Gantt chart renders
- [ ] Day/Week/Month toggle works
- [ ] Drag-and-drop reordering works
- [ ] Resource allocation visible

---

## Test Data Requirements

### CMDB CSV Format

```csv
hostname,ip_address,os,environment,application_name,criticality,owner,location
web-server-01,10.0.1.10,RHEL 8.5,production,Customer Portal,high,IT Ops,DC-East
db-server-01,10.0.1.20,Ubuntu 22.04,production,PostgreSQL Primary,critical,DBA Team,DC-East
app-server-01,10.0.1.30,Windows 2019,staging,API Gateway,medium,Dev Team,DC-West
```

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `hostname` | Unique server identifier | `web-server-01` |
| `ip_address` | Server IP address | `10.0.1.10` |
| `os` | Operating system | `RHEL 8.5` |
| `environment` | Deployment environment | `production` |
| `application_name` | Application running on server | `Customer Portal` |

### Recommended Fields

| Field | Description | Example |
|-------|-------------|---------|
| `criticality` | Business criticality | `critical`, `high`, `medium`, `low` |
| `owner` | Responsible team | `IT Ops` |
| `location` | Data center location | `DC-East` |

### Sample Test Data

For comprehensive testing, include:
- **10-30 assets** for quick tests
- **50+ assets** for batch processing tests
- Mix of:
  - Web servers (Linux/Windows)
  - Database servers (PostgreSQL, MongoDB, Oracle)
  - Application servers
  - Legacy systems (COBOL, SAP)
  - Cloud services

---

## Known Issues and Workarounds

### Bug #1167 - Discovery Inventory CheckViolationError

**Symptom**: Discovery stuck at "Processing asset inventory..."
**Root Cause**: `environment` not in allowed conflict types
**Fix**: Run `cd backend && alembic upgrade head`
**Status**: Fixed in migration 142

### Bug #1168 - 6R Recommendation FK Violation

**Symptom**: Phase 6 (6R Recommendations) fails for all applications
**Root Cause**: Child flow ID passed instead of master flow ID
**Fix**: Run `cd backend && alembic upgrade head`
**Status**: Fixed in migration 142 + recommendation_executor.py

### Bug #1169 - UUID Display on Risk Page

**Symptom**: Application tabs show truncated UUIDs instead of names
**Location**: `/assessment/{id}/risk`
**Impact**: Low - cosmetic issue
**Status**: Open

---

## Bug Reporting Guidelines

### Required Information

1. **Title**: Clear, concise description
2. **Flow**: Discovery / Collection / Assessment / Plan
3. **Steps to Reproduce**: Numbered list
4. **Expected Result**: What should happen
5. **Actual Result**: What actually happened
6. **Screenshots**: Relevant screenshots
7. **Logs**: Backend error logs (`docker logs migration_backend`)
8. **Environment**: Docker version, browser

### Severity Guidelines

| Severity | Criteria | Example |
|----------|----------|---------|
| **Critical** | Blocks entire flow, no workaround | FK constraint prevents all 6R |
| **High** | Major feature broken, difficult workaround | Phase stuck indefinitely |
| **Medium** | Feature partially broken, has workaround | Display shows wrong data |
| **Low** | Minor issue, cosmetic | UUID shown instead of name |

### Bug Report Template

```markdown
## Bug Title

**Flow**: [Discovery/Collection/Assessment/Plan]
**Severity**: [Critical/High/Medium/Low]

### Steps to Reproduce
1. Navigate to...
2. Click on...
3. Wait for...

### Expected Result
[What should happen]

### Actual Result
[What actually happened]

### Error Messages
```
[Paste error from console or backend logs]
```

### Screenshots
- [screenshot1.png]
- [screenshot2.png]

### Environment
- Docker: [version]
- Browser: [Chrome/Firefox/etc]
- OS: [macOS/Linux/Windows]
```

---

## Success Criteria

### Full E2E Test Pass Requirements

| Flow | Criteria |
|------|----------|
| **Discovery** | Assets created in inventory, canonical apps generated |
| **Collection** | Gap analysis complete, questionnaires generated |
| **Assessment** | All 6 phases complete, 6R recommendations for all apps |
| **Plan** | Waves assigned, timeline renders, roadmap displays |

### Minimum Test Coverage

- [ ] Discovery with 10+ assets
- [ ] Collection gap analysis runs
- [ ] Assessment completes all 6 phases
- [ ] Plan displays waves and timeline
- [ ] No Critical or High severity bugs blocking flow completion

---

## Quick Reference

| Action | URL/Command |
|--------|-------------|
| Frontend | `http://localhost:8081` |
| Backend API | `http://localhost:8000` |
| View backend logs | `docker logs migration_backend -f` |
| Run migrations | `cd backend && alembic upgrade head` |
| Database access | `docker exec -it migration_postgres psql -U postgres -d migration_db` |
| Restart backend | `docker restart migration_backend` |

---

*This guide is tool-agnostic and can be used with any QA testing framework (Playwright, Cypress, Selenium, manual testing, or AI agents).*
