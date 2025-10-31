# Intelligent Questionnaire Patterns

**Date**: 2025-10-31
**Status**: ✅ Active
**Impact**: Enhanced user experience through context-aware question options

---

## Overview

The adaptive questionnaire system now includes **intelligent, context-aware question generation** that tailors options based on asset attributes like operating system and technology stack. This reduces cognitive load and guides users toward the most appropriate answers.

---

## Implemented Patterns

### 1. Operating System-Aware Technology Stack (October 2025)

**Trigger**: `technology_stack` field when `asset_context.operating_system` is available

**Implementation**: `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py:57-131`

**Behavior**:
- **AIX**: Shows WebSphere, DB2, PowerHA, MQ Series (IBM middleware stack)
- **Windows**: Shows IIS, .NET Framework, SQL Server, Active Directory
- **Linux**: Shows Apache, NGINX, Docker, Kubernetes, PostgreSQL
- **Solaris**: Shows Oracle WebLogic, GlassFish, Oracle Database

**Example**:
```python
if "AIX" in os:
    return "multiselect", [
        {"value": "websphere_85", "label": "WebSphere Application Server 8.5"},
        {"value": "db2", "label": "IBM DB2"},
        {"value": "powerha", "label": "PowerHA SystemMirror"},
        # ... more AIX-specific options
    ]
```

**Backend Log**:
```
Providing AIX-specific technology_stack options for OS: AIX
```

---

### 2. Technology Stack-Aware Architecture Pattern (October 2025)

**Trigger**: `architecture_pattern` field when `asset_context.technology_stack` is available

**Implementation**: `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py:133-229`

**Behavior**: Reorders architecture pattern options based on detected technology stack

#### Pattern Detection Rules

| Technology Detected | Recommended Patterns (Priority Order) |
|-------------------|--------------------------------------|
| **Container/K8s** (Docker, Kubernetes) | 1. Microservices<br>2. Event-Driven<br>3. Layered<br>4. Hybrid<br>5. Monolithic |
| **Serverless** (Lambda, Azure Functions) | 1. Serverless<br>2. Event-Driven<br>3. Microservices<br>4. Hybrid |
| **IBM Middleware** (WebSphere, DB2, MQ) | 1. Layered/N-Tier<br>2. Monolithic<br>3. SOA<br>4. Hybrid<br>5. Microservices |
| **Windows/.NET** (IIS, .NET, ASP.NET) | 1. Layered/N-Tier<br>2. Monolithic<br>3. Microservices<br>4. SOA<br>5. Hybrid |
| **Modern Web** (Node.js, Python, NGINX) | 1. Microservices<br>2. Layered<br>3. Monolithic<br>4. Event-Driven<br>5. Hybrid |
| **Oracle/Java EE** (WebLogic, GlassFish) | 1. SOA<br>2. Layered<br>3. Monolithic<br>4. Hybrid<br>5. Microservices |

**Example**:
```python
# AIX asset with WebSphere, DB2, MQ Series
tech_stack = ["websphere_85", "db2", "mq_series"]

# Result: IBM enterprise pattern ordering
options = [
    {"value": "layered", "label": "Layered/N-Tier Architecture"},
    {"value": "monolith", "label": "Monolithic Application"},
    {"value": "soa", "label": "Service-Oriented Architecture (SOA)"},
    {"value": "hybrid", "label": "Hybrid Architecture"},
    {"value": "microservices", "label": "Microservices Architecture"},
]
```

**Backend Log**:
```
Providing IBM enterprise architecture_pattern options for tech stack: {WEBSPHERE_85,DB2,MQ_SERIES}
```

---

### 3. Compliance Constraints "None" Option (October 2025)

**Trigger**: `compliance_constraints` field (always available)

**Implementation**: `backend/app/services/manual_collection/adaptive_form_service/config/field_options.py:114-127`

**Behavior**: Provides "None" as the first option for assets without compliance requirements

**Before**:
```python
"compliance_constraints": [
    {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
    {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
    # ... no "None" option
]
```

**After**:
```python
"compliance_constraints": [
    {"value": "none", "label": "None - No specific compliance requirements"},  # ADDED
    {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
    {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
    # ...
]
```

**Rationale**: Not all applications have regulatory compliance requirements. Providing "None" as the first option:
1. Makes it clear that compliance is optional
2. Reduces confusion for users with non-regulated assets
3. Prevents users from incorrectly selecting a compliance framework

---

## Architecture

### Execution Order Priority

The intelligent logic follows a **specific-to-general** pattern:

```python
# 1. Check SPECIFIC conditions with asset context FIRST
if attr_name == "technology_stack" and asset_context:
    os = asset_context.get("operating_system", "").upper()
    if "AIX" in os:
        return aix_specific_options  # EARLY RETURN

# 2. Check GENERAL fallback options SECOND
if attr_name in FIELD_OPTIONS:
    return FIELD_OPTIONS[attr_name]  # Generic options

# 3. Default fallback LAST
return default_field_type, []
```

**Critical Rule**: Specific conditions MUST be checked before general fallbacks to prevent early returns that bypass intelligent logic.

**Anti-Pattern** (Bug from previous implementation):
```python
# WRONG - General check first
if attr_name in FIELD_OPTIONS:  # ← technology_stack IS here
    return FIELD_OPTIONS[attr_name]  # ← EARLY RETURN, OS logic never reached!

# OS-aware logic (NEVER EXECUTED)
if attr_name == "technology_stack" and asset_context:
    # This code is unreachable!
```

---

## Testing

### Test Flow ID: `fd0ce065-4e12-4534-9e91-5708061b99aa`

**Asset**: AIX Production Server (`f6d3dad3-b970-4693-8b70-03c306e67fcb`)
**OS**: AIX 7.2
**Tech Stack**: `['websphere_85', 'db2', 'mq_series']`

**Verification Steps**:
1. Created collection flow with AIX asset
2. Proceeded through gap analysis (14 gaps identified)
3. Generated questionnaire
4. Verified Question 1 (Compliance Constraints):
   - ✅ First option: "None - No specific compliance requirements"
5. Verified Question 3 (Architecture Pattern):
   - ✅ Options ordered: Layered → Monolithic → SOA → Hybrid → Microservices
6. Verified backend logs:
   - ✅ "Providing IBM enterprise architecture_pattern options for tech stack: {WEBSPHERE_85,DB2,MQ_SERIES}"

---

## Future Patterns to Implement

As requested by user: **"Intelligence needs to be infused into ALL questions"**

### High-Priority Candidates

1. **Business Logic Complexity**: Context-aware based on `technology_stack`
   - Simple CRUD → "Simple - Basic CRUD, minimal business logic"
   - Enterprise middleware → "Complex - Advanced workflows, multi-step processes"

2. **Security Vulnerabilities**: Context-aware based on `eol_technology_assessment`
   - EOL technologies → Highlight "High Severity" option first
   - Current technologies → "None Known" option first

3. **Change Tolerance**: Context-aware based on `business_criticality`
   - Mission Critical → "Low - Significant training needed"
   - Low Priority → "High - Users adapt quickly"

4. **Availability Requirements**: Context-aware based on `business_criticality`
   - Mission Critical → 99.99% options first
   - Development/Test → "Best Effort" first

5. **Dependencies**: Context-aware based on `architecture_pattern`
   - Microservices → "High - Depends on 8-15 systems" first
   - Monolithic → "Minimal - Standalone" first

---

## Benefits

1. **Reduced Cognitive Load**: Users see most relevant options first
2. **Faster Form Completion**: Less scrolling through irrelevant options
3. **Improved Data Quality**: Users select more accurate answers
4. **Platform-Specific Guidance**: Shows expertise in different technology stacks
5. **Contextual Awareness**: System "understands" the asset being described

---

## Related Files

- `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py` - Core logic
- `backend/app/services/manual_collection/adaptive_form_service/config/field_options.py` - Default options
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py` - Asset context threading
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/agents.py` - Business context passing
- `docs/analysis/BUG_REPORT_OS_AWARE_QUESTIONNAIRE_DATA_STRUCTURE_MISMATCH.md` - Initial implementation

---

## Architectural Lessons

1. **Execution Order Matters**: Always check specific conditions before general fallbacks
2. **Early Returns Prevent Logic**: Be aware of early returns that bypass subsequent code
3. **Context Threading**: Asset data must flow through entire pipeline (utils → agents → tools)
4. **Progressive Enhancement**: Start with one intelligent field, then expand systematically
5. **User-Centric Design**: Not all assets have compliance, not all questions are universal

---

**Next Steps**: Implement remaining intelligent patterns for all 11+ questionnaire fields.
