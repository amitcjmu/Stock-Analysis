# Collection Flow Phase/Status Fixes and Assessment Readiness

## Problem 1: Phase/Status Confusion - ADR-012 Violation

**Symptom**: Database had `current_phase = 'completed'` (a status value) instead of valid phase name
**Root Cause**: Agent decision logic set `next_phase="completed"` instead of MFO phase name
**Architecture**: MFO (Master Flow Orchestrator) automatically maps parent phase names to child flow phases

### Solution: Use MFO Phase Names in Agent Decisions

```python
# backend/app/services/crewai_flows/agents/decision/collection_decisions.py:261
# ❌ WRONG - "completed" is a status value, not a phase name
return AgentDecision(
    action=PhaseAction.PROCEED,
    next_phase="completed",  # Invalid!
    confidence=0.95
)

# ✅ CORRECT - Use MFO phase name, automatic mapping happens
return AgentDecision(
    action=PhaseAction.PROCEED,
    next_phase="synthesis",  # MFO maps to "finalization" for child flows
    confidence=0.95,
    reasoning="Collection flow completed successfully. Data synthesis meets quality standards."
)
```

### Phase Mapping Architecture

```python
# backend/app/services/master_flow/collection_mfo_utils.py:278
# Automatic MFO → Child Flow phase mapping
MFO_TO_CHILD_PHASE_MAP = {
    "synthesis": "finalization",
    # ... other mappings
}
```

### Frontend Route Configuration

```typescript
// src/config/flowRoutes.ts:71-72
export const FLOW_PHASE_ROUTES = {
  collection: {
    'finalization': (flowId: string) => `/collection/synthesis/${flowId}`,
    // Maps child flow "finalization" phase to synthesis UI route
  }
};
```

### Database Fix

```sql
-- Fix existing invalid phases
UPDATE migration.collection_flows
SET current_phase = 'finalization'
WHERE current_phase = 'completed';
```

**Key Principle**: Per ADR-012, `status` = lifecycle (running/paused/completed), `phase` = operational progress. Never mix them.

---

## Problem 2: Assessment Readiness False Negatives

**Symptom**: Assessment validation failed despite assets having required fields (business_criticality, environment)
**Root Cause**: Validation only checked `collection_questionnaire_response` table, but gap analysis doesn't create gaps for fields that already exist in assets

### Solution: Dual-Source Validation Pattern

Check BOTH questionnaire responses AND pre-existing asset fields:

```python
# backend/app/api/v1/endpoints/collection_crud_update_commands/assessment_validation.py:91-149

# Step 1: Check questionnaire responses (as before)
has_business_criticality_from_questionnaire = any(
    qid in collected_question_ids
    for qid in readiness_requirements["business_criticality_questions"]
)

# Step 2: ALSO check asset fields directly
selected_asset_ids = (flow.flow_metadata or {}).get("selected_asset_ids", [])
has_business_criticality_from_assets = False
has_environment_from_assets = False

if selected_asset_ids:
    assets_result = await db.execute(
        select(Asset).where(
            Asset.id.in_(selected_asset_ids),
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        )
    )
    assets = list(assets_result.scalars().all())

    for asset in assets:
        # Check criticality field OR custom_attributes.business_criticality
        if asset.criticality:
            has_business_criticality_from_assets = True
        elif asset.custom_attributes and asset.custom_attributes.get("business_criticality"):
            has_business_criticality_from_assets = True

        # Check environment field OR custom_attributes.environment
        if asset.environment:
            has_environment_from_assets = True
        elif asset.custom_attributes and asset.custom_attributes.get("environment"):
            has_environment_from_assets = True

        # Early exit optimization
        if has_business_criticality_from_assets and has_environment_from_assets:
            break

# Step 3: Combine - field satisfied if exists in EITHER source
has_business_criticality = (
    has_business_criticality_from_questionnaire
    or has_business_criticality_from_assets
)
has_environment_or_technical_detail = (
    has_environment_from_questionnaire or has_environment_from_assets
)

# Step 4: Set assessment_ready flag based on combined check
if has_business_criticality and has_environment_or_technical_detail:
    flow.assessment_ready = True
```

**Key Principle**: Gap analysis only collects MISSING data. Assessment validation must respect this by checking both questionnaire responses and pre-existing asset fields.

---

## Problem 3: Asset Selection UX - Selected Items Not Visible

**Symptom**: Users had to scroll to find which applications they selected
**Solution**: Smart sorting that dynamically prioritizes selected items

```typescript
// src/pages/collection/ApplicationSelection/index.tsx:127-153
const filteredAssets = useMemo(() => {
  let filtered = allAssets;

  // Apply asset type filter
  if (!selectedAssetTypes.has("ALL")) {
    filtered = allAssets.filter((asset) =>
      selectedAssetTypes.has(asset.asset_type?.toUpperCase() || "UNKNOWN"),
    );
  }

  // Create shallow copy to avoid mutating react-query cached data
  return [...filtered].sort((a, b) => {
    const aSelected = selectedApplications.has(a.id.toString());
    const bSelected = selectedApplications.has(b.id.toString());

    // If selection status differs, prioritize selected items
    if (aSelected !== bSelected) {
      return aSelected ? -1 : 1;
    }

    // If both have same selection status, sort alphabetically
    const aName = a.asset_name || a.name || "";
    const bName = b.asset_name || b.name || "";
    return aName.localeCompare(bName);
  });
}, [allAssets, selectedAssetTypes, selectedApplications]);
```

**Critical**: Use `[...filtered].sort()` NOT `filtered.sort()` to avoid mutating React Query cached data (Qodo Bot review finding).

---

## Problem 4: Continue Button Not Available for Running Flows

**Symptom**: Users couldn't navigate to current phase page while flow was running
**Root Cause**: Button only showed for stuck (progress=0%) or completed flows

### Solution: Always Show Continue/View Progress for Running Flows

```typescript
// src/components/collection/progress/TabbedFlowDetails.tsx:141-170
{/* Continue/View Progress button - always show for running or completed flows */}
{(flow.status === 'running' || isCompleted) && onContinue && (
  <Button
    variant="default"
    size="sm"
    onClick={handleContinue}
    disabled={isProcessing}
    title={isCompleted ? "Continue to Assessment" : "View Current Phase"}
  >
    {isProcessing ? (
      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
    ) : (
      <ArrowRight className="h-4 w-4 mr-1" />
    )}
    {isCompleted ? "Continue" : "View Progress"}
  </Button>
)}
```

**Key Pattern**: Button label changes based on state:
- Running flows: "View Progress" (navigate to current phase)
- Completed flows: "Continue" (proceed to next workflow stage)

---

## Problem 5: Assessment Flow Error - Non-Application Assets

**Symptom**: Collection selected server-type asset, assessment flow failed with "No applications selected"
**Root Cause**: Collection can select ANY asset type (server, database, storage), but assessment expects application entities

### Solution: Show Asset/Application Mapping Information

```typescript
// src/pages/assessment/[flowId]/sixr-review.tsx:66-118
if (state.selectedApplicationIds.length === 0) {
  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-amber-900 mb-2">
          Loading Assessment Data
        </h2>
        <p className="text-amber-800 mb-4">
          Assessment flow is being initialized from collection data.
        </p>

        {state.selectedApplications && state.selectedApplications.length > 0 ? (
          <div className="mt-4 p-4 bg-white rounded-lg border border-amber-200">
            <h3 className="font-medium text-sm text-gray-900 mb-3">
              Selected Assets from Collection:
            </h3>
            <div className="space-y-2">
              {state.selectedApplications.map((app) => (
                <div key={app.application_id} className="flex items-center justify-between text-sm">
                  <div>
                    <span className="font-medium">{app.application_name || app.application_id}</span>
                    {app.application_type && (
                      <span className="ml-2 text-gray-500">({app.application_type})</span>
                    )}
                  </div>
                  {/* Fixed: was app.application_name !== app.application_name (impossible) */}
                  {app.application_name && app.application_name !== app.application_id && (
                    <span className="text-gray-600">→ App: {app.application_name}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-4 p-4 bg-white rounded-lg">
            <p className="text-sm text-gray-700">
              If this persists, check that assets were properly selected in collection phase
              and have application associations.
            </p>
          </div>
        )}
      </div>
    </AssessmentFlowLayout>
  );
}
```

**Future Enhancement**: Add ASSET_APPLICATION_RESOLUTION phase between collection and assessment to allow users to map non-application assets to applications before 6R analysis begins.

---

## TypeScript Type Safety Patterns

### Error Handling: Use `unknown` Not `any`

```typescript
// ❌ WRONG
} catch (error: any) {
  console.error("Error:", error);
}

// ✅ CORRECT
} catch (error: unknown) {
  console.error("Error:", error);
  if (error instanceof Error) {
    // Now can safely access error.message
  }
}
```

### Leverage Type Inference in Map Functions

```typescript
// ❌ WRONG - Explicit any defeats type checking
state.selectedApplications.map((app: any) => ...)

// ✅ CORRECT - Let TypeScript infer from state type
state.selectedApplications.map((app) => ...)
```

---

## React Query Cache Protection

**Critical Pattern**: Never mutate React Query cached data directly

```typescript
// ❌ WRONG - Mutates cache
const sortedData = cachedData.sort((a, b) => ...);

// ✅ CORRECT - Shallow copy first
const sortedData = [...cachedData].sort((a, b) => ...);
```

**Why**: React Query caches API responses. Sorting in-place mutates the cache, causing:
- Stale data display
- Unexpected re-renders
- Cache invalidation issues

**When to Use**: Any array transformation (sort, filter, map) on data from `useQuery` or `useInfiniteQuery`.

---

## Validation Comments Pattern

When adding new valid phases, update validation comments in ALL related files:

```typescript
// src/pages/collection/Progress.tsx:242
// Valid collection phases: asset_selection, gap_analysis, questionnaire_generation,
// manual_collection, synthesis, finalization

// src/components/collection/progress/FlowDetailsCard.tsx:156
// Same comment ensures consistency
```

**Why**: Helps future developers understand valid phase transitions without diving into backend code.

---

## Pre-commit Workflow

1. Run on all files at least once: `pre-commit run --all-files`
2. Fix reported issues (line length, trailing whitespace, type errors)
3. Commit with fixed files
4. If new issues appear, fix and amend commit (ONLY if not pushed and you're the author)

**Flake8 Line Length Fix Pattern**:
```python
# ❌ WRONG - 127 characters
logger.info(f"Assessment readiness check - business_criticality: {has_business_criticality} (questionnaire: {has_business_criticality_from_questionnaire})")

# ✅ CORRECT - Break at logical points
logger.info(
    f"Assessment readiness check - "
    f"business_criticality: {has_business_criticality} "
    f"(questionnaire: {has_business_criticality_from_questionnaire}, "
    f"assets: {has_business_criticality_from_assets})"
)
```

---

## Git Workflow for Multi-File Fixes

```bash
# 1. Create feature branch
git checkout -b fix/descriptive-name

# 2. Stage all changes including Serena memories
git add backend/ src/ .serena/

# 3. Run pre-commit
pre-commit run --all-files

# 4. Fix issues, stage fixes
git add <fixed-files>

# 5. Comprehensive commit message
git commit -m "fix: Descriptive title

## Problem 1: ...
- Root cause: ...
- Fix: ...

## Problem 2: ...
"

# 6. Push and create PR
git push -u origin fix/descriptive-name
gh pr create --title "..." --body "..."

# 7. After merge, cleanup
git checkout main
git pull origin main
git branch -d fix/descriptive-name
```

---

## Qodo Bot Review Patterns

**Common Issues**:

1. **Impossible Conditions**: `x !== x` always false
   - Fix: Check for typo, likely meant different variable

2. **Cache Mutations**: Direct sort/filter on cached arrays
   - Fix: Add shallow copy `[...array]` before mutation

3. **Performance Optimizations**: Database aggregation suggestions
   - Evaluate: Current implementation may be correct for use case
   - Defer if optimization is premature

**Response Pattern**:
- Fix critical bugs immediately (impossible conditions, cache mutations)
- Evaluate performance suggestions (may defer if current approach is intentional)
- Commit fixes with clear explanation of what was addressed and what was deferred

---

## Related Patterns
- `adr-012-collection-flow-status-remediation` - Status vs phase separation
- `api_request_patterns_422_errors` - Field naming conventions
- `qodo_bot_feedback_resolution_patterns` - PR review handling
