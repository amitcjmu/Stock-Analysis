# CRITICAL: Adaptive Forms Multi-Asset Redesign Required

## Current Problem

When users select multiple assets for a collection flow, the questionnaire generation creates questions for ALL assets but the form tries to display them all together, causing:

### Technical Issues
1. **Duplicate React Keys**: Sub-questions have same `field_id` for each asset (e.g., 3 instances of `programming_language`)
2. **Data Corruption**: Impossible to save responses to correct asset
3. **React Errors**: "Encountered two children with the same key" errors

### UX Issues
1. Users can't tell which question applies to which asset
2. Form shows 50+ questions mixed together from multiple assets
3. No way to track completion per asset
4. Confusing validation messages

## Root Cause

Backend generates asset-specific questions correctly:
```json
{
  "field_id": "app_technical_bc015f19-...",  // Asset 1
  "sub_questions": [
    {"field_id": "programming_language"},  // ❌ Duplicate
    {"field_id": "framework"}              // ❌ Duplicate
  ]
},
{
  "field_id": "app_technical_b6f4f7bb-...",  // Asset 2
  "sub_questions": [
    {"field_id": "programming_language"},  // ❌ Duplicate
    {"field_id": "framework"}              // ❌ Duplicate
  ]
}
```

Frontend flattens all questions into single array, causing duplicate keys.

## Required Redesign

### 1. Asset Selector (Top of Form)
```tsx
<Select>
  <option>Asset 1: 10.1.1.10 (Server) - 0% Complete</option>
  <option>Asset 2: 10.1.1.11 (Server) - 0% Complete</option>
  <option>Asset 3: CRM Application - 50% Complete</option>
</Select>
```

### 2. Single Asset Questions Display
- Show ONLY questions for selected asset
- Use asset-specific field IDs (already in backend data)
- Display asset context at top: "Answering for: [Asset Name]"

### 3. Progress Tracking Per Asset
```tsx
Overall Progress: 1/3 Assets Complete (33%)
Current Asset: 10.1.1.10 - 4/12 Questions Answered (33%)
```

### 4. Navigation Between Assets
```tsx
<Button onClick={saveAndNext}>Save & Next Asset →</Button>
<Button onClick={saveAndPrevious}>← Previous Asset</Button>
<Button onClick={saveAndFinish}>Save & Finish Later</Button>
```

### 5. Data Persistence Strategy
- Save responses per asset (asset_id in database)
- Track completion status per asset
- Allow partial completion (save progress per asset)
- Final "Submit All" when all assets complete

## Implementation Files to Modify

### Frontend
1. **`src/pages/collection/AdaptiveForms.tsx`**
   - Add asset selector dropdown
   - Filter questions by selected asset
   - Add asset navigation buttons

2. **`src/hooks/collection/useAdaptiveFormFlow.ts`**
   - Track selected asset state
   - Filter questions by asset_id
   - Save responses with asset_id
   - Track per-asset completion

3. **`src/components/collection/AdaptiveFormRenderer.tsx`** (if exists)
   - Render only selected asset's questions
   - Use composite keys: `${assetId}_${fieldId}`

### Backend (Minimal Changes)
- Already generates asset-specific questions ✅
- May need endpoint to save responses per asset
- Return completion status per asset

## Breaking Down Questions by Asset

The backend already provides asset context:
```json
{
  "field_id": "app_technical_bc015f19-cb81-44c7-b3a4-8ca1bec37da6",
  "asset_id": "bc015f19-cb81-44c7-b3a4-8ca1bec37da6",
  "asset_specific": true,
  "metadata": {
    "asset_ids": ["bc015f19-cb81-44c7-b3a4-8ca1bec37da6"]
  }
}
```

Frontend should:
1. Group questions by `asset_id` or `metadata.asset_ids[0]`
2. Show only current asset's questions
3. Flatten sub_questions with parent prefix: `${parent.field_id}__${sub.field_id}`

## Wireframe

```
┌─────────────────────────────────────────────┐
│ Adaptive Data Collection                    │
├─────────────────────────────────────────────┤
│                                             │
│ Select Asset: [▼ 10.1.1.10 (Server)      ] │
│                                             │
│ Asset: 10.1.1.10                            │
│ Type: Server | Environment: Production      │
│ Progress: 4/12 Questions (33%)              │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ Technical Details                           │
│                                             │
│ 1. Programming Language *                   │
│    [☐ Java] [☐ Python] [☐ JavaScript]      │
│                                             │
│ 2. Framework                                │
│    [___________________________]            │
│                                             │
│ 3. Architecture Pattern                     │
│    [▼ Select pattern             ]          │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ [← Previous Asset] [Save Progress]          │
│                      [Save & Next Asset →]  │
│                                             │
│ Overall: 1/3 Assets Complete                │
└─────────────────────────────────────────────┘
```

## Migration Strategy

### Phase 1: Quick Fix (Immediate)
Add unique prefixes to sub_questions to prevent React errors:
```typescript
const flattenedQuestions = questions.flatMap(q => {
  if (q.field_type === 'form_group' && q.sub_questions) {
    return q.sub_questions.map(sq => ({
      ...sq,
      field_id: `${q.field_id}__${sq.field_id}` // Unique ID
    }))
  }
  return [q]
})
```

### Phase 2: Asset Selector (This Sprint)
1. Add asset dropdown selector
2. Filter questions by asset
3. Track per-asset completion
4. Asset navigation buttons

### Phase 3: Enhanced UX (Next Sprint)
1. Asset completion checklist
2. Bulk operations (apply to all similar assets)
3. Smart defaults based on asset type
4. Validation per asset

## Priority
🔴 **CRITICAL** - Current implementation is unusable with multiple assets

## Related Issues
- React duplicate key errors
- Form submission saves to wrong/all assets
- No way to track which asset needs completion
- Poor UX with 50+ mixed questions
