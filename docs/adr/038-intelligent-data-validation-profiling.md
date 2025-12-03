# ADR-038: Intelligent Data Validation and Profiling

**Status**: Accepted
**Date**: 2025-12-03
**Context**: Azure Production Error - VARCHAR(255) truncation on multi-valued application names
**Deciders**: Engineering Team
**Related**: ADR-027 (Universal Flow Type Config Pattern), Issue #1204

## Context and Problem Statement

During production deployment on Azure, 298 assets failed to create due to a `StringDataRightTruncationError`:

```
asyncpg.exceptions.StringDataRightTruncationError: value too long for type character varying(255)
```

**Root Cause**: The `application_name` field contained comma-separated lists of ~20 RPA applications (~487 characters), exceeding the VARCHAR(255) limit.

**Real Problem**: This is NOT a column size issue - it's a **data architecture problem**. Shared servers across multiple applications result in multi-valued fields that the current import pipeline doesn't detect or handle.

**Current State of Data Validation** (per ADR-027):
- Phase order: Data Import → Data Validation → Field Mapping → Data Cleansing → Asset Inventory
- Data Validation exists but only:
  - Checks structure on first record only
  - Samples 5-10 records for PII/security scanning
  - No multi-value detection
  - No field length analysis against schema constraints

## Decision Drivers

1. **Production Data Quality**: Prevent VARCHAR truncation errors before asset creation
2. **Multi-Value Semantics**: Recognize that comma-separated values often represent 1-to-many relationships
3. **User Control**: Allow users to decide how to handle detected issues (split/truncate/skip)
4. **Leverage Existing Infrastructure**: AssetDependency table exists for 1-to-many relationships
5. **Minimal Phase Changes**: Enhance existing Data Validation phase rather than adding new phase

## Considered Options

### Option 1: Expand VARCHAR Columns
**Rejected**: Just moves the problem to other fields. Doesn't address multi-value semantics.

### Option 2: Add New Pre-Mapping Phase
**Rejected**: ADR-027 already places Data Validation before Field Mapping. No need for new phase.

### Option 3: Enhance Data Validation with Intelligent Profiling (SELECTED)
**Accepted**: Leverages existing phase, adds comprehensive data analysis, includes user approval gate.

## Decision

Enhance the existing **Data Validation** phase with intelligent data profiling capabilities:

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Discovery Flow Phases                             │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Data Import                                                          │
│     └─ Raw CSV/Excel imported into raw_data storage                     │
│                                                                          │
│  2. Data Validation (ENHANCED)                                           │
│     ├─ Full Dataset Analysis (all records, not samples)                 │
│     ├─ Multi-Value Detection (comma/semicolon/pipe)                     │
│     ├─ Field Length Analysis (vs schema constraints)                    │
│     ├─ Data Quality Scoring (completeness/consistency/compliance)       │
│     ├─ Profile Report Generation                                         │
│     └─ User Approval Gate (must resolve critical issues)                │
│                                                                          │
│  3. Field Mapping                                                        │
│  4. Data Cleansing                                                       │
│  5. Asset Inventory                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. Schema Constraints Utility
Extract column constraints from SQLAlchemy Asset model:

```python
# backend/app/utils/schema_constraints.py
from functools import lru_cache
from app.models.asset.models import Asset

@lru_cache(maxsize=1)
def get_asset_schema_constraints() -> Dict[str, Dict[str, Any]]:
    """Extract column constraints from Asset model."""
    constraints = {}
    for column in Asset.__table__.columns:
        col_info = {
            "type": str(column.type),
            "nullable": column.nullable,
        }
        if hasattr(column.type, 'length') and column.type.length:
            col_info["max_length"] = column.type.length
        constraints[column.name] = col_info
    return constraints
```

#### 2. Multi-Value Detection
Identify fields containing delimiter-separated values:

```python
MULTI_VALUE_PATTERNS = {
    "comma": re.compile(r"[^,]+(?:,\s*[^,]+){2,}"),      # 3+ comma-separated
    "semicolon": re.compile(r"[^;]+(?:;\s*[^;]+){2,}"),  # 3+ semicolon-separated
    "pipe": re.compile(r"[^|]+(?:\|\s*[^|]+){2,}"),      # 3+ pipe-separated
}

def detect_multi_values(field_name: str, values: List[str]) -> Dict[str, Any]:
    """Detect if field contains multi-valued data."""
    multi_value_records = []
    for idx, value in enumerate(values):
        if not value or not isinstance(value, str):
            continue
        for pattern_name, pattern in MULTI_VALUE_PATTERNS.items():
            if pattern.match(value):
                multi_value_records.append({
                    "record_index": idx,
                    "value": value[:100] + "..." if len(value) > 100 else value,
                    "delimiter": pattern_name,
                })
                break
    return {
        "field": field_name,
        "is_multi_valued": len(multi_value_records) > 0,
        "affected_count": len(multi_value_records),
        "samples": multi_value_records[:5],
    }
```

#### 3. Full Dataset Analysis
Replace sampling with comprehensive analysis:

```python
class FieldStatistics:
    """Track statistics for a single field."""
    def __init__(self):
        self.lengths: List[int] = []
        self.null_count: int = 0
        self.unique_values: set = set()

    def add_value(self, value: Any):
        if value is None or value == "":
            self.null_count += 1
        else:
            str_val = str(value)
            self.lengths.append(len(str_val))
            if len(self.unique_values) < 1000:  # Cap for memory
                self.unique_values.add(str_val)

    def summary(self) -> Dict[str, Any]:
        return {
            "min_length": min(self.lengths) if self.lengths else 0,
            "max_length": max(self.lengths) if self.lengths else 0,
            "avg_length": statistics.mean(self.lengths) if self.lengths else 0,
            "null_count": self.null_count,
            "unique_count": len(self.unique_values),
        }
```

#### 4. Field Length Analysis
Compare actual data against schema constraints:

```python
def check_field_length_violations(
    field_stats: Dict[str, Dict[str, Any]],
    schema_constraints: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Check if any field values exceed schema constraints."""
    violations = []
    for field_name, stats in field_stats.items():
        schema = schema_constraints.get(field_name)
        if not schema or "max_length" not in schema:
            continue

        if stats["max_length"] > schema["max_length"]:
            violations.append({
                "severity": "critical",
                "field": field_name,
                "issue": f"Value exceeds VARCHAR({schema['max_length']}) limit",
                "schema_limit": schema["max_length"],
                "max_found": stats["max_length"],
                "recommendations": [
                    f"Truncate values to {schema['max_length']} characters",
                    "Split multi-valued fields into separate records",
                ]
            })
    return violations
```

#### 5. Data Profile Report
Aggregate all analysis results:

```python
@dataclass
class DataProfileReport:
    generated_at: datetime
    total_records: int
    total_fields: int

    # Quality scores (0-100)
    completeness_score: float
    consistency_score: float
    constraint_compliance_score: float
    overall_quality_score: float

    # Issues by severity
    critical_issues: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

    # Field-level details
    field_profiles: Dict[str, Dict[str, Any]]

    # User action required
    requires_user_decision: bool
    blocking_issue_count: int
```

#### 6. User Approval Gate
Require user decisions before proceeding:

```json
{
  "data_profile": {
    "total_records": 298,
    "quality_scores": {
      "completeness": 78,
      "consistency": 92,
      "constraint_compliance": 54,
      "overall": 75
    },
    "critical_issues": [
      {
        "field": "application_name",
        "issue": "Value exceeds VARCHAR(255) limit",
        "max_found": 487,
        "affected_records": 12
      }
    ],
    "warnings": [
      {
        "field": "application_name",
        "issue": "Multi-valued field detected",
        "affected_records": 45
      }
    ]
  },
  "requires_user_decision": true,
  "blocking_issues": 1
}
```

### API Design

#### GET `/api/v1/unified-discovery/{flow_id}/data-profile`
Retrieve data profile for a discovery flow.

#### POST `/api/v1/unified-discovery/{flow_id}/data-profile/decisions`
Submit user decisions for handling data issues:

```python
class FieldDecision(BaseModel):
    field_name: str
    action: Literal["split", "truncate", "skip", "keep"]
    custom_delimiter: Optional[str] = None

class DataProfileDecisions(BaseModel):
    decisions: List[FieldDecision]
    proceed_with_warnings: bool = False
```

### UI Design

Enhanced `/discovery/data-validation` page:

1. **Quality Scores Card**: Visual progress bars for completeness, consistency, compliance
2. **Critical Issues Section**: Red badges, must resolve before proceeding
3. **Warnings Section**: Yellow badges, can proceed after acknowledgment
4. **Field Statistics Table**: Min/max/avg length, null count, unique count
5. **Handling Modal**: Options for each issue (split/truncate/skip/keep)
6. **Approval Footer**: Checkbox acknowledgment + Proceed button

### Handling Options

| Issue Type | Option | Effect |
|------------|--------|--------|
| Multi-valued | Split | Create separate records per value |
| Multi-valued | Keep | Store full value (may cause issues later) |
| Multi-valued | First Value | Use only first value before delimiter |
| Length Violation | Truncate | Truncate to schema limit |
| Length Violation | Skip | Exclude record from import |

### Integration with AssetDependency

When user selects "Split" for multi-valued application names:
1. Create one Asset per unique hostname
2. For each application in the comma-separated list:
   - Create/find CanonicalApplication
   - Create AssetDependency record linking asset → application

## Consequences

### Positive
- Prevents VARCHAR truncation errors in production
- Gives users visibility into data quality issues
- Enables intelligent handling of multi-valued fields
- Leverages existing AssetDependency table for proper relationships
- No new phases required - enhances existing Data Validation

### Negative
- Additional processing time for large datasets (mitigated by chunking)
- Requires UI enhancement for decision controls
- Users must make decisions on data issues (cannot be fully automated)

### Risks
- Large datasets (>100K records) may have performance implications
- Complex multi-value patterns (nested quotes, escaped delimiters) may not be detected

## Implementation

See Issue #1204 and sub-issues #1205-#1214 for detailed implementation tasks.

**Files to Modify**:
- `backend/app/utils/schema_constraints.py` (new)
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/validation_checks.py`
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/executor.py`
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/profile_generator.py` (new)
- `backend/app/api/v1/endpoints/unified_discovery/data_validation.py` (new)
- `src/app/discovery/data-validation/page.tsx`
- `src/services/discoveryService.ts`

## References

- Issue #1204: Enhance Data Validation Phase with Intelligent Data Profiling
- ADR-027: Universal Flow Type Config Pattern (phase ordering)
- ADR-036: Canonical Application Junction Table Architecture (AssetDependency)
- Azure Production Error Logs (December 2025)
