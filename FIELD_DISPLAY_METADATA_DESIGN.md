# Field Display Metadata Enhancement

**Goal:** Make field mapping dropdowns user-friendly with display names and hints
**Branch:** `fix/demo-readiness-dnc-flows`

---

## Problem

**Current:** Dropdown shows raw DB column names
```
application_type              ← Ugly
cpu_utilization_percent_max   ← Hard to read
```

**Target:** Show pretty names with hints
```
Application Type              ← Clean
COTS / Custom / Custom-COTS / SaaS  ← Helpful hint
```

**Lost feature:** Before PR #847, we had helpful hints. After making it dynamic, we lost them.

---

## Solution: JSON Config File

Use `backend/config/field_display_metadata.json` because:

- No database table needed
- No migrations needed
- No SQL queries per request
- Load once at startup
- Edit file to update
- Git-tracked changes

---

## File Structure

### New File: `backend/config/field_display_metadata.json`

```json
{
  "application_type": {
    "displayName": "Application Type",
    "shortHint": "COTS / Custom / Custom-COTS / SaaS"
  },
  "lifecycle": {
    "displayName": "Lifecycle Stage",
    "shortHint": "Retire / Replace / Retain / Invest"
  },
  "hosting_model": {
    "displayName": "Hosting Model",
    "shortHint": "On-Prem / Cloud / Hybrid / Colo"
  },
  "server_role": {
    "displayName": "Server Role",
    "shortHint": "Web / DB / App / Citrix / File / Email"
  },
  "risk_level": {
    "displayName": "Risk Level",
    "shortHint": "Low / Medium / High / Critical"
  },
  "tshirt_size": {
    "displayName": "T-Shirt Size",
    "shortHint": "XS / S / M / L / XL / XXL"
  },
  "business_unit": {
    "displayName": "Business Unit",
    "shortHint": null
  },
  "vendor": {
    "displayName": "Vendor",
    "shortHint": "Software/hardware vendor name"
  },
  "database_type": {
    "displayName": "Database Type",
    "shortHint": "PostgreSQL / MySQL / Oracle / SQL Server / MongoDB"
  },
  "database_version": {
    "displayName": "Database Version",
    "shortHint": "Version number"
  },
  "database_size_gb": {
    "displayName": "Database Size (GB)",
    "shortHint": "In gigabytes"
  },
  "security_zone": {
    "displayName": "Security Zone",
    "shortHint": "DMZ / Internal / External / Restricted"
  },
  "pii_flag": {
    "displayName": "Contains PII",
    "shortHint": "true / false"
  },
  "application_data_classification": {
    "displayName": "Data Classification",
    "shortHint": "Public / Internal / Confidential / Restricted"
  },
  "cpu_utilization_percent_max": {
    "displayName": "CPU Utilization (Max %)",
    "shortHint": "0-100%"
  },
  "memory_utilization_percent_max": {
    "displayName": "Memory Utilization (Max %)",
    "shortHint": "0-100%"
  },
  "storage_free_gb": {
    "displayName": "Storage Free (GB)",
    "shortHint": "Available storage in GB"
  },
  "has_saas_replacement": {
    "displayName": "Has SaaS Replacement",
    "shortHint": "true / false"
  },
  "proposed_treatmentplan_rationale": {
    "displayName": "Treatment Plan Rationale",
    "shortHint": "Explanation for recommended approach"
  },
  "annual_cost_estimate": {
    "displayName": "Annual Cost Estimate",
    "shortHint": "Estimated yearly cost in USD"
  },
  "business_criticality": {
    "displayName": "Business Criticality",
    "shortHint": "1-5 scale (1=Low, 5=Critical)"
  },
  "six_r_strategy": {
    "displayName": "6R Strategy",
    "shortHint": "Rehost / Replatform / Refactor / Repurchase / Retire / Retain"
  },
  "migration_complexity": {
    "displayName": "Migration Complexity",
    "shortHint": "Low / Medium / High"
  },
  "environment": {
    "displayName": "Environment",
    "shortHint": "Production / Staging / Development / QA"
  },
  "operating_system": {
    "displayName": "Operating System",
    "shortHint": "Windows / Linux / Unix / AIX"
  },
  "cpu_cores": {
    "displayName": "CPU Cores",
    "shortHint": "Number of cores"
  },
  "memory_gb": {
    "displayName": "Memory (GB)",
    "shortHint": "RAM in gigabytes"
  },
  "storage_gb": {
    "displayName": "Storage (GB)",
    "shortHint": "Total storage in gigabytes"
  }
}
```

**Note:** Only include fields that need custom display names or hints. Fields not in JSON will use raw column name (current behavior).

---

## Implementation

### Backend Changes

**File: `backend/app/api/v1/endpoints/data_import/handlers/field_handler.py`**

1. **Load JSON at module level** (once at startup):
```python
import json
import os

# Load metadata file (once at startup)
METADATA_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../../../../config/field_display_metadata.json"
)

FIELD_DISPLAY_METADATA = {}
try:
    with open(METADATA_FILE_PATH, 'r') as f:
        FIELD_DISPLAY_METADATA = json.load(f)
    logger.info(f"Loaded display metadata for {len(FIELD_DISPLAY_METADATA)} fields")
except Exception as e:
    logger.warning(f"Could not load field display metadata: {e}. Using raw field names.")
```

2. **Enhance field info with metadata** (in `get_assets_table_fields()`):
```python
for col in columns:
    field_name = col.column_name

    # Lookup metadata by field name
    metadata = FIELD_DISPLAY_METADATA.get(field_name, {})

    field_info = {
        "name": field_name,
        "display_name": metadata.get("displayName"),  # None if not in JSON
        "short_hint": metadata.get("shortHint"),      # None if not in JSON
        "type": ...,
        "category": ...,
        "description": ...,
        # ... rest of existing fields
    }
```

### Frontend Changes

**File: `src/components/discovery/attribute-mapping/field-mappings/TargetFieldSelector.tsx`**

Update dropdown item rendering (around line 136):
```tsx
<button onClick={() => onSelect(field.name)}>
  <div className="flex-1">
    {/* Use display_name if available, fallback to raw name */}
    <div className="font-medium text-gray-900">
      {field.display_name || field.name}
    </div>

    {/* Show short hint if available */}
    {field.short_hint && (
      <div className="text-xs text-blue-600 mt-0.5">
        {field.short_hint}
      </div>
    )}
  </div>
  {/* ... badges */}
</button>
```

**Same change needed in:**
- `src/components/discovery/attribute-mapping/FieldMappingsTab/components/EnhancedFieldDropdown.tsx` (line 149-162)

---

## Data Flow

```
Startup:
  backend/config/field_display_metadata.json
    ↓ (loaded once)
  FIELD_DISPLAY_METADATA dictionary in memory

API Request:
  GET /api/v1/data-import/available-target-fields
    ↓
  Query information_schema for columns
    ↓
  For each column: lookup in FIELD_DISPLAY_METADATA
    ↓
  Merge: column info + metadata (if exists)
    ↓
  Return to frontend

Frontend:
  Render: field.display_name || field.name
  Show: field.short_hint (if exists)
```

---

## Fallback Behavior

**If JSON file missing/empty/unreadable:**
- ✅ Backend logs warning
- ✅ API still works (returns raw column names)
- ✅ Frontend shows raw names (current behavior)
- ✅ No errors, graceful degradation

**If field not in JSON:**
- ✅ `display_name` = `null` → Frontend shows raw `field.name`
- ✅ `short_hint` = `null` → No hint shown
- ✅ Same as current behavior

---

## Maintenance

### Adding New Fields
1. Edit `backend/config/field_display_metadata.json`
2. Add entry: `"new_field": { "displayName": "...", "shortHint": "..." }`
3. Restart backend (or hot-reload in dev)
4. Done!

### Updating Hints
1. Edit JSON file
2. Restart backend
3. Done!

No database migrations, no code changes needed.

---

## Files to Create/Modify

### New Files:
1. `backend/config/field_display_metadata.json` - Metadata for ~30 key CMDB fields

### Modified Files:
1. `backend/app/api/v1/endpoints/data_import/handlers/field_handler.py` - Load JSON, enhance fields
2. `src/components/discovery/attribute-mapping/field-mappings/TargetFieldSelector.tsx` - Show display_name + short_hint
3. `src/components/discovery/attribute-mapping/FieldMappingsTab/components/EnhancedFieldDropdown.tsx` - Show display_name + short_hint

---

## Example: Before/After

### Before (Current):
```
API Response:
{
  "name": "application_type",
  "type": "string",
  "description": "Application Type field",
  "category": "business"
}

Dropdown shows:
application_type
Application Type field
```

### After (With JSON):
```
API Response:
{
  "name": "application_type",
  "display_name": "Application Type",
  "short_hint": "COTS / Custom / Custom-COTS / SaaS",
  "type": "string",
  "description": "Application Type field",
  "category": "business"
}

Dropdown shows:
Application Type
COTS / Custom / Custom-COTS / SaaS
```

---

## Scope

### Initial Implementation (Phase 1):
Add metadata for **~30 most important CMDB fields**:
- application_type
- lifecycle
- hosting_model
- server_role
- risk_level
- tshirt_size
- database_type
- security_zone
- pii_flag
- application_data_classification
- cpu_utilization_percent_max
- memory_utilization_percent_max
- storage_free_gb
- has_saas_replacement
- business_criticality
- six_r_strategy
- migration_complexity
- environment
- And ~12 more common fields

### Future Enhancement (Phase 2):
Add metadata for remaining fields as needed (incremental approach).

---

## Benefits

| Benefit | Impact |
|---------|--------|
| **Better UX** | Users see friendly names, not DB columns |
| **Guided mapping** | Short hints help users understand valid values |
| **Simple** | Just a JSON file, no database complexity |
| **Fast** | In-memory lookup, no queries |
| **Maintainable** | Edit file, restart backend |
| **Git-tracked** | Changes visible in PRs |
| **Backward compatible** | Works with/without JSON file |
| **No breaking changes** | Adds fields, doesn't remove any |

---

## TypeScript Interface

```typescript
interface TargetField {
  name: string;              // DB column name
  display_name?: string;     // NEW: Pretty name
  short_hint?: string;       // NEW: Value hints
  type: string;
  required: boolean;
  description: string;
  category: string;
}
```

---

## Scope

Add display metadata for **ALL CMDB-related fields** (~90 fields total):
- 24 new CMDB fields from PR #833
- Related table fields (rto_minutes, rpo_minutes, etc.)
- Core asset fields (hostname, ip_address, cpu_cores, etc.)
- Business fields (business_owner, department, etc.)
- Migration planning fields (six_r_strategy, migration_wave, etc.)

---

## Success Criteria

✅ Users see "Application Type" instead of "application_type"
✅ Short hints appear in dropdowns for key CMDB fields
✅ Fallback works gracefully (no errors if JSON missing)
✅ No performance impact (loaded at startup)
✅ Easy to add new field metadata (just edit JSON)
✅ All existing functionality preserved
