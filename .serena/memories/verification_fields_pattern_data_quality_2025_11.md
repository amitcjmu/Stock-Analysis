# Verification Fields Pattern for Data Quality Confirmation

**Date**: November 6, 2025
**Context**: OS field should show pre-selected value but allow user editing

---

## Problem

Gap-based questionnaire generation skipped `operating_system` field when data existed → user couldn't confirm/correct discovered OS data → agents lacked context for intelligent option ordering.

**User Requirement**: "Show existing data as pre-selected dropdown, but allow user to change it"

## Distinction: Missing vs Verification Fields

### Missing Fields (True Gaps)
- No data exists in database
- Question required to collect data
- No default value

### Verification Fields (Data Quality Confirmation)
- Data exists (from discovery/CMDB/API)
- Question required to **confirm** data accuracy
- Pre-filled with existing value
- User can edit if incorrect

## Solution Pattern

Return both missing fields AND existing values for verification:

```python
# backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py

def _check_missing_critical_fields(asset) -> Tuple[List[str], dict]:
    """Check for missing critical fields using 22-attribute assessment system.

    Returns:
        Tuple of (missing_attributes, existing_values)
        - missing_attributes: List of attribute names with no value OR need verification
        - existing_values: Dict mapping attribute_name -> current value (for pre-fill)
    """
    # Fields that should ALWAYS be shown for user verification (even if present)
    VERIFICATION_FIELDS = [
        "operating_system_version",  # Critical for EOL context and intelligent options
    ]

    missing_attributes = []
    existing_values = {}

    for attr_name, attr_config in attribute_mapping.items():
        if not attr_config.get("required", False):
            continue

        has_value = False
        current_value = None

        # Check if asset has value for this attribute
        for field_path in attr_config.get("asset_fields", []):
            field_value = getattr(asset, field_path, None)
            if field_value and not (isinstance(field_value, (list, dict)) and len(field_value) == 0):
                has_value = True
                current_value = field_value
                break

        # True gaps: always include
        if not has_value:
            missing_attributes.append(attr_name)

        # Verification fields: include even if present (for user confirmation)
        elif attr_name in VERIFICATION_FIELDS:
            existing_values[attr_name] = current_value  # Store for pre-fill
            missing_attributes.append(attr_name)  # Treat as "missing" to generate question

    return missing_attributes, existing_values
```

## Usage in Gap Analysis

```python
# Old signature (only missing)
missing_fields = _check_missing_critical_fields(asset)

# New signature (missing + existing)
missing_fields, existing_values = _check_missing_critical_fields(asset)

# Store existing values in analysis
if existing_values:
    if "existing_field_values" not in asset_analysis:
        asset_analysis["existing_field_values"] = {}
    asset_analysis["existing_field_values"][asset_id] = existing_values
```

## Wiring to Question Generator

**TODO** (next session): Pass existing values to question builder

```python
# In question generation:
question = {
    "field_id": "operating_system",
    "question_text": "What is the Operating System?",
    "field_type": "select",
    "required": True,
    "options": [...],
    "default_value": existing_values.get("operating_system_version"),  # Pre-fill
    "metadata": {
        "pre_filled": True,
        "source": "discovery",
        "discovered_value": "AIX 7.2",
    }
}
```

## Frontend Handling

```typescript
// Dropdown shows pre-selected value
<select value={question.default_value || ""}>
  <option value="">-- Select --</option>
  <option value="aix_7.2" selected>IBM AIX 7.2</option>  // Pre-selected
  <option value="rhel_8">Red Hat Enterprise Linux 8</option>
  ...
</select>

// Badge indicates data source
{question.metadata?.pre_filled && (
  <Badge>Pre-filled from {question.metadata.source}</Badge>
)}
```

## When to Apply Verification Fields

**Use verification pattern when**:
- Data discovered automatically (CMDB, API, ML)
- High-value field critical for downstream logic (OS → EOL detection)
- User expertise required to confirm accuracy
- Data may be stale or incomplete

**Examples**:
- `operating_system` - Needed for EOL/security context
- `business_criticality` - ML prediction needs human confirmation
- `compliance_requirements` - Auto-detected from industry, user confirms
- `dependencies` - Graph analysis finds some, user verifies completeness

**Don't use verification pattern when**:
- Data is immutable (created_at, id)
- User has no domain knowledge to confirm (internal metrics)
- Field not critical for decision-making
- High confidence in discovery accuracy

## Pattern Rules

1. **Always include in missing_attributes**: Generates question in questionnaire
2. **Store in existing_values**: Provides pre-fill value
3. **Mark in metadata**: Frontend can show "verified" badge after confirmation
4. **Log as verification**: Distinguish from true gap collection in analytics

## Testing

```python
def test_verification_field_with_existing_data():
    """OS field should be in missing AND existing_values when data exists."""
    asset = Asset(operating_system="AIX", os_version="7.2")

    missing, existing = _check_missing_critical_fields(asset)

    assert "operating_system_version" in missing  # Generates question
    assert existing["operating_system_version"] == "AIX 7.2"  # Pre-fill value
```

## Benefits

1. **Data Quality**: User confirms auto-discovered data
2. **Context Threading**: Agents get verified OS for intelligent options
3. **User Trust**: Transparency about data sources
4. **Correction Path**: Easy to fix incorrect discovery
5. **Audit Trail**: Track which fields were verified vs newly entered

## Files

- `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py:234-310`
- `backend/app/services/manual_collection/adaptive_form_service/config/field_options.py:173-188` (OS options)

## Related Patterns

- Intelligent questionnaire context threading
- Gap-based question generation
- Data quality metrics
