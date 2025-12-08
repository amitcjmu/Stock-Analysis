# Issue #1193: Collection Flow Server Data Inheritance Fix (December 2025)

## Problem Statement
Applications were receiving infrastructure gap questions (OS version, CPU/memory, network config) even though these are server-level attributes. An application can depend on multiple servers with different operating systems, making "What is the operating system?" questions nonsensical at the application level.

## Root Cause (GPT5.1 Codex Discovery)
**BLOCKING BUG**: The field_id names in COLLECTION_FLOW_FIELD_METADATA (e.g., `operating_system`, `cpu_cores`) don't match the attribute names in AssetTypeRequirements (e.g., `operating_system_version`, `cpu_memory_storage_specs`).

This caused ALL gaps to be skipped for ALL asset types, not just applications. The "0 infrastructure questions" for apps was a false positive - servers were also affected.

## Solution Implemented

### 1. Field-to-Attribute Mapping (scanner.py)
```python
def _build_field_to_attr_map(self) -> Dict[str, List[str]]:
    """Build mapping from field_id to list of attribute names."""
    # Uses CriticalAttributesDefinition.get_attribute_mapping()
    # Maps: "operating_system" -> ["operating_system_version"]
    #       "cpu_cores" -> ["cpu_memory_storage_specs"]
    #       "technology_stack" -> ["technology_stack"]  # Direct match

def _is_field_applicable(self, field_id: str, applicable_attrs: Set[str]) -> bool:
    """Check if ANY mapped attributes are applicable for asset type."""
```

### 2. Safety Fallback for Unknown Asset Types
```python
applicable_attrs = (
    set(applicable_attrs_list)
    if applicable_attrs_list
    else set(AssetTypeRequirements.ALL_CRITICAL_ATTRIBUTES)  # Fallback
)
```
This ensures unknown/typo asset types still check all infrastructure fields.

### 3. AssetTypeRequirements Updates
Applications now EXCLUDE server-level infrastructure:
- `operating_system_version` - Collected from dependent servers
- `cpu_memory_storage_specs` - Collected from dependent servers
- `network_configuration` - Collected from dependent servers

Applications KEEP app-level metrics:
- `availability_requirements` - SLA requirements at app level
- `performance_baseline` - App-level performance metrics

## Regression Tests Added
- `test_server_retains_infrastructure_gaps` - Servers still get OS gaps
- `test_application_skips_infrastructure_gaps` - Apps DON'T get infra gaps
- `test_unknown_asset_type_keeps_mapped_infrastructure_gaps` - Unknown types fallback

## GPT5.1 Codex Follow-up Notes

### 1. Alias Source Divergence Risk (MITIGATED)
Two modules define critical attributes:
- `app.services.collection.critical_attributes`
- `app.services.crewai_flows.tools.critical_attributes_tool.base`

**Mitigation**: `verify_consistency()` function in collection/critical_attributes.py validates keys match and raises RuntimeError if they drift. Last synchronized: Bug #728 fix.

### 2. Data Quality Dependency
Skipping infra for apps relies on `asset_dependencies` table being populated with server dependencies. If these links are missing, apps WILL still show infra gaps (by design - no inheritance source).

**Recommendation**: Ensure data loading/backfill scripts maintain dependency relationships.

## Files Changed
- `backend/app/services/collection/gap_analysis/intelligent_gap_scanner/scanner.py`
- `backend/app/services/collection/gap_analysis/asset_type_requirements.py`
- `backend/app/services/collection/gap_analysis/intelligent_gap_scanner/data_extractors.py`
- `backend/app/services/collection/gap_analysis/comprehensive_task_builder.py`
- `backend/tests/unit/collection/test_intelligent_gap_scanner.py`

## Results
- **Before**: 21 questions across 4 sections (including Infrastructure)
- **After**: 10 questions across 2 sections (Resilience, Dependencies)
- Backend logs: "skipped 11 inapplicable fields"

## PR Reference
PR #1274: https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/pull/1274
