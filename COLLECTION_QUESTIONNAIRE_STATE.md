# Collection Flow Questionnaire - Current State Investigation

**Investigation Date:** October 24, 2025
**Branch:** feat/issue-768-collection-adaptive-questionnaire-day1
**Last Commit:** f37eea53d - "fix(collection): Convert all questionnaire questions to MCQ format"

## Quick Reference

| Aspect | Current State |
|--------|--------------|
| **Question Format** | All MCQ (Multiple Choice Questions) |
| **Total Questions** | 67+ dynamically generated (not from seed templates) |
| **Data Persistence** | PostgreSQL JSONB + relationships |
| **Frontend Display** | Dynamic category-based grouping (7 categories) |
| **API Pattern** | RESTful with batch support |
| **Multi-tenancy** | Full isolation via client_account_id + engagement_id |

## 1. Question Definition Architecture

### Two-Tier Question System

#### Tier 1: Static Seed Templates
**Purpose:** Baseline questions for manual CRUD operations
**Location:** `/backend/scripts/seed_data/`

Files:
- `server_questions.py` - 10 server questions
- `application_questions.py` - 10 app questions
- `database_questions.py` - 10 database questions
- `network_questions.py` - 10 network questions
- `storage_questions.py` - 10 storage questions
- `collection_question_templates.py` - Aggregator

Example (Server Question 5):
```python
{
    "question_text": "What is the server role?",
    "question_type": "dropdown",
    "section": "Technical",
    "weight": 7,
    "is_required": True,
    "answer_options": ["Web Server", "App Server", "Database Server", "File Server", "Domain Controller", "Other"]
}
```

#### Tier 2: Dynamic Generated Questions
**Purpose:** Context-aware questions based on gap analysis
**Generation:** CrewAI agents during questionnaire generation phase
**Location:** `/backend/app/services/ai_analysis/questionnaire_generator/`

Generated from:
- Gap analysis results
- Asset characteristics
- Automation tier
- Historical patterns

**Key Difference:** Questions from Tier 2 are numbered differently (e.g., `server_05_patching` in E2E tests refers to a different question than the static seed template Question 5).

---

## 2. Current Question Format (MCQ Standard)

All questions follow this JSON structure:

```json
{
  "field_id": "unique_question_identifier",
  "question_text": "What is the question asking?",
  "field_type": "select|text|textarea|form_group|multiselect|checkbox|radio",
  "category": "metadata|infrastructure|application|business|technical_debt|data_validation|technical_details",
  "required": true,
  "options": [
    {"value": "option_value", "label": "Display Label"},
    {"value": "another_value", "label": "Another Option"}
  ],
  "help_text": "Guidance for answering the question",
  "priority": "high|medium|low",
  "metadata": {
    "asset_id": "uuid-of-asset",
    "asset_type": "Server|Application|Database|Network|Storage",
    "gap_type": "gap_category"
  }
}
```

### MCQ Conversion Rules (Commit f37eea53d)

| Question Type | Converted To | Example Options |
|--------------|-------------|-----------------|
| Data Quality (50) | select | Verified/Needs Update/Incorrect/Requires Manual Review |
| Dependency | select | Minimal/Low/Moderate/High/Very High/Unknown |
| Technical | select | Cloud Native/Modernized/Legacy/Mainframe/Unknown |
| Generic | select | Available/Partial/Not Available/Not Applicable/Unknown |
| Fallback | select | Complete/Mostly Complete/Incomplete/Requires Investigation |

---

## 3. Question Generation Pipeline

```
Gap Analysis Results
    ↓
Questionnaire Generation Phase (PhaseConfig)
    ↓
CrewAI Questionnaire Generation Crew
    ├── Input Mapping: gaps, context, automation_tier
    ├── Processing:
    │   ├── question_builders.py (MCQ format)
    │   ├── question_generators.py (asset-specific)
    │   └── section_builders.py (organization)
    └── Output Mapping: questionnaires, categories, adaptive_logic
    ↓
AdaptiveQuestionnaire Model (insert/update)
    ├── questions JSONB array
    ├── completion_status: pending → in_progress → completed
    ├── responses_collected: dict of answers
    └── question_count: calculated
    ↓
API Endpoint: GET /flows/{flow_id}/questionnaires
    ↓
Frontend: QuestionnaireDisplay component
    ├── Parse questionnaire data
    ├── Group by category dynamically
    ├── Filter by selected asset
    └── Render form with answer controls
    ↓
User Interaction (Answer Questions)
    ↓
API Endpoint: POST /flows/{flow_id}/questionnaires/{questionnaire_id}/responses
    ↓
Database: Update responses_collected in adaptive_questionnaires table
    ↓
Collection Flow State Update
```

---

## 4. API Endpoints

**Base Path:** `/api/v1/collection`

### Questionnaire Operations

#### GET `/flows/{flow_id}/questionnaires`
- **Purpose:** Fetch questionnaires for a collection flow
- **Returns:** `List[AdaptiveQuestionnaireResponse]`
- **Logic Flow:**
  1. Get flow by ID (validated with client_account_id + engagement_id)
  2. Query incomplete questionnaires (status != "completed")
  3. Return serialized questionnaire responses
  4. If none exist and phase is still "questionnaire_generation", wait/retry

#### GET `/flows/{flow_id}/questionnaires/{questionnaire_id}/responses`
- **Purpose:** Retrieve previously saved answers for a questionnaire
- **Returns:** `{"responses": {"question_id": "answer_value", ...}}`

#### POST `/flows/{flow_id}/questionnaires/{questionnaire_id}/responses`
- **Purpose:** Submit or update answers to questionnaire
- **Request Body:** `QuestionnaireSubmissionRequest`
  ```json
  {
    "responses": {
      "question_id": "answer_value",
      "another_question_id": "another_answer"
    },
    "questionnaire_id": "uuid",
    "collection_flow_id": "uuid"
  }
  ```
- **Returns:** `{"status": "success", "message": "...", "saved_count": n}`
- **Side Effects:** Updates `responses_collected` in database

#### POST `/flows/{flow_id}/questionnaires/responses/batch`
- **Purpose:** Bulk submit multiple question responses
- **Request Body:** `List[Dict[str, Any]]` with multiple response objects
- **RBAC:** Requires COLLECTION_CREATE_ROLES
- **Returns:** `{"status": "success", "count": n}`

#### POST `/flows/{flow_id}/questionnaires/{questionnaire_id}/submit` (LEGACY)
- **Purpose:** Deprecated endpoint for backward compatibility
- **Behavior:** Forwards to `/responses` endpoint

---

## 5. Data Model

**Table:** `migration.adaptive_questionnaires`

### Schema
```sql
CREATE TABLE migration.adaptive_questionnaires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Multi-tenant isolation
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,

    -- Flow relationship
    collection_flow_id UUID NOT NULL REFERENCES collection_flows(id) ON DELETE CASCADE,

    -- Identification
    title VARCHAR(500) NOT NULL,
    description TEXT,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(100) NOT NULL, -- 'basic', 'detailed', 'comprehensive'
    version VARCHAR(50) DEFAULT '1.0',

    -- Content
    applicable_tiers JSONB DEFAULT '[]'::jsonb, -- automation tiers
    question_set JSONB DEFAULT '{}'::jsonb,
    questions JSONB DEFAULT '[]'::jsonb, -- Main question array
    question_count INTEGER DEFAULT 0,

    -- Validation and scoring
    validation_rules JSONB DEFAULT '{}'::jsonb,
    scoring_rules JSONB DEFAULT '{}'::jsonb,

    -- Status and responses
    completion_status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, failed
    responses_collected JSONB DEFAULT '{}'::jsonb, -- {question_id: answer_value}

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_template BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    success_rate NUMERIC(3,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_collection_flow_id (collection_flow_id),
    INDEX idx_client_account_id (client_account_id),
    INDEX idx_engagement_id (engagement_id),
    INDEX idx_template_name (template_name)
)
```

### Related Tables
- `collection_questionnaire_response` - Individual response records
- `collection_flows` - Parent flow relationship
- `client_accounts` - Multi-tenant isolation
- `engagements` - Engagement/project isolation

---

## 6. Frontend Components

### Main Display Component
**File:** `/src/pages/collection/adaptive-forms/components/QuestionnaireDisplay.tsx`

Features:
- Multi-asset questionnaire support with asset selector
- Dynamic filtering by selected asset
- Progress tracking (completion percentage)
- Form validation
- Save/Submit functionality

### Form Data Transformation
**File:** `/src/utils/collection/formDataTransformation.ts`

Key Functions:
- `convertQuestionToFormField(question, index, sectionId)` - Converts backend question to FormField
- `mapQuestionTypeToFieldType(questionType)` - Maps question types to HTML field types
- `normalizeOptions(opts)` - Handles both string[] and FieldOption[] formats

Type Mappings:
- `select` → `select`
- `multi_select` → `multiselect`
- `text` → `text`
- `textarea` → `textarea`
- `boolean` → `checkbox`
- `form_group` → `form_group` (compound question)

### API Client
**File:** `/src/services/api/collection-flow/questionnaires.ts`

Methods:
```typescript
class QuestionnairesApi {
  async getFlowQuestionnaires(flowId: string): Promise<AdaptiveQuestionnaireResponse[]>
  async getQuestionnaireResponses(flowId: string, questionnaireId: string): Promise<{responses: {}}>
  async submitQuestionnaireResponse(flowId: string, questionnaireId: string, request: QuestionnaireSubmissionRequest): Promise<{status: string}>
  async getFlowGaps(flowId: string): Promise<CollectionGapAnalysisResponse[]>
  async scanGaps(flowId: string, selectedAssetIds: string[]): Promise<ScanGapsResponse>
  async analyzeGaps(flowId: string, gaps: DataGap[], selectedAssetIds: string[]): Promise<{job_id: string}>
}
```

---

## 7. Question 5 - Context and Discrepancy

### Seed Template Q5 (Static)
**File:** `/backend/scripts/seed_data/server_questions.py` (line 47)

```python
{
    "question_text": "What is the server role?",
    "question_type": "dropdown",
    "section": "Technical",
    "weight": 7,
    "is_required": True,
    "answer_options": ["Web Server", "App Server", "Database Server", "File Server", "Domain Controller", "Other"]
}
```

### E2E Test Reference (Dynamic)
**File:** `/tests/e2e/collection-dynamic-questions.spec.ts` (line 167-171)

```typescript
await expect(page.locator('[data-testid="question-server_05_patching"]')).toBeVisible();
...
await page.fill('[data-testid="question-server_05_patching"]', 'Monthly patch window');
```

### Analysis

**IMPORTANT:** These are TWO DIFFERENT questions!

1. **Seed Q5** (Static): "What is the server role?" - Static baseline template
2. **E2E Q5** (Dynamic): "What is the patching question?" - Dynamically generated

**Why the numbering matches:** Both use numbering scheme, but from different generation sources.

**Seed Template Patching Question:** Located at Q10, not Q5
```python
{
    "question_text": "What is the patching schedule?",
    "question_type": "dropdown",
    "section": "Operations",
    "weight": 6,
    "answer_options": ["Monthly", "Quarterly", "Annual", "Ad-hoc", "None"]
}
```

---

## 8. Recent MCQ Conversion Changes (Oct 24, 2025)

### Commit: f37eea53d
**Title:** "fix(collection): Convert all questionnaire questions to MCQ format and fix frontend category filtering"

### Changes Made

#### 1. Backend Question Format Conversion
**Files Modified:**
- `question_builders.py` - MCQ conversion functions
- `question_generators.py` - Asset-specific MCQ questions
- `section_builders.py` - Question organization

**Conversions:**
- **Data Quality (50 questions):** textarea → select
  - Options: Verified/Needs Update/Incorrect (high/low confidence)/Requires Manual Review

- **Dependency Questions:** textarea → select (complexity assessment)
  - Options: Minimal/Low/Moderate/High/Very High/Unknown

- **Technical Questions:** textarea → select (modernization readiness)
  - Options: Cloud Native/Modernized/Legacy (supported/unsupported)/Mainframe/Unknown

- **Form Group Sub-Questions:**
  - Backup Strategy: select (Full Daily/Incremental/Differential/Continuous/Snapshot/None/Unknown)
  - Performance Requirements: select (Low/Medium/High/Very High/Mission Critical/Unknown)
  - Replication Setup: select (None/Master-Slave/Master-Master/Cluster/Unknown)

#### 2. Frontend Category Filtering Fix
**File Modified:** `src/utils/collection/formDataTransformation.ts`

**Problem:** 53+ questions were excluded due to hardcoded category list

**Solution:** Replaced static array with dynamic Map-based grouping

Supported Categories (now all functional):
- `metadata` - Configuration and system info
- `infrastructure` - Hardware and deployment details
- `application` - App-specific information
- `business` - Business criticality and impact
- `technical_debt` - Technical limitations
- `data_validation` - Data quality and verification
- `technical_details` - Deep technical characteristics

#### 3. Metadata Handling
- Removed `collection_date` from user-facing questionnaire
- System now handles internally
- Empty sections filtered during processing

#### 4. Gap Scanner Update
**File Modified:** `gap_detector.py`

Updated unified assets table query for better gap detection consistency.

---

## 9. Data Persistence Strategy

### Question Storage
**Location:** `AdaptiveQuestionnaire.questions` (JSONB array)
```json
[
  {
    "field_id": "q1_identifier",
    "question_text": "...",
    "field_type": "select",
    "options": [...],
    "category": "technical_details"
  },
  { /* more questions */ }
]
```

### Response Storage
**Location:** `AdaptiveQuestionnaire.responses_collected` (JSONB object)
```json
{
  "q1_identifier": "selected_value",
  "q2_identifier": "another_answer",
  "q3_identifier": null
}
```

### Completion Tracking
**Calculation:**
```python
completion_percentage = (answered_questions / total_questions) * 100
```

- Incomplete questionnaires: `completion_status` in ["pending", "in_progress"]
- Completed questionnaires: `completion_status` = "completed"

### Multi-Tenant Isolation
All queries include:
```python
where(
    AdaptiveQuestionnaire.client_account_id == context.client_account_id,
    AdaptiveQuestionnaire.engagement_id == context.engagement_id,
    AdaptiveQuestionnaire.collection_flow_id == flow.id
)
```

---

## 10. Key Files Reference

### Backend
```
backend/
├── scripts/seed_data/
│   ├── collection_question_templates.py
│   ├── server_questions.py
│   ├── application_questions.py
│   ├── database_questions.py
│   ├── network_questions.py
│   └── storage_questions.py
├── app/models/collection_flow/
│   └── adaptive_questionnaire_model.py
├── app/api/v1/endpoints/
│   ├── collection_questionnaires.py
│   └── collection_crud_questionnaires/
│       ├── queries.py
│       ├── commands.py
│       ├── utils.py
│       └── __init__.py
├── app/services/ai_analysis/questionnaire_generator/
│   └── tools/
│       ├── question_builders.py
│       ├── question_generators.py
│       └── section_builders.py
└── alembic/versions/
    ├── 005_add_gap_analysis_and_questionnaire_tables.py
    └── 009_add_collection_flow_id_to_questionnaires.py
```

### Frontend
```
src/
├── pages/collection/adaptive-forms/
│   ├── components/QuestionnaireDisplay.tsx
│   └── index.tsx
├── utils/collection/
│   └── formDataTransformation.ts
├── services/api/collection-flow/
│   ├── questionnaires.ts
│   └── types.ts
└── components/collection/forms/
    └── AdaptiveFormContainer.tsx
```

---

## 11. Status & Next Steps

### Current Status
- All questions converted to MCQ format ✓
- Frontend category filtering fixed ✓
- Multi-asset questionnaire support ✓
- Batch response submission ✓
- Multi-tenant isolation verified ✓

### Known Considerations
1. **Question 5 Naming:** E2E test uses dynamically generated questions, not seed templates
2. **Seed Templates:** Used for basic CRUD workflows, not adaptive questionnaires
3. **Dynamic Generation:** CrewAI creates context-aware questions from gaps
4. **Legacy Endpoints:** `/submit` endpoint maintained for backward compatibility

---

## 12. Testing Notes

### E2E Tests
**File:** `/tests/e2e/collection-dynamic-questions.spec.ts`

Tests dynamic question filtering:
- Asset type filtering
- Answered vs unanswered filtering
- Agent-based question pruning
- Dependency-triggered reopening
- Progress completion tracking
- Critical gaps highlighting

### Integration Tests
- Questionnaire generation
- Response submission
- Batch operations
- Multi-asset handling

### Unit Tests
- Question transformation
- Form data conversion
- Category grouping

---

**Last Updated:** Oct 24, 2025
**Last Commit:** f37eea53d
**Status:** All MCQ conversion complete, frontend fixes applied
