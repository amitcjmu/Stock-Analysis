# FlowTypeConfig Parameter Debugging Patterns - September 2025

## Critical Production Fix: FlowTypeConfig Parameter Mismatches

### Problem Pattern
FlowTypeConfig constructor parameter errors prevent flow registration during application startup, causing production failures.

### Diagnostic Pattern
```bash
# Look for these error patterns in logs:
FlowTypeConfig.__init__() got an unexpected keyword argument 'flow_metadata'
FlowTypeConfig.__init__() got an unexpected keyword argument 'child_flow_service_class'
FlowTypeConfig.__init__() got an unexpected keyword argument 'validation_config'
```

### Root Cause Investigation
1. **Check FlowTypeConfig definition** in `backend/app/services/flow_type_registry.py`
2. **Compare with flow config files** in `backend/app/services/flow_configs/`
3. **Look for parameter name mismatches**

### Valid FlowTypeConfig Parameters (as of Sept 2025)
```python
@dataclass
class FlowTypeConfig:
    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    phases: List[PhaseConfig] = field(default_factory=list)
    crew_class: Optional[Type] = None
    output_schema: Optional[Type[BaseModel]] = None
    input_schema: Optional[Type[BaseModel]] = None
    capabilities: FlowCapabilities = field(default_factory=FlowCapabilities)
    default_configuration: Dict[str, Any] = field(default_factory=dict)
    initialization_handler: Optional[str] = None
    finalization_handler: Optional[str] = None
    error_handler: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # ← Put extra config here
    tags: List[str] = field(default_factory=list)
    child_flow_service: Optional[Type] = None  # ← Not child_flow_service_class
```

### Common Parameter Name Fixes
```python
# WRONG parameter names → CORRECT parameter names
flow_metadata → metadata
child_flow_service_class → child_flow_service

# WRONG: Invalid top-level parameters
validation_config={...}
ui_config={...}

# CORRECT: Move to metadata field
metadata={
    "validation_config": {...},
    "ui_config": {...},
    # other metadata
}
```

### ServiceRegistry Dependency Injection Pattern
**Problem**: `safe_extend_tools()` functions calling tool creators without required ServiceRegistry parameter

**Solution**: Enhanced parameter detection and injection
```python
def safe_extend_tools(
    tools: List,
    getter,
    tool_name: str = "tools",
    context_info: Dict[str, Any] = None,
    service_registry: Optional["ServiceRegistry"] = None
) -> int:
    try:
        import inspect
        sig = inspect.signature(getter)
        params = sig.parameters

        # Call getter with appropriate parameters based on signature
        if "registry" in params:
            # New pattern: requires registry parameter
            if "context_info" in params:
                new_tools = getter(context_info, registry=service_registry)
            else:
                new_tools = getter(registry=service_registry)
        elif "context_info" in params and context_info is not None:
            # Legacy pattern: takes context_info
            new_tools = getter(context_info)
        else:
            # Simple pattern: no parameters
            new_tools = getter()
```

### Verification Commands
```bash
# Test flow initialization after fixes
docker logs migration_backend --tail 50 | grep -E "(flow|discovery|registered|Error)"

# Should see:
# ✅ Registered flow type: discovery (v2.0.0)
# ✅ Flow configuration complete: 9 flows registered
# ✅ All flow configurations verified successfully
```

### Key Files Modified in This Pattern
- `backend/app/services/flow_configs/discovery_flow_config.py` - Parameter name fixes
- `backend/app/services/persistent_agents/agent_tools_utils.py` - ServiceRegistry injection
- Any other flow config files with similar parameter issues

## Prevention Strategy
1. **Always check FlowTypeConfig definition** before adding new parameters
2. **Use metadata field** for custom configuration data
3. **Implement dynamic parameter detection** for tool injection functions
4. **Test flow initialization** after any flow config changes
