# ADR-040: Declarative Agent Tool Configuration

**Status**: Accepted
**Date**: 2025-12-05
**Context**: Issue #1060 - Refactor tool_manager.py from scattered if/elif blocks
**Deciders**: Engineering Team
**Related**: ADR-015 (TenantScopedAgentPool), ADR-024 (TenantMemoryManager)

## Context and Problem Statement

The `tool_manager.py` module had grown to include scattered if/elif blocks for each agent type:

```python
# Before: Scattered if/elif blocks (6+ blocks)
if agent_type == "discovery":
    tools.extend(create_asset_creation_tools(context_info))
    tools.extend(create_data_validation_tools(context_info))
elif agent_type == "field_mapper":
    tools.append(MappingConfidenceTool(context_info=context_info))
    tools.extend(create_critical_attributes_tools(context_info))
elif agent_type == "questionnaire_generator":
    # ... more code
```

**Problems**:
1. Adding new agent types required modifying multiple code blocks
2. String literals for agent types were error-prone
3. No centralized view of agent-tool mappings
4. Configuration was mixed with execution logic
5. Difficult to test tool configurations in isolation

## Decision Drivers

1. **Single Source of Truth**: All agent-tool mappings in one place
2. **Maintainability**: Adding new agents should require only configuration changes
3. **Testability**: Configuration should be testable without loading actual tools
4. **Validation**: Invalid configurations should fail fast at startup
5. **Clarity**: Tool requirements (context, registry) should be explicit, not introspected

## Considered Options

### Option 1: Keep Scattered if/elif Blocks
**Rejected**: Growing maintenance burden, prone to errors.

### Option 2: Plugin-Based Dynamic Discovery
**Rejected**: Over-engineered for current needs. We have a known, finite set of agents.

### Option 3: Declarative Configuration with Dataclasses (SELECTED)
**Accepted**: Right balance of explicitness, maintainability, and simplicity.

## Decision

Create a centralized declarative configuration module (`agent_tool_config.py`) using Python dataclasses.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent Tool Configuration System                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  agent_tool_config.py (Single Source of Truth)                          │
│  ├─ ToolFactoryConfig (dataclass)                                       │
│  │   ├─ module_path: str           # Import path                        │
│  │   ├─ factory_name: str          # Function/class name                │
│  │   ├─ requires_context: bool     # Needs context_info?                │
│  │   ├─ requires_registry: bool    # Needs ServiceRegistry?             │
│  │   └─ is_class: bool             # Instantiate vs call?               │
│  │                                                                       │
│  ├─ AgentToolConfig (dataclass)                                         │
│  │   ├─ agent_type: str            # Agent identifier                   │
│  │   ├─ specific_tools: List[str]  # Tool names from TOOL_FACTORIES     │
│  │   ├─ common_categories: List    # Category names                     │
│  │   └─ description: str           # Documentation                      │
│  │                                                                       │
│  ├─ TOOL_FACTORIES: Dict[str, ToolFactoryConfig]                        │
│  ├─ AGENT_TOOL_CONFIGS: Dict[str, AgentToolConfig]                      │
│  └─ COMMON_TOOL_CATEGORIES: Dict[str, str]                              │
│                                                                          │
│  tool_manager.py (Uses configuration)                                   │
│  └─ _load_tool_from_factory()      # Dynamic loading from config        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Implementation Details

#### 1. Tool Factory Configuration

```python
@dataclass
class ToolFactoryConfig:
    """Configuration for a tool factory function."""
    module_path: str           # e.g., "app.services.crewai_flows.tools.asset_creation_tool"
    factory_name: str          # e.g., "create_asset_creation_tools"
    requires_context: bool = True   # Most tools need context
    requires_registry: bool = False # Some tools need ServiceRegistry
    is_class: bool = False          # True if instantiating a class
```

#### 2. Agent Tool Configuration

```python
@dataclass
class AgentToolConfig:
    """Complete tool configuration for an agent type."""
    agent_type: str
    specific_tools: List[str] = field(default_factory=list)
    common_categories: List[str] = field(default_factory=list)
    description: str = ""
```

#### 3. Configuration Dictionaries

```python
TOOL_FACTORIES: Dict[str, ToolFactoryConfig] = {
    "asset_creation": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.asset_creation_tool",
        factory_name="create_asset_creation_tools",
    ),
    "mapping_confidence": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.mapping_confidence_tool",
        factory_name="MappingConfidenceTool",
        is_class=True,  # Instantiate, don't call
    ),
    "asset_intelligence": ToolFactoryConfig(
        module_path="app.services.tools.asset_intelligence_tools",
        factory_name="get_asset_intelligence_tools",
        requires_context=False,  # Explicit: no context needed
    ),
    # ... more tools
}

AGENT_TOOL_CONFIGS: Dict[str, AgentToolConfig] = {
    "discovery": AgentToolConfig(
        agent_type="discovery",
        specific_tools=["asset_creation", "data_validation"],
        common_categories=["data_analysis"],
        description="Discovery agent for data analysis and asset creation",
    ),
    # ... more agents
}
```

#### 4. Dynamic Loading with Security

```python
def _load_tool_from_factory(cls, tool_name: str, context_info: Dict, tools: List) -> int:
    """
    Security Note: Dynamic imports via importlib are safe here because
    TOOL_FACTORIES configuration is static and defined in agent_tool_config.py,
    not from user input. All module paths are hardcoded at development time.
    """
    factory_config = get_tool_factory(tool_name)
    module = importlib.import_module(factory_config.module_path)
    factory = getattr(module, factory_config.factory_name)

    # Use explicit config flags instead of signature inspection
    if factory_config.is_class:
        if factory_config.requires_context:
            tool_instance = factory(context_info=context_info)
        else:
            tool_instance = factory()
        tools.append(tool_instance)
    elif factory_config.requires_registry:
        # ... handle registry case
    elif factory_config.requires_context:
        new_tools = factory(context_info)
        tools.extend(new_tools)
    else:
        new_tools = factory()
        tools.extend(new_tools)
```

### Adding New Agents

To add a new agent type, only configuration changes are needed:

```python
# Step 1: Add any new tool factories (if needed)
TOOL_FACTORIES["new_tool"] = ToolFactoryConfig(
    module_path="app.services.tools.new_tool",
    factory_name="create_new_tools",
)

# Step 2: Add agent configuration
AGENT_TOOL_CONFIGS["new_agent"] = AgentToolConfig(
    agent_type="new_agent",
    specific_tools=["new_tool", "existing_tool"],
    common_categories=["data_analysis"],
    description="New agent for specific purpose",
)
```

No code changes in tool_manager.py required.

### Validation

Configuration is validated at import time:

```python
def validate_configuration() -> List[str]:
    """Validate all agent tool configurations."""
    errors = []
    for agent_type, config in AGENT_TOOL_CONFIGS.items():
        for tool_name in config.specific_tools:
            if tool_name not in TOOL_FACTORIES:
                errors.append(f"Agent '{agent_type}' references unknown tool '{tool_name}'")
        for category in config.common_categories:
            if category not in COMMON_TOOL_CATEGORIES:
                errors.append(f"Agent '{agent_type}' references unknown category '{category}'")
    return errors
```

## Consequences

### Positive
- **Single Source of Truth**: All agent-tool mappings visible in one file
- **Easy to Extend**: New agents = dictionary entries only
- **Testable**: 24 unit tests validate configuration without loading tools
- **Self-Documenting**: Configuration serves as documentation
- **Validated Early**: Invalid configs fail at startup, not runtime
- **Explicit Dependencies**: `requires_context`, `requires_registry` flags replace introspection

### Negative
- **Learning Curve**: Developers must understand the configuration pattern
- **Indirection**: Tool loading happens via config lookup, not direct calls

### Neutral
- **Dynamic Imports**: Still uses `importlib.import_module()`, but paths are static/hardcoded

## Related Files

- `backend/app/services/persistent_agents/agent_tool_config.py` - Configuration module
- `backend/app/services/persistent_agents/tool_manager.py` - Uses configuration
- `backend/tests/unit/services/persistent_agents/test_agent_tool_config.py` - 24 unit tests

## References

- Issue #1060: Refactor tool_manager.py to declarative configuration
- PR #1254: Implementation
- ADR-015: TenantScopedAgentPool (agent architecture)
- ADR-024: TenantMemoryManager (related agent tooling)
