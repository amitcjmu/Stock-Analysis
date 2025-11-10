# Issue #980 - QA Validation Report
## Questionnaire Generation Improvements - Post-Bug Fix Assessment

**Date**: November 9, 2025
**QA Tester**: Claude Code (qa-playwright-tester agent)
**Test Environment**: Docker localhost:8081
**Collection Flow**: d6847bde-19ad-4377-8dc2-ad2abe5e8217 (Analytics Dashboard asset)
**Database Questionnaire ID**: 5bb419d9-d6d9-415b-9947-95016a4086aa
**Questionnaire Generated**: November 10, 2025 01:22:15 UTC

---

## Executive Summary

**Overall Result**: ❌ **2 OUT OF 3 ISSUES REMAIN UNRESOLVED**

### Issues Status:
1. ✅ **FIXED**: Duplicate questions (no duplicates found)
2. ❌ **NOT FIXED**: Generic "status" questions still appearing
3. ⚠️ **NOT TESTED**: Form submission loop (validation blocked by issue #2)

### Critical Finding:
The MCQ templates added to `attribute_question_builders.py` ARE correctly defined, but the **routing logic in `section_builders.py` is NOT executing the intended code path**. Instead of calling `generate_missing_field_question()` for fields like `application_type`, `canonical_name`, and `description`, the system is falling through to the generic `else` clause and calling `generate_generic_question()`.

---

## Test Scenario Details

### Test Setup:
- **Asset**: Analytics Dashboard (059a1f71-69ef-41cc-8899-3c89cd560497)
- **Total Questions**: 11 (matching 11 detected gaps)
- **Total Sections**: 6 sections
- **Question Distribution**:
  - Business Information: 1 question
  - Application Details: 2 questions
  - Technical Details: 2 questions
  - Missing Field: 1 question
  - General: 4 questions ⚠️ **(PROBLEMATIC SECTION)**
  - Dependencies: 1 question

---

## Detailed Validation Results

### 1. ✅ NO DUPLICATE QUESTIONS

**Test**: Count all questions and verify no duplicate question text

**Result**: **PASS** - All 11 questions are unique

**Evidence**:
- Question count from database: 11 questions
- Question count from frontend: 11 questions displayed
- Console logs confirm: "Generated 6 sections with 11 total questions"
- **No duplicate question text found**

**Comparison to Previous Issue**:
- **Before**: Questions 4 & 5 both asked "What is the technical modernization readiness..."
- **After**: No duplicate questions detected

---

### 2. ❌ GENERIC "STATUS" QUESTIONS STILL PRESENT

**Test**: Verify all questions use proper MCQ format, not generic status questions

**Result**: **FAIL** - 4 out of 11 questions still use generic "status" format

#### Problematic Questions Identified:

##### Question 7: Application Type
- **Question Text**: "What is the **status of application type** for Analytics Dashboard?"
- **Field ID**: `application_type`
- **Field Type**: `select`
- **Options**: 5 generic status options
  - Available - Information exists and is accessible
  - Partially Available - Some information exists but incomplete
  - Not Available - Information needs to be gathered
  - Not Applicable - This attribute doesn't apply to this asset
  - Unknown - Assessment not yet completed
- **Expected**: MCQ with 9 application type options (Web Application, API Service, Batch Job, etc.)
- **Actual**: Generic status question ❌

##### Question 8: Canonical Name
- **Question Text**: "What is the **status of canonical name** for Analytics Dashboard?"
- **Field ID**: `canonical_name`
- **Field Type**: `select` (should be `text`)
- **Options**: 5 generic status options (same as above)
- **Expected**: Text input asking "What is the canonical (official) name for Analytics Dashboard?"
- **Actual**: Generic status question ❌

##### Question 9: Compliance Flags
- **Question Text**: "What is the **status of compliance flags.data classification** for Analytics Dashboard?"
- **Field ID**: `compliance_flags.data_classification`
- **Field Type**: `select` (should be `multiselect`)
- **Options**: 5 generic status options (same as above)
- **Expected**: Multiselect with 7 compliance options (PCI DSS, HIPAA, GDPR, SOX, ISO 27001, FedRAMP, None)
- **Actual**: Generic status question ❌

##### Question 10: Description
- **Question Text**: "What is the **status of description** for Analytics Dashboard?"
- **Field ID**: `description`
- **Field Type**: `select` (should be `textarea`)
- **Options**: 5 generic status options (same as above)
- **Expected**: Textarea asking "What is the business purpose and functionality of Analytics Dashboard?"
- **Actual**: Generic status question ❌

#### Questions That Work Correctly:

##### ✅ Question 2: Architecture Pattern
- **Question Text**: "What is the Architecture Pattern?"
- **Field Type**: `radio`
- **Options**: 7 architecture options (Monolithic, Microservices, SOA, Layered, Event-Driven, Serverless, Hybrid)
- **Status**: **CORRECT** - Uses proper MCQ format

##### ✅ Question 3: Technology Stack
- **Question Text**: "What is the Technology Stack?"
- **Field Type**: `multiselect`
- **Options**: 17 technology options (Java, .NET, Python, Node.js, databases, etc.)
- **Status**: **CORRECT** - Uses proper MCQ format

---

### 3. ⚠️ FORM SUBMISSION NOT TESTED

**Test**: Fill out form and verify submission navigates away from questionnaire page

**Result**: **NOT TESTED** - Cannot proceed with form submission testing until generic status questions are fixed

**Reasoning**:
- The 4 problematic questions need to be answered to submit the form
- Answering them with generic status values would corrupt the data model
- Form submission testing should be performed after routing logic is fixed

---

## Root Cause Analysis

### Issue Location:
**File**: `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py`
**Function**: `group_attributes_by_category()`
**Lines**: 373-406

### The Problem:

The routing logic has IF conditions (lines 373-387) that are supposed to match field names and route them to `generate_missing_field_question()`:

```python
# Application metadata gaps (type, name, description)
elif any(
    x in attr_name.lower()
    for x in ["application_type", "canonical_name", "description"]
):
    question = generate_missing_field_question({}, asset_context)
    category = "application"

# Compliance/security gaps
elif any(
    x in attr_name.lower()
    for x in ["compliance", "security", "data_classification"]
):
    question = generate_missing_field_question({}, asset_context)
    category = "business"
```

**BUT**, the system is logging:
```
Gap field 'application_type' using Issue #980 intelligent builder for 1 asset(s)
Gap field 'canonical_name' using Issue #980 intelligent builder for 1 asset(s)
Gap field 'description' using Issue #980 intelligent builder for 1 asset(s)
Gap field 'compliance_flags.data_classification' using Issue #980 intelligent builder for 1 asset(s)
```

Then in the output JSON, these fields have questions generated by `generate_generic_question()` instead!

### Why the Routing Logic Fails:

The IF conditions check for substrings in `attr_name.lower()`, but there are THREE possible issues:

1. **Execution Order**: An earlier IF condition might be matching before reaching lines 373-387
2. **String Matching**: The `attr_name` value might not contain the expected substring
3. **Code Path**: The catch-all `else` (lines 402-406) is executing instead

### Evidence from Backend Logs:

At timestamp `2025-11-10 01:22:15,939`, the system generated questions for:
- `application_type` → Used `generate_generic_question()` ❌
- `canonical_name` → Used `generate_generic_question()` ❌
- `compliance_flags.data_classification` → Used `generate_generic_question()` ❌
- `description` → Used `generate_generic_question()` ❌

But for:
- `architecture_pattern` → Used `generate_missing_field_question()` from critical attributes ✅
- `technology_stack` → Used `generate_missing_field_question()` from critical attributes ✅

### The Key Difference:

`architecture_pattern` and `technology_stack` are **CRITICAL ATTRIBUTES** (lines 285-296), so they bypass the gap routing logic entirely and call `build_question_from_attribute()`, which internally uses the MCQ templates.

The other fields (`application_type`, `canonical_name`, `description`, `compliance_flags`) are **GAPS WITHOUT CRITICAL ATTRIBUTE MAPPING** (line 298), so they go through the gap routing logic. The routing logic SHOULD call `generate_missing_field_question()`, but instead it's calling `generate_generic_question()`.

---

## Screenshots

### Screenshot 1: Full Questionnaire Overview
![Questionnaire Overview](/Users/chocka/CursorProjects/migrate-ui-orchestrator/.playwright-mcp/questionnaire_overview.png)

**Shows**:
- 11 questions across 6 sections
- Analytics Dashboard as the asset
- Progress tracker showing 0% completion

### Screenshot 2: General Section with Status Questions
![General Section Status Questions](/Users/chocka/CursorProjects/migrate-ui-orchestrator/.playwright-mcp/issue_980_general_section_status_questions.png)

**Shows**:
- Questions 7-10 with problematic "What is the status of..." text
- All 4 questions have "Select an option" dropdowns with generic status values
- These should be proper MCQ questions instead

---

## Database Evidence

### Questionnaire Record:
```sql
SELECT id, collection_flow_id, asset_id, title, jsonb_array_length(questions)
FROM migration.adaptive_questionnaires
WHERE id = '5bb419d9-d6d9-415b-9947-95016a4086aa';
```

**Result**:
- ID: 5bb419d9-d6d9-415b-9947-95016a4086aa
- Collection Flow: a98e0c7a-857b-45b7-b4c8-75e2b4ef19bf
- Asset: 059a1f71-69ef-41cc-8899-3c89cd560497 (Analytics Dashboard)
- Question Count: 11
- Created: 2025-11-10 01:22:15 UTC

### Sample Question JSON (application_type):
```json
{
    "field_id": "application_type",
    "question_text": "What is the status of application type for Analytics Dashboard?",
    "field_type": "select",
    "required": true,
    "category": "general",
    "options": [
        {"value": "available", "label": "Available - Information exists and is accessible"},
        {"value": "partial", "label": "Partially Available - Some information exists but incomplete"},
        {"value": "not_available", "label": "Not Available - Information needs to be gathered"},
        {"value": "not_applicable", "label": "Not Applicable - This attribute doesn't apply to this asset"},
        {"value": "unknown", "label": "Unknown - Assessment not yet completed"}
    ],
    "help_text": "Assess the availability status of application type information",
    "priority": "medium",
    "gap_type": "application_type"
}
```

**Analysis**: This JSON matches `generate_generic_question()` output exactly (see `assessment_question_builders.py:180-226`)

---

## Recommendations

### Immediate Actions Required:

1. **Debug Routing Logic**:
   - Add debug logging to `section_builders.py:325-406` to log which IF condition is being evaluated
   - Log the value of `attr_name` and `attr_name.lower()` for each gap
   - Identify why lines 373-379 and 382-387 are NOT matching

2. **Verify String Matching**:
   - Check if `attr_name` contains expected substrings
   - Example: Does `"application_type" in "application_type".lower()` return True?
   - May need to adjust substring matching logic

3. **Test Fix Approach**:
   - Option A: Update routing conditions to match actual `attr_name` values
   - Option B: Normalize `attr_name` before matching (remove prefixes, handle dots)
   - Option C: Use explicit field name mapping dictionary instead of substring matching

4. **Delete Old Questionnaire**:
   ```sql
   DELETE FROM migration.adaptive_questionnaires
   WHERE id = '5bb419d9-d6d9-415b-9947-95016a4086aa';
   ```
   Then regenerate to test fixes

### Testing Protocol After Fix:

1. Delete existing questionnaire
2. Regenerate questionnaire
3. Verify all 4 problematic questions now use proper MCQ format:
   - `application_type` → 9 options (Web Application, API Service, etc.)
   - `canonical_name` → Text input
   - `description` → Textarea input
   - `compliance_flags` → 7 multiselect options (PCI DSS, HIPAA, etc.)
4. Test form submission flow

---

## Comparison: Expected vs Actual

### Expected Behavior (from `attribute_question_builders.py`):

#### application_type (lines 102-118):
- **Question**: "What type of application is Analytics Dashboard?"
- **Type**: select (dropdown)
- **Options**: 9 choices
  1. Web Application - Browser-based interface
  2. API Service - RESTful or SOAP web service
  3. Batch Job - Scheduled background processing
  4. Database - Data storage and management
  5. Middleware - Integration or message broker
  6. Desktop Application - Client-installed software
  7. Mobile Application - iOS/Android app
  8. Mainframe Application - Legacy mainframe system
  9. Other - Custom or hybrid application type

#### canonical_name (lines 119-124):
- **Question**: "What is the canonical (official) name for Analytics Dashboard?"
- **Type**: text
- **Validation**: Required, min 2 characters

#### description (lines 125-130):
- **Question**: "What is the business purpose and functionality of Analytics Dashboard?"
- **Type**: textarea
- **Validation**: Required, 10-500 characters

#### compliance_flags (lines 131-145):
- **Question**: "What compliance requirements apply to Analytics Dashboard?"
- **Type**: multiselect
- **Options**: 7 choices
  1. PCI DSS - Payment Card Industry Data Security Standard
  2. HIPAA - Health Insurance Portability and Accountability Act
  3. GDPR - General Data Protection Regulation
  4. SOX - Sarbanes-Oxley Act
  5. ISO 27001 - Information Security Management
  6. FedRAMP - Federal Risk and Authorization Management Program
  7. None - No specific compliance requirements

### Actual Behavior (from database):

All 4 fields use the SAME generic question template:
- **Question**: "What is the status of {field_name} for Analytics Dashboard?"
- **Type**: select (dropdown)
- **Options**: 5 generic status choices (Available, Partially Available, Not Available, Not Applicable, Unknown)

---

## Backend Logs Analysis

### Relevant Log Entries (2025-11-10 01:22:15 UTC):

```
INFO - Gap field 'application_type' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'canonical_name' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'compliance_flags.data_classification' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'description' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'resilience' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'tech_debt' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'technical_details.api_endpoints' using Issue #980 intelligent builder for 1 asset(s)
INFO - Gap field 'technical_details.dependencies' using Issue #980 intelligent builder for 1 asset(s)
INFO - Generated 5 sections using 22 critical attributes
INFO - Generated 6 sections with 11 total questions
```

**Observation**: The log message "using Issue #980 intelligent builder" appears on line 301 of `section_builders.py`, which is BEFORE the routing IF/ELIF/ELSE logic. This log is misleading - it says "intelligent builder" will be used, but doesn't guarantee which builder function will be called.

### Form Execution Error (Not Related to Questions):

```
ERROR - ❌ Phase execution failed: b244cff0-7dfa-4a93-88ab-839662250962 - manual_collection
- Failed to execute phase 'completed': Invalid phase 'completed' for flow type 'collection'
```

**Analysis**: This error occurred when trying to execute the flow, but it didn't prevent questionnaire loading. The questionnaires were retrieved from the database successfully. This error is related to phase transition logic, not question generation.

---

## Conclusion

### Summary of Findings:

1. ✅ **Issue #1 RESOLVED**: No duplicate questions
2. ❌ **Issue #2 NOT RESOLVED**: Generic status questions remain (4 out of 11 questions affected)
3. ⚠️ **Issue #3 NOT TESTED**: Form submission deferred until Issue #2 is fixed

### Next Steps:

1. **Developer Action Required**: Fix routing logic in `section_builders.py` to correctly route `application_type`, `canonical_name`, `description`, and `compliance_flags` to `generate_missing_field_question()`

2. **Suggested Debug Approach**:
   ```python
   # Add after line 325 in section_builders.py
   logger.info(f"🔍 Routing gap field: '{attr_name}' (lowercase: '{attr_name.lower()}')")

   # Add inside each IF/ELIF clause
   logger.info(f"✅ Matched routing condition: [condition name]")

   # Add in else clause (line 402)
   logger.info(f"⚠️ No routing match - using generic builder for: '{attr_name}'")
   ```

3. **Validation Checklist After Fix**:
   - [ ] Delete questionnaire ID 5bb419d9-d6d9-415b-9947-95016a4086aa
   - [ ] Regenerate questionnaire
   - [ ] Verify question 7 (application_type) has 9 MCQ options
   - [ ] Verify question 8 (canonical_name) is text input
   - [ ] Verify question 9 (compliance_flags) has 7 multiselect options
   - [ ] Verify question 10 (description) is textarea input
   - [ ] Test form submission flow
   - [ ] Verify no form submission loop

---

## Appendix: Code References

### Files Examined:

1. **section_builders.py** (lines 298-417)
   - Path: `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py`
   - Contains gap routing logic

2. **attribute_question_builders.py** (lines 1-150+)
   - Path: `backend/app/services/ai_analysis/questionnaire_generator/tools/attribute_question_builders.py`
   - Contains MCQ templates for critical fields

3. **assessment_question_builders.py** (lines 180-226)
   - Path: `backend/app/services/ai_analysis/questionnaire_generator/tools/assessment_question_builders.py`
   - Contains `generate_generic_question()` that creates "status" questions

### Database Queries Used:

```sql
-- Find most recent questionnaires
SELECT id, collection_flow_id, asset_id, title, jsonb_array_length(questions) as qcount, created_at
FROM migration.adaptive_questionnaires
ORDER BY created_at DESC
LIMIT 5;

-- View questions for specific questionnaire
SELECT jsonb_pretty(questions)
FROM migration.adaptive_questionnaires
WHERE id = '5bb419d9-d6d9-415b-9947-95016a4086aa';
```

---

**Report Generated**: November 9, 2025
**QA Tester**: Claude Code (Anthropic)
**Status**: Ready for Developer Review
