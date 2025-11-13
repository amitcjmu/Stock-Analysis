# E2E Test IDs Required for Frontend Implementation

This document lists all `data-testid` attributes that need to be added to frontend components for E2E tests to pass.

## 📋 Overview

**Total Test IDs Needed**: ~90 unique test IDs across 3 workflows

**Files to Update**:
- Collection page/layout components
- Bulk Answer Modal components
- Bulk Import Wizard components
- Questionnaire Panel components

---

## 1️⃣ Multi-Asset Bulk Answer Workflow (collection-bulk-answer.spec.ts)

### Main Page Actions
```tsx
// Collection page - main action button
data-testid="bulk-answer-button"
```

### Multi-Asset Answer Modal
```tsx
// Modal container
data-testid="multi-asset-answer-modal"

// Asset selection
data-testid="asset-checkbox-{assetId}"                    // Dynamic per asset
data-testid="asset-checkbox-asset-with-conflict-1"        // For testing conflicts
data-testid="asset-checkbox-asset-with-conflict-2"
data-testid="asset-checkbox-asset-with-conflict-3"
data-testid="selected-count"                              // Shows "X assets selected"

// Navigation buttons
data-testid="continue-to-answers-button"
data-testid="preview-answers-button"
data-testid="submit-bulk-answers-button"
```

### Bulk Answer Form
```tsx
// Form container
data-testid="bulk-answer-form"

// Question inputs (dynamic based on question_id)
data-testid="question-app_01_name"                        // Text input
data-testid="question-app_02_language"                    // Dropdown
data-testid="question-app_03_database"                    // Dropdown
data-testid="question-{questionId}"                       // Generic pattern
```

### Preview & Conflict Handling
```tsx
// Preview summary
data-testid="preview-summary"                             // Shows asset/question counts
data-testid="conflict-warning"                            // Warning banner
data-testid="conflict-count"                              // Shows "X conflicts"
data-testid="view-conflicts-button"

// Conflict resolution
data-testid="conflict-detail"                             // Conflict details panel
data-testid="conflict-strategy"                           // Dropdown: overwrite/skip/merge
data-testid="submit-with-conflicts-button"
```

### Success/Error States
```tsx
data-testid="success-message"                             // Success toast/banner
data-testid="error-message"                               // Error toast/banner
```

### Validation
```tsx
data-testid="validation-error"                            // Validation error message
data-testid="required-field-error"                        // Required field error
```

### Asset Filtering
```tsx
data-testid="asset-type-filter"                           // Dropdown: Application/Server/Database
data-testid="filtered-asset-count"                        // Shows count after filtering
```

---

## 2️⃣ Bulk CSV/JSON Import Workflow (collection-bulk-import.spec.ts)

### Main Page Actions
```tsx
data-testid="bulk-import-button"
```

### Import Wizard Modal
```tsx
// Modal container
data-testid="import-wizard-modal"
```

### Step 1: File Upload
```tsx
data-testid="file-upload-input"                           // File input element
data-testid="upload-error"                                // Upload error message
data-testid="clear-file-button"                           // Clear uploaded file
data-testid="file-format"                                 // Shows "CSV" or "JSON"
```

### Step 2: File Analysis Results
```tsx
data-testid="analysis-complete"                           // Analysis complete indicator
data-testid="detected-rows"                               // Shows "X rows"
data-testid="detected-columns"                            // Shows "X columns"
data-testid="continue-to-mapping-button"
```

### Step 3: Field Mapping
```tsx
// Mapping table
data-testid="field-mapping-table"

// Confidence indicators (per field)
data-testid="confidence-indicator-{csvColumn}"            // Shows "95%" confidence
data-testid="confidence-indicator-app_name"

// Mapping dropdowns (per CSV column)
data-testid="mapping-select-{csvColumn}"                  // Dropdown for field mapping
data-testid="mapping-select-prog_lang"
data-testid="mapping-select-server_name"
data-testid="mapping-select-os_type"
data-testid="mapping-select-cpu_count"

// Mapping summary
data-testid="mapped-fields-count"                         // Shows "3 of 3 mapped"
data-testid="continue-to-config-button"
```

### Step 4: Import Configuration
```tsx
data-testid="import-configuration"                        // Config panel

// Configuration options
data-testid="overwrite-existing-checkbox"
data-testid="gap-recalc-mode"                             // Dropdown: fast/thorough
data-testid="start-import-button"
```

### Step 5: Validation Warnings
```tsx
data-testid="validation-warnings"                         // Warning panel
data-testid="warning-count"                               // Shows "X warnings"
data-testid="expand-warnings-button"

// Specific warnings
data-testid="warning-invalid-dropdown"
data-testid="warning-missing-required"
data-testid="warning-confirmation-dialog"
data-testid="confirm-proceed-button"
```

### Step 6: Import Progress
```tsx
data-testid="import-progress-bar"                         // Progress bar element
data-testid="progress-percent"                            // Shows "X%"
data-testid="current-stage"                               // Shows stage name

// Progress stages
// - "Validating data"
// - "Creating assets"
// - "Answering questions"
// - "Recalculating gaps"

// Cancel functionality
data-testid="cancel-import-button"
data-testid="cancel-confirmation-dialog"
data-testid="confirm-cancel-button"
data-testid="import-canceled"                             // Canceled state indicator
data-testid="retry-import-button"
```

### Step 7: Import Complete
```tsx
data-testid="import-complete"                             // Completion indicator

// Results summary
data-testid="assets-created"                              // Shows count
data-testid="questions-answered"                          // Shows count
data-testid="import-errors"                               // Shows error count

// Close button
data-testid="close-wizard-button"
```

---

## 3️⃣ Dynamic Question Filtering Workflow (collection-dynamic-questions.spec.ts)

### Asset Selection
```tsx
data-testid="asset-row-{assetId}"                         // Clickable asset row
data-testid="asset-row-app-1"                             // Example: Application asset
data-testid="asset-row-server-1"                          // Example: Server asset
data-testid="asset-row-db-1"                              // Example: Database asset
```

### Questionnaire Panel
```tsx
data-testid="open-questionnaire-button"
data-testid="questionnaire-panel"                         // Main panel container
data-testid="asset-type-badge"                            // Shows asset type
```

### Question Filtering Controls
```tsx
// Filter dropdowns
data-testid="question-filter-dropdown"                    // Filter control
data-testid="answered-filter"                             // Dropdown: all/answered/unanswered
data-testid="section-filter"                              // Filter by section

// Question counts
data-testid="total-questions-count"                       // Total questions
data-testid="unanswered-questions-count"                  // Unanswered count
data-testid="filtered-questions-count"                    // After filtering
```

### Agent-Based Pruning
```tsx
data-testid="agent-pruning-toggle"                        // Toggle for agent pruning
data-testid="refresh-questions-button"                    // Trigger agent analysis
data-testid="agent-analysis-indicator"                    // "Agent analyzing..."
data-testid="agent-pruning-complete"                      // Analysis complete
data-testid="pruned-questions-count"                      // Shows count pruned
data-testid="agent-fallback-message"                      // Agent timeout/error message
```

### Question Display
```tsx
// Question list
data-testid="question-list"

// Individual questions (dynamic)
data-testid="question-item-{questionId}"
data-testid="question-{questionId}-text"
data-testid="question-{questionId}-status"                // answered/unanswered

// Answer inputs
data-testid="answer-input-{questionId}"
```

### Dependency-Triggered Re-emergence
```tsx
data-testid="dependency-warning"                          // Warning banner
data-testid="reopened-questions-list"                     // List of reopened questions
data-testid="reopened-count"                              // Shows count
data-testid="dependency-reason"                           // Why questions reopened
```

### Progress Indicators
```tsx
data-testid="progress-bar"                                // Overall progress bar
data-testid="completion-percent"                          // Shows "X% complete"
data-testid="answered-weight"                             // Weight-based calculation
data-testid="total-weight"
```

### Critical Gaps
```tsx
data-testid="critical-gaps-panel"                         // Panel showing critical gaps
data-testid="critical-gap-count"                          // Count of critical gaps
data-testid="critical-gap-{questionId}"                   // Individual critical gap
data-testid="highlight-critical-toggle"                   // Toggle to highlight critical
```

---

## 📝 Implementation Notes

### 1. Dynamic Test IDs
Many test IDs are **dynamic** and should follow these patterns:

```tsx
// Asset checkboxes
<Checkbox data-testid={`asset-checkbox-${asset.id}`} />

// Question inputs
<Input data-testid={`question-${questionId}`} />

// Confidence indicators
<Badge data-testid={`confidence-indicator-${csvColumn}`}>95%</Badge>

// Mapping selects
<Select data-testid={`mapping-select-${csvColumn}`} />
```

### 2. Conditional Test IDs
Some test IDs should only appear conditionally:

```tsx
// Only show if there are conflicts
{hasConflicts && (
  <Alert data-testid="conflict-warning">
    <span data-testid="conflict-count">{conflicts.length} conflicts</span>
  </Alert>
)}

// Only show during agent analysis
{agentStatus === 'analyzing' && (
  <Spinner data-testid="agent-analysis-indicator" />
)}
```

### 3. Multiple Elements with Same Test ID
Some test IDs appear on multiple elements (e.g., `current-stage` updates as progress changes):

```tsx
// Progress stage updates
<div data-testid="current-stage">
  {stage === 'validating' && 'Validating data'}
  {stage === 'creating' && 'Creating assets'}
  {stage === 'answering' && 'Answering questions'}
  {stage === 'recalculating' && 'Recalculating gaps'}
</div>
```

### 4. Test Data Requirements
E2E tests assume certain test data exists:

```tsx
// Assets for conflict testing
data-testid="asset-checkbox-asset-with-conflict-1"
data-testid="asset-checkbox-asset-with-conflict-2"
data-testid="asset-checkbox-asset-with-conflict-3"

// Assets for type filtering
data-testid="asset-row-app-1"      // Application
data-testid="asset-row-server-1"   // Server
data-testid="asset-row-db-1"       // Database
```

**Recommendation**: Create test data seeder that creates assets with these IDs.

---

## ✅ Implementation Checklist

### Phase 1: Core Components (Required for all tests)
- [ ] Collection page - main buttons
  - [ ] `bulk-answer-button`
  - [ ] `bulk-import-button`
- [ ] Asset selection components
  - [ ] `asset-checkbox-{assetId}`
  - [ ] `selected-count`

### Phase 2: Bulk Answer Modal
- [ ] Modal container and navigation
  - [ ] `multi-asset-answer-modal`
  - [ ] `continue-to-answers-button`
  - [ ] `preview-answers-button`
  - [ ] `submit-bulk-answers-button`
- [ ] Question form inputs
  - [ ] `bulk-answer-form`
  - [ ] `question-{questionId}` (dynamic)
- [ ] Conflict handling
  - [ ] `conflict-warning`
  - [ ] `conflict-count`
  - [ ] `conflict-strategy`
- [ ] Success/error states
  - [ ] `success-message`
  - [ ] `error-message`

### Phase 3: Bulk Import Wizard
- [ ] File upload
  - [ ] `import-wizard-modal`
  - [ ] `file-upload-input`
  - [ ] `analysis-complete`
- [ ] Field mapping
  - [ ] `field-mapping-table`
  - [ ] `mapping-select-{csvColumn}` (dynamic)
  - [ ] `confidence-indicator-{csvColumn}` (dynamic)
- [ ] Progress tracking
  - [ ] `import-progress-bar`
  - [ ] `current-stage`
  - [ ] `progress-percent`
- [ ] Results
  - [ ] `import-complete`
  - [ ] `assets-created`
  - [ ] `questions-answered`

### Phase 4: Dynamic Questions
- [ ] Questionnaire panel
  - [ ] `questionnaire-panel`
  - [ ] `question-list`
  - [ ] `question-item-{questionId}` (dynamic)
- [ ] Filtering
  - [ ] `question-filter-dropdown`
  - [ ] `answered-filter`
- [ ] Agent pruning
  - [ ] `agent-pruning-toggle`
  - [ ] `agent-analysis-indicator`
- [ ] Progress
  - [ ] `progress-bar`
  - [ ] `completion-percent`

---

## 🧪 Testing the Implementation

After adding test IDs, verify with:

```bash
# Run E2E tests
npm run test:e2e -- tests/e2e/collection-bulk-answer.spec.ts
npm run test:e2e -- tests/e2e/collection-bulk-import.spec.ts
npm run test:e2e -- tests/e2e/collection-dynamic-questions.spec.ts

# Or all at once
npm run test:e2e -- tests/e2e/collection-*.spec.ts

# With UI for debugging
npx playwright test --ui
```

---

## 📚 Reference

- **Test Files**:
  - `/tests/e2e/collection-bulk-answer.spec.ts` (6 scenarios)
  - `/tests/e2e/collection-bulk-import.spec.ts` (7 scenarios)
  - `/tests/e2e/collection-dynamic-questions.spec.ts` (8 scenarios)

- **Component Locations** (likely):
  - `/src/app/collection/page.tsx` - Main collection page
  - `/src/components/collection/BulkAnswerModal.tsx` - Bulk answer modal
  - `/src/components/collection/ImportWizard.tsx` - Import wizard
  - `/src/components/collection/QuestionnairePanel.tsx` - Questionnaire panel

---

**Generated**: 2025-10-24
**For**: Issues #783, #784, #785 - E2E Test Implementation
