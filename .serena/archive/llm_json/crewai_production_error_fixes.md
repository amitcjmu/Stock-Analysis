# CrewAI Production Error Fixes

## Insight 1: DataCleansingExecutor Missing Abstract Method
**Problem**: Abstract class instantiation failure during data_cleansing phase
**Root Cause**: Missing `_prepare_crew_input()` method after modularization
**Solution**: Implement required abstract method in executor class
**Code**:
```python
# File: backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing/executor.py
def _prepare_crew_input(self) -> Dict[str, Any]:
    """Prepare input data for crew execution"""
    return {
        "raw_data": self.state.raw_data,
        "field_mappings": getattr(self.state, "field_mappings", {}),
        "cleansing_type": "comprehensive_data_cleansing",
    }
```
**Usage**: Required for all phase executors inheriting from BasePhaseExecutor

## Insight 2: Field Mapping Tool Parameter Mismatch
**Problem**: Tool expects wrapped parameters but agents pass direct format
**Error**: `Field required [type=missing, input_value={'source_fields': [...]}`
**Solution**: Make tool accept both parameter formats for backward compatibility
**Code**:
```python
# File: backend/app/services/crewai_flows/tools/data_validation_tool.py
def _run(self, mapping_request: Dict[str, Any]) -> str:
    # Handle both parameter formats
    if "mapping_request" in mapping_request:
        actual_request = mapping_request["mapping_request"]
    elif "source_fields" in mapping_request:
        actual_request = mapping_request
    else:
        actual_request = mapping_request

    result = FieldSuggestionImpl.generate_suggestions(actual_request)
    return json.dumps(result)
```
**Usage**: When CrewAI tools receive inconsistent parameter structures

## Insight 3: Modularization Pattern for Large Files
**Problem**: data_validation_tool.py exceeded 400-line limit
**Solution**: Split into modular structure preserving backward compatibility
**Structure**:
```
data_validation/
├── __init__.py        # Public API (imports all exports)
├── base_tools.py      # CrewAI tool wrappers
├── implementations.py # Core business logic
```
**Code** (backward-compatible facade):
```python
# Original file becomes import facade
from .data_validation import *
__all__ = ['BaseFieldSuggestionTool', 'ValidationTool', ...]
```
**Usage**: Apply when pre-commit fails on file length violations

## Key Commands Used
```bash
# Fix import order violations
cd backend && pre-commit run --all-files

# Modularization verification
python -m py_compile app/services/crewai_flows/tools/data_validation_tool.py

# Git workflow for production fixes
git commit -m "fix: Resolve critical production errors..."
git push origin fix/discovery-flow-data-population-20250118
```

## Lessons Learned
1. **Always check abstract method implementations** after modularization
2. **Tool parameter mismatches** often occur between agent calls and tool definitions
3. **Backward compatibility** > forcing all consumers to update
4. **Modularization must preserve all public imports** to avoid breaking changes
