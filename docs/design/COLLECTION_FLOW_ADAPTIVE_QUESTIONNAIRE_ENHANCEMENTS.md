# Collection Flow Adaptive Questionnaire Enhancements - Design Document

**Version**: 2.0 (GPT-5 Review Integrated, All Questions Resolved)
**Date**: 2025-01-23 (Updated: 2025-10-23)
**Status**: ✅ **100% FINALIZED - Ready for Phase 1 Implementation**
**Author**: System Architect (via User Requirements + GPT-5 Review + User Decisions)
**Reviewers**: GPT-5 (Platform Architecture Alignment)
**Total Design Questions Resolved**: 15 (10 original + 5 GPT-5 additions)
**Architecture Compliance**: ADR-024, RequestContext Pattern, Multi-Model Service, ContextAwareRepository

---

## Executive Summary

This document specifies four major enhancements to the Collection Flow adaptive questionnaire system:

1. **Multi-Asset Answer Population**: Allow users to answer questions for multiple assets simultaneously via modal-based UI
2. **Asset-Type-Specific Question Filtering**: Show only relevant questions based on asset type (Application vs Server vs Database)
3. **Dynamic Gap Closure**: Automatically hide answered questions and intelligently re-emerge questions when dependencies change
4. **Bulk Import Integration**: Enable bulk upload of app-specific data and dependencies with intelligent gap recalculation

These enhancements address key UX friction points identified in the current single-asset-only questionnaire flow.

---

## 1. Requirements & User Stories

### 1.1 Multi-Asset Answer Population

**User Story**:
As a migration analyst, when I have 50 Windows servers with identical OS versions, I want to select all 50 and answer "OS: Windows Server 2019" once, rather than answering 50 individual forms.

**Acceptance Criteria**:
- ✅ User can select multiple assets via table view with checkboxes
- ✅ "Bulk Answer" button opens modal with asset picker and question wizard
- ✅ Questions presented in wizard-style flow (one question at a time, all questions must be answered)
- ✅ When assets have conflicting existing answers, show merge-style UI to resolve
- ✅ User can choose to overwrite all, fill blanks only, or create consolidated answer
- ✅ Progress tracker shows "5/12 questions answered" within modal
- ✅ All questions use dropdown menus (with "Other" option) to prevent junk data

### 1.2 Asset-Type-Specific Question Filtering

**User Story**:
As a user answering questions for a database server, I should NOT see questions about "web framework" or "authentication method" that only apply to applications.

**Acceptance Criteria**:
- ✅ Questions mapped to asset types via `collection_question_rules` DB table
- ✅ Asset types use high-level taxonomy: Application, Server, Database, Network, Storage
- ✅ Specialized types inherit parent questions (e.g., Oracle DB inherits Database questions)
- ✅ Override capability: Parent questions can be explicitly excluded for child types
- ✅ CrewAI agent can dynamically prune/generate questions on-demand via "Refresh Questions" button
- ✅ Hardcoded question set serves as graceful fallback with banner "Limited questions - agent processing in background"

### 1.3 Dynamic Gap Closure

**User Story**:
As a user, once I've answered "OS: Windows Server 2019" for a server, that question should disappear from my form and my progress should update to reflect completion.

**Acceptance Criteria**:
- ✅ Questions marked closed immediately on answer save (real-time)
- ✅ All questions enforce dropdown menus (including "Other" with validation) to ensure data quality
- ✅ Progress % recalculates on "Save Progress" or phase transition (batch update, not real-time)
- ✅ Closed questions can re-emerge if CrewAI agent detects dependency changes (e.g., OS version changes → re-ask tech stack)
- ✅ User can manually reopen questions via "Reopen Question" icon next to answered questions
- ✅ Agent uses all inputs (asset type, existing data, engagement context, dependency analysis) to determine re-emergence
- ✅ Fallback: If agent unavailable, critical field changes (OS version, IP, decommission status) trigger re-opening

### 1.4 Bulk Import Integration

**User Story**:
As a migration lead, I want to upload a CSV of 200 applications with their dependencies and tech stack details, then have the system update the database and show me only the remaining data gaps.

**Acceptance Criteria**:
- ✅ Bulk import accessible via both: (1) Tab in adaptive forms ("Single Asset" | "Multi-Asset" | "Bulk Import"), and (2) Dedicated import page in sidebar
- ✅ Unified import service handles CSV and JSON formats
- ✅ CSV format: Simple dependencies (`source_app_id, target_app_id, dependency_type, criticality, protocol, port`)
- ✅ JSON format: Complex nested/transitive dependencies with relationship metadata
- ✅ Intelligent field mapping: Analyzes CSV headers, suggests target enrichment table, maps to standard terms (hides internal table/column names)
- ✅ Custom attributes: Unmapped fields stored in `asset_custom_attributes` JSONB column
- ✅ Future enhancement: Agent analyzes patterns across imports and suggests new standard fields
- ✅ Post-import gap analysis: User chooses "Fast (imported only)" or "Thorough (with dependencies)" recalculation
- ✅ Incremental update: Only recalculates gaps for imported assets (or dependent assets if "Thorough" selected)

---

## 2. Architecture Overview

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                   Collection Flow Enhancement                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Multi-Asset  │  │ Asset-Type   │  │ Dynamic Gap Closure    ││
│  │ Answer Modal │  │ Question     │  │ & Re-emergence         ││
│  │              │  │ Filter       │  │                        ││
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────────┘│
│         │                 │                   │                 │
│         └─────────────────┴───────────────────┘                 │
│                           │                                     │
│                           ▼                                     │
│         ┌─────────────────────────────────────────┐             │
│         │  Unified Import Service                 │             │
│         │  (CSV/JSON → Enrichment Tables)         │             │
│         └─────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────┐
        │         Backend Services Layer                │
        │                                               │
        │  ┌──────────────────────────────────────┐    │
        │  │ CollectionBulkAnswerService          │    │
        │  │ - Multi-asset answer orchestration   │    │
        │  │ - Conflict resolution logic          │    │
        │  └──────────────────────────────────────┘    │
        │                                               │
        │  ┌──────────────────────────────────────┐    │
        │  │ DynamicQuestionEngine                │    │
        │  │ - Asset-type question filtering      │    │
        │  │ - CrewAI agent integration           │    │
        │  │ - Hardcoded fallback rules           │    │
        │  └──────────────────────────────────────┘    │
        │                                               │
        │  ┌──────────────────────────────────────┐    │
        │  │ UnifiedImportOrchestrator            │    │
        │  │ - CSV/JSON parsing                   │    │
        │  │ - Intelligent field mapping          │    │
        │  │ - Enrichment table updates           │    │
        │  └──────────────────────────────────────┘    │
        │                                               │
        │  ┌──────────────────────────────────────┐    │
        │  │ IncrementalGapAnalyzer               │    │
        │  │ - Smart recalculation (fast/thorough)│    │
        │  │ - Dependency graph traversal         │    │
        │  └──────────────────────────────────────┘    │
        └───────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────┐
        │         Database Layer (PostgreSQL)           │
        │                                               │
        │  • adaptive_questionnaires (existing)         │
        │  • collection_question_rules (NEW)            │
        │  • collection_answer_history (NEW)            │
        │  • asset_custom_attributes (NEW)              │
        │  • application_enrichment (existing)          │
        │  • server_enrichment (existing)               │
        │  • database_enrichment (existing)             │
        └───────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Layer |
|-----------|---------------|-------|
| `MultiAssetAnswerModal` | UI for bulk asset selection and answer wizard | Frontend |
| `AssetPickerTable` | Reusable table with multi-select checkboxes | Frontend |
| `AnswerVariantReconciler` | Merge-style conflict resolution UI | Frontend |
| `BulkImportWizard` | Guided CSV/JSON upload and field mapping | Frontend |
| `CollectionBulkAnswerService` | Orchestrates multi-asset answer propagation | Backend Service |
| `DynamicQuestionEngine` | Asset-type filtering + CrewAI pruning | Backend Service |
| `UnifiedImportOrchestrator` | Parses imports, updates enrichment tables | Backend Service |
| `IncrementalGapAnalyzer` | Recalculates gaps efficiently post-import | Backend Service |

---

## 3. Database Schema Changes

### 3.1 New Tables

#### 3.1.1 `collection_question_rules`
Maps questions to asset types and defines inheritance rules.

```sql
CREATE TABLE migration.collection_question_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,

    -- Question identification
    question_id VARCHAR(255) NOT NULL,  -- e.g., "os_version", "tech_stack"
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,  -- "dropdown", "multi_select", "text"

    -- Asset type applicability
    asset_type VARCHAR(100) NOT NULL,  -- "Application", "Server", "Database", "Network", "Storage"
    is_applicable BOOLEAN NOT NULL DEFAULT TRUE,

    -- Inheritance rules
    inherits_from_parent BOOLEAN DEFAULT TRUE,
    override_parent BOOLEAN DEFAULT FALSE,

    -- Answer options (for dropdowns)
    answer_options JSONB,  -- ["Windows Server 2019", "Windows Server 2022", "Linux Ubuntu 20.04"]

    -- Display configuration
    display_order INTEGER,
    section VARCHAR(100),  -- "Basic Information", "Technical Details", etc.
    weight INTEGER DEFAULT 40,  -- For progress calculation
    is_required BOOLEAN DEFAULT FALSE,

    -- Agent generation hints
    generation_hint TEXT,  -- Helps CrewAI agent understand question context

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    CONSTRAINT fk_question_rules_client FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(id),
    CONSTRAINT fk_question_rules_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(id),
    CONSTRAINT unique_question_asset_type UNIQUE (client_account_id, engagement_id, question_id, asset_type)
);

CREATE INDEX idx_question_rules_asset_type ON migration.collection_question_rules(asset_type, client_account_id, engagement_id);
CREATE INDEX idx_question_rules_applicable ON migration.collection_question_rules(is_applicable, client_account_id, engagement_id);
-- Composite index for high-frequency lookups (per GPT-5 suggestion)
CREATE INDEX idx_question_rules_composite ON migration.collection_question_rules(client_account_id, engagement_id, question_id);
```

**Future Enhancement (v2)**: Add `collection_questions_catalog` table with metadata (display name, help text, validation rules) and FK from `collection_question_rules.question_id` to enforce referential integrity.

#### 3.1.2 `collection_answer_history`
Tracks answer changes for audit and re-emergence logic.

```sql
CREATE TABLE migration.collection_answer_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,

    -- Reference to questionnaire and asset
    questionnaire_id UUID NOT NULL,
    asset_id UUID NOT NULL,
    question_id VARCHAR(255) NOT NULL,

    -- Answer data
    answer_value TEXT,
    answer_source VARCHAR(50) NOT NULL,  -- "user_input", "bulk_import", "agent_generated", "bulk_answer_modal"
    confidence_score DECIMAL(5,2),

    -- Change tracking
    previous_value TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by VARCHAR(255),

    -- Re-emergence tracking
    reopened_at TIMESTAMP WITH TIME ZONE,
    reopened_reason TEXT,
    reopened_by VARCHAR(50),  -- "user_manual", "agent_dependency_change", "critical_field_change"

    -- Metadata
    metadata JSONB,  -- Additional context (e.g., bulk operation ID, import file name)

    CONSTRAINT fk_answer_history_questionnaire FOREIGN KEY (questionnaire_id)
        REFERENCES migration.adaptive_questionnaires(id),
    CONSTRAINT fk_answer_history_client FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(id),
    CONSTRAINT fk_answer_history_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(id)
);

CREATE INDEX idx_answer_history_asset ON migration.collection_answer_history(asset_id, client_account_id, engagement_id);
CREATE INDEX idx_answer_history_question ON migration.collection_answer_history(question_id, asset_id);
CREATE INDEX idx_answer_history_reopened ON migration.collection_answer_history(reopened_at) WHERE reopened_at IS NOT NULL;
-- Composite index for timeline queries (Per GPT-5)
CREATE INDEX idx_answer_history_timeline ON migration.collection_answer_history(client_account_id, engagement_id, questionnaire_id, question_id, changed_at DESC);
```

**Why the timeline index**: Supports efficient queries for "Show all answer changes for this questionnaire, grouped by question, ordered by time" (used in audit timeline UI).

#### 3.1.3 `asset_custom_attributes`
Stores unmapped fields from bulk imports.

```sql
CREATE TABLE migration.asset_custom_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,

    -- Asset reference
    asset_id UUID NOT NULL,
    asset_type VARCHAR(100) NOT NULL,  -- "Application", "Server", etc.

    -- Custom attribute data
    attributes JSONB NOT NULL,  -- Flexible schema for unmapped fields

    -- Import tracking
    source VARCHAR(100),  -- "csv_import", "json_import", "api_integration"
    import_batch_id UUID,  -- Links to import operation
    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Pattern analysis (for future agent suggestions)
    pattern_detected BOOLEAN DEFAULT FALSE,
    suggested_standard_field VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_custom_attrs_client FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(id),
    CONSTRAINT fk_custom_attrs_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(id),
    CONSTRAINT unique_asset_custom_attrs UNIQUE (asset_id, client_account_id, engagement_id)
);

CREATE INDEX idx_custom_attrs_asset ON migration.asset_custom_attributes(asset_id, client_account_id, engagement_id);
CREATE INDEX idx_custom_attrs_pattern ON migration.asset_custom_attributes(pattern_detected) WHERE pattern_detected = TRUE;
```

#### 3.1.4 `collection_background_tasks` (NEW - Per GPT-5 Requirement)
Persists background task state to database for resume/retry and status polling.

```sql
CREATE TABLE migration.collection_background_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    child_flow_id UUID NOT NULL,

    -- Task identification
    task_type VARCHAR(50) NOT NULL,  -- "bulk_import", "question_refresh", "gap_recalculation"
    status VARCHAR(50) NOT NULL,  -- "pending", "processing", "completed", "failed", "cancelled"

    -- Progress tracking
    progress_percent INTEGER DEFAULT 0,
    current_stage VARCHAR(100),
    rows_processed INTEGER DEFAULT 0,
    total_rows INTEGER,

    -- Task data
    input_params JSONB NOT NULL,  -- Original request parameters
    result_data JSONB,  -- Final result data
    error_message TEXT,

    -- Cancellation support
    is_cancellable BOOLEAN DEFAULT FALSE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by VARCHAR(255),

    -- Idempotency and retry
    idempotency_key VARCHAR(255),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_tasks_client FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(id),
    CONSTRAINT fk_tasks_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(id),
    CONSTRAINT unique_idempotency_key UNIQUE (client_account_id, engagement_id, idempotency_key) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_tasks_status ON migration.collection_background_tasks(status, client_account_id, engagement_id);
CREATE INDEX idx_tasks_child_flow ON migration.collection_background_tasks(child_flow_id);
CREATE INDEX idx_tasks_type ON migration.collection_background_tasks(task_type, status);
CREATE INDEX idx_tasks_created ON migration.collection_background_tasks(created_at DESC);
```

**Benefits**:
- Survives server restarts (tasks can resume from last saved state)
- Enables cancellation with rollback capability
- Provides historical audit trail of long-running operations
- Supports idempotent retry logic

### 3.2 Schema Updates to Existing Tables

#### 3.2.1 `adaptive_questionnaires` - Add Answer Storage

```sql
-- Add column for storing answers within questionnaire
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN IF NOT EXISTS answers JSONB DEFAULT '{}';

-- Add column for tracking closed questions
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN IF NOT EXISTS closed_questions JSONB DEFAULT '[]';

-- Add column for bulk operation tracking
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN IF NOT EXISTS last_bulk_update_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN migration.adaptive_questionnaires.answers IS
'Stores question_id -> answer_value mapping for quick lookup';

COMMENT ON COLUMN migration.adaptive_questionnaires.closed_questions IS
'Array of question_ids that have been answered and closed';
```

#### 3.2.2 `application_enrichment`, `server_enrichment`, etc. - Add Import Tracking

```sql
-- Add to all enrichment tables
ALTER TABLE migration.application_enrichment
ADD COLUMN IF NOT EXISTS last_import_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_import_batch_id UUID,
ADD COLUMN IF NOT EXISTS last_import_timestamp TIMESTAMP WITH TIME ZONE;

-- Repeat for server_enrichment, database_enrichment, network_enrichment, storage_enrichment
```

---

## 4. Backend API Contracts

**IMPORTANT - RequestContext Pattern**: All endpoints MUST use headers for tenant scoping to align with platform standards:
- `X-Client-Account-ID`: Tenant isolation (required)
- `X-Engagement-ID`: Engagement isolation (required)
- `X-User-ID`: User identity for audit trail (required)

Body/query parameters for `client_account_id` and `engagement_id` are **deprecated** and serve as fallback only. Frontends MUST send headers.

### 4.1 Multi-Asset Answer Endpoints

#### POST `/api/v1/collection/bulk-answers`
Submit answers for multiple assets at once.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body**:
```json
{
  "collection_flow_id": "uuid-here",
  "child_flow_id": "child-flow-uuid",
  "asset_ids": ["asset-uuid-1", "asset-uuid-2", "asset-uuid-3"],
  "answers": [
    {
      "question_id": "os_version",
      "answer_value": "Windows Server 2019",
      "confidence_score": 100.0
    },
    {
      "question_id": "business_criticality",
      "answer_value": "High",
      "confidence_score": 100.0
    }
  ],
  "conflict_resolution_strategy": "overwrite_all",
  "dry_run": false,
  "preview_id": "preview-uuid-from-preview-call",
  "idempotency_key": "unique-operation-id"
}
```

**Validation Rules**:
- `asset_ids`: Maximum 1,000 assets per submission (per Q11 decision)
- `child_flow_id`: REQUIRED - Collection child flow ID (not master flow ID)
- `dry_run`: If true, performs validation and returns preview without saving
- `preview_id`: Links this submission to a prior preview call for audit correlation
- `idempotency_key`: Prevents duplicate submissions (optional but recommended)
- `conflict_resolution_strategy`: Single global strategy (no per-question override per Q6 decision)

**Response** (200 OK):
```json
{
  "success": true,
  "assets_updated": 3,
  "questions_answered": 2,
  "conflicts_resolved": 1,
  "progress_delta": 15.5,  // % increase in completion
  "updated_questionnaire_ids": ["quest-uuid-1", "quest-uuid-2"]
}
```

**Response** (409 Conflict) - If strategy is "manual_resolution":
```json
{
  "status": "conflict",
  "error_code": "BULK_ANSWER_CONFLICTS_REQUIRE_RESOLUTION",
  "message": "Conflicting answers detected for 1 question(s)",
  "details": {
    "preview_id": "preview-uuid",
    "total_conflicts": 1,
    "conflicts": [
      {
        "question_id": "os_version",
        "asset_groups": [
          {
            "current_answer": "Windows Server 2016",
            "asset_ids": ["asset-uuid-1"],
            "count": 1
          },
          {
            "current_answer": "Windows Server 2019",
            "asset_ids": ["asset-uuid-2", "asset-uuid-3"],
            "count": 2
          }
        ]
      }
    ]
  }
}
```

**Response** (400 Bad Request) - Validation errors:
```json
{
  "status": "error",
  "error_code": "BULK_ANSWER_VALIDATION_FAILED",
  "message": "Answer validation failed for 2 question(s)",
  "details": {
    "validation_errors": [
      {
        "question_id": "os_version",
        "error": "answer_not_in_allowed_options",
        "provided_value": "Windows XP",
        "allowed_options": ["Windows Server 2019", "Windows Server 2022", "Other"]
      }
    ]
  }
}
```

#### GET `/api/v1/collection/bulk-answer-preview` (DEPRECATED)
**⚠️ DEPRECATED**: Use POST variant below to avoid URL length issues with large asset selections.

Preview conflicts before submitting bulk answers.

**Query Parameters**:
- `asset_ids` (comma-separated UUIDs, max 50)
- `question_ids` (comma-separated question IDs)

#### POST `/api/v1/collection/bulk-answer-preview` (RECOMMENDED)
Preview conflicts before submitting bulk answers. Supports large asset selections without URL length limits.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body**:
```json
{
  "child_flow_id": "child-flow-uuid",
  "asset_ids": ["asset-uuid-1", "asset-uuid-2", "..."],
  "question_ids": ["os_version", "business_criticality"]
}
```

**Response** (200 OK):
```json
{
  "preview_id": "preview-uuid-abc123",
  "total_assets": 5,
  "total_questions": 3,
  "potential_conflicts": 2,
  "validation_errors": [],
  "conflicts": [
    {
      "question_id": "os_version",
      "question_text": "What is the Operating System version?",
      "existing_answers": [
        {"value": "Windows Server 2016", "count": 2, "asset_ids": ["uuid1", "uuid2"]},
        {"value": "Windows Server 2019", "count": 3, "asset_ids": ["uuid3", "uuid4", "uuid5"]}
      ]
    }
  ]
}
```

**Notes**:
- `preview_id`: Use this in the submit request to correlate preview → submission for audit trail
- `validation_errors`: Server-side validation of answers against question rules (empty if all valid)

### 4.2 Dynamic Question Endpoints

#### GET `/api/v1/collection/questions/filtered`
Get questions filtered by asset type and current data.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Query Parameters**:
- `child_flow_id` (required)
- `asset_id` (required)
- `asset_type` (required)
- `include_answered` (boolean, default: false)
- `refresh_agent_analysis` (boolean, default: false)

**Response** (200 OK):
```json
{
  "asset_id": "uuid-here",
  "asset_type": "Server",
  "total_questions": 12,
  "answered_questions": 5,
  "remaining_questions": 7,
  "questions": [
    {
      "question_id": "os_version",
      "question_text": "What is the Operating System version?",
      "question_type": "dropdown",
      "section": "Basic Information",
      "display_order": 1,
      "weight": 40,
      "is_required": true,
      "answer_options": ["Windows Server 2019", "Windows Server 2022", "Linux Ubuntu 20.04", "Other"],
      "current_answer": null,
      "is_closed": false
    }
  ],
  "agent_status": "completed",  // or "processing", "fallback", "error"
  "fallback_used": false
}
```

#### POST `/api/v1/collection/questions/refresh`
Trigger CrewAI agent to regenerate/prune questions for an asset.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body**:
```json
{
  "child_flow_id": "child-flow-uuid",
  "asset_id": "uuid-here",
  "asset_type": "Application",
  "trigger_reason": "user_requested"
}
```

**Notes**:
- `trigger_reason`: One of "user_requested", "dependency_change", "data_update"
- This endpoint uses `multi_model_service.generate_response()` for LLM tracking (per CLAUDE.md)

**Response** (202 Accepted):
```json
{
  "status": "processing",
  "refresh_task_id": "task-uuid-here",
  "estimated_completion_seconds": 30,
  "polling_endpoint": "/api/v1/collection/questions/refresh-status/{task_id}"
}
```

#### POST `/api/v1/collection/questions/reopen`
Manually reopen a closed question.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body**:
```json
{
  "child_flow_id": "child-flow-uuid",
  "questionnaire_id": "uuid-here",
  "asset_id": "uuid-here",
  "question_id": "os_version",
  "reopen_reason": "User requested re-assessment"
}
```

**Notes**:
- Creates first-class history entry with `reopened_by: "user_manual"` (per GPT-5 enhancement)

**Response** (200 OK):
```json
{
  "success": true,
  "question_reopened": true,
  "history_recorded": true
}
```

### 4.3 Bulk Import Endpoints

#### POST `/api/v1/collection/bulk-import/analyze`
Analyze uploaded file and suggest field mappings.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body** (multipart/form-data):
- `file`: CSV or JSON file (max 10 MB, 10,000 rows)
- `child_flow_id`: UUID string
- `import_type`: "dependencies" | "application_data" | "server_data" | "database_data"

**Response** (200 OK):
```json
{
  "file_name": "app_dependencies.csv",
  "total_rows": 250,
  "detected_columns": ["source_app", "target_app", "dependency_type", "criticality"],
  "suggested_mappings": [
    {
      "csv_column": "source_app",
      "suggested_field": "source_application_id",
      "confidence": 0.95,
      "target_table": "application_enrichment"
    },
    {
      "csv_column": "criticality",
      "suggested_field": "business_criticality",
      "confidence": 0.88,
      "target_table": "application_enrichment"
    }
  ],
  "unmapped_columns": ["custom_field_1", "internal_code"],
  "validation_warnings": [
    "Row 15: 'source_app' value not found in existing assets"
  ]
}
```

#### POST `/api/v1/collection/bulk-import/execute`
Execute the import with user-confirmed mappings.

**Request Headers** (REQUIRED):
```
X-Client-Account-ID: 1
X-Engagement-ID: 1
X-User-ID: user@example.com
```

**Request Body**:
```json
{
  "child_flow_id": "child-flow-uuid",
  "import_batch_id": "uuid-from-analyze",
  "confirmed_mappings": [
    {"csv_column": "source_app", "target_field": "source_application_id"},
    {"csv_column": "criticality", "target_field": "business_criticality"},
    {"csv_column": "custom_field_1", "target_field": "custom_attribute"}
  ],
  "gap_recalculation_mode": "thorough",
  "overwrite_existing": false,
  "allow_cancellation": true
}
```

**Notes**:
- `allow_cancellation`: If true, user can cancel before DB commit (per GPT-5 Q6)
- Task state persists to DB for resume/retry on failure (per GPT-5 enhancement)

**Response** (202 Accepted):
```json
{
  "status": "processing",
  "import_task_id": "task-uuid-here",
  "estimated_completion_seconds": 120,
  "polling_endpoint": "/api/v1/collection/bulk-import/status/{task_id}"
}
```

#### GET `/api/v1/collection/bulk-import/status/{task_id}`
Poll import status.

**Response** (200 OK - In Progress):
```json
{
  "status": "processing",
  "progress_percent": 45,
  "rows_processed": 112,
  "total_rows": 250,
  "current_stage": "updating_enrichment_tables"
}
```

**Response** (200 OK - Completed):
```json
{
  "status": "completed",
  "progress_percent": 100,
  "rows_processed": 250,
  "total_rows": 250,
  "summary": {
    "assets_created": 10,
    "assets_updated": 240,
    "custom_attributes_stored": 35,
    "gaps_closed": 150,
    "new_gaps_identified": 12,
    "average_confidence_increase": 18.5
  },
  "gap_analysis_results": {
    "recalculation_mode": "thorough",
    "assets_analyzed": 250,
    "dependencies_analyzed": 87,
    "new_questions_generated": 12
  }
}
```

---

## 5. Frontend Component Specifications

### 5.1 Multi-Asset Answer Modal

**Component Path**: `src/components/collection/MultiAssetAnswerModal.tsx`

**Props**:
```typescript
interface MultiAssetAnswerModalProps {
  isOpen: boolean;
  onClose: () => void;
  collectionFlowId: string;
  clientAccountId: number;
  engagementId: number;
  preselectedAssetIds?: string[];
}
```

**UI Flow**:
1. **Asset Selection Step** (if no preselection):
   - Table view with columns: [Checkbox, Asset Name, Type, Current Progress %, Last Updated]
   - Search/filter by name, type, owner
   - "Select All" / "Clear Selection" buttons
   - Continue button shows "Answer for X assets"

2. **Question Wizard Step**:
   - Progress indicator: "Question 3 of 12"
   - Question text with tooltip help icon
   - Dropdown menu (enforced, no free text)
   - "Other" option opens validated text input modal
   - Navigation: "Previous" / "Next" / "Skip for Now"

3. **Conflict Resolution Step** (if needed):
   - Merge-style UI showing existing answer groups
   - Example: "3 assets say 'Windows 2016', 2 assets say 'Windows 2019'"
   - User selects winning answer or creates new consolidated answer
   - Option to "Apply to all conflicts" for similar questions

4. **Confirmation Step**:
   - Summary: "5 assets × 12 questions = 60 answers to be saved"
   - Breakdown by question showing answer value
   - "Save All Answers" button with loading state

**State Management**:
```typescript
const useMultiAssetAnswerWizard = () => {
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [conflicts, setConflicts] = useState<ConflictInfo[]>([]);

  // React Query mutations
  const previewMutation = useMutation(collectionService.getBulkAnswerPreview);
  const submitMutation = useMutation(collectionService.submitBulkAnswers);

  return { /* ... */ };
};
```

### 5.2 Asset Picker Table

**Component Path**: `src/components/collection/AssetPickerTable.tsx`

**Props**:
```typescript
interface AssetPickerTableProps {
  clientAccountId: number;
  engagementId: number;
  collectionFlowId: string;
  onSelectionChange: (assetIds: string[]) => void;
  initialSelection?: string[];
}
```

**Features**:
- Reusable component for any multi-asset selection scenario
- Server-side pagination (React Query with pagination params)
- Column sorting (by name, type, progress)
- Search with debounce (500ms)
- Bulk actions: "Select All on Page" / "Select All Matching Filter"

### 5.3 Bulk Import Wizard

**Component Path**: `src/components/collection/BulkImportWizard.tsx`

**Steps**:
1. **File Upload**:
   - Drag-and-drop or file picker
   - Supported formats: CSV, JSON
   - File size limit warning (10 MB)
   - Preview first 10 rows

2. **Field Mapping**:
   - Table showing: [CSV Column, Sample Value, Suggested Mapping (dropdown), Confidence Badge]
   - Dropdown options: Standard fields (e.g., "Business Owner") + "Custom Attribute" + "Skip"
   - Validation indicators (green check, yellow warning, red error)

3. **Configuration**:
   - Radio: "Overwrite existing values" / "Fill gaps only"
   - Radio: "Fast recalculation (imported assets only)" / "Thorough (with dependencies)"
   - Checkbox: "Send email notification on completion"

4. **Import Execution**:
   - Progress bar with stage indicator
   - Real-time log stream (last 10 messages)
   - "Cancel Import" button (if not yet committed to DB)

5. **Results Summary**:
   - Cards showing: Assets Updated, Gaps Closed, Confidence Increase
   - Link to view updated questionnaires
   - Option to download import report (CSV)

**Polling Hook**:
```typescript
const useBulkImportPolling = (taskId: string | null) => {
  return useQuery({
    queryKey: ['bulk-import-status', taskId],
    queryFn: () => collectionService.getBulkImportStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (data) => {
      if (data?.status === 'completed' || data?.status === 'error') {
        return false; // Stop polling
      }
      return 2000; // Poll every 2 seconds
    }
  });
};
```

### 5.4 Answer Variant Reconciler

**Component Path**: `src/components/collection/AnswerVariantReconciler.tsx`

**UI Design** (Updated with "Keep Majority" - Per Q13):
```
┌────────────────────────────────────────────────────┐
│ Question: What is the Operating System?            │
├────────────────────────────────────────────────────┤
│                                                    │
│ Current Answers:                                   │
│                                                    │
│ ● Windows Server 2016                (3 assets) ← MAJORITY │
│   ├─ Server-001                                   │
│   ├─ Server-002                                   │
│   └─ Server-003                                   │
│                                                    │
│ ● Windows Server 2019                (2 assets)   │
│   ├─ Server-004                                   │
│   └─ Server-005                                   │
│                                                    │
│ [🎯 Keep Majority (3 assets: Windows Server 2016)] │ ← NEW QUICK ACTION
│                                                    │
│ Or choose a different answer:                     │
│ [Dropdown: ▼ Select unified answer]               │
│ Options:                                           │
│   - Keep Windows Server 2016 (overwrite 2 assets) │
│   - Keep Windows Server 2019 (overwrite 3 assets) │
│   - Windows Server 2022 (overwrite all)           │
│   - Other (specify)                               │
│                                                    │
│ [Cancel]  [Apply to This Question]  [Apply to All]│
└────────────────────────────────────────────────────┘
```

**Features**:
- **"Keep Majority" button**: Prominent quick action that auto-selects the most common answer
- Badge shows "MAJORITY" next to the winning answer group
- One-click resolution for common scenarios (e.g., 80/20 split)
- Reduces decision fatigue for large asset selections

---

## 6. Backend Service Implementations

**CRITICAL - Architecture Compliance Requirements**:

### **1. ContextAwareRepository Pattern (MANDATORY)**
All services MUST use the `ContextAwareRepository` pattern for tenant isolation:
- Multi-tenant filtering applied by default (no manual `WHERE client_account_id = ...`)
- RequestContext headers automatically injected into queries
- Type-safe repository methods with proper scoping
- **NO raw session queries** - always use repository layer

### **2. ADR-024 Agent Memory Compliance (MANDATORY)**
Per ADR-024, **CrewAI built-in memory is DISABLED globally**. All agent learning uses `TenantMemoryManager`:

```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# ✅ CORRECT - Use TenantMemoryManager for agent learning
memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

# Store agent learnings after question pruning
await memory_manager.store_learning(
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="question_relevance",
    pattern_data={
        "asset_type": "Server",
        "pruned_questions": ["web_framework", "auth_method"],
        "confidence": 0.92
    }
)

# ❌ WRONG - CrewAI memory is disabled
crew = create_crew(
    agents=[agent],
    tasks=[task],
    memory=True  # FORBIDDEN - Violates ADR-024
)
```

**Why this matters**: CrewAI memory causes 401/422 errors with DeepInfra and lacks multi-tenant isolation. `TenantMemoryManager` uses PostgreSQL + pgvector with proper scoping.

### **3. LLM Cost Tracking (MANDATORY)**
All agent LLM calls MUST route through `multi_model_service.generate_response()` for automatic cost tracking:

```python
# ✅ CORRECT - Automatic tracking to llm_usage_logs
response = await multi_model_service.generate_response(
    prompt=prompt,
    task_type="question_pruning",
    complexity=TaskComplexity.AGENTIC
)

# ❌ WRONG - Bypasses cost tracking
response = litellm.completion(model="deepinfra/llama-4", messages=[...])
```

### **4. JSON Safety (NaN/Infinity Sanitization)**
All agent outputs and analytics fields MUST sanitize NaN/Infinity before returning to frontend:

```python
from app.core.json_safety import sanitize_for_json

# Before sending response
response_data = sanitize_for_json({
    "confidence_score": agent_result.confidence,  # May contain NaN
    "metrics": agent_result.metrics  # May contain Infinity
})

return JSONResponse(content=response_data)
```

**Why**: Frontend JSON parsing fails on `NaN` and `Infinity`. All numeric fields from agents must be validated.

### 6.1 CollectionBulkAnswerService

**File**: `backend/app/services/collection/bulk_answer_service.py`

**Key Methods**:

```python
from app.repositories.context_aware_repository import ContextAwareRepository
from app.models.request_context import RequestContext

class CollectionBulkAnswerService:
    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        question_engine: DynamicQuestionEngine,
        gap_analyzer: IncrementalGapAnalyzer
    ):
        self.db = db
        self.context = context  # Contains client_account_id, engagement_id, user_id
        self.question_engine = question_engine
        self.gap_analyzer = gap_analyzer

        # Initialize context-aware repositories
        self.questionnaire_repo = ContextAwareRepository(
            db, AdaptiveQuestionnaire, context
        )
        self.answer_history_repo = ContextAwareRepository(
            db, CollectionAnswerHistory, context
        )

    async def preview_bulk_answers(
        self,
        child_flow_id: UUID,
        asset_ids: List[UUID],
        question_ids: List[str]
    ) -> BulkAnswerPreview:
        """
        Analyzes existing answers and identifies conflicts.
        Returns preview data for UI to show before submission.
        Uses child_flow_id for Collection child flow context (NOT master flow_id).
        """
        conflicts = []

        for question_id in question_ids:
            # Query using context-aware repo (tenant filters automatic)
            existing_answers = await self._get_existing_answers(
                child_flow_id, asset_ids, question_id
            )

            # Group by answer value
            answer_groups = self._group_by_value(existing_answers)

            if len(answer_groups) > 1:
                conflicts.append({
                    "question_id": question_id,
                    "existing_answers": answer_groups
                })

        return BulkAnswerPreview(
            total_assets=len(asset_ids),
            total_questions=len(question_ids),
            potential_conflicts=len(conflicts),
            conflicts=conflicts
        )

    async def submit_bulk_answers(
        self,
        request: BulkAnswerRequest
    ) -> BulkAnswerResult:
        """
        Applies bulk answers to multiple assets with conflict resolution.
        Uses chunked atomic transactions for data integrity and partial failure reporting.

        Chunking Strategy (Per GPT-5):
        - Processes assets in chunks of 100 per transaction
        - Each chunk commits independently
        - Partial failures reported with structured errors per chunk
        - Idempotency key prevents duplicate processing of same chunk
        """
        CHUNK_SIZE = 100  # Assets per transaction
        updated_questionnaires = []
        failed_chunks = []

        # Process in chunks
        for chunk_idx, asset_chunk in enumerate(self._chunks(request.asset_ids, CHUNK_SIZE)):
            try:
                async with self.db.begin():  # Atomic transaction per chunk
                    chunk_results = []

                    for asset_id in asset_chunk:
                        # Get or create questionnaire for this asset
                        questionnaire = await self._get_questionnaire(
                            request.child_flow_id,
                            asset_id
                        )

                        for answer in request.answers:
                            # Apply conflict resolution strategy
                            should_apply = await self._should_apply_answer(
                                questionnaire, answer, request.conflict_resolution_strategy
                            )

                            if should_apply:
                                # Update answers JSONB
                                questionnaire.answers[answer.question_id] = answer.answer_value

                                # Add to closed_questions
                                if answer.question_id not in questionnaire.closed_questions:
                                    questionnaire.closed_questions.append(answer.question_id)

                                # Record history
                                await self._record_answer_history(
                                    questionnaire.id,
                                    asset_id,
                                    answer,
                                    source="bulk_answer_modal"
                                )

                        chunk_results.append(questionnaire.id)

                    updated_questionnaires.extend(chunk_results)

            except Exception as e:
                # Record failed chunk with structured error
                failed_chunks.append({
                    "chunk_index": chunk_idx,
                    "asset_ids": asset_chunk,
                    "error": str(e),
                    "error_code": "CHUNK_PROCESSING_FAILED"
                })
                logger.error(f"Chunk {chunk_idx} failed: {e}")

        # Batch update progress calculation for successful assets only
        await self._recalculate_progress_batch(updated_questionnaires)

        return BulkAnswerResult(
            success=True,
            assets_updated=len(request.asset_ids),
            questions_answered=len(request.answers),
            updated_questionnaire_ids=updated_questionnaires
        )
```

### 6.2 DynamicQuestionEngine

**File**: `backend/app/services/collection/dynamic_question_engine.py`

**Key Methods**:

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

class DynamicQuestionEngine:
    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        agent_pool: TenantScopedAgentPool
    ):
        self.db = db
        self.context = context
        self.agent_pool = agent_pool

        # Context-aware repos
        self.question_rules_repo = ContextAwareRepository(
            db, CollectionQuestionRule, context
        )

    async def get_filtered_questions(
        self,
        child_flow_id: UUID,
        asset_id: UUID,
        asset_type: str,
        include_answered: bool = False,
        refresh_agent_analysis: bool = False
    ) -> FilteredQuestions:
        """
        Returns questions applicable to this asset type.
        Uses agent pruning if refresh requested, otherwise uses DB rules.
        """
        # Step 1: Get base questions from DB rules
        base_questions = await self._get_db_questions(
            client_account_id, engagement_id, asset_type
        )

        # Step 2: Apply inheritance rules
        questions = await self._apply_inheritance(
            base_questions, asset_type
        )

        # Step 3: Agent-based pruning (if requested)
        if refresh_agent_analysis:
            try:
                # IMPORTANT: Uses multi_model_service for LLM tracking (per CLAUDE.md)
                agent_result = await asyncio.wait_for(
                    self._prune_questions_with_agent(
                        asset_id, asset_type, questions
                    ),
                    timeout=30
                )
                questions = agent_result.pruned_questions
                agent_status = "completed"
                fallback_used = False
            except asyncio.TimeoutError:
                # Graceful degradation
                logger.warning(f"Agent pruning timeout for asset {asset_id}")
                agent_status = "fallback"
                fallback_used = True

    async def _prune_questions_with_agent(
        self,
        asset_id: UUID,
        asset_type: str,
        questions: List[Question]
    ) -> PruneResult:
        """
        Uses multi_model_service for automatic LLM cost tracking.
        """
        prompt = f"Analyze questions for {asset_type} asset {asset_id}..."

        response = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="question_pruning",
            complexity=TaskComplexity.AGENTIC  # Complex analysis requires Llama 4
        )

        return self._parse_pruning_response(response)
        else:
            agent_status = "not_requested"
            fallback_used = False

        # Step 4: Filter out answered questions (if requested)
        if not include_answered:
            questionnaire = await self._get_questionnaire(asset_id)
            questions = [
                q for q in questions
                if q.question_id not in questionnaire.closed_questions
            ]

        return FilteredQuestions(
            questions=questions,
            agent_status=agent_status,
            fallback_used=fallback_used
        )

    async def handle_dependency_change(
        self,
        client_account_id: int,
        engagement_id: int,
        changed_asset_id: UUID,
        changed_field: str,
        old_value: Any,
        new_value: Any
    ) -> List[UUID]:
        """
        Detects which questions should reopen due to dependency change.
        Uses agent analysis with critical field fallback.
        """
        # Check if this is a critical field
        critical_fields = ["os_version", "ip_address", "decommission_status"]

        if changed_field in critical_fields:
            # Fallback: Always reopen dependent questions
            return await self._reopen_dependent_questions_fallback(
                changed_asset_id, changed_field
            )

        # Otherwise, use agent analysis
        try:
            agent_result = await self.agent_pool.analyze_dependency_impact(
                changed_asset_id, changed_field, old_value, new_value
            )

            affected_question_ids = agent_result.questions_to_reopen

            # Reopen questions
            await self._batch_reopen_questions(
                client_account_id,
                engagement_id,
                changed_asset_id,
                affected_question_ids,
                reason=f"Dependency change: {changed_field} changed from {old_value} to {new_value}"
            )

            return affected_question_ids

        except Exception as e:
            logger.error(f"Agent dependency analysis failed: {e}")
            # Fallback to critical field logic
            return await self._reopen_dependent_questions_fallback(
                changed_asset_id, changed_field
            )
```

### 6.3 UnifiedImportOrchestrator

**File**: `backend/app/services/collection/import_orchestrator.py`

**Key Methods**:

```python
class UnifiedImportOrchestrator:
    """
    Shared by Discovery and Collection flows for bulk data imports.
    Follows DRY principle and provides consistent validation.
    """

    def __init__(
        self,
        db: AsyncSession,
        gap_analyzer: IncrementalGapAnalyzer
    ):
        self.db = db
        self.gap_analyzer = gap_analyzer

    async def analyze_import_file(
        self,
        file: UploadFile,
        import_type: str,
        client_account_id: int,
        engagement_id: int
    ) -> ImportAnalysis:
        """
        Analyzes CSV/JSON and suggests field mappings.
        Returns intelligent suggestions based on header names.
        """
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            data = await self._parse_csv(file)
        elif file.filename.endswith('.json'):
            data = await self._parse_json(file)
        else:
            raise ValueError("Unsupported file format")

        # Detect columns
        detected_columns = list(data[0].keys()) if data else []

        # Intelligent field mapping
        suggested_mappings = []
        for csv_column in detected_columns:
            mapping = await self._suggest_field_mapping(
                csv_column, import_type, data
            )
            suggested_mappings.append(mapping)

        # Identify unmapped columns
        unmapped_columns = [
            col for col, mapping in zip(detected_columns, suggested_mappings)
            if mapping.confidence < 0.5
        ]

        # Validation warnings
        validation_warnings = await self._validate_data(
            data, suggested_mappings, client_account_id, engagement_id
        )

        # Create import batch record
        import_batch_id = uuid.uuid4()
        await self._create_import_batch(
            import_batch_id, file.filename, len(data),
            client_account_id, engagement_id
        )

        return ImportAnalysis(
            file_name=file.filename,
            total_rows=len(data),
            detected_columns=detected_columns,
            suggested_mappings=suggested_mappings,
            unmapped_columns=unmapped_columns,
            validation_warnings=validation_warnings,
            import_batch_id=import_batch_id
        )

    async def execute_import(
        self,
        request: ImportExecutionRequest,
        background_tasks: BackgroundTasks
    ) -> ImportTask:
        """
        Executes import in background task.
        Returns task ID for polling.
        """
        task_id = uuid.uuid4()

        # Create task record
        task = ImportTask(
            id=task_id,
            status="processing",
            progress_percent=0,
            current_stage="validating"
        )

        # Start background processing
        background_tasks.add_task(
            self._process_import_background,
            task_id=task_id,
            request=request
        )

        return task

    async def _process_import_background(
        self,
        task_id: UUID,
        request: ImportExecutionRequest
    ):
        """
        Background task for import processing.
        Updates task progress as it proceeds.
        """
        try:
            # Stage 1: Load data (10%)
            await self._update_task_progress(task_id, 10, "loading_data")
            data = await self._load_import_data(request.import_batch_id)

            # Stage 2: Transform data (30%)
            await self._update_task_progress(task_id, 30, "transforming_data")
            transformed = await self._transform_data(
                data, request.confirmed_mappings
            )

            # Stage 3: Update enrichment tables (60%)
            await self._update_task_progress(task_id, 60, "updating_enrichment_tables")
            summary = await self._update_enrichment_tables(
                transformed,
                request.client_account_id,
                request.engagement_id,
                request.overwrite_existing
            )

            # Stage 4: Store custom attributes (70%)
            await self._update_task_progress(task_id, 70, "storing_custom_attributes")
            await self._store_custom_attributes(
                transformed.custom_attributes,
                request.client_account_id,
                request.engagement_id,
                request.import_batch_id
            )

            # Stage 5: Recalculate gaps (90%)
            await self._update_task_progress(task_id, 90, "recalculating_gaps")
            gap_results = await self.gap_analyzer.recalculate_incremental(
                client_account_id=request.client_account_id,
                engagement_id=request.engagement_id,
                asset_ids=summary.updated_asset_ids,
                mode=request.gap_recalculation_mode
            )

            # Stage 6: Complete (100%)
            await self._update_task_progress(task_id, 100, "completed")
            await self._finalize_import_task(
                task_id, summary, gap_results
            )

        except Exception as e:
            logger.error(f"Import task {task_id} failed: {e}")
            await self._mark_task_failed(task_id, str(e))
```

### 6.4 IncrementalGapAnalyzer

**File**: `backend/app/services/collection/incremental_gap_analyzer.py`

**Key Methods**:

```python
class IncrementalGapAnalyzer:
    """
    Efficiently recalculates gaps after bulk imports.
    Supports two modes: Fast (imported assets only) and Thorough (with dependencies).
    """

    async def recalculate_incremental(
        self,
        client_account_id: int,
        engagement_id: int,
        asset_ids: List[UUID],
        mode: str = "fast"  # "fast" or "thorough"
    ) -> GapAnalysisResults:
        """
        Recalculates gaps for specified assets.
        In thorough mode, also analyzes dependent assets.
        """
        if mode == "fast":
            return await self._recalculate_fast(
                client_account_id, engagement_id, asset_ids
            )
        elif mode == "thorough":
            return await self._recalculate_thorough(
                client_account_id, engagement_id, asset_ids
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")

    async def _recalculate_fast(
        self,
        client_account_id: int,
        engagement_id: int,
        asset_ids: List[UUID]
    ) -> GapAnalysisResults:
        """
        Analyzes only the specified assets.
        Fastest option for large imports.
        """
        new_gaps = []
        closed_gaps = []

        for asset_id in asset_ids:
            asset = await self._get_asset(client_account_id, engagement_id, asset_id)

            # Analyze current state
            gaps = await self._identify_gaps(asset)

            # Get previous gaps from questionnaire
            questionnaire = await self._get_questionnaire(asset_id)
            previous_gap_ids = set(
                q["question_id"] for q in questionnaire.questions
            )
            current_gap_ids = set(g.question_id for g in gaps)

            # Identify newly closed gaps
            for gap_id in previous_gap_ids - current_gap_ids:
                closed_gaps.append(gap_id)

            # Identify new gaps
            for gap_id in current_gap_ids - previous_gap_ids:
                new_gaps.append(gap_id)

            # Update questionnaire
            await self._update_questionnaire_gaps(
                questionnaire, gaps
            )

        return GapAnalysisResults(
            assets_analyzed=len(asset_ids),
            new_gaps_identified=len(new_gaps),
            gaps_closed=len(closed_gaps),
            mode="fast"
        )

    async def _recalculate_thorough(
        self,
        client_account_id: int,
        engagement_id: int,
        asset_ids: List[UUID]
    ) -> GapAnalysisResults:
        """
        Analyzes specified assets AND their dependencies.
        Uses dependency graph traversal with depth limits.

        Traversal Guardrails (Per GPT-5):
        - Max depth: 3 levels from source assets
        - Max assets: 10,000 per traversal (prevents graph explosion)
        - Timeout: 60 seconds for graph building
        - Circular dependency detection with visited set
        """
        MAX_DEPTH = 3
        MAX_ASSETS = 10_000

        # Build dependency graph with timeout
        dependency_graph = await asyncio.wait_for(
            self._build_dependency_graph(client_account_id, engagement_id),
            timeout=60
        )

        # Find all dependent assets (BFS traversal with depth limit)
        all_affected_assets = set(asset_ids)
        visited = set()
        queue = [(asset_id, 0) for asset_id in asset_ids]  # (asset_id, depth)

        while queue and len(all_affected_assets) < MAX_ASSETS:
            asset_id, depth = queue.pop(0)

            if asset_id in visited or depth >= MAX_DEPTH:
                continue

            visited.add(asset_id)
            dependents = dependency_graph.get_dependents(asset_id)

            for dependent in dependents:
                if dependent not in visited:
                    all_affected_assets.add(dependent)
                    queue.append((dependent, depth + 1))

        if len(all_affected_assets) >= MAX_ASSETS:
            logger.warning(f"Dependency traversal hit max assets limit: {MAX_ASSETS}")
            # Continue with truncated set

        # Recalculate for all affected assets
        return await self._recalculate_fast(
            client_account_id,
            engagement_id,
            list(all_affected_assets)
        )
```

---

## 7. Implementation Phases

**Router Registration (Per GPT-5 - CRITICAL)**:
All new endpoints MUST be registered in the central router registry to prevent 404 errors:

```python
# backend/app/api/router_registry.py
from app.api.v1.collection import (
    bulk_answer_router,
    dynamic_questions_router,
    bulk_import_router
)

# Register under /api/v1/collection/* prefix
app.include_router(
    bulk_answer_router,
    prefix="/api/v1/collection",
    tags=["collection-bulk-operations"]
)

app.include_router(
    dynamic_questions_router,
    prefix="/api/v1/collection",
    tags=["collection-questions"]
)

app.include_router(
    bulk_import_router,
    prefix="/api/v1/collection",
    tags=["collection-import"]
)
```

**Frontend API Base URL**: `http://localhost:8081/api/v1/collection` (NOT port 3000)

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Database schema and core backend services

**Tasks**:
- ✅ Create Alembic migration for new tables (collection_question_rules, collection_answer_history, asset_custom_attributes, collection_background_tasks)
- ✅ Update existing tables (adaptive_questionnaires, enrichment tables)
- ✅ Implement `DynamicQuestionEngine` with hardcoded fallback
- ✅ Implement `CollectionBulkAnswerService` (preview and submit with chunking)
- ✅ Register routers in `router_registry.py` under `/api/v1/collection/*`
- ✅ Add unit tests for service layer (90% coverage)
- ✅ Document API contracts in OpenAPI spec

**Deliverables**:
- Migration files: `093_collection_question_rules.py`, `094_collection_answer_history.py`, `095_asset_custom_attributes.py`, `096_collection_background_tasks.py`
- Service files: `dynamic_question_engine.py`, `bulk_answer_service.py`
- Router files: `bulk_answer_router.py`, `dynamic_questions_router.py`, `bulk_import_router.py`
- Test files: `test_bulk_answer_service.py`, `test_dynamic_question_engine.py`

### Phase 2: Multi-Asset Answer UI (Weeks 3-4)
**Goal**: Frontend modal for bulk answering

**Tasks**:
- ✅ Implement `AssetPickerTable` component with server-side pagination
- ✅ Implement `MultiAssetAnswerModal` with wizard flow
- ✅ Implement `AnswerVariantReconciler` for conflict resolution
- ✅ Add React Query hooks for bulk answer API
- ✅ Integrate into existing Collection adaptive forms page
- ✅ E2E Playwright test for bulk answer flow

**Deliverables**:
- Components: `AssetPickerTable.tsx`, `MultiAssetAnswerModal.tsx`, `AnswerVariantReconciler.tsx`
- Hooks: `useMultiAssetAnswerWizard.ts`, `useBulkAnswerPreview.ts`
- Tests: `multi-asset-answer.spec.ts`

### Phase 3: Asset-Type Question Filtering (Weeks 5-6)
**Goal**: Show only relevant questions per asset type

**Tasks**:
- ✅ Seed `collection_question_rules` table with initial mappings (bootstrap data)
- ✅ Implement question inheritance logic in `DynamicQuestionEngine`
- ✅ Add "Refresh Questions" button to adaptive forms UI
- ✅ Integrate CrewAI agent for dynamic pruning
- ✅ Implement graceful degradation with fallback banner
- ✅ Update question display logic to filter by asset type

**Deliverables**:
- Seed script: `seed_collection_question_rules.py`
- Agent integration: `questionnaire_pruning_agent.py`
- UI updates: `AdaptiveFormQuestions.tsx` (filtered questions)
- Banner component: `AgentProcessingBanner.tsx`

### Phase 4: Dynamic Gap Closure (Weeks 7-8)
**Goal**: Hide answered questions, intelligently re-emerge on dependency changes

**Tasks**:
- ✅ Implement real-time question closure on answer save
- ✅ Update progress calculation to batch on "Save Progress" button
- ✅ Implement dependency change listener (database triggers or event-driven)
- ✅ Integrate CrewAI agent for re-emergence analysis
- ✅ Add manual reopen functionality (UI icon + API endpoint)
- ✅ Record all answer changes in `collection_answer_history`

**Deliverables**:
- Service updates: `DynamicQuestionEngine.handle_dependency_change()`
- Event handlers: `AssetChangeEventListener.py`
- UI updates: `QuestionItem.tsx` (with reopen icon)
- History tracking: Automatic on all answer saves

### Phase 5: Bulk Import Integration (Weeks 9-11)
**Goal**: CSV/JSON import with intelligent mapping and gap recalculation

**Tasks**:
- ✅ Implement `UnifiedImportOrchestrator` service (shared by Discovery & Collection)
- ✅ Build intelligent field mapping algorithm (header analysis)
- ✅ Implement `IncrementalGapAnalyzer` with fast/thorough modes
- ✅ Create `BulkImportWizard` component with 5-step flow
- ✅ Add background task polling with progress updates
- ✅ Implement custom attribute storage in JSONB column
- ✅ Add bulk import tab to adaptive forms page
- ✅ Create dedicated import page in sidebar (under Collection section)
- ✅ E2E Playwright test for full import workflow

**Deliverables**:
- Services: `import_orchestrator.py`, `incremental_gap_analyzer.py`
- Components: `BulkImportWizard.tsx`, `FieldMappingTable.tsx`
- Hooks: `useBulkImportPolling.ts`
- Tests: `bulk-import-flow.spec.ts`

### Phase 6: Testing & Optimization (Weeks 12-13)
**Goal**: Comprehensive testing, performance optimization, documentation

**Tasks**:
- ✅ Full E2E test coverage (QA Playwright agent)
- ✅ Performance testing (1000 assets, 20 questions, bulk answer in <5 seconds)
- ✅ Load testing bulk import (10,000 row CSV completes in <2 minutes)
- ✅ Security audit (multi-tenant isolation, SQL injection prevention)
- ✅ User acceptance testing with 5 real migration analysts
- ✅ Documentation: User guide, API docs, architecture diagrams
- ✅ Pre-commit compliance across all new code

**Deliverables**:
- Test reports: `qa_test_results.md`, `performance_benchmarks.md`
- Documentation: `COLLECTION_FLOW_USER_GUIDE.md`, updated API docs
- Security audit report: `security_audit_jan2025.md`

### Phase 7: Production Rollout (Week 14)
**Goal**: Gradual rollout with feature flags

**Tasks**:
- ✅ Deploy to Railway staging environment
- ✅ Enable feature flags: `collection.bulk_answer.enabled`, `collection.dynamic_questions.enabled`, `collection.bulk_import.enabled`
- ✅ Monitor for errors (Sentry alerts configured)
- ✅ Run production smoke tests with test engagement
- ✅ Gradually enable for production engagements (10% → 50% → 100%)
- ✅ Collect user feedback, iterate on UX improvements
- ✅ Post-launch retrospective

**Deliverables**:
- Production deployment checklist completed
- Feature flag configuration documented
- User feedback report: `collection_enhancements_feedback.md`
- Retrospective notes: `retrospective_jan2025.md`

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Backend Services** (Pytest):
```python
# test_bulk_answer_service.py
async def test_preview_bulk_answers_no_conflicts():
    # Given: 5 assets with no existing answers
    # When: Preview bulk answer for "os_version"
    # Then: Returns preview with 0 conflicts

async def test_submit_bulk_answers_with_overwrite():
    # Given: 3 assets, 2 have existing "os_version" answers
    # When: Submit bulk answer with overwrite strategy
    # Then: All 3 assets have new answer, history recorded

async def test_bulk_answer_tenant_isolation():
    # Given: Assets from different tenants
    # When: Submit bulk answer for tenant A
    # Then: Only tenant A assets updated, tenant B unchanged
```

**Frontend Components** (React Testing Library):
```typescript
// MultiAssetAnswerModal.test.tsx
test('renders asset selection table with pagination', () => {
  // Given: Modal opened with 50 assets
  // When: Rendered
  // Then: Shows first 10 assets, pagination controls
});

test('shows conflict resolution UI when conflicts detected', async () => {
  // Given: Preview returns conflicts
  // When: User reaches confirmation step
  // Then: Conflict resolution step shown first
});
```

### 8.2 Integration Tests

**API Endpoints** (Pytest with TestClient):
```python
async def test_bulk_answer_endpoint_end_to_end(test_client):
    # 1. Create test engagement with 10 assets
    # 2. POST /api/v1/collection/bulk-answers with answers
    # 3. Verify 200 response
    # 4. Query database to confirm answers saved
    # 5. Verify answer_history records created
    # 6. Verify progress recalculated
```

**Database Operations**:
```python
async def test_question_rules_inheritance():
    # Given: Oracle DB asset type (inherits from Database)
    # When: Query filtered questions
    # Then: Returns Database questions + Oracle-specific questions
    # And: Excludes parent questions marked with override
```

### 8.3 E2E Tests (Playwright)

**Scenario 1: Multi-Asset Bulk Answer**:
```typescript
test('user answers questions for 5 servers via bulk modal', async ({ page }) => {
  // 1. Navigate to Collection → Adaptive Forms
  // 2. Click "Bulk Answer" button
  // 3. Select 5 servers from asset picker
  // 4. Answer wizard questions (OS, Criticality, Owner)
  // 5. Resolve conflicts (if any)
  // 6. Submit and verify success message
  // 7. Check that progress updated for all 5 servers
  // 8. Verify questions no longer show for those servers
});
```

**Scenario 2: Bulk CSV Import**:
```typescript
test('user imports 100 applications via CSV and sees gap reduction', async ({ page }) => {
  // 1. Navigate to Collection → Bulk Import
  // 2. Upload CSV file (100 apps with tech stack data)
  // 3. Review suggested mappings, confirm
  // 4. Select "Thorough" recalculation mode
  // 5. Wait for import to complete (polling)
  // 6. Verify summary shows 80 gaps closed
  // 7. Navigate to questionnaires, confirm reduced question count
});
```

**Scenario 3: Dynamic Question Filtering**:
```typescript
test('database asset shows only database-relevant questions', async ({ page }) => {
  // 1. Navigate to Collection → Adaptive Forms
  // 2. Select a "Database" asset
  // 3. Verify questions shown:
  //    - ✅ Database version, replication type, backup frequency
  //    - ❌ Web framework, authentication method (application-only)
  // 4. Click "Refresh Questions" button
  // 5. Wait for agent processing banner
  // 6. Verify questions updated based on agent analysis
});
```

---

## 9. Security Considerations

### 9.1 Multi-Tenant Isolation

**Pattern**: Every query MUST include `client_account_id` and `engagement_id` filters.

**Enforcement**:
```python
# Bad - Missing tenant filters
result = await db.execute(
    select(AdaptiveQuestionnaire).where(AdaptiveQuestionnaire.id == questionnaire_id)
)

# Good - Tenant filters included
result = await db.execute(
    select(AdaptiveQuestionnaire).where(
        AdaptiveQuestionnaire.id == questionnaire_id,
        AdaptiveQuestionnaire.client_account_id == client_account_id,
        AdaptiveQuestionnaire.engagement_id == engagement_id
    )
)

# Verify rowcount after updates
if result.rowcount == 0:
    raise SecurityError("Tenant isolation violation or record not found")
```

### 9.2 Input Validation

**CSV/JSON Import**:
- ✅ File size limit: 10 MB
- ✅ Row limit: 10,000 rows per import
- ✅ Sanitize column headers (remove SQL keywords)
- ✅ Validate data types before DB insert
- ✅ Use parameterized queries (SQLAlchemy ORM) to prevent SQL injection

**Dropdown Enforcement**:
- ✅ All question answers validated against `answer_options` in `collection_question_rules`
- ✅ "Other" option requires validation (see constraints below)
- ✅ Backend rejects answers not in allowed list

**"Other" Option Validation Constraints** (Per GPT-5):
```python
OTHER_VALIDATION_RULES = {
    "max_length": 100,  # Characters
    "allowed_charset": r"^[a-zA-Z0-9\s\-_.,()]+$",  # Alphanumeric + basic punctuation
    "blacklist": [  # Prevent SQL injection attempts
        "--", "/*", "*/", ";", "DROP", "DELETE", "UPDATE", "INSERT"
    ],
    "min_length": 3  # Prevent empty "Other" submissions
}

# Validation logic
def validate_other_answer(value: str) -> ValidationResult:
    if len(value) > OTHER_VALIDATION_RULES["max_length"]:
        return ValidationResult(valid=False, error="Exceeds 100 characters")

    if not re.match(OTHER_VALIDATION_RULES["allowed_charset"], value):
        return ValidationResult(valid=False, error="Contains invalid characters")

    if any(keyword.lower() in value.lower() for keyword in OTHER_VALIDATION_RULES["blacklist"]):
        return ValidationResult(valid=False, error="Contains prohibited keywords")

    return ValidationResult(valid=True)
```

**"Other" Audit Trail**:
- All "Other" answers logged in `collection_answer_history` with `answer_source: "user_other"`
- Admin dashboard shows frequency of "Other" values for potential promotion to standard options

### 9.3 Rate Limiting

**Bulk Operations**:
- ✅ Limit bulk answer submissions: 10 requests per minute per user
- ✅ Limit bulk import uploads: 5 files per hour per engagement
- ✅ Agent refresh requests: 20 requests per hour per engagement

**Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/bulk-answers")
@limiter.limit("10/minute")
async def submit_bulk_answers(request: BulkAnswerRequest):
    # ...
```

### 9.4 Role-Based Access Control (RBAC)

**STATUS**: ❌ **Deferred to Phase 2** (Per user decision on Q8)

**Phase 1-7 Approach**:
- All authenticated users can perform bulk operations
- No role-based restrictions on endpoints
- Audit trail records all actions with `user_id` for accountability
- Future RBAC implementation will not require API contract changes

**Phase 2 Will Add**:
- Role definitions: `migration_analyst`, `migration_lead`, `migration_admin`, `system_admin`
- Approval gates for high-impact operations
- Decorator-based enforcement: `@require_role(["migration_lead"])`

### 9.5 Audit Trail

**Automatic Logging**:
- ✅ All bulk answer submissions recorded in `collection_answer_history` with `user_id`
- ✅ Import operations logged with user ID, timestamp, file name, role at time of action
- ✅ Question reopening events recorded as first-class entries (per GPT-5 enhancement)
- ✅ CrewAI agent invocations tracked via `llm_usage_logs` (automatic via LiteLLM callback)
- ✅ RBAC enforcement failures logged to security audit table

**Reopen Events as First-Class Audit Entries** (Per GPT-5):
```python
# Each reopen creates a structured history entry
history_entry = {
    "event_type": "question_reopened",
    "question_id": "os_version",
    "reopened_by": "user_manual",  # or "agent_dependency_change", "critical_field_change"
    "reopened_reason": "OS version changed from Windows 2016 → 2019",
    "user_id": context.user_id,
    "timestamp": datetime.utcnow()
}
```

**Audit Timeline UI**: Frontend displays question history as timeline with expand/collapse for details.

---

## 10. Performance Optimization

### 10.1 Database Indexing

**Critical Indexes**:
```sql
-- For bulk answer lookups
CREATE INDEX idx_questionnaires_collection_flow ON migration.adaptive_questionnaires(collection_flow_id, client_account_id, engagement_id);

-- For answer history queries
CREATE INDEX idx_answer_history_asset_question ON migration.collection_answer_history(asset_id, question_id);

-- For custom attribute searches
CREATE INDEX idx_custom_attrs_import_batch ON migration.asset_custom_attributes(import_batch_id);
```

### 10.2 Batch Processing

**Bulk Answer Service**:
- ✅ Process answers in chunks of 100 assets per transaction
- ✅ Use SQLAlchemy bulk operations (`bulk_insert_mappings`, `bulk_update_mappings`)
- ✅ Defer progress calculation to batch update (not per-answer)

**Import Orchestrator**:
- ✅ Parse CSV in streaming mode (avoid loading entire file in memory)
- ✅ Insert enrichment table updates in batches of 500 rows
- ✅ Commit every 1000 rows to avoid long-running transactions

### 10.3 Caching

**Question Rules**:
- ✅ Cache `collection_question_rules` per asset type (TTL: 1 hour)
- ✅ Invalidate cache on rule updates (admin operations)
- ✅ **Cache Invalidation Events** (Per GPT-5): Publish event to all API nodes for immediate invalidation

**Cache Invalidation Pattern** (Per GPT-5 Enhancement):
```python
from app.core.cache_events import publish_cache_invalidation

async def update_question_rules(rule_id: UUID, updates: dict):
    # Update database
    await question_rules_repo.update(rule_id, updates)

    # Publish invalidation event to all API nodes
    await publish_cache_invalidation(
        cache_key=f"question_rules:asset_type:{rule.asset_type}",
        scope="cluster"  # Invalidate across all instances
    )

    logger.info(f"Cache invalidated for asset_type {rule.asset_type}")
```

**Asset Picker**:
- ✅ Cache asset list with server-side pagination (TTL: 5 minutes)
- ✅ Use React Query cache for frontend (staleTime: 5 minutes)

### 10.4 Background Processing

**Agent Operations**:
- ✅ All CrewAI agent calls run in background tasks (FastAPI BackgroundTasks)
- ✅ Provide polling endpoints for status checks
- ✅ Set timeouts (30 seconds for question pruning, 60 seconds for dependency analysis)
- ✅ Implement graceful degradation on timeout (fallback to hardcoded logic)

---

## 11. Migration Plan

### 11.1 Data Migration

**Backfill Question Rules**:
```python
# scripts/seed_collection_question_rules.py
async def seed_initial_question_rules():
    """
    Populates collection_question_rules with baseline questions.
    Run once after migration 093 is deployed.
    """
    baseline_questions = [
        {
            "question_id": "os_version",
            "question_text": "What is the Operating System version?",
            "asset_type": "Server",
            "answer_options": ["Windows Server 2019", "Windows Server 2022", "Linux Ubuntu 20.04", "Linux RHEL 8", "Other"]
        },
        {
            "question_id": "business_criticality",
            "question_text": "What is the business criticality?",
            "asset_type": "Application",
            "answer_options": ["Low", "Medium", "High", "Mission Critical"]
        },
        # ... 50+ baseline questions
    ]

    for question in baseline_questions:
        await db.execute(
            insert(CollectionQuestionRule).values(**question)
        )
```

**Migrate Existing Questionnaire Data**:
```python
# scripts/migrate_questionnaire_answers.py
async def migrate_existing_answers():
    """
    Migrates answers from questions JSONB to answers JSONB.
    Populates closed_questions array.
    """
    questionnaires = await db.execute(
        select(AdaptiveQuestionnaire)
    )

    for q in questionnaires:
        answers = {}
        closed = []

        for question in q.questions:
            if question.get("answer_value"):
                answers[question["question_id"]] = question["answer_value"]
                closed.append(question["question_id"])

        q.answers = answers
        q.closed_questions = closed

    await db.commit()
```

### 11.2 Feature Flags

**Gradual Rollout**:
```python
# config/feature_flags.py
FEATURE_FLAGS = {
    "collection.bulk_answer.enabled": {
        "default": False,
        "staging": True,
        "production": False  # Enable gradually by engagement_id
    },
    "collection.dynamic_questions.enabled": {
        "default": False,
        "staging": True,
        "production": False
    },
    "collection.bulk_import.enabled": {
        "default": False,
        "staging": True,
        "production": False
    }
}
```

**Usage in Code**:
```python
from app.core.feature_flags import is_feature_enabled

if is_feature_enabled("collection.bulk_answer.enabled", engagement_id):
    # Show "Bulk Answer" button
    pass
else:
    # Hide button, show "Coming Soon" banner
    pass
```

### 11.3 Backward Compatibility

**API Versioning**:
- ✅ New endpoints: `/api/v1/collection/*` (no breaking changes to existing endpoints)
- ✅ Existing `/api/v1/collection/questionnaires` endpoint unchanged
- ✅ Frontend gracefully handles missing fields (e.g., `answers` column may be null for old records)

**Database**:
- ✅ New columns have `DEFAULT` values (e.g., `answers JSONB DEFAULT '{}'`)
- ✅ Existing data remains functional without migration (migration script is optional optimization)

---

## 12. Open Questions & Future Enhancements

### 12.1 Design Decisions (FINALIZED)

All open questions have been resolved. This section documents the final decisions:

#### **Q1: Agent Pattern Analysis for Custom Attributes**
**DECISION**: ❌ **NOT included in current design phases (1-7)**
- Moved to Phase 8 (Future Enhancements)
- Agent-suggested standard fields require more UX research
- Current design will store custom attributes in JSONB without automatic promotion

#### **Q2: Bulk Import File Size Limits**
**DECISION**: ✅ **Keep current limits: 10 MB / 10,000 rows**
- Simpler implementation and validation
- Meets 95% of use cases based on historical data
- Users can split large files manually if needed
- Future: Consider auto-splitting in Phase 8 if demand exists

#### **Q3: Question Reopen Notifications**
**DECISION**: ✅ **No email/in-app notifications - Questions appear in app's collection list**
- Reopened questions simply show up in the user's questionnaire view
- Progress percentage decreases to reflect new gaps
- No alert fatigue from notification spam
- Users discover reopened questions organically during data entry

#### **Q4: Multi-Engagement Bulk Answer**
**DECISION**: ✅ **Strict engagement isolation (no cross-engagement selection)**
- Aligns with multi-tenant security principles
- Prevents accidental data leakage across engagements
- Simpler permission model (no "global admin" role needed)
- Asset picker filters by `engagement_id` from RequestContext

#### **Q5: RequestContext Transport Standardization**
**DECISION**: ✅ **Headers ONLY - Reject requests without proper headers**
- All endpoints require: `X-Client-Account-ID`, `X-Engagement-ID`, `X-User-ID`
- Body/query parameters for tenant context are **rejected with 400 Bad Request**
- Ensures consistency across entire platform
- Frontend must send headers on all API calls

**Enforcement**:
```python
@router.post("/bulk-answers")
async def submit_bulk_answers(
    request: BulkAnswerRequest,
    context: RequestContext = Depends(get_request_context)  # Fails if headers missing
):
    # context.client_account_id, context.engagement_id, context.user_id
```

#### **Q6: Per-Question Conflict Strategy Override**
**DECISION**: ✅ **Single global strategy only (no per-question overrides)**
- Simpler UX - less decision fatigue
- Three global strategies sufficient: `overwrite_all`, `fill_blanks_only`, `manual_resolution`
- Reduces API payload complexity
- Phase 8 can add per-question overrides if user research shows demand

#### **Q7: Tenant-Specific Critical Fields Configuration**
**DECISION**: ✅ **Keep hardcoded critical fields list (no tenant customization)**
- Critical fields that trigger question reopening: `os_version`, `ip_address`, `decommission_status`
- Expands globally as new patterns emerge
- Simpler implementation (no configuration UI or admin workflow)
- Phase 8 can add `tenant_critical_fields` table if needed

#### **Q8: RBAC Roles and Approval Gates**
**DECISION**: ❌ **Deferred to Phase 2 - Not required for Phase 1-7**
- Current phases assume `migration_lead` role for all users
- RBAC enforcement and approval gates add complexity without immediate value
- Phase 2 will introduce:
  - Role definitions: `migration_analyst`, `migration_lead`, `migration_admin`, `system_admin`
  - Approval gates for high-impact operations (>5k assets, rule changes)
  - Blocking vs async approval workflow research

**Phase 1-7 Simplification**: All authenticated users can perform bulk operations (audit trail only)

#### **Q9: Import Field Collision Resolution**
**DECISION**: ✅ **Enrichment table fields always win over custom attributes**
- Predictable behavior: Standard fields take priority
- Custom attributes only used for unmapped CSV columns
- If CSV column maps to both enrichment field AND custom attribute, enrichment field is updated
- Custom attribute is **not created** if enrichment field exists
- Prevents data duplication and confusion

**Example**: CSV column `owner_name` → `application_enrichment.owner` (custom attribute NOT created)

#### **Q10: Background Task Cancellation and Rollback**
**DECISION**: ✅ **Cancel before DB commit only**
- User can cancel during:
  - File upload
  - Validation
  - Field mapping confirmation
  - Transformation (pre-commit)
- Once DB writes begin, cancellation is **not allowed**
- Task transitions to `processing` state when DB commit starts
- Simpler implementation (no savepoints or two-phase commit)
- UI shows "Cancel" button only during cancellable stages

**Future Enhancement (Phase 6)**: Add full rollback with savepoints if user testing shows demand

#### **Q11: Hard Ceiling for Bulk Answer Asset Count** (GPT-5)
**DECISION**: ✅ **Limit to 1,000 assets per submission with friendly error**
- Backend validates `len(asset_ids) <= 1000` before processing
- Returns 400 Bad Request with guidance: "Maximum 1,000 assets per bulk answer. Consider multiple submissions or contact support."
- Prevents memory issues and timeouts
- Chunking (100 assets/txn) handles up to 1,000 efficiently

**Enforcement**:
```python
if len(request.asset_ids) > 1000:
    raise HTTPException(
        status_code=400,
        detail={
            "error_code": "BULK_ANSWER_ASSET_LIMIT_EXCEEDED",
            "message": "Maximum 1,000 assets per bulk answer submission",
            "guidance": "Consider multiple submissions or contact support for larger operations"
        }
    )
```

#### **Q12: Bulk Import Dry-Run Support** (GPT-5)
**DECISION**: ✅ **No dry-run parameter - Use analyze endpoint for preview**
- The `POST /bulk-import/analyze` endpoint already provides full preview (rows, mappings, validation warnings)
- Adding `dry_run: true` to `/bulk-import/execute` would duplicate functionality
- Simpler implementation, less API surface
- Users get preview during mapping confirmation step (existing UX)

#### **Q13: Conflict "Keep-Majority" Quick Action** (GPT-5)
**DECISION**: ✅ **Add "Keep Majority" button in conflict resolution UI**
- Automatically selects the answer value with the most occurrences
- Example: 80 assets say "Windows 2019", 20 say "Windows 2016" → One-click applies "Windows 2019" to all
- Speeds up conflict resolution for large selections
- UI shows: "Keep Majority (80 assets: Windows 2019)" as prominent button

**Frontend Implementation**:
```typescript
// In AnswerVariantReconciler component
const majorityAnswer = getMajorityAnswer(conflict.asset_groups);
<Button onClick={() => applyMajority(majorityAnswer)}>
  Keep Majority ({majorityAnswer.count} assets: {majorityAnswer.value})
</Button>
```

#### **Q14: Admin Endpoint to Seed Question Rules** (GPT-5)
**DECISION**: ✅ **No admin endpoint - Use Alembic seed script only**
- Seeding `collection_question_rules` handled by `seed_collection_question_rules.py` script
- Keeps admin API surface smaller (no additional security concerns)
- Standard pattern: `python scripts/seed_collection_question_rules.py --engagement-id=1`
- **Phase 2 Enhancement**: Admin UI for per-engagement question rule customization (not bulk seeding)

**Phase 2 Admin Section**: Will include UI for:
- Adding/editing question rules per engagement
- Configuring asset-type-specific questions
- Managing "Other" value promotions to standard options

#### **Q15: Real-Time Telemetry Events** (GPT-5)
**DECISION**: ✅ **Defer to Phase 8 - No telemetry events in Phase 1-7**
- No Redis/event bus emissions for `question_reopened` or `bulk_answer_applied`
- Avoids premature optimization before real-time dashboard exists
- Database audit trail (`collection_answer_history`, `collection_background_tasks`) provides complete historical data
- **Phase 8 Addition**: Emit events when real-time admin monitoring is built

**Rationale**: Build features when they're needed, not speculatively. Audit tables provide 100% fidelity for future event replay if needed.

### 12.2 Future Enhancements

**Phase 2 (Deferred from Phase 1)**:
- ✅ **RBAC Implementation**: Role definitions, approval gates, decorator-based enforcement
- ✅ **Agent Pattern Analysis**: Auto-suggest custom attributes for promotion to standard fields (threshold: >20 imports)

**Phase 8 (Future)**:
- ✅ **Per-Question Conflict Strategy**: Allow override per question in bulk answer modal
- ✅ **Tenant-Specific Critical Fields**: Configurable question reopening triggers per engagement
- ✅ **Full Task Rollback**: Savepoint-based cancellation with automatic rollback
- ✅ **Auto-Split Large Imports**: Handle 50k+ row files by splitting into multiple batches
- ✅ **Machine Learning Field Mapping**: Train on historical imports for smarter suggestions
- ✅ **Real-time Collaboration**: Multiple users answering questions simultaneously (HTTP polling, no WebSockets)
- ✅ **Question Templates**: Save common question sets for reuse across engagements
- ✅ **Advanced Dependency Analysis**: Graph visualization of asset relationships
- ✅ **Bulk Export**: Download all questionnaire answers as CSV for external analysis

---

## 13. Success Metrics

### 13.1 Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to complete 50 asset questionnaires | <10 minutes (was 50 minutes) | User testing |
| Bulk answer modal load time | <2 seconds for 1000 assets | Performance profiling |
| Bulk import processing speed | >5000 rows/minute | Load testing |
| Question relevance accuracy | >90% (asset-type filtering) | User surveys |
| Gap closure rate post-import | >70% gaps closed | Analytics dashboard |
| User satisfaction (bulk features) | >8/10 Net Promoter Score | Post-deployment survey |

### 13.2 Qualitative Metrics

- ✅ Reduced user friction: "Bulk answer saved me hours of repetitive work"
- ✅ Improved data quality: "Dropdown enforcement prevents typos"
- ✅ Better UX: "I only see questions relevant to my asset type"
- ✅ Transparency: "I understand why questions reappeared after dependency change"

---

## 14. Appendix

### 14.1 Glossary

- **Asset Type**: High-level categorization (Application, Server, Database, Network, Storage)
- **Bulk Answer Modal**: UI component for answering questions for multiple assets simultaneously
- **Closed Question**: Question that has been answered and hidden from the user
- **Conflict Resolution**: Process of reconciling different existing answers when applying bulk answer
- **Custom Attribute**: Unmapped field from bulk import stored in JSONB column
- **Gap Analysis**: Process of identifying missing data fields for migration assessment
- **Incremental Gap Analyzer**: Service that recalculates gaps only for affected assets (not full re-scan)
- **Question Inheritance**: Child asset types inherit questions from parent types
- **Re-emergence**: Closed questions reappearing due to dependency changes

### 14.2 References

- CLAUDE.md: Project coding guidelines and architecture patterns
- ADR-012: Flow Status Management Separation
- `/docs/analysis/Notes/000-lessons.md`: Core architectural lessons
- `/docs/analysis/Notes/coding-agent-guide.md`: Implementation patterns
- Memory: `collection_questionnaire_generation_fix` - Questionnaire generation patterns
- Memory: `asset_aware_questionnaire_generation_2025_24` - Asset-centric architecture
- Memory: `api_request_patterns_422_errors` - POST request body requirements

---

## 15. Design Decisions Summary (Quick Reference)

All 15 design questions have been resolved. This section provides a quick reference for implementation:

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| **1** | Agent pattern analysis for custom attributes | ❌ Phase 8 | Requires UX research, not needed for MVP |
| **2** | Bulk import file size limits | ✅ 10 MB / 10k rows | Covers 95% of use cases, simple validation |
| **3** | Question reopen notifications | ✅ No notifications | Questions appear in app organically, no alert fatigue |
| **4** | Multi-engagement bulk answer | ✅ Strict isolation | Aligns with security, prevents data leakage |
| **5** | RequestContext transport | ✅ Headers ONLY | Platform consistency, reject body/query |
| **6** | Per-question conflict strategy | ✅ Single global | Simpler UX, less complexity |
| **7** | Tenant-specific critical fields | ✅ Hardcoded list | Simpler implementation, expand globally |
| **8** | RBAC roles and approval gates | ❌ Phase 2 | Adds complexity without immediate value |
| **9** | Import field collision resolution | ✅ Enrichment wins | Predictable, no duplication |
| **10** | Background task cancellation | ✅ Before commit only | Simple, clear boundaries |
| **11** | Hard ceiling for bulk answers | ✅ 1,000 assets max | Prevents memory issues, friendly error |
| **12** | Bulk import dry-run support | ✅ No (use analyze) | Analyze endpoint already provides preview |
| **13** | "Keep Majority" quick action | ✅ Yes | Speeds up conflict resolution |
| **14** | Admin endpoint to seed rules | ✅ No (Alembic script) | Smaller API surface, standard pattern |
| **15** | Real-time telemetry events | ❌ Phase 8 | Build when needed, audit tables sufficient |

**Phase 1-7 Scope** (Included): Questions 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14
**Deferred to Phase 2**: Question 8 (RBAC)
**Deferred to Phase 8**: Questions 1, 15 (Agent analysis, real-time events)

---

## 16. Implementation Readiness Checklist

Before starting Phase 1 implementation, verify:

### Architecture Compliance ✅
- [x] All endpoints use `child_flow_id` (not `flow_id` or `collection_flow_id`)
- [x] All endpoints require RequestContext headers (`X-Client-Account-ID`, `X-Engagement-ID`, `X-User-ID`)
- [x] All services use `ContextAwareRepository` for tenant filtering
- [x] All agent LLM calls route through `multi_model_service.generate_response()`
- [x] CrewAI memory disabled (`memory=False`), using `TenantMemoryManager` only
- [x] JSON safety applied to all agent outputs (NaN/Infinity sanitization)

### Database Schema ✅
- [x] 4 new tables designed: `collection_question_rules`, `collection_answer_history`, `asset_custom_attributes`, `collection_background_tasks`
- [x] 2 updated tables: `adaptive_questionnaires`, enrichment tables
- [x] 13+ indexes including composite indexes for high-frequency queries
- [x] All tables use `migration` schema with CHECK constraints

### API Contracts ✅
- [x] 8 endpoints specified with full request/response schemas
- [x] Structured error responses with `status`, `error_code`, `message`, `details`
- [x] Chunking semantics (100 assets/txn, partial failure reporting)
- [x] Validation rules (1,000 asset max, "Other" constraints, file size limits)
- [x] Router registration pattern (`/api/v1/collection/*` prefix)

### Frontend Components ✅
- [x] 4 major components designed: `MultiAssetAnswerModal`, `AssetPickerTable`, `AnswerVariantReconciler`, `BulkImportWizard`
- [x] "Keep Majority" quick action for conflict resolution
- [x] React Query polling strategy (no WebSockets)
- [x] snake_case field naming throughout

### Testing Strategy ✅
- [x] Unit tests (90% coverage target)
- [x] Integration tests (API endpoints end-to-end)
- [x] E2E Playwright tests (3 major scenarios)
- [x] Performance targets (5000 rows/min import, <5s bulk answer)

---

**End of Design Document**

**Document Status**: ✅ **100% Complete - All questions resolved, ready for implementation**

**Next Steps**:
1. ✅ Generate Phase 1 Alembic migrations (4 files)
2. ✅ Implement backend services with architecture compliance
3. ✅ Build frontend components per specifications
4. ✅ Register routers in `router_registry.py`
5. ✅ Write comprehensive tests (unit, integration, E2E)
6. ✅ Deploy to staging with feature flags

**Contact**: For questions or clarifications, refer to Section 12 (Design Decisions) or Section 15 (Quick Reference)
