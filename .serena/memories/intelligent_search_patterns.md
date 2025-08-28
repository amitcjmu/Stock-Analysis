# Intelligent Search Patterns for Code Navigation

## Serena's Symbolic Search Strategy

### Core Principle: Read Less, Understand More
- **NEVER** read entire files unless absolutely necessary
- **ALWAYS** use symbolic tools first
- **PREFER** targeted searches over broad reads
- **USE** overview before diving deep

## Search Pattern Hierarchy

### 1. Start with Overview (Least Expensive)
```python
# Get high-level understanding first
get_symbols_overview(relative_path="backend/app/services")
# Returns: Top-level classes, functions, structure

# Then narrow down
get_symbols_overview(relative_path="backend/app/services/discovery_service.py")
# Returns: All symbols in specific file
```

### 2. Symbol-Based Search (Targeted)
```python
# Direct symbol access when name is known
find_symbol(
    name_path="DiscoveryService/execute_discovery",
    relative_path="backend/app/services",
    include_body=False  # Get signature first
)

# Then read body only if needed
find_symbol(
    name_path="DiscoveryService/execute_discovery",
    relative_path="backend/app/services/discovery_service.py",
    include_body=True  # Now get implementation
)
```

### 3. Pattern Search (Flexible)
```python
# Search for patterns when exact location unknown
search_for_pattern(
    substring_pattern=r"class.*Agent.*Pool",
    restrict_search_to_code_files=True,
    relative_path="backend"
)

# Search for specific implementations
search_for_pattern(
    substring_pattern=r"TenantScoped.*Pool",
    context_lines_before=2,
    context_lines_after=2
)
```

### 4. Reference Search (Relationships)
```python
# Find all usages of a symbol
find_referencing_symbols(
    name_path="CrewAIFlowService",
    relative_path="backend/app/services/crewai_flow_service.py"
)
# Returns: All files and locations using this service
```

## Efficient Search Patterns by Task

### Finding a Class Implementation
```python
# Step 1: Confirm it exists
search_for_pattern(
    substring_pattern=r"class TenantScopedAgentPool",
    restrict_search_to_code_files=True
)

# Step 2: Get overview if found
get_symbols_overview(
    relative_path="backend/app/services/persistent_agents/tenant_scoped_agent_pool.py"
)

# Step 3: Read specific methods only
find_symbol(
    name_path="TenantScopedAgentPool/__init__",
    relative_path="backend/app/services/persistent_agents/tenant_scoped_agent_pool.py",
    include_body=True
)
```

### Finding Configuration or Constants
```python
# Search for configuration patterns
search_for_pattern(
    substring_pattern=r"(DATABASE_URL|REDIS_URL|API_KEY)",
    paths_include_glob="**/*.env*",
    relative_path="backend"
)

# Find environment variable usage
search_for_pattern(
    substring_pattern=r"os\.getenv\(['\"].*['\"]",
    restrict_search_to_code_files=True
)
```

### Analyzing Dependencies
```python
# Find all imports of a module
search_for_pattern(
    substring_pattern=r"from app\.services\.discovery.*import",
    restrict_search_to_code_files=True
)

# Check circular dependencies
find_referencing_symbols(
    name_path="ServiceA",
    relative_path="backend/app/services/service_a.py"
)
```

### Understanding Error Sources
```python
# Find error definitions
search_for_pattern(
    substring_pattern=r"class.*Error.*\(.*Exception\)",
    restrict_search_to_code_files=True
)

# Find error handling
search_for_pattern(
    substring_pattern=r"except.*Error",
    context_lines_after=5
)
```

## Advanced Search Techniques

### Using Name Path Patterns
```python
# Absolute path (from root)
find_symbol(name_path="/DiscoveryService")  # Top-level only

# Relative path (any level)
find_symbol(name_path="process_flow")  # Any process_flow method

# Nested path (specific hierarchy)
find_symbol(name_path="DiscoveryService/process_flow")  # Specific method

# With wildcards (substring matching)
find_symbol(
    name_path="discover",
    substring_matching=True  # Matches discover_resources, run_discovery, etc.
)
```

### Combining Search Methods
```python
# 1. Find all test files for a service
test_files = search_for_pattern(
    substring_pattern=r"test.*discovery",
    paths_include_glob="**/test_*.py"
)

# 2. Get overview of test structure
for file in test_files:
    get_symbols_overview(relative_path=file)

# 3. Read specific test only
find_symbol(
    name_path="test_discovery_execution",
    relative_path="tests/unit/test_discovery_service.py",
    include_body=True
)
```

### Efficient Import Analysis
```python
# Instead of reading entire file for imports
# Use targeted pattern search
search_for_pattern(
    substring_pattern=r"^(from|import)\s+",
    relative_path="backend/app/services/discovery_service.py",
    context_lines_after=0  # Just the import lines
)
```

## Search Optimization Tips

### 1. Use Glob for File Discovery
```python
# Find all modularized packages
list_dir(
    relative_path="backend/app/services",
    recursive=False
)
# Look for directories with __init__.py

# Find specific file types
find_file(
    file_mask="*.yaml",
    relative_path="backend/config"
)
```

### 2. Leverage LSP Symbol Kinds
```python
# Find only classes (kind=5)
find_symbol(
    name_path="",
    include_kinds=[5],
    relative_path="backend/app/models"
)

# Find only functions (kind=12)
find_symbol(
    name_path="",
    include_kinds=[12],
    relative_path="backend/app/utils"
)
```

### 3. Smart Depth Control
```python
# Get class with all methods (depth=1)
find_symbol(
    name_path="DiscoveryService",
    depth=1,  # Include immediate children
    include_body=False  # Just signatures
)

# Get full hierarchy (depth=2+)
find_symbol(
    name_path="BaseService",
    depth=3,  # Include grandchildren
    include_body=False
)
```

## Common Search Mistakes to Avoid

### ❌ Bad: Reading Entire File First
```python
# WRONG: Wastes tokens
content = read_file("backend/app/services/discovery_service.py")
# Then searching in content
```

### ✅ Good: Symbolic Search First
```python
# RIGHT: Efficient
find_symbol(
    name_path="DiscoveryService/execute_discovery",
    include_body=True
)
```

### ❌ Bad: Broad Pattern Search
```python
# WRONG: Returns too much
search_for_pattern(substring_pattern=r"def")
```

### ✅ Good: Specific Pattern Search
```python
# RIGHT: Targeted
search_for_pattern(
    substring_pattern=r"def execute_discovery",
    restrict_search_to_code_files=True
)
```

### ❌ Bad: Sequential File Reads
```python
# WRONG: Slow and expensive
for file in files:
    read_file(file)
```

### ✅ Good: Parallel Overview
```python
# RIGHT: Fast overview
get_symbols_overview(relative_path="backend/app/services")
```

## Search Decision Tree

```
Need to find something?
├── Know exact symbol name?
│   └── Use find_symbol()
├── Know pattern but not location?
│   └── Use search_for_pattern()
├── Need file structure?
│   └── Use list_dir() or find_file()
├── Need symbol relationships?
│   └── Use find_referencing_symbols()
├── Need high-level understanding?
│   └── Use get_symbols_overview()
└── Last resort: Read specific file
    └── Use read_file() with line limits
```

## Performance Metrics

### Token Efficiency Comparison
- Read entire file (1000 lines): ~5000 tokens
- Get symbols overview: ~500 tokens
- Find specific symbol: ~200 tokens
- Search pattern (5 matches): ~300 tokens

### Speed Comparison
- Full file read: 2-3 seconds
- Symbol search: <1 second
- Pattern search: 1-2 seconds
- Overview: <1 second

## Key Takeaways

1. **Start broad, narrow down**: Overview → Symbol → Body
2. **Use the right tool**: Each search method has its purpose
3. **Combine methods**: Multi-step searches are more efficient
4. **Avoid file reads**: Only when absolutely necessary
5. **Think in symbols**: Not in files or lines
6. **Leverage context**: Use relative_path to narrow scope
7. **Be specific**: Better patterns = fewer results = less tokens
