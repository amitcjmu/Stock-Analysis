# Field Display Metadata Implementation

## Overview

This document describes the implemented solution for enhancing field display metadata in the attribute mapping UI using SQLAlchemy's `Column.info` pattern.

**Status:** ✅ Implemented (PR #903)
**Approach:** Option 1 from GitHub Discussion #898 - SQLAlchemy Column.info

---

## Problem Statement

The attribute mapping UI displayed raw database column names (e.g., `application_type`, `cpu_count`) without context, making it difficult for users to:
- Understand what each field represents
- Choose the correct target field for mapping
- Distinguish between similar fields

---

## Solution: SQLAlchemy Column.info Metadata

We use SQLAlchemy's built-in `Column.info` dictionary to store metadata directly within model definitions.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Asset Model Layer                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SQLAlchemy Column Definition                               │ │
│  │                                                              │ │
│  │ application_type = Column(                                 │ │
│  │     String(20),                                            │ │
│  │     info={                                                 │ │
│  │         "display_name": "Application Type",               │ │
│  │         "short_hint": "COTS / Custom / Custom-COTS / SaaS",│ │
│  │         "category": "business"                             │ │
│  │     }                                                       │ │
│  │ )                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API Layer                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ field_handler.py                                           │ │
│  │                                                              │ │
│  │ # Extract metadata from Column.info                       │ │
│  │ sa_column = getattr(Asset, field_name, None)             │ │
│  │ if sa_column and hasattr(sa_column, "info"):             │ │
│  │     display_name = sa_column.info.get("display_name")    │ │
│  │     short_hint = sa_column.info.get("short_hint")        │ │
│  │     category = sa_column.info.get("category")            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend UI Layer                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ TargetFieldSelector.tsx / EnhancedFieldDropdown.tsx       │ │
│  │                                                              │ │
│  │ <div className="font-medium">                             │ │
│  │   {field.display_name || field.name}                      │ │
│  │ </div>                                                      │ │
│  │ {field.short_hint && (                                    │ │
│  │   <div className="text-xs text-gray-500">                 │ │
│  │     {field.short_hint}                                    │ │
│  │   </div>                                                   │ │
│  │ )}                                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Backend: Model Layer

#### Metadata Structure
Each field's `info` dictionary contains:
- `display_name` (string): User-friendly field name
- `short_hint` (string): Brief description/example
- `category` (string): One of 6 standardized categories

#### Standardized Categories
1. **identification** - Names, IDs, unique identifiers
2. **technical** - Technical specs (CPU, memory, OS, IP)
3. **performance** - Utilization metrics, capacity
4. **business** - Ownership, criticality, cost center
5. **migration** - Assessment data, wave, readiness
6. **other** - Everything else

#### Example Implementation

**File:** `backend/app/models/asset/cmdb_fields.py`

```python
from sqlalchemy import Column, String, Integer

class CMDBFieldsMixin:
    application_type = Column(
        String(20),
        nullable=True,
        comment="Application type: cots, custom, custom_cots, other",
        info={
            "display_name": "Application Type",
            "short_hint": "COTS / Custom / Custom-COTS / SaaS",
            "category": "business",
        },
    )

    cpu_count = Column(
        Integer,
        nullable=True,
        comment="Number of CPU cores/vCPUs allocated",
        info={
            "display_name": "CPU Count",
            "short_hint": "Number of cores/vCPUs",
            "category": "technical",
        },
    )
```

#### Modularization
To maintain 400-line file limit, Asset model fields are organized into mixins:
- `location_fields.py` - Location and environment fields
- `performance_fields.py` - Performance and utilization fields
- `business_fields.py` - Business and organizational fields
- `migration_fields.py` - Migration assessment fields
- `discovery_fields.py` - Discovery metadata fields
- `cmdb_fields.py` - CMDB-specific fields

### 2. Backend: API Layer

#### Field Handler
**File:** `backend/app/api/v1/endpoints/data_import/handlers/field_handler.py`

Extracts metadata from `Column.info`:

```python
def get_available_target_fields():
    fields = []
    for field_name in get_asset_columns():
        # Extract metadata from Column.info
        display_name = None
        short_hint = None
        category = "other"

        try:
            sa_column = getattr(Asset, field_name, None)
            if sa_column and hasattr(sa_column, "info"):
                column_info = sa_column.info
                display_name = column_info.get("display_name")
                short_hint = column_info.get("short_hint")
                category = column_info.get("category", category)
        except Exception as e:
            logger.debug(f"Could not extract metadata for {field_name}: {e}")

        fields.append({
            "name": field_name,
            "display_name": display_name,
            "short_hint": short_hint,
            "category": category,
            "description": generate_field_description(field_name),
            "required": is_required_field(field_name),
        })

    return fields
```

#### Helper Utilities
**File:** `backend/app/api/v1/endpoints/data_import/handlers/field_metadata.py`

Contains reusable helper functions:
- `categorize_field(field_name)` - Fallback categorization logic
- `is_required_field(field_name)` - Check if field is required
- `generate_field_description(field_name)` - Generate technical description

### 3. Frontend: UI Layer

#### TypeScript Interfaces
**Files:**
- `src/components/discovery/attribute-mapping/field-mappings/types.ts`
- `src/contexts/FieldOptionsContext/types.ts`

```typescript
interface TargetField {
  name: string;
  display_name?: string;     // NEW
  short_hint?: string;        // NEW
  category: string;
  description?: string;
  required: boolean;
}
```

#### UI Components

**File:** `src/components/discovery/attribute-mapping/field-mappings/TargetFieldSelector.tsx`

```tsx
// Display friendly name and hint
<div className="font-medium text-gray-900">
  {field.display_name || field.name}
</div>
{field.short_hint && (
  <div className="text-xs text-gray-500 mt-1">
    {field.short_hint}
  </div>
)}

// Capitalize category names
<span className={`text-xs px-1 py-0.5 rounded ${getCategoryColor(field.category)}`}>
  {field.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
</span>
```

**Category Sorting:**
- All categories appear alphabetically
- "Other" always appears last
- Implementation: Filter out 'other', sort remaining, append 'other' at end

---

## Benefits of This Approach

### ✅ Advantages

1. **Type-Safe:** Metadata is validated at model definition time
2. **Co-Located:** Metadata lives with the schema it describes
3. **No External Config:** No JSON files to maintain or sync
4. **IDE Support:** Autocomplete and type hints work naturally
5. **Easy to Extend:** Just add more keys to `info` dict
6. **Version Controlled:** Changes tracked with model changes
7. **No Performance Impact:** Metadata extracted once per request

### ⚠️ Trade-offs

1. **Not Tenant-Specific:** All tenants see same metadata (acceptable for our use case)
2. **Requires Model Changes:** Can't update metadata without code deploy (acceptable - metadata is stable)

---

## Coverage

### Fields with Metadata (56 total)

#### Core Identification (7)
- `name`, `fqdn`, `ip_address`, `asset_id`, `serial_number`, `mac_address`, `hostname`

#### Technical Specs (15)
- `os_name`, `os_version`, `cpu_count`, `cpu_speed_ghz`, `memory_gb`, `disk_capacity_gb`, etc.

#### Performance (6)
- `cpu_utilization_percent_avg`, `memory_utilization_percent_avg`, `disk_utilization_percent_avg`, etc.

#### Business Context (12)
- `application_type`, `criticality`, `business_owner`, `technical_owner`, `cost_center`, etc.

#### Migration Assessment (8)
- `migration_wave`, `migration_group`, `migration_complexity`, `migration_readiness`, etc.

#### Discovery & Tracking (8)
- `discovery_method`, `discovery_source`, `last_discovered_at`, `confidence_score`, etc.

---

## Example User Experience

### Before
```
Dropdown shows:
┌─────────────────────────┐
│ application_type        │
│ cpu_count              │
│ memory_gb              │
└─────────────────────────┘
```

### After
```
Dropdown shows:
┌─────────────────────────────────────────┐
│ Application Type                        │
│ COTS / Custom / Custom-COTS / SaaS      │
│ [Business]                              │
├─────────────────────────────────────────┤
│ CPU Count                               │
│ Number of cores/vCPUs                   │
│ [Technical]                             │
├─────────────────────────────────────────┤
│ Memory (GB)                             │
│ RAM in gigabytes                        │
│ [Technical]                             │
└─────────────────────────────────────────┘
```

---

## Testing

### Manual Testing Completed
- ✅ All 6 categories display correctly
- ✅ Display names and hints appear in dropdowns
- ✅ "Other" category sorts last
- ✅ Category names are capitalized
- ✅ Search works with display names and hints
- ✅ Fallback to raw column name if metadata missing

### Automated Testing
- Unit tests for `categorize_field()` helper
- Integration tests for field metadata extraction
- Frontend component tests for display logic

---

## Future Enhancements

### Potential Additions
1. **Field Examples:** Add `example` key with sample values
2. **Validation Rules:** Add `validation` key with regex/rules
3. **Data Type Hints:** Add `data_type` key for better UI widgets
4. **Related Fields:** Add `related_to` key for field dependencies
5. **i18n Support:** Add multi-language support to metadata

### Evolution Path
If tenant-specific metadata becomes needed:
1. Create `FieldMetadata` model table
2. Link to `client_account_id` or `engagement_id`
3. Use as override layer on top of Column.info defaults

---

## Related Documentation

- **GitHub Discussion #898** - Original design discussion and options
- **PR #903** - Implementation pull request
- **docs/code-reviews/review-comments-repository.md** - Code review patterns

---

## Maintenance

### Adding Metadata to New Fields

1. Add `info` dict to Column definition:
```python
new_field = Column(
    String(100),
    info={
        "display_name": "Friendly Name",
        "short_hint": "Brief description",
        "category": "business"  # Choose from 6 categories
    }
)
```

2. No API changes needed - metadata automatically extracted

3. Frontend automatically displays new metadata

### Updating Existing Metadata

1. Edit the `info` dict in the model file
2. Deploy to backend
3. Frontend picks up changes on next API call

---

## Implementation Timeline

- **Design Phase:** Discussion #898 reviewed 3 options
- **Decision:** Option 1 (SQLAlchemy Column.info) selected
- **Implementation:** PR #903
- **Review:** Qodo-pro automated review + manual review
- **Status:** ✅ Ready for merge

---

**Last Updated:** 2025-11-03
**Document Owner:** Engineering Team
**Related PRs:** #903
