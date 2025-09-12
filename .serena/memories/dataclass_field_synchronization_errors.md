# Dataclass Field Synchronization Errors

## Problem Pattern
Backend startup fails with TypeError when dataclass fields are missing:
```python
PhaseConfig.__init__() got an unexpected keyword argument 'expected_duration_minutes'
```

## Root Cause
Mismatch between dataclass definition and usage in constants/configs.

## Solution Applied
Added missing fields to `backend/app/services/flow_type_registry.py`:

### PhaseConfig Missing Fields
```python
outputs: List[str] = field(default_factory=list)
expected_duration_minutes: Optional[int] = None
parallel_execution: bool = False
dependencies: List[str] = field(default_factory=list)
success_criteria: Dict[str, Any] = field(default_factory=dict)
failure_conditions: Dict[str, Any] = field(default_factory=dict)
```

### FlowCapabilities Missing Fields
```python
supports_parallel_execution: bool = False
supports_phase_rollback: bool = False
supports_incremental_execution: bool = False
supports_failure_recovery: bool = False
supports_real_time_monitoring: bool = False
supports_dynamic_scaling: bool = False
```

## Prevention
- Keep dataclass definitions in sync with usage
- Check `discovery_phase_constants.py` when modifying PhaseConfig
- Validate all config files load successfully on startup
