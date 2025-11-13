# E2E Flow: Collection Phase - Comprehensive Implementation Guide

**Last Updated:** November 2025
**Current Implementation:** Two-Phase Gap Analysis + Intelligent Questionnaire Generation

This document outlines the end-to-end user and data flow for the **Collection** phase of the migration process, fully integrated with the Master Flow Orchestrator (MFO) architecture and featuring intelligent CrewAI agents for gap analysis and adaptive questionnaire generation.

---

## 1. Executive Summary

### Purpose
The Collection Flow bridges the gap between automated discovery and comprehensive assessment by intelligently collecting missing asset data through:

1. **Two-Phase Gap Analysis** - Programmatic scanning + AI enhancement
2. **Intelligent Questionnaire Generation** - Context-aware MCQ questions (Issue #980)
3. **Asset-Aware Deduplication** - Engagement-scoped questionnaires shared across flows
4. **Adaptive Forms** - Dynamic question display based on data gaps (Issue #795)

### Key Architectural Changes (October-November 2025)

**✅ Intelligent Questionnaire Generation (Issue #980 - November 2025)**
- Programmatic gap detection identifies 22 critical attributes
- AI agents enhance gaps with confidence scores and suggested resolutions
- Context-aware MCQ options adapt based on asset characteristics (EOL status, criticality)
- 90.9% MCQ question format (target: >80%)
- Zero generic "What is the..." questions

**✅ Asset-Aware Questionnaire Deduplication (November 2025)**
- Questionnaires linked to `(engagement_id, asset_id)` instead of `collection_flow_id`
- Same asset in multiple flows = user answers once, data reused
- Partial unique index enables gradual migration without breaking existing flows

**✅ Two-Phase Gap Analysis (October 2025)**
- **Tier 1 (Programmatic)**: Fast, deterministic field-level gap detection
- **Tier 2 (AI Enhancement)**: Confidence scoring, resolution suggestions, context analysis
- Gaps persisted to `collection_data_gaps` table with priority/severity

**✅ Adaptive Forms Working as Designed (Issue #795 - October 2025)**
- Fewer questions = better data quality (not a bug!)
- Forms show only gaps per asset (Asset 1: 10 questions, Asset 2: 3 questions)
- Intelligent filtering based on existing data completeness

---

## 2. MFO Integration Architecture

The Collection flow follows the **Master Flow Orchestrator** pattern (ADR-006):

### Two-Table Pattern (ADR-012)

**Master Table**: `crewai_flow_state_extensions`
- Purpose: Lifecycle management (`running`, `paused`, `completed`)
- Primary ID: `master_flow_id` (UUID)
- Used by: MFO endpoints `/api/v1/master-flows/*`

**Child Table**: `collection_flows`
- Purpose: Operational state (phases, UI display, selected assets)
- Primary ID: `id` (internal UUID)
- External ID: `flow_id` (UUID, used in legacy endpoints)
- Linked via: `master_flow_id` foreign key to master table

### API Pattern

**ALWAYS use `master_flow_id` for:**
- `/api/v1/master-flows/*` - Flow lifecycle operations (create, resume, pause, delete)
- Frontend flow state queries
- Cross-flow coordination

**Collection-specific operations use:**
- `/api/v1/collection/*` - Collection operations (questionnaires, gap analysis)
- Accept `master_flow_id` or legacy `flow_id` (internally resolved)

---

## 3. Updated Phase Progression (7 Phases)

**Migration 076_remap_collection_flow_phases** consolidated 8 phases → 7 phases:

| Phase | Name | Purpose | CrewAI Agents | Duration | Auto/Manual |
|-------|------|---------|---------------|----------|-------------|
| 1 | `initialization` | Setup flow state, load config | None | <1s | Auto |
| 2 | `asset_selection` | Identify assets, collect initial data | Platform Detection Agent, Data Collection Agent | 10-30s | User-initiated |
| 3 | `gap_analysis` | Two-phase gap detection (programmatic + AI) | Gap Analysis Specialist (tier_2 only) | 15-45s | Auto |
| 4 | `questionnaire_generation` | Generate context-aware MCQ questions | Questionnaire Designer Agent | 10-30s | Auto |
| 5 | `manual_collection` | User completes adaptive forms | None | Minutes-Hours | Manual |
| 6 | `data_validation` | Validate responses, resolve conflicts | Quality Assessment Agent | 5-15s | Auto |
| 7 | `finalization` | Prepare handoff to Assessment Flow | None | <5s | Auto |

**Key Changes from Previous Version:**
- ❌ Removed: `platform_detection` and `automated_collection` (separate phases)
- ✅ Added: `asset_selection` (consolidates both removed phases)
- ✅ Updated: `gap_analysis` now two-phase (tier_1 + tier_2)
- ✅ Updated: `questionnaire_generation` now uses Issue #980 intelligent builders

---

## 4. Two-Phase Gap Analysis Architecture (October 2025)

### Tier 1: Programmatic Gap Scanner (Fast, Deterministic)

**Purpose**: Detect missing/incomplete fields by comparing assets against 22 critical attributes

**Implementation**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/collection/gap_analysis/tier_processors.py`

**Critical Attributes Checked** (from `CriticalAttributesDefinition`):
```python
CRITICAL_ATTRIBUTES = {
    "infrastructure": ["operating_system", "cpu_cores", "memory_gb", "storage_gb",
                      "network_bandwidth", "virtualization_type"],
    "application": ["technology_stack", "architecture_pattern", "integration_points",
                   "data_volume", "application_type"],
    "business": ["business_criticality", "change_tolerance", "compliance_requirements",
                "stakeholder_impact"],
    "technical_debt": ["code_quality_score", "security_vulnerabilities",
                      "eol_technology", "documentation_quality"]
}
```

**Gap Detection Logic**:
```python
# Check direct Asset model fields
for field in ["operating_system", "environment", "technology_stack"]:
    value = getattr(asset, field, None)
    if not value or (isinstance(value, list) and len(value) == 0):
        gaps.append({
            "field_name": field,
            "gap_type": "missing_field",
            "priority": 1,  # Critical
            "category": "infrastructure"
        })

# Check JSON fields (technical_details, custom_attributes)
if asset.technical_details:
    architecture = asset.technical_details.get("architecture_pattern")
    if not architecture:
        gaps.append({"field_name": "architecture_pattern", "gap_type": "missing_field"})
```

**Performance**: ~5-10s for 100 assets (no AI calls)

**Output**: Deterministic gap list with field names, categories, priorities

---

### Tier 2: AI Enhancement (Intelligent, Context-Aware)

**Purpose**: Enhance tier_1 gaps with confidence scores, suggested resolutions, and context analysis

**Implementation**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/collection/gap_analysis/service.py`

**CrewAI Agent**: `gap_analysis_specialist` from `TenantScopedAgentPool` (ADR-015)

**AI Agent Task**:
```python
task_description = f"""
Analyze {len(assets)} assets and enhance detected gaps:

Assets Summary:
{json.dumps([{"name": a.name, "type": a.asset_type} for a in assets[:5]], indent=2)}

Tier 1 Gaps Detected:
{json.dumps(tier_1_gaps[:10], indent=2)}

Your Task:
1. Assign confidence scores (0.0-1.0) to each gap
2. Suggest specific resolution actions
3. Identify data quality issues (conflicting values, low confidence)
4. Prioritize gaps by business impact

Output JSON format:
{{
  "gaps": [
    {{"field_name": "operating_system", "confidence_score": 0.85,
      "suggested_resolution": "Verify OS version from CMDB", "priority": 1}}
  ]
}}
"""
```

**Agent Tools**:
- `gap_analysis_tools` - Field mapping suggestions, data quality checks
- `critical_attributes_tool` - 22-attribute validation framework
- `asset_intelligence_tool` - Asset-specific context (EOL status, criticality)

**Performance**: ~30-45s for 10 assets (LLM inference)

**Output**: Enhanced gaps with confidence scores + resolution suggestions

---

### Gap Persistence: `collection_data_gaps` Table

```sql
CREATE TABLE migration.collection_data_gaps (
    id UUID PRIMARY KEY,
    collection_flow_id UUID REFERENCES collection_flows(id),
    asset_id UUID,  -- Optional: asset-specific gaps
    gap_type VARCHAR(100),  -- missing_field, unmapped_attribute, data_quality_issue
    gap_category VARCHAR(50),  -- infrastructure, application, business, technical_debt
    field_name VARCHAR(255),
    description TEXT,
    impact_on_sixr VARCHAR(20),  -- critical, high, medium, low
    priority INTEGER,  -- 1=critical, 2=high, 3=medium, 4=low
    suggested_resolution TEXT,
    confidence_score FLOAT,  -- AI-assigned (tier_2 only)
    resolution_status VARCHAR(20) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Query gaps for questionnaire generation
SELECT field_name, gap_category, priority, suggested_resolution
FROM migration.collection_data_gaps
WHERE collection_flow_id = $1
  AND resolution_status = 'pending'
ORDER BY priority ASC, confidence_score DESC;
```

---

## 5. Intelligent Questionnaire Generation (Issue #980 - November 2025)

### Problem Solved
**Before**: Generic text questions like "What is the Resilience?" with no MCQ options

**After**: Context-aware MCQ questions with intelligent option ordering based on asset characteristics

### Implementation Architecture

**Service**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/ai_analysis/questionnaire_generator/tools/`

**Key Files**:
- `section_builders.py` - Main orchestrator, routes gaps to intelligent builders
- `attribute_question_builders.py` - MCQ builders for critical attributes
- `assessment_question_builders.py` - MCQ builders for 6R/assessment fields
- `intelligent_options/*.py` - Context-aware option generation (EOL, criticality, etc.)

---

### Context-Aware Option Routing

**Step 1: Asset Context Threading**

```python
# Backend extracts asset context (EOL status, criticality)
def _determine_eol_status(operating_system: str, os_version: str, technology_stack: List[str]) -> str:
    eol_patterns = {
        "AIX 7.1": "EOL_EXPIRED",
        "AIX 7.2": "EOL_EXPIRED",
        "Windows Server 2008": "EOL_EXPIRED",
        "RHEL 7": "EOL_SOON"
    }
    # Runtime pattern matching
    return eol_patterns.get(f"{operating_system} {os_version}", "CURRENT")

asset_context = {
    "id": str(asset.id),
    "operating_system": "AIX",
    "os_version": "7.2",
    "eol_technology": "EOL_EXPIRED",  # Computed at runtime
    "criticality": "mission_critical"
}
```

**Step 2: Intelligent Option Generation**

```python
# intelligent_options/security_options.py
def get_security_vulnerabilities_options(asset_context: Dict) -> Tuple[str, List[Dict]]:
    eol_status = asset_context.get("eol_technology", "").upper()

    # EOL_EXPIRED → High Severity first (urgent)
    if "EOL_EXPIRED" in eol_status:
        return "select", [
            {"value": "high_severity", "label": "High Severity - Critical vulnerabilities exist"},
            {"value": "medium_severity", "label": "Medium Severity - Moderate risk"},
            {"value": "low_severity", "label": "Low Severity - Minor issues"},
            {"value": "none_known", "label": "None Known - No vulnerabilities identified"}
        ]

    # CURRENT → None Known first (optimistic)
    elif "CURRENT" in eol_status:
        return "select", [
            {"value": "none_known", "label": "None Known - No vulnerabilities identified"},
            {"value": "low_severity", "label": "Low Severity - Minor issues"},
            {"value": "medium_severity", "label": "Medium Severity - Moderate risk"},
            {"value": "high_severity", "label": "High Severity - Critical vulnerabilities exist"}
        ]
```

**Step 3: Question Builder Integration**

```python
# section_builders.py - Routes gaps to intelligent builders
if any(x in attr_name.lower() for x in ["dependency", "dependencies"]):
    question = generate_dependency_question({}, asset_context)
    category = "dependencies"
elif "quality" in attr_name.lower():
    question = generate_data_quality_question({}, asset_context)
    category = "data_validation"
elif any(x in attr_name.lower() for x in ["technical", "architecture", "tech_debt"]):
    question = generate_generic_technical_question(asset_context)
    category = "technical_details"
```

---

### Validation Results (November 9, 2025)

**Test Flow**: Analytics Dashboard Collection Flow (1 asset, 11 gaps)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| MCQ Percentage | >80% | 90.9% | ✅ EXCEEDED |
| Generic Questions | 0% | 0% | ✅ PERFECT |
| Contextual Questions | >90% | 100% | ✅ EXCEEDED |
| Backend Errors | 0 | 0 | ✅ PERFECT |

**Sample Questions Generated**:
- ✅ "What is the dependency complexity level for Analytics Dashboard?" (MCQ: 6 options with quantified ranges)
- ✅ "What is the business criticality of Analytics Dashboard?" (MCQ: 5 options with descriptive labels)
- ✅ "What is the technical modernization readiness for Analytics Dashboard?" (MCQ: 6 options based on EOL status)

**Backend Logs Confirm Wiring**:
```
✅ Gap field 'resilience' using Issue #980 intelligent builder
✅ Gap field 'tech_debt' using Issue #980 intelligent builder
✅ Gap field 'technical_details.dependencies' using Issue #980 intelligent builder
✅ 0% legacy fallback usage (all questions from intelligent builders)
```

---

## 6. Asset-Aware Questionnaire Deduplication (November 2025)

### Problem Solved
**Before**: User selects Asset X in Flow A, Flow B, Flow C → answers same 10 questions 3 times

**After**: Asset X has ONE questionnaire per engagement → reused across all flows

### Schema Architecture

**Migration**: `128_add_asset_id_to_questionnaires.py`

```sql
-- Add asset_id column (nullable for backward compatibility)
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN asset_id UUID REFERENCES migration.assets(id) ON DELETE CASCADE;

-- Make collection_flow_id nullable (flows now share questionnaires)
ALTER TABLE migration.adaptive_questionnaires
ALTER COLUMN collection_flow_id DROP NOT NULL;

-- Partial unique constraint (only enforces when asset_id IS NOT NULL)
CREATE UNIQUE INDEX uq_questionnaire_per_asset_per_engagement
ON migration.adaptive_questionnaires(engagement_id, asset_id)
WHERE asset_id IS NOT NULL;  -- Gradual migration pattern
```

### Get-or-Create Logic

**Implementation**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication.py`

```python
async def get_existing_questionnaire_for_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession
) -> Optional[AdaptiveQuestionnaire]:
    """Check if questionnaire already exists for this asset in this engagement."""
    result = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed"  # Retry on failure
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"♻️ Reusing questionnaire {existing.id} for asset {asset_id}")
    return existing
```

### Reuse Decision Matrix

| Status | Reuse? | Reason |
|--------|--------|--------|
| `completed` | ✅ Yes | User already answered - reuse responses |
| `in_progress` | ✅ Yes | Let user continue where they left off |
| `ready` | ✅ Yes | Generated but not answered - reuse questions |
| `pending` | ✅ Yes | Generation in progress - reusing pending record |
| `failed` | ❌ No | Regenerate questionnaire |

### Multi-Tenant Scoping

**CRITICAL**: Unique constraint is per `(engagement_id, asset_id)`, NOT globally

**Rationale**: Same asset in different engagements = different business context
- Engagement A: Asset ABC for financial migration (HIPAA compliance)
- Engagement B: Asset ABC for infrastructure audit (no compliance)

---

## 7. Adaptive Forms Architecture (Issue #795 - Working as Designed)

### Important: Fewer Questions = Better Data Quality (Not a Bug!)

**Issue #795 Report**: "Asset 2 shows only 3 sections instead of 7 - BUG!"

**Root Cause Analysis Revealed**:
- ✅ Serena memory: "questions should be generated based on gaps"
- ✅ Asset 2 has better data quality → fewer gaps → fewer questions
- ✅ Playwright testing: System working correctly
- ✅ Backend: Gap analysis correctly identifying missing fields only
- ❌ **NOT A BUG** - Intelligent adaptive behavior

**Design Intent**: Adaptive forms show only gap-based questions per asset
- Asset with complete data: 3 questions (only missing fields)
- Asset with incomplete data: 10 questions (many missing fields)
- This is **INTENDED BEHAVIOR** - system adapts to data quality

### Frontend Implementation

**Component**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/pages/collection/AdaptiveForms.tsx`

**Hook**: `useAdaptiveFormFlow` from `src/hooks/collection/useAdaptiveFormFlow.ts`

**Question Filtering Logic** (Backend):
```python
# Only generate questions for detected gaps
questions = []
for gap in collection_data_gaps:
    if gap.resolution_status == "pending":
        question = generate_question_for_gap(gap, asset_context)
        questions.append(question)

# Result: Asset with 0 gaps = 0 questions (no form displayed)
# Result: Asset with 10 gaps = 10 questions (adaptive form)
```

**Frontend Display Pattern**:
```typescript
// AdaptiveForm.tsx
{questionnaires.map((questionnaire) => (
  <AdaptiveFormSection
    key={questionnaire.id}
    assetName={questionnaire.asset_name}  // Asset-specific
    questions={questionnaire.questions}   // Gap-based (varies per asset)
    onSubmit={handleSubmit}
  />
))}
```

---

## 8. API Endpoint Reference (November 2025)

### Master Flow Operations (MFO - ADR-006)

**Base Path**: `/api/v1/master-flows`

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| POST | `/` | Create new collection flow via MFO | master_flow_id |
| GET | `/active?type=collection` | List active collection flows | List[FlowSummary] |
| GET | `/{master_flow_id}` | Get flow details | FlowDetails |
| POST | `/{master_flow_id}/resume` | Resume paused flow | Status |
| POST | `/{master_flow_id}/pause` | Pause running flow | Status |
| POST | `/{master_flow_id}/complete` | Mark flow complete | Status |
| DELETE | `/{master_flow_id}` | Delete flow (cascade) | Status |

---

### Collection-Specific Operations

**Base Path**: `/api/v1/collection`

#### Flow Management

| Method | Endpoint | Purpose | CrewAI Agents | Duration |
|--------|----------|---------|---------------|----------|
| POST | `/flows` | Create collection flow (legacy) | None | <1s |
| GET | `/flows/{flow_id}` | Get flow details | None | <1s |
| POST | `/flows/{flow_id}/execute` | Trigger gap analysis + questionnaire generation | Gap Analysis Specialist, Questionnaire Designer | 30-90s |
| POST | `/flows/{flow_id}/continue` | Resume paused flow | Depends on phase | Varies |
| DELETE | `/flows/{flow_id}` | Delete flow | None | <1s |

#### Gap Analysis

| Method | Endpoint | Purpose | CrewAI Agents | Duration |
|--------|----------|---------|---------------|----------|
| POST | `/flows/{flow_id}/analyze-gaps` | Two-phase gap analysis (tier_1 + tier_2) | Gap Analysis Specialist (tier_2) | 15-45s |
| GET | `/flows/{flow_id}/gaps` | Retrieve detected gaps | None | <1s |
| POST | `/flows/{flow_id}/rerun-gap-analysis` | Re-execute gap analysis | Gap Analysis Specialist | 15-45s |

#### Questionnaire Management

| Method | Endpoint | Purpose | CrewAI Agents | Duration |
|--------|----------|---------|---------------|----------|
| GET | `/flows/{flow_id}/questionnaires` | Get adaptive questionnaires (with asset deduplication) | None | <1s |
| GET | `/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` | Get saved responses | None | <1s |
| POST | `/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` | Submit questionnaire responses | None | <2s |
| POST | `/flows/{flow_id}/questionnaires/{questionnaire_id}/submit` | Legacy submit endpoint (redirects to `/responses`) | None | <2s |

#### Bulk Operations

| Method | Endpoint | Purpose | Duration |
|--------|----------|---------|----------|
| POST | `/bulk-import` | Bulk import assets from spreadsheet | 10-60s |
| POST | `/flows/batch-delete` | Delete multiple flows | <5s |
| POST | `/cleanup` | Clean up stale/abandoned flows | 5-15s |

---

### Required Headers for ALL Endpoints

```http
X-Client-Account-ID: 12345678-1234-1234-1234-123456789012
X-Engagement-ID: 87654321-4321-4321-4321-210987654321
Authorization: Bearer <jwt_token>
```

---

## 9. CrewAI Agent Activation Points

### Agent 1: Gap Analysis Specialist (ADR-015)

**Activation**: `POST /api/v1/collection/flows/{flow_id}/analyze-gaps` (tier_2 only)

**Pool**: `TenantScopedAgentPool` - Persistent per `(client_account_id, engagement_id)`

**Configuration**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/persistent_agents/config/agent_pool_constants.py`

```python
"gap_analysis_specialist": {
    "role": "Gap Analysis Specialist",
    "goal": "Identify missing critical attributes and data quality issues",
    "tools": ["gap_analysis_tools", "critical_attributes_tool", "asset_intelligence_tool"],
    "max_retries": 3,
    "memory_enabled": False  # Per ADR-024, use TenantMemoryManager instead
}
```

**Task Execution**:
```python
# service.py - Gap Analysis Service
agent = await TenantScopedAgentPool.get_or_create_agent(
    client_id=self.client_account_id,
    engagement_id=self.engagement_id,
    agent_type="gap_analysis_specialist"
)

task_output = await self._execute_agent_task(agent, task_description)
```

**Output**: Enhanced gaps with confidence scores, resolution suggestions

---

### Agent 2: Questionnaire Designer Agent

**Activation**: `POST /api/v1/collection/flows/{flow_id}/execute` → Phase 4: `questionnaire_generation`

**Pool**: `TenantScopedAgentPool`

**Configuration**:
```python
"questionnaire_designer": {
    "role": "Adaptive Questionnaire Designer",
    "goal": "Generate intelligent questionnaires based on gaps and asset types",
    "tools": ["questionnaire_generation", "gap_analysis", "asset_intelligence"],
    "max_retries": 3,
    "memory_enabled": False  # Per ADR-024
}
```

**Task Execution**:
```python
# questionnaire_generator/tools/generation.py
async def _arun(self, gaps_data: Dict) -> Dict:
    """Async method for agent execution (PRIMARY interface)"""
    # Generate questions using intelligent builders (Issue #980)
    questions = []
    for gap in gaps_data["gaps"]:
        question = self._route_gap_to_intelligent_builder(gap, asset_context)
        questions.append(question)

    return {"sections": self._group_questions_by_category(questions)}
```

**Output**: Context-aware MCQ questionnaires with 90.9% structured question rate

---

### Agent Memory Architecture (ADR-024)

**CRITICAL**: CrewAI built-in memory is **DISABLED** globally

**Replacement**: `TenantMemoryManager` for enterprise agent learning

```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# Store agent learnings after task completion
memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    pattern_data={
        "source_field": "cust_name",
        "target_field": "customer_name",
        "confidence": 0.95
    }
)
```

**Why TenantMemoryManager over CrewAI Memory**:
- ✅ Multi-tenant isolation (engagement/client/global scopes)
- ✅ PostgreSQL + pgvector (native to stack, no ChromaDB)
- ✅ Enterprise: data classification, audit trails, encryption
- ❌ CrewAI memory causes 401 errors (DeepInfra key → OpenAI endpoint)

---

## 10. Architectural Decision Records (ADRs)

### ADR-006: Master Flow Orchestrator
- **Decision**: All flows register with `crewai_flow_state_extensions` table
- **Impact**: Single source of truth for flow lifecycle
- **Collection Flow**: Uses `master_flow_id` for all operations

### ADR-012: Flow Status Management Separation
- **Decision**: Master flow tracks lifecycle, child flow tracks operational state
- **Impact**: Frontend uses child flow status for decisions
- **Collection Flow**: `collection_flows.current_phase` drives UI, not master flow status

### ADR-024: TenantMemoryManager - Enterprise Agent Memory
- **Decision**: CrewAI built-in memory disabled, use TenantMemoryManager
- **Impact**: All agent learning uses PostgreSQL + pgvector
- **Collection Flow**: Gap analysis agent stores learnings in `tenant_memory` table

### ADR-028: SQL Safety - Enum Types Over String Comparisons
- **Decision**: Use PostgreSQL CHECK constraints, not ENUMs
- **Impact**: Prevents SQL injection in phase/status checks
- **Collection Flow**: `current_phase` validated with CHECK constraints

---

## 11. Serena Memory Cross-References

**Collection Flow Architectural Memories**:
- `collection_gap_analysis_comprehensive_implementation_2025_24` - Two-phase gap analysis
- `intelligent-questionnaire-context-aware-options` - Issue #980 MCQ generation
- `asset_aware_questionnaire_generation_2025_24` - Asset-centric architecture
- `issue_980_questionnaire_wiring_complete_2025_11` - Complete Issue #980 validation
- `collection_flow_comprehensive_fixes_2025_09_30` - September architectural fixes
- `collection_gap_analysis_lean_refactor_2025_10` - Single-agent refactor (87% code reduction)
- `two-phase-gap-analysis-implementation-lessons` - Tier 1/2 patterns
- `asset_based_questionnaire_deduplication_schema_2025_11` - Deduplication schema

**Bug Resolution Memories**:
- `issue_661_vs_659_clarification_assessment_vs_collection` - Collection vs Assessment separation
- `bug_801_questionnaire_status_flow_analysis` - Questionnaire lifecycle
- `discovery_flow_data_display_issues_2025_09` - Data handoff patterns

---

## 12. Known Issues and Future Enhancements

### Resolved Issues
- ✅ **Issue #795**: Adaptive forms showing fewer questions is **WORKING AS DESIGNED** (gap-based filtering)
- ✅ **Issue #980**: Intelligent questionnaire generation **FULLY WIRED** (90.9% MCQ rate)
- ✅ **Issue #677**: Questionnaire display race conditions **FIXED** (proper async state management)
- ✅ **Issue #430**: Discovery flow completion **FIXED** (ADR-012 compliance)

### Future Enhancements
1. **Machine Learning Gap Prediction** - Predict gaps before scanning (based on asset type patterns)
2. **Bulk Questionnaire Import** - Import pre-filled questionnaires from spreadsheets
3. **Multi-Language Support** - Localized questionnaires for global teams
4. **Mobile-Responsive Forms** - Native mobile questionnaire completion
5. **Voice-to-Text Input** - Conversational questionnaire completion

---

## 13. Development Environment Setup

### Docker-First Development (MANDATORY - ADR-010)

```bash
# Start all services (frontend on :8081, backend on :8000, DB on :5433)
cd config/docker && docker-compose up -d

# View logs
docker logs migration_backend -f
docker logs migration_frontend -f

# Access containers
docker exec -it migration_backend bash
docker exec -it migration_postgres psql -U postgres -d migration_db

# NEVER run 'npm run dev' locally - always use Docker!
```

### Database Verification

```bash
# Check gap analysis results
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT COUNT(*), gap_type, gap_category, priority \
   FROM migration.collection_data_gaps \
   WHERE created_at > NOW() - INTERVAL '5 minutes' \
   GROUP BY gap_type, gap_category, priority;"

# Check questionnaire deduplication
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT COUNT(*), completion_status, asset_id IS NOT NULL as has_asset \
   FROM migration.adaptive_questionnaires \
   GROUP BY completion_status, has_asset;"
```

---

## 14. Testing Strategies

### End-to-End Playwright Tests

**Location**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/`

**Key Tests**:
- `collection-gap-analysis-new.spec.ts` - Two-phase gap analysis validation
- `questionnaire-upsert-fix-980.spec.ts` - Issue #980 MCQ validation
- `issue-677-questionnaire-display-race-condition-fix.spec.ts` - Race condition handling

**Sample Test Pattern**:
```typescript
test('validates intelligent MCQ questionnaire generation', async ({ page }) => {
  // Create flow with asset selection
  await page.goto('/collection/adaptive-forms?applicationId=asset-uuid');

  // Wait for gap analysis + questionnaire generation (max 90s)
  await page.waitForSelector('text=/questionnaire|form/i', { timeout: 90000 });

  // Verify MCQ questions
  const mcqQuestions = await page.locator('select, input[type="radio"], input[type="checkbox"]').count();
  const textQuestions = await page.locator('input[type="text"]:not([readonly])').count();

  const mcqPercentage = (mcqQuestions / (mcqQuestions + textQuestions)) * 100;
  expect(mcqPercentage).toBeGreaterThan(80);  // Target: >80% MCQ

  // Verify no generic questions
  const genericQuestions = await page.locator('text=/What is the \\w+\\?/').count();
  expect(genericQuestions).toBe(0);
});
```

---

## 15. Troubleshooting Guide

### Common Issues

#### 1. "Questionnaire Generation Timed Out"

**Symptoms**: Frontend shows spinner for >60s, then fallback bootstrap questionnaire

**Root Cause**: Tier 2 AI analysis taking >60s (LLM inference delay)

**Solution**:
```typescript
// Increase frontend timeout in vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        proxyTimeout: 200000  // 200 seconds for AI operations
      }
    }
  }
});
```

#### 2. "Questionnaire Shows Same Questions for All Assets"

**Symptoms**: Asset A and Asset B show identical questions (no adaptive behavior)

**Root Cause**: Gap analysis not detecting asset-specific gaps

**Diagnosis**:
```bash
# Check if gaps are asset-specific
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT asset_id, COUNT(*) as gap_count \
   FROM migration.collection_data_gaps \
   WHERE collection_flow_id = 'flow-uuid' \
   GROUP BY asset_id;"
```

**Solution**: Verify assets have different data completeness levels

#### 3. "Asset-Aware Deduplication Not Working"

**Symptoms**: User answers same questions multiple times for same asset across flows

**Root Cause**: `asset_id` column not populated in `adaptive_questionnaires`

**Diagnosis**:
```bash
# Check questionnaire asset linkage
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT id, asset_id IS NOT NULL as has_asset, completion_status \
   FROM migration.adaptive_questionnaires \
   WHERE engagement_id = 'engagement-uuid' \
   ORDER BY created_at DESC LIMIT 10;"
```

**Solution**: Run migration `128_add_asset_id_to_questionnaires.py` and verify backfill

---

## 16. Performance Benchmarks

**Test Environment**: Docker Compose, MacOS, M1 Pro, 16GB RAM

| Operation | Assets | Duration | Notes |
|-----------|--------|----------|-------|
| Tier 1 Gap Analysis | 100 | 8s | Programmatic only, no AI |
| Tier 2 Gap Analysis | 10 | 35s | With AI enhancement |
| Questionnaire Generation | 10 gaps | 12s | Issue #980 intelligent builders |
| Asset Deduplication Check | 1000 assets | <1s | Indexed query |
| Form Submission | 50 responses | 2s | Batch insert |

---

## 17. Related Documentation

- [Collection Flow Technical Implementation](./technical-implementation.md)
- [Adaptive Forms Deep Dive](./02_Adaptive_Forms.md)
- [Gap Analysis Implementation](../../analysis/Notes/collection-gap-analysis-architecture.md)
- [Issue #980 Resolution](../../analysis/Notes/issue-980-intelligent-questionnaire-wiring.md)
- [Issue #795 Analysis](../../analysis/Notes/issue-795-adaptive-forms-working-as-designed.md)
- [ADR-006: Master Flow Orchestrator](../../adr/006-master-flow-orchestrator.md)
- [ADR-012: Flow Status Management Separation](../../adr/012-flow-status-management-separation.md)
- [ADR-024: TenantMemoryManager Architecture](../../adr/024-tenant-memory-manager-architecture.md)

---

**Document Version**: 2.0 (November 2025)
**Authors**: Documentation Curator Agent
**Validated Against**: Production deployment (Railway), November 9, 2025 Playwright tests
