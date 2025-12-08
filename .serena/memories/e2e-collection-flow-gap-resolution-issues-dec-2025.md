# Collection Flow Gap Resolution Issues - E2E Test Findings

## Test Date: December 2025

## Summary
E2E testing of collection flow revealed critical gap resolution issues where questionnaire responses don't properly close gaps or persist to asset data.

## Issue 1: Field Name Mismatch in Gap Resolution

### Problem
When submitting questionnaire responses, only 7 of 22 gaps are marked as resolved. The remaining 18 responses have `NULL gap_id` because questionnaire field names don't match gap field names.

### Examples of Mismatches
| Questionnaire Field | Gap Field | Status |
|---------------------|-----------|--------|
| `code_quality_metric_level` | `code_quality_metrics` | NOT MATCHED |
| `documentation_completeness` | `documentation_quality` | NOT MATCHED |
| `eol_assessment_status` | `eol_technology_assessment` | NOT MATCHED |
| `cpu_cores` | `cpu_memory_storage_specs` | NOT MATCHED |
| `architecture_pattern` | `architecture_pattern` | MATCHED ✅ |

### Database Evidence
```sql
-- 25 responses saved, but only 7 have gap_id linked
SELECT id, question_id, gap_id FROM migration.collection_questionnaire_responses
WHERE collection_flow_id = '15b3a9b2-3ce8-4321-8845-22d5f94b3584';
-- Result: 25 rows, 7 with gap_id, 18 with NULL gap_id
```

### Root Cause Location
The gap-to-response matching logic likely in:
- `backend/app/services/collection/questionnaire_submission.py`
- `backend/app/api/v1/endpoints/collection_flow/adaptive_forms.py`

## Issue 2: Gaps Reappear on New Collection Flows

### Problem
When creating a new collection flow for an asset that already completed a questionnaire:
- All gaps reappear (22 gaps for Consul)
- Previous questionnaire responses don't prevent gap detection
- Expected: 0 gaps (or only unresolved gaps)

### Explanation
Gap detection uses asset table field values, not questionnaire_responses table. The questionnaire responses:
1. Are stored in `collection_questionnaire_responses`
2. Mark gaps as "resolved" in `collection_data_gaps`
3. But do NOT update asset table fields (`assets.technology_stack`, etc.)

Each new collection flow creates NEW gap records due to unique constraint:
`uq_gaps_dedup (collection_flow_id, field_name, gap_type, asset_id)`

### Design Question
Is this intentional? Should questionnaire responses:
A) Update the underlying asset fields (data enrichment)
B) Only mark gaps as resolved per-flow (audit trail)
C) Both - enrich asset AND mark per-flow resolution

## Test Data
- Asset ID: `1f9e22f8-7d91-4c9b-bb25-b725e9913985` (Consul)
- First Collection Flow ID: `37fdbd1e-9784-414a-90a6-ee594e807c8e`
- Second Collection Flow ID: `e9f19dc0-ca0c-40a4-b8bf-a7bea8f2953c`
- First flow internal ID: `15b3a9b2-3ce8-4321-8845-22d5f94b3584`

## Recommendations
1. **Fix field name mapping** in gap-to-response matching logic
2. **Consider data enrichment** - write questionnaire responses back to asset fields
3. **Add gap inheritance** - new flows should recognize previously resolved gaps
