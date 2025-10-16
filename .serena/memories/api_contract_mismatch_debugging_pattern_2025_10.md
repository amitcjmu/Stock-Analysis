# API Contract Mismatch: Backend vs Frontend Data Structure

## Problem
Frontend crashes with `TypeError: Cannot read properties of undefined (reading 'infrastructure')` because backend returns different data structure than frontend expects.

**Root Cause**: Backend returned `missing_critical_attributes` (flat array), but frontend expected `missing_attributes` (categorized object with keys: infrastructure, application, business, technical_debt).

## Solution Architecture
**Fix in backend, not frontend**. Backend should transform data to match TypeScript interface contracts.

### Why Backend Fix Is Correct
1. **Separation of Concerns**: Business logic (categorization rules) belongs in backend
2. **Single Source of Truth**: Category definitions maintained in one place
3. **API Contract Clarity**: Backend provides data in documented format
4. **Maintainability**: Changes only require backend updates, no frontend cascade

## Implementation Pattern

```python
# backend/app/api/v1/master_flows/assessment/helpers.py

def categorize_missing_attributes(missing_attrs: List[str]) -> Dict[str, List[str]]:
    """
    Categorize missing attributes into frontend TypeScript interface structure.

    Matches: AssetReadinessDetail interface
    Categories: infrastructure, application, business, technical_debt
    """
    category_map = {
        "infrastructure": {
            "asset_name", "technology_stack", "operating_system",
            "cpu_cores", "memory_gb", "storage_gb",
        },
        "application": {
            "business_criticality", "application_type", "architecture_pattern",
            "dependencies", "user_base", "data_sensitivity",
            "compliance_requirements", "sla_requirements",
        },
        "business": {
            "business_owner", "annual_operating_cost",
            "business_value", "strategic_importance",
        },
        "technical_debt": {
            "code_quality_score", "last_update_date",
            "support_status", "known_vulnerabilities",
        },
    }

    result = {
        "infrastructure": [],
        "application": [],
        "business": [],
        "technical_debt": [],
    }

    for attr in missing_attrs:
        categorized = False
        for category, attrs in category_map.items():
            if attr in attrs:
                result[category].append(attr)
                categorized = True
                break

        if not categorized:
            logger.warning(f"Missing attribute '{attr}' not in category map")

    return result

# Usage in endpoint
missing_attrs_flat = get_missing_critical_attributes(asset)
missing_attrs_categorized = categorize_missing_attributes(missing_attrs_flat)

blockers.append({
    "asset_id": str(asset.id),
    "missing_attributes": missing_attrs_categorized,  # ✅ Categorized object
})
```

## Frontend TypeScript Interface

```typescript
// src/types/assessment.ts
export interface AssetReadinessDetail {
  asset_id: string;
  asset_name: string;
  assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  missing_attributes: {  // ✅ Must match backend structure
    infrastructure: string[];
    application: string[];
    business: string[];
    technical_debt: string[];
  };
}
```

## Debugging Workflow
1. **Check browser console** for exact error message
2. **Identify component** that's crashing (e.g., `AssetBlockerAccordion.tsx:82`)
3. **Compare API response** (Network tab) vs TypeScript interface
4. **Fix in backend** if structure mismatch
5. **Validate with QA agent** using browser automation

## When to Use This Pattern
- Frontend crashes with "Cannot read properties of undefined"
- API returns data but frontend can't consume it
- TypeScript interfaces don't match backend response
- Nested object access fails (e.g., `data.foo.bar` → undefined)

## Related Files
- `backend/app/api/v1/master_flows/assessment/helpers.py:68-142`
- `backend/app/api/v1/master_flows/assessment/info_endpoints.py:225-246`
- `src/types/assessment.ts:98-111`
- Commit: `a076e71` (Frontend crash fix)

## Anti-Pattern to Avoid
❌ **Don't fix in frontend** by transforming backend data:
```typescript
// ❌ BAD - Frontend doing backend's job
const categorized = {
  infrastructure: data.missing_critical_attributes.filter(attr =>
    ['cpu_cores', 'ram_gb'].includes(attr)
  ),
  // ... more categories
};
```

✅ **Do fix in backend** - return correct structure from API
