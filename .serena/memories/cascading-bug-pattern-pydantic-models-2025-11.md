# Cascading Bug Pattern in Pydantic Model Instantiation

## Problem
When instantiating Pydantic models, incorrect parameter names cause cascading TypeErrors. Fixing one parameter reveals another, creating a chain of related bugs.

**Example Error Sequence**:
```
Bug #10: TypeError: IntelligentGap.__init__() got unexpected argument 'field_display_name'
  ↓ Fixed: field_display_name → field_name
Bug #12: TypeError: IntelligentGap.__init__() got unexpected argument 'section_name'
  ↓ Fixed: Removed section_name parameter
Bug #13: TypeError: IntelligentGap.__init__() got unexpected argument 'confidence'
  ↓ Fixed: confidence → confidence_score
Bug #14: TypeError: IntelligentGap.__init__() got unexpected argument 'data_sources_checked'
  ↓ Fixed: data_sources_checked → data_found
```

## Root Cause
- Developer used descriptive parameter names that didn't match Pydantic model definition
- Initial TypeError only shows FIRST invalid parameter
- Each fix reveals the NEXT invalid parameter in sequence
- Without comprehensive parameter validation, bugs discovered one-by-one in production

## Solution Pattern

### 1. Check Model Definition FIRST
Before writing instantiation code, read the Pydantic model:

```python
# ALWAYS check model definition
from app.services.collection.gap_analysis.models import IntelligentGap

# Read model file to see exact parameter names
class IntelligentGap(BaseModel):
    field_id: str           # ✅ Correct name
    field_name: str         # ✅ NOT field_display_name
    section: str            # ✅ NOT section_name
    is_true_gap: bool
    confidence_score: float # ✅ NOT confidence
    data_found: List[DataSource]  # ✅ NOT data_sources_checked
    priority: str
```

### 2. Use Model Inspector Tool
```python
# Inspect model fields programmatically
from pydantic import BaseModel

def get_model_params(model_class: type[BaseModel]) -> dict:
    """Extract exact parameter names from Pydantic model."""
    return {
        field_name: field_info.annotation
        for field_name, field_info in model_class.model_fields.items()
    }

# Usage
params = get_model_params(IntelligentGap)
print(params)  # Shows: {'field_id': str, 'field_name': str, ...}
```

### 3. Test All Parameters Together
Don't fix one-by-one in production. Test complete instantiation locally:

```python
# ❌ WRONG - Will discover bugs one-by-one
gaps.append(
    IntelligentGap(
        field_id=field_id,
        field_display_name=name,      # Bug #10 - will error first
        section_name=section_name,    # Bug #12 - hidden until #10 fixed
        confidence=confidence,         # Bug #13 - hidden until #12 fixed
        data_sources_checked=sources, # Bug #14 - hidden until #13 fixed
    )
)

# ✅ CORRECT - Verify all parameters match model
gaps.append(
    IntelligentGap(
        field_id=field_id,
        field_name=self._get_field_display_name(field_id),
        section=section_id,
        is_true_gap=True,
        confidence_score=confidence,
        data_found=data_sources_checked,
        priority=field_meta.get("importance", "medium"),
    )
)
```

## Prevention Checklist

Before committing Pydantic instantiation code:

- [ ] Read model definition file (`models.py`)
- [ ] Check exact parameter names (not just types)
- [ ] Test instantiation locally with real data
- [ ] Run mypy type checking (`mypy app/`)
- [ ] Enable Pydantic validation errors in tests
- [ ] Use IDE autocomplete for parameter names

## Real-World Fix Example

**File**: `backend/app/services/collection/gap_analysis/intelligent_gap_scanner/scanner.py:202-212`

**Before (4 bugs)**:
```python
gaps.append(
    IntelligentGap(
        field_id=field_id,
        field_display_name=self._get_field_display_name(field_id),  # ❌ Bug #10
        section=section_id,
        section_name=section_name,  # ❌ Bug #12
        is_true_gap=True,
        confidence=confidence,  # ❌ Bug #13
        data_sources_checked=data_sources_checked,  # ❌ Bug #14
        priority=field_meta.get("importance", "medium"),
    )
)
```

**After (all fixed)**:
```python
# ✅ FIX Bug #10: field_display_name → field_name
# ✅ FIX Bug #12: Removed section_name parameter
# ✅ FIX Bug #13: confidence → confidence_score
# ✅ FIX Bug #14: data_sources_checked → data_found
gaps.append(
    IntelligentGap(
        field_id=field_id,
        field_name=self._get_field_display_name(field_id),
        section=section_id,
        is_true_gap=True,
        confidence_score=confidence,
        data_found=data_sources_checked,
        priority=field_meta.get("importance", "medium"),
    )
)
```

## Mypy Integration

Enable strict Pydantic checking in `mypy.ini`:
```ini
[mypy]
plugins = pydantic.mypy

[pydantic-mypy]
init_forbid_extra = True
init_typed = True
warn_required_dynamic_aliases = True
```

This catches parameter name mismatches at type-check time, not runtime.

## Impact
- ✅ Prevents cascading bug discovery in production
- ✅ Catches all parameter errors in single mypy run
- ✅ IDE autocomplete prevents typos
- ✅ Self-documenting code (parameter names match model)

## When This Pattern Appears

**High Risk Scenarios**:
1. Creating instances of newly defined Pydantic models
2. Refactoring model field names
3. Multiple developers working on same model
4. Models with >5 parameters (easy to miss one)
5. Descriptive variable names != model field names

**Example**:
```python
# Variable name != model field name
section_name = "infrastructure"  # Descriptive
section = section_meta["id"]     # Actual model field

# Easy to confuse which one to use
IntelligentGap(section_name=section_name)  # ❌ WRONG
IntelligentGap(section=section)            # ✅ CORRECT
```

## Related Bugs
- Bug #10: `field_display_name` → `field_name`
- Bug #12: Removed `section_name` parameter
- Bug #13: `confidence` → `confidence_score`
- Bug #14: `data_sources_checked` → `data_found`

All fixed in PR #1109 (November 2025)
