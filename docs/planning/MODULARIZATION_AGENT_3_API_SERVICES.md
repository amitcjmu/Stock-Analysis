# Agent 3: API & Services Modularization Tasks

## 🎯 Your Mission
Modularize API endpoints and service layers that exceed 400 lines, focusing on separating HTTP handling from business logic, creating reusable service modules, and improving testability.

## 📋 Assigned Files

### Task 1: Modularize `field_mapping.py` (1,698 lines) - CRITICAL
**File**: `/backend/app/api/v1/endpoints/data_import/field_mapping.py`  
**Current Issues**:
- Massive endpoint file mixing HTTP, validation, and business logic
- Complex mapping algorithms embedded in route handlers
- Duplicate code across different mapping endpoints
- Agent integration mixed with API logic

**Modularization Plan**:
```
field_mapping/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── mapping_routes.py           # ~200 lines - HTTP route definitions
│   ├── validation_routes.py        # ~150 lines - Validation endpoints
│   ├── suggestion_routes.py        # ~150 lines - AI suggestion endpoints
│   └── approval_routes.py          # ~150 lines - Approval workflow
├── services/
│   ├── __init__.py
│   ├── mapping_service.py          # ~250 lines - Core mapping logic
│   ├── validation_service.py       # ~200 lines - Validation logic
│   ├── suggestion_service.py       # ~200 lines - AI suggestions
│   └── transformation_service.py   # ~200 lines - Data transformation
├── validators/
│   ├── __init__.py
│   ├── field_validators.py         # ~150 lines - Field validation
│   └── mapping_validators.py       # ~150 lines - Mapping rules
├── models/
│   ├── __init__.py
│   └── mapping_schemas.py          # ~100 lines - Pydantic models
└── utils/
    ├── __init__.py
    ├── mapping_helpers.py           # ~100 lines - Helper functions
    └── type_inference.py            # ~100 lines - Type detection
```

**Implementation Steps**:
1. Extract Pydantic schemas to models directory
2. Create service layer for business logic
3. Separate route handlers from logic
4. Extract validation to dedicated modules
5. Create transformation service
6. Update dependency injection
7. Ensure backward compatibility

### Task 2: Modularize `agentic_critical_attributes.py` (1,289 lines)
**File**: `/backend/app/api/v1/endpoints/data_import/agentic_critical_attributes.py`  
**Current Issues**:
- Agent communication mixed with API endpoints
- Complex attribute analysis in route handlers
- CrewAI integration tightly coupled
- Hard to test agent logic independently

**Modularization Plan**:
```
agentic_critical_attributes/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── analysis_routes.py          # ~150 lines - Analysis endpoints
│   ├── suggestion_routes.py        # ~150 lines - Suggestion endpoints
│   └── feedback_routes.py          # ~100 lines - Feedback handling
├── services/
│   ├── __init__.py
│   ├── attribute_analyzer.py       # ~200 lines - Analysis logic
│   ├── agent_coordinator.py        # ~200 lines - Agent orchestration
│   └── learning_service.py         # ~150 lines - ML feedback loop
├── agents/
│   ├── __init__.py
│   ├── critical_attribute_agent.py # ~200 lines - Main agent
│   ├── validation_agent.py         # ~150 lines - Validation agent
│   └── suggestion_agent.py         # ~150 lines - Suggestion agent
├── models/
│   ├── __init__.py
│   └── attribute_schemas.py        # ~100 lines - Data models
└── utils/
    └── attribute_helpers.py         # ~100 lines - Utilities
```

### Task 3: Modularize `unified_discovery.py` (966 lines)
**File**: `/backend/app/api/v1/unified_discovery.py`  
**Current Issues**:
- All discovery endpoints in single file
- Mixed v1/v3 compatibility code
- Complex flow orchestration in endpoints
- WebSocket and REST mixed together

**Modularization Plan**:
```
unified_discovery/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── flow_routes.py              # ~150 lines - Flow management
│   ├── import_routes.py            # ~150 lines - Import endpoints
│   ├── status_routes.py            # ~150 lines - Status/monitoring
│   └── websocket_routes.py         # ~150 lines - WebSocket handlers
├── services/
│   ├── __init__.py
│   ├── discovery_orchestrator.py   # ~200 lines - Main orchestration
│   ├── flow_coordinator.py         # ~150 lines - Flow coordination
│   └── compatibility_service.py    # ~100 lines - v1/v3 bridge
└── middleware/
    ├── __init__.py
    └── discovery_middleware.py      # ~100 lines - Request processing
```

### Task 4: Modularize `assessment_flow_service.py` (682 lines)
**File**: `/backend/app/services/assessment_flow_service.py`  
**Current Issues**:
- Service mixing multiple assessment types
- Database operations mixed with business logic
- Complex scoring algorithms in single file
- Agent integration scattered throughout

**Modularization Plan**:
```
assessment_flow_service/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── assessment_manager.py       # ~150 lines - Main manager
│   └── flow_coordinator.py         # ~100 lines - Flow coordination
├── assessors/
│   ├── __init__.py
│   ├── risk_assessor.py            # ~150 lines - Risk assessment
│   ├── complexity_assessor.py      # ~150 lines - Complexity scoring
│   └── readiness_assessor.py       # ~150 lines - Readiness check
├── repositories/
│   ├── __init__.py
│   └── assessment_repository.py    # ~150 lines - Data access
└── models/
    └── assessment_models.py         # ~100 lines - Domain models
```

### Task 5: Modularize `discovery_service.py` (524 lines)
**File**: `/backend/app/services/discovery_service.py`  
**Current Issues**:
- Generic service handling too many concerns
- Mixed synchronous and asynchronous operations
- Caching logic intertwined with business logic

**Modularization Plan**:
```
discovery_service/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── discovery_manager.py        # ~100 lines - Main interface
│   └── discovery_cache.py          # ~100 lines - Caching layer
├── operations/
│   ├── __init__.py
│   ├── data_operations.py          # ~100 lines - Data handling
│   ├── validation_operations.py    # ~100 lines - Validation
│   └── transformation_ops.py       # ~100 lines - Transformations
└── integrations/
    ├── __init__.py
    └── external_integrations.py     # ~100 lines - External APIs
```

### Task 6: Modularize `agent_service_layer.py` (459 lines)
**File**: `/backend/app/services/agent_service_layer.py`  
**Current Issues**:
- Central agent coordination getting complex
- Mixed CrewAI and custom agent logic
- Performance monitoring mixed with execution

**Modularization Plan**:
```
agent_service_layer/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── agent_manager.py            # ~100 lines - Agent lifecycle
│   └── agent_registry.py           # ~80 lines - Agent registry
├── execution/
│   ├── __init__.py
│   ├── agent_executor.py           # ~100 lines - Execution engine
│   └── task_scheduler.py           # ~80 lines - Task scheduling
├── monitoring/
│   ├── __init__.py
│   └── agent_monitor.py            # ~100 lines - Performance monitoring
└── communication/
    └── agent_messenger.py           # ~80 lines - Inter-agent comm
```

## ✅ Success Criteria

For each module:
1. **No file exceeds 300 lines** (target: 150-250)
2. **Clear separation** between HTTP and business logic
3. **Services are framework-agnostic**
4. **100% backward compatibility** maintained
5. **API documentation** updated

## 🔧 Common Patterns to Apply

### Pattern 1: Thin Route Handlers
```python
# routes/mapping_routes.py
@router.post("/mappings")
async def create_mapping(
    data: MappingCreate,
    service: MappingService = Depends(get_mapping_service)
):
    """Thin handler - delegates to service"""
    return await service.create_mapping(data)

# services/mapping_service.py
class MappingService:
    async def create_mapping(self, data: MappingCreate):
        """Business logic here"""
        validated = await self.validator.validate(data)
        transformed = await self.transformer.transform(validated)
        return await self.repository.save(transformed)
```

### Pattern 2: Service Layer Abstraction
```python
# services/discovery_orchestrator.py
class DiscoveryOrchestrator:
    def __init__(
        self,
        flow_service: FlowService,
        import_service: ImportService,
        agent_service: AgentService
    ):
        self.flow = flow_service
        self.import = import_service
        self.agent = agent_service
    
    async def start_discovery(self, config: DiscoveryConfig):
        """Orchestrates multiple services"""
        flow = await self.flow.create(config)
        import_job = await self.import.start(flow.id)
        await self.agent.process(import_job)
        return flow
```

### Pattern 3: Repository Pattern
```python
# repositories/assessment_repository.py
class AssessmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save_assessment(self, assessment: Assessment):
        """Pure data access - no business logic"""
        self.db.add(assessment)
        await self.db.commit()
        return assessment
```

## 📝 Progress Tracking

Update after completing each file:
- [ ] `field_mapping.py` - Split into 12 modules
- [ ] `agentic_critical_attributes.py` - Split into 10 modules
- [ ] `unified_discovery.py` - Split into 7 modules
- [ ] `assessment_flow_service.py` - Split into 7 modules
- [ ] `discovery_service.py` - Split into 6 modules
- [ ] `agent_service_layer.py` - Split into 6 modules

## 🚨 Important Notes

1. **Maintain API Contracts**: No breaking changes to endpoints
2. **Preserve Dependencies**: Update injection properly
3. **Keep Transaction Boundaries**: Database transactions intact
4. **Update OpenAPI Docs**: Swagger documentation current
5. **Test API Compatibility**: Integration tests must pass

## 🔍 Verification Commands

```bash
# Run API tests
pytest tests/api/v1/test_field_mapping.py -v

# Check endpoint availability
curl http://localhost:8000/api/v1/field-mapping/health

# Verify service injection
python -c "from app.services.field_mapping import MappingService; print('OK')"

# OpenAPI schema validation
python -m app.main --validate-openapi

# Load testing for performance
locust -f tests/load/api_endpoints.py
```

## 💡 Tips for Success

1. **Start with schemas** - Extract models first
2. **Create services before routes** - Logic before HTTP
3. **Use dependency injection** - FastAPI Depends()
4. **Keep transactions in services** - Not in routes
5. **Document service interfaces** - Clear contracts

---

**Estimated Time**: 3-4 days for all files  
**Priority Order**: 1, 2, 3, 4, 5, 6 (as listed)  
**Risk Level**: Medium (API changes affect clients)