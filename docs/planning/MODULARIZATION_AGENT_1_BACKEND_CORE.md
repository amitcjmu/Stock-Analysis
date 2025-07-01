# Agent 1: Backend Core Modularization Tasks

## 🎯 Your Mission
Modularize critical backend Python files that exceed 400 lines, focusing on core business logic and CrewAI flows. Your work will improve maintainability and enable parallel development.

## 📋 Assigned Files

### Task 1: Modularize `unified_discovery_flow.py` (1,799 lines) - CRITICAL
**File**: `/backend/app/services/crewai_flows/unified_discovery_flow.py`  
**Current Issues**: 
- Monolithic CrewAI flow with all phases in one file
- Mixed concerns: flow logic, agent coordination, state management
- Difficult to test individual phases

**Modularization Plan**:
```
unified_discovery_flow/
├── __init__.py
├── base_flow.py                    # ~200 lines - Base flow class and common methods
├── flow_config.py                   # ~100 lines - Configuration and constants
├── phases/
│   ├── __init__.py
│   ├── data_validation.py          # ~250 lines - Data validation phase
│   ├── field_mapping.py            # ~250 lines - Field mapping phase
│   ├── data_cleansing.py           # ~250 lines - Data cleansing phase
│   ├── asset_inventory.py          # ~250 lines - Asset inventory phase
│   ├── dependency_analysis.py      # ~250 lines - Dependency analysis
│   └── tech_debt_assessment.py     # ~250 lines - Tech debt phase
├── state_management.py              # ~150 lines - State handling
└── crew_coordination.py             # ~200 lines - Crew orchestration
```

**Implementation Steps**:
1. Create directory structure
2. Extract base flow class with common methods
3. Move each phase (@listen method) to separate file
4. Extract state management logic
5. Create phase orchestrator
6. Update imports in dependent files
7. Ensure all tests pass

### Task 2: Modularize `context.py` (1,447 lines)
**File**: `/backend/app/api/v1/endpoints/context.py`  
**Current Issues**:
- Handles multiple context types in one file
- Mixed REST endpoints with business logic
- Complex multi-tenant logic intertwined with API

**Modularization Plan**:
```
context/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── client_routes.py            # ~200 lines - Client account endpoints
│   ├── engagement_routes.py        # ~200 lines - Engagement endpoints
│   ├── user_routes.py              # ~200 lines - User context endpoints
│   └── admin_routes.py             # ~200 lines - Admin endpoints
├── services/
│   ├── __init__.py
│   ├── client_service.py           # ~200 lines - Client business logic
│   ├── engagement_service.py       # ~200 lines - Engagement logic
│   └── validation_service.py       # ~150 lines - Context validation
└── models/
    ├── __init__.py
    └── context_schemas.py           # ~100 lines - Pydantic schemas
```

**Implementation Steps**:
1. Create context package structure
2. Separate API routes from business logic
3. Extract service layer for each context type
4. Consolidate schemas in one place
5. Update dependency injection
6. Test each module independently

### Task 3: Modularize `flow_management.py` (1,352 lines)
**File**: `/backend/app/api/v1/discovery_handlers/flow_management.py`  
**Current Issues**:
- Massive handler file with all flow operations
- Mixed HTTP handling with complex business logic
- Duplicate code across handlers

**Modularization Plan**:
```
flow_management/
├── __init__.py
├── handlers/
│   ├── __init__.py
│   ├── create_handler.py           # ~200 lines - Flow creation
│   ├── status_handler.py           # ~200 lines - Status operations
│   ├── update_handler.py           # ~200 lines - Flow updates
│   └── delete_handler.py           # ~150 lines - Deletion logic
├── validators/
│   ├── __init__.py
│   ├── flow_validator.py           # ~150 lines - Flow validation
│   └── permission_validator.py     # ~100 lines - Access control
├── services/
│   ├── __init__.py
│   └── flow_service.py             # ~300 lines - Core flow logic
└── utils/
    ├── __init__.py
    └── flow_helpers.py             # ~100 lines - Helper functions
```

### Task 4: Modularize `data_import_repository.py` (819 lines)
**File**: `/backend/app/repositories/data_import_repository.py`  
**Current Issues**:
- Large repository with many query methods
- Complex query building logic mixed with business rules
- Hard to test individual queries

**Modularization Plan**:
```
data_import_repository/
├── __init__.py
├── base_repository.py              # ~150 lines - Base repository class
├── queries/
│   ├── __init__.py
│   ├── import_queries.py           # ~200 lines - Import queries
│   ├── validation_queries.py       # ~150 lines - Validation queries
│   └── analytics_queries.py        # ~150 lines - Analytics queries
├── commands/
│   ├── __init__.py
│   ├── create_commands.py          # ~150 lines - Create operations
│   └── update_commands.py          # ~150 lines - Update operations
└── specifications/
    ├── __init__.py
    └── import_specs.py             # ~100 lines - Query specifications
```

## ✅ Success Criteria

For each file:
1. **No module exceeds 300 lines** (target: 200-250)
2. **All tests pass** without modification
3. **Public interfaces unchanged** (no breaking changes)
4. **Import paths updated** throughout codebase
5. **Documentation added** for module structure

## 🔧 Common Patterns to Apply

### Pattern 1: Separate Handlers from Logic
```python
# Before: Mixed in one file
@router.post("/create")
async def create_flow(data: FlowCreate):
    # 100 lines of validation
    # 100 lines of business logic
    # Database operations
    
# After: Separated
# handler.py
@router.post("/create")
async def create_flow(data: FlowCreate, service: FlowService = Depends()):
    return await service.create_flow(data)

# service.py
class FlowService:
    async def create_flow(self, data: FlowCreate):
        # Business logic here
```

### Pattern 2: Extract Validation
```python
# validators/flow_validator.py
class FlowValidator:
    @staticmethod
    def validate_create(data: FlowCreate) -> None:
        # Validation logic
        
    @staticmethod
    def validate_update(data: FlowUpdate) -> None:
        # Validation logic
```

### Pattern 3: Phase-Based Organization
```python
# phases/data_validation.py
class DataValidationPhase:
    @listen("start_data_validation")
    async def execute(self, state):
        # Phase-specific logic
```

## 📝 Progress Tracking

Update after completing each file:
- [ ] `unified_discovery_flow.py` - Split into 10 modules
- [ ] `context.py` - Split into 8 modules  
- [ ] `flow_management.py` - Split into 9 modules
- [ ] `data_import_repository.py` - Split into 7 modules

## 🚨 Important Notes

1. **Test First**: Run tests before starting to ensure they pass
2. **Incremental Changes**: Commit after each successful extraction
3. **Preserve Behavior**: No functional changes, only restructuring
4. **Update Imports**: Use find/replace for import updates
5. **Document Decisions**: Add README.md to new package directories

## 🔍 Verification Commands

```bash
# Before starting
pytest tests/unit/test_unified_discovery_flow.py -v

# After each extraction
python -m pytest tests/unit/test_[module].py -v

# Check for import errors
python -c "from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow"

# Verify line counts
find app/services/crewai_flows/unified_discovery_flow/ -name "*.py" -exec wc -l {} \;
```

## 💡 Tips for Success

1. **Create the structure first** before moving code
2. **Move tests alongside code** to maintain organization
3. **Use IDE refactoring tools** for safer moves
4. **Keep git commits small** for easy rollback
5. **Ask for review** after first module extraction

---

**Estimated Time**: 3-4 days for all files  
**Priority Order**: 1, 2, 3, 4 (as listed)  
**Risk Level**: Low with proper testing