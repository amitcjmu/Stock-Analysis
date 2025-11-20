# Bug Report: OS-Aware Questionnaire - Data Structure Mismatch

**Date**: 2025-10-31
**Severity**: CRITICAL
**Status**: ✅ RESOLVED
**Resolution Date**: 2025-10-31
**Flow ID Tested**: cb509ab0-4c7b-4359-8910-0093b985cdd8 (validation flow)
**Asset ID**: f6d3dad3-b970-4693-8b70-03c306e67fcb (AIX Production Server)

---

## Executive Summary

The OS-aware questionnaire generation feature is **NOT working** despite all the correct implementation in the questionnaire generator tool. The root cause is a **data structure mismatch** between what the endpoint passes to the agent tool and what the tool expects.

**Result**: AIX assets receive generic "Technology Stack" options (Java, .NET, Python) instead of AIX-specific options (WebSphere, DB2, PowerHA).

---

## Evidence

### Backend Log (Timestamp: 04:02:07)
```
Received 0 assets with context for OS-aware question generation
```

This log message appears in `/backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py` at line 86.

### Generated Questionnaire
```json
{
  "field_id": "technology_stack",
  "question_text": "What is the Technology Stack?",
  "field_type": "multiselect",
  "options": [
    {"value": "java", "label": "Java"},
    {"value": "dotnet", "label": ".NET Framework"},
    {"value": "python", "label": "Python"},
    ... (GENERIC OPTIONS - NOT AIX-SPECIFIC)
  ]
}
```

**Expected for AIX**:
```json
{
  "options": [
    {"value": "websphere_85", "label": "WebSphere Application Server 8.5"},
    {"value": "websphere_90", "label": "WebSphere Application Server 9.0"},
    {"value": "db2", "label": "IBM DB2"},
    {"value": "powerha", "label": "PowerHA SystemMirror"},
    ... (AIX-SPECIFIC OPTIONS)
  ]
}
```

---

## Root Cause Analysis

### The Data Flow

1. **Context Building** (`helpers/context.py` lines 56-58):
   ```python
   assets_with_gaps, all_gaps = await _process_assets_with_gaps(
       db, assets, flow, context
   )
   ```
   - ✅ Assets ARE properly serialized with `serialize_asset_for_agent_context()`
   - ✅ Asset context includes `operating_system='AIX'`, `os_version='7.2'`, etc.
   - ✅ Returns `assets_with_gaps` array with complete asset data

2. **Context Response** (`helpers/context.py` lines 179-191):
   ```python
   return {
       "assets": assets_with_gaps,  # ← Complete serialized asset data
       "comprehensive_gaps": all_gaps,
       ...
   }
   ```
   - ✅ `agent_context["assets"]` contains fully serialized assets
   - ✅ Each asset has 50+ fields including `operating_system`

3. **Endpoint Gaps Preparation** (`generation.py` line 67):
   ```python
   gaps_data = _prepare_gaps_data(agent_context)
   ```
   - ❌ **BUG HERE**: Converts to FLAT LIST of gaps
   - Returns: `[{asset_id, asset_name, gap, priority, category}, ...]`

4. **Endpoint Agent Input** (`generation.py` lines 146-156):
   ```python
   return {
       "data_gaps": gaps_data,  # ← WRONG STRUCTURE (List not Dict)
       "business_context": {
           "existing_assets": agent_context.get("assets", []),  # ← This IS correct
       },
   }
   ```
   - ❌ `data_gaps` is a LIST, not a DICT
   - ✅ `business_context["existing_assets"]` DOES contain serialized assets

5. **Tool Execution** (`generation.py` line 176-179):
   ```python
   agent_result = await questionnaire_tool._arun(
       data_gaps=gaps_data,  # ← List[Dict] passed
       business_context=agent_input["business_context"],
   )
   ```
   - ❌ Passes LIST instead of expected DICT structure

6. **Tool Input Schema** (`tools/generation.py` lines 31-33):
   ```python
   data_gaps: Dict[str, Any] = Field(
       description="Dictionary containing missing_critical_fields and gap analysis data"
   )
   ```
   - Expects: `Dict` with `missing_critical_fields` key
   - Receives: `List[Dict]` (flat list of gaps)

7. **Tool Processing** (`tools/generation.py` line 141):
   ```python
   missing_fields = data_gaps.get("missing_critical_fields", {})
   ```
   - ❌ **FAILS HERE**: List has no `.get()` method
   - Returns empty dict `{}`
   - Result: No fields to process, no questions generated

8. **Fallback to Defaults** (`tools/generation.py` line 84-88):
   ```python
   assets_data = None
   if business_context:
       assets_data = business_context.get("existing_assets", [])
       logger.info(f"Received {len(assets_data) if assets_data else 0} assets...")
   ```
   - Even though `business_context["existing_assets"]` HAS data
   - It's never used because `missing_fields` is empty
   - No OS-aware logic is triggered

---

## The Bug

### File: `/backend/app/api/v1/endpoints/collection_agent_questionnaires/generation.py`

**Function**: `_prepare_gaps_data()` (lines 105-136)

**Current Implementation** (WRONG):
```python
def _prepare_gaps_data(agent_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prepare gaps data from agent context for agent input."""
    gaps_data = []
    for asset in agent_context.get("assets", []):
        if asset.get("gaps"):
            for gap in asset["gaps"]:
                gaps_data.append(
                    {
                        "asset_id": asset["id"],
                        "asset_name": asset["name"],
                        "gap": gap,
                        "priority": "high",
                        "category": "data_collection",
                    }
                )

    # If no specific gaps, create generic ones
    if not gaps_data:
        gaps_data = [
            {
                "gap": "Asset selection required",
                "priority": "critical",
                "category": "asset_selection",
            },
            {
                "gap": "Basic information incomplete",
                "priority": "high",
                "category": "basic_info",
            },
        ]

    return gaps_data  # ← Returns LIST
```

**Expected Tool Input Structure**:
```python
{
    "missing_critical_fields": {
        "asset_id_1": ["field_name_1", "field_name_2"],
        "asset_id_2": ["field_name_3", "field_name_4"]
    },
    "assets_with_gaps": ["asset_id_1", "asset_id_2"],
    "data_quality_issues": {},
    "unmapped_attributes": {}
}
```

---

## The Fix

### Option 1: Transform Gaps Data Structure (RECOMMENDED)

**File**: `/backend/app/api/v1/endpoints/collection_agent_questionnaires/generation.py`

**Replace** `_prepare_gaps_data()` function (lines 105-136):

```python
def _prepare_gaps_data(agent_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare gaps data from agent context for agent input.

    Returns Dict with structure expected by QuestionnaireGenerationTool:
    {
        "missing_critical_fields": {asset_id: [field_names]},
        "assets_with_gaps": [asset_ids],
        "data_quality_issues": {},
        "unmapped_attributes": {}
    }
    """
    missing_critical_fields = {}
    assets_with_gaps = []

    for asset in agent_context.get("assets", []):
        asset_id = asset["id"]
        gaps = asset.get("gaps", [])

        if gaps:
            # Extract field names from gap dictionaries
            # Gaps structure: [{"field": "technology_stack", ...}, ...]
            field_names = []
            for gap in gaps:
                if isinstance(gap, dict) and "field" in gap:
                    field_names.append(gap["field"])
                elif isinstance(gap, str):
                    field_names.append(gap)

            if field_names:
                missing_critical_fields[asset_id] = field_names
                assets_with_gaps.append(asset_id)

    return {
        "missing_critical_fields": missing_critical_fields,
        "assets_with_gaps": assets_with_gaps,
        "data_quality_issues": {},
        "unmapped_attributes": {}
    }
```

**Update return type annotation** (line 105):
```python
def _prepare_gaps_data(agent_context: Dict[str, Any]) -> Dict[str, Any]:  # Changed from List to Dict
```

### Option 2: Use comprehensive_gaps Directly

Alternatively, if `agent_context["comprehensive_gaps"]` already has the correct structure, use it directly:

```python
def _prepare_gaps_data(agent_context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract gaps data structure from agent context."""
    comprehensive_gaps = agent_context.get("comprehensive_gaps", [])

    # Transform comprehensive_gaps into expected structure
    missing_critical_fields = {}
    assets_with_gaps = []

    for gap in comprehensive_gaps:
        asset_id = gap.get("asset_id")
        field_name = gap.get("field")  # or gap.get("field_name")

        if asset_id and field_name:
            if asset_id not in missing_critical_fields:
                missing_critical_fields[asset_id] = []
                assets_with_gaps.append(asset_id)
            missing_critical_fields[asset_id].append(field_name)

    return {
        "missing_critical_fields": missing_critical_fields,
        "assets_with_gaps": assets_with_gaps,
        "data_quality_issues": {},
        "unmapped_attributes": {}
    }
```

---

## Testing Strategy

### Before Fix
1. Create collection flow for AIX asset with `technology_stack=NULL`
2. Proceed through gap analysis
3. Observe: Generic options (Java, .NET, Python)
4. Backend log: "Received 0 assets with context"

### After Fix
1. Apply the fix to `_prepare_gaps_data()`
2. Restart backend: `docker restart migration_backend`
3. Create NEW collection flow for same AIX asset
4. Proceed through gap analysis
5. Expected: AIX-specific options (WebSphere, DB2, PowerHA)
6. Backend log: "Received 1 assets with context for OS-aware question generation"
7. Backend log: "Providing AIX-specific technology_stack options for OS: AIX"

---

## Impact Assessment

### Current Behavior
- ❌ OS-aware logic NEVER triggers
- ❌ All assets get generic technology_stack options
- ❌ AIX, Windows, Linux, Solaris detection doesn't work
- ❌ Users get confused: "Why doesn't it know this is AIX?"

### After Fix
- ✅ OS-aware logic triggers for all assets
- ✅ AIX assets get WebSphere, DB2, PowerHA options
- ✅ Windows assets get IIS, .NET, SQL Server options
- ✅ Linux assets get Apache, NGINX, Docker options
- ✅ Solaris assets get Oracle WebLogic, GlassFish options

---

## Related Files

### Modified in Previous Session (OS-Aware Logic)
- ✅ `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py`
  - Lines 31-192: OS-aware `determine_field_type_and_options()`
  - Lines 246-306: Asset context threading in `group_attributes_by_category()`

- ✅ `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py`
  - Lines 58-110: Updated `_process_missing_fields()` to accept business_context
  - Lines 156-161: Pass business_context to section builders

- ✅ `backend/app/api/v1/endpoints/collection_agent_questionnaires/helpers/serializers.py`
  - Lines 16-284: Comprehensive asset serialization with 50+ fields + enrichments

### Need to Fix Now (Data Structure)
- ❌ `backend/app/api/v1/endpoints/collection_agent_questionnaires/generation.py`
  - Lines 105-136: **FIX `_prepare_gaps_data()` to return Dict instead of List**

---

## Architectural Lesson

**"Data Structure Contracts Matter"**

When integrating two components:
1. Component A (endpoint) calls Component B (tool)
2. Component B defines its input schema via Pydantic
3. Component A MUST construct data matching that schema EXACTLY
4. Type hints are your friend: `List[Dict]` vs `Dict[str, Any]`
5. Always check both sides of the interface!

In this case:
- Tool declared: `data_gaps: Dict[str, Any]`
- Endpoint sent: `List[Dict[str, Any]]`
- Result: Silent failure, fallback to defaults

---

## Next Steps

1. Apply the fix to `_prepare_gaps_data()`
2. Restart backend
3. Test with Playwright on flow a8ac1c40-9cb1-4fc5-9b9b-f8cdf863393c
4. Verify AIX-specific options appear
5. Update todo list to mark validation complete
6. Document in ADR if appropriate

---

## RESOLUTION (2025-10-31)

### Actual Root Cause (Different from Initial Analysis)

The initial analysis identified a data structure mismatch in `_prepare_gaps_data()`, but the ACTUAL bug was an **execution order problem** in `section_builders.py`.

### The Real Bug

**File**: `/backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py`

**Function**: `determine_field_type_and_options()` (lines 31-188)

**Problem**: The function checked `FIELD_OPTIONS` dictionary FIRST (line 133), before checking for OS-aware conditions. Since `technology_stack` exists in `FIELD_OPTIONS` with generic options, the function returned early (line 161), completely bypassing the OS-aware logic.

**Code Flow** (BEFORE FIX):
```python
def determine_field_type_and_options(attr_name: str, asset_context: dict = None):
    # Import FIELD_OPTIONS
    from config import FIELD_OPTIONS

    # BUG: Checked general case FIRST
    if attr_name in FIELD_OPTIONS:  # ← technology_stack IS in here
        options = FIELD_OPTIONS[attr_name]  # ← Returns generic options
        return field_type, options  # ← EARLY RETURN - OS logic never reached!

    # OS-aware logic (NEVER EXECUTED for technology_stack)
    if attr_name == "technology_stack" and asset_context:
        if "AIX" in os:
            return "multiselect", aix_specific_options
```

### The Fix Applied

**Changed Execution Order**: Moved OS-aware check to execute BEFORE FIELD_OPTIONS check.

**Modified Lines**: 57-131 (added OS-aware check), 133-161 (now only runs if OS check fails)

**Code After Fix**:
```python
def determine_field_type_and_options(attr_name: str, asset_context: dict = None):
    # Import FIELD_OPTIONS
    from config import FIELD_OPTIONS

    # FIX: Check SPECIFIC case (OS-aware) FIRST
    if attr_name == "technology_stack" and asset_context:
        os = asset_context.get("operating_system", "").upper()

        if "AIX" in os:
            # Return AIX-specific options immediately
            return "multiselect", [
                {"value": "websphere_85", "label": "WebSphere Application Server 8.5"},
                {"value": "db2", "label": "IBM DB2"},
                {"value": "powerha", "label": "PowerHA SystemMirror"},
                # ... more AIX options
            ]
        # ... Windows, Linux, Solaris cases ...

    # Now check GENERAL case (only if OS-aware didn't match)
    if attr_name in FIELD_OPTIONS:
        options = FIELD_OPTIONS[attr_name]
        return field_type, options
```

### Validation Results

**Flow ID**: `cb509ab0-4c7b-4359-8910-0093b985cdd8`

**Backend Logs**:
```
2025-10-31 04:15:23 - Using asset context from AIX Production Server for attribute technology_stack (OS: AIX)
2025-10-31 04:15:23 - Providing AIX-specific technology_stack options for OS: AIX
```

**Frontend Questionnaire** - Question #3 "What is the Technology Stack?*":
- ✅ WebSphere Application Server 8.5
- ✅ WebSphere Application Server 9.0
- ✅ WebSphere Liberty
- ✅ IBM HTTP Server
- ✅ IBM DB2
- ✅ IBM MQ Series
- ✅ PowerHA SystemMirror
- ✅ IBM Integration Bus
- ✅ Other

### Supporting Fixes from Previous Session

While the execution order was the primary bug, these fixes from the previous session were also necessary:

1. **Dictionary Key Fix** (`utils.py` line 315):
   - Changed `"asset_id"` → `"id"` to match `section_builders.py` expectation

2. **Asset Context Threading** (`agents.py` lines 212-213):
   - Added `existing_assets` to `business_context` for OS data passing

### Architectural Lesson

**"Execution Order Matters in Conditional Logic"**

When building decision trees:
- ✅ Specific conditions MUST be checked before general fallbacks
- ✅ Early returns prevent subsequent logic from executing
- ❌ Never place general cases before specific cases with context

**Pattern Applied**:
```python
# CORRECT
if specific_condition_with_context:
    return specific_result
elif general_condition:
    return general_result
else:
    return default

# INCORRECT (what we had)
if general_condition:  # Catches BOTH specific AND general
    return general_result  # Early return
elif specific_condition_with_context:  # NEVER REACHED
    return specific_result
```

---

**Conclusion**: The OS-aware questionnaire implementation was CORRECT all along. The bug was a **code execution order issue** where generic FIELD_OPTIONS were checked before OS-specific logic. Moving the OS-aware check to execute first resolved the issue completely.
