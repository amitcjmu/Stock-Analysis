# Intelligent Field Type Fallback Pattern for Context-Aware Forms

**Date**: November 6, 2025
**Context**: Business logic complexity showing as textarea instead of dropdown

---

## Problem

Context-aware intelligent option function returned `None` when asset tech stack didn't match patterns → fell back to heuristic → heuristic saw "complexity" keyword → defaulted to `textarea` instead of `select`.

## Root Cause

Three-tier resolution chain broke at fallback:

```python
# Tier 1: Context-aware (intelligent reordering)
if asset_context:
    result = _check_context_aware_field(attr_name, asset_context)
    if result:
        return result  # ✅ Returns ("select", options) with smart ordering

# Tier 2: Static FIELD_OPTIONS
if attr_name in FIELD_OPTIONS:
    return infer_field_type_from_config(attr_name, FIELD_OPTIONS[attr_name])

# Tier 3: Heuristic fallback
return get_fallback_field_type_and_options(attr_name)  # ❌ Can return ("textarea", [])
```

Context-aware function returned `None` instead of falling through:
```python
def get_business_logic_complexity_options(asset_context: Dict):
    if "WEBSPHERE" in tech_stack:
        return "select", [very_complex_first_options]
    elif "NODEJS" in tech_stack:
        return "select", [simple_first_options]

    return None  # ❌ Falls back to heuristic → textarea
```

## Solution

**Never return None from context-aware functions** - always provide explicit fallback:

```python
# backend/app/services/ai_analysis/questionnaire_generator/tools/intelligent_options/business_options.py

def get_business_logic_complexity_options(asset_context: Dict) -> Optional[Tuple[str, List]]:
    """Suggest complexity levels based on technology stack patterns."""
    tech_stack = asset_context.get("technology_stack", "")

    # Try intelligent ordering based on tech stack
    if any(kw in tech_stack for kw in ["WEBSPHERE", "WEBLOGIC", "SAP"]):
        options = [
            {"value": "very_complex", "label": "Very Complex - Intricate business rules"},
            {"value": "complex", "label": "Complex - Advanced workflows"},
            {"value": "moderate", "label": "Moderate - Standard business rules"},
            {"value": "simple", "label": "Simple - Basic CRUD"},
        ]
        logger.info(f"Providing enterprise complexity options (very_complex first)")
        return "select", options

    elif any(kw in tech_stack for kw in ["NODEJS", "PYTHON", "GO"]):
        options = [
            {"value": "simple", "label": "Simple - Basic CRUD"},
            {"value": "moderate", "label": "Moderate - Standard business rules"},
            {"value": "complex", "label": "Complex - Advanced workflows"},
            {"value": "very_complex", "label": "Very Complex - Intricate business rules"},
        ]
        logger.info(f"Providing microservices complexity options (simple first)")
        return "select", options

    # CRITICAL: Never return None - provide balanced default with explicit type
    options = [
        {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
        {"value": "moderate", "label": "Moderate - Standard business rules, some workflows"},
        {"value": "complex", "label": "Complex - Advanced workflows, multi-step processes"},
        {"value": "very_complex", "label": "Very Complex - Intricate business rules, regulatory logic"}
    ]
    logger.info("Providing default balanced complexity options (no tech stack match)")
    return "select", options  # ✅ Explicit type prevents heuristic fallback
```

## Three-Tier Fallback Pattern

```python
def determine_field_type_and_options(attr_name: str, asset_context: Optional[Dict] = None):
    # Tier 1: Context-aware intelligent options (highest priority)
    if asset_context:
        result = _check_context_aware_field(attr_name, asset_context)
        if result:
            return result  # Smart reordering based on asset characteristics

    # Tier 2: Static FIELD_OPTIONS from config (medium priority)
    if attr_name in FIELD_OPTIONS:
        return infer_field_type_from_config(attr_name, FIELD_OPTIONS[attr_name])

    # Tier 3: Heuristic fallback (lowest priority, last resort)
    return get_fallback_field_type_and_options(attr_name)
```

**Key Principle**: Each tier should return explicit values, never None. None signals "try next tier", but final tier must provide deterministic result.

## When to Apply

- Context-aware UI generation where field types must be deterministic
- Multi-tier resolution chains (intelligent → static → heuristic)
- Dynamic form generation from metadata
- Any system where `None` means "delegate" not "unknown"

## Pattern Rules

1. **Context-aware functions**: Return `Tuple[str, List]` or `None`
   - `None` = "no intelligent opinion, try next tier"
   - Never return `None` as final fallback

2. **Static config**: Always returns deterministic result
   - Predefined field type + options

3. **Heuristic fallback**: Last resort, always returns something
   - Uses keyword patterns to guess type
   - Should rarely be reached if Tier 1/2 are comprehensive

## Testing

```python
def test_business_logic_complexity_no_tech_stack():
    """Verify fallback returns select, not None/textarea."""
    context = {"technology_stack": []}  # No matching patterns
    field_type, options = get_business_logic_complexity_options(context)

    assert field_type == "select"  # Not "textarea"
    assert len(options) == 4
    assert options[0]["value"] == "simple"  # Balanced ordering
```

## Files

- `backend/app/services/ai_analysis/questionnaire_generator/tools/intelligent_options/business_options.py:102-121`
- `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py:73-115`
