# Agent Service Layer Implementation Roadmap

## Executive Summary

This roadmap outlines the transition from HTTP-based agent communication to a direct service layer architecture, eliminating mock data confusion and improving agent reliability.

## Current State Analysis

### Problems with Current Architecture
1. **Mock Data Confusion**: Endpoints return demo data when real data doesn't exist
2. **HTTP Complexity**: Agents struggle with async HTTP calls and authentication
3. **Performance Issues**: Unnecessary network overhead for in-container calls
4. **Context Loss**: Multi-tenant context gets lost in HTTP translations

### Affected Components
- `/backend/app/services/agents/intelligent_flow_agent.py`
- `/backend/app/services/agents/flow_processing/tools/*.py`
- `/backend/app/services/crewai_flows/tools/*.py`
- All CrewAI agent implementations

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Establish core service layer infrastructure

**Tasks**:
- [x] Create `AgentServiceLayer` base class
- [x] Implement async-to-sync conversion pattern
- [x] Add multi-tenant context handling
- [ ] Set up comprehensive error handling
- [ ] Add performance monitoring/logging
- [ ] Create unit test framework

**Deliverables**:
- Working service layer with 2-3 example methods
- Unit tests with 80% coverage
- Performance benchmarks

### Phase 2: Flow Management (Week 2)
**Goal**: Replace flow-related HTTP calls

**Priority Methods**:
```python
get_flow_status(flow_id: str) -> Dict[str, Any]
get_active_flows() -> List[Dict[str, Any]]
validate_phase_transition(flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]
get_phase_requirements(phase: str) -> Dict[str, Any]
update_flow_progress(flow_id: str, phase: str, data: Dict) -> Dict[str, Any]
```

**Migration Targets**:
- `FlowContextTool` in intelligent_flow_agent.py
- `FlowStatusAnalyzer` tool
- `NavigationDecisionMaker` tool

### Phase 3: Data Services (Week 3)
**Goal**: Handle data import and mapping operations

**Priority Methods**:
```python
get_import_data(flow_id: str, limit: int = None) -> Dict[str, Any]
get_field_mappings(flow_id: str) -> Dict[str, Any]
validate_mappings(flow_id: str, mappings: Dict) -> Dict[str, Any]
get_cleansing_results(flow_id: str) -> Dict[str, Any]
get_validation_issues(flow_id: str) -> List[Dict[str, Any]]
```

**Migration Targets**:
- Field mapping crews
- Data cleansing tools
- Import validation tools

### Phase 4: Asset Services (Week 4)
**Goal**: Asset discovery and analysis

**Priority Methods**:
```python
get_discovered_assets(flow_id: str, asset_type: str = None) -> List[Dict[str, Any]]
get_asset_dependencies(flow_id: str) -> Dict[str, Any]
get_tech_debt_analysis(flow_id: str) -> Dict[str, Any]
validate_asset_data(asset_id: str) -> Dict[str, Any]
get_asset_relationships(asset_id: str) -> Dict[str, Any]
```

**Migration Targets**:
- Asset discovery crews
- Dependency analysis tools
- Tech debt assessment tools

### Phase 5: Agent Learning (Week 5)
**Goal**: Implement learning and pattern recognition

**Priority Methods**:
```python
record_agent_decision(decision_type: str, context: Dict, outcome: Dict) -> bool
get_similar_patterns(context: Dict, limit: int = 5) -> List[Dict[str, Any]]
get_recommendations(scenario: str, context: Dict) -> List[Dict[str, Any]]
update_confidence_scores(pattern_id: str, success: bool) -> Dict[str, Any]
```

## Migration Process

### Step-by-Step Migration Guide

#### 1. Identify HTTP Calls
```bash
# Find all HTTP usage in agents
find backend/app/services/agents -name "*.py" -exec grep -l "requests\|aiohttp\|httpx\|http://" {} \;
```

#### 2. Create Service Method
```python
# For each HTTP endpoint, create equivalent service method
# Example: GET /api/v1/flow/{id}/status
def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
    """Direct replacement for HTTP endpoint"""
    try:
        future = self.executor.submit(asyncio.run, self._async_get_flow_status(flow_id))
        return future.result(timeout=30)
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

#### 3. Update Agent Tool
```python
# Before
response = requests.get(f"http://localhost/api/v1/flow/{flow_id}")
data = response.json()

# After  
service = get_agent_service(client_id, engagement_id)
data = service.get_flow_status(flow_id)
```

#### 4. Remove Mock Data Logic
- Identify endpoints with fallback/demo data
- Ensure service methods return only real data
- Add clear "not_found" states

## Testing Strategy

### Unit Tests (Per Method)
```python
def test_get_flow_status_not_found():
    """Test handling of non-existent flows"""
    service = AgentServiceLayer("test-client", "test-engagement")
    result = service.get_flow_status("non-existent")
    
    assert result["status"] == "not_found"
    assert result["flow_exists"] is False
    assert "upload data" in result.get("guidance", "")
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_flow_lifecycle():
    """Test complete flow from creation to completion"""
    # Create flow
    # Update phases
    # Validate transitions
    # Check final state
```

### Performance Tests
```python
def test_service_performance():
    """Ensure service calls complete within SLA"""
    service = AgentServiceLayer("test", "test")
    
    start = time.time()
    result = service.get_flow_status("test-id")
    duration = time.time() - start
    
    assert duration < 1.0  # Should complete in under 1 second
```

## Rollback Plan

### Gradual Migration
1. Keep HTTP endpoints active during migration
2. Add feature flags for service layer usage
3. Monitor both paths for issues
4. Gradually increase service layer traffic
5. Deprecate HTTP endpoints after validation

### Rollback Triggers
- Error rate > 5%
- Response time > 2x baseline
- Agent task completion rate drops
- Critical bug discovered

## Success Metrics

### Technical Metrics
- **Response Time**: < 100ms p95 (from ~500ms HTTP)
- **Error Rate**: < 0.1% (from ~2% with network issues)
- **Code Coverage**: > 80% for service layer
- **Agent Success Rate**: > 95% task completion

### Business Metrics
- **Agent Efficiency**: 50% faster flow processing
- **Data Quality**: No mock data confusion
- **Developer Velocity**: Easier debugging and testing
- **System Reliability**: Fewer timeout/network errors

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Foundation | Core service layer, error handling, monitoring |
| 2 | Flow Management | 5 flow methods, migrate 3 agent tools |
| 3 | Data Services | 5 data methods, migrate import/mapping tools |
| 4 | Asset Services | 5 asset methods, migrate discovery tools |
| 5 | Agent Learning | 4 learning methods, pattern recognition |
| 6 | Testing & Rollout | Full test suite, gradual production rollout |

## Risk Mitigation

### Technical Risks
1. **Threading Issues**: Use single ThreadPoolExecutor per service
2. **Memory Leaks**: Implement proper cleanup in `__del__`
3. **Database Connections**: Use connection pooling
4. **Context Confusion**: Validate context on every call

### Operational Risks
1. **Migration Errors**: Comprehensive test coverage
2. **Performance Regression**: Continuous monitoring
3. **Agent Failures**: Gradual rollout with fallbacks
4. **Knowledge Gap**: Team training sessions

## Next Steps

1. **Immediate Actions**:
   - Complete Phase 1 error handling
   - Set up monitoring infrastructure
   - Create first integration test

2. **This Week**:
   - Implement 3 core flow methods
   - Migrate FlowContextTool
   - Establish performance baseline

3. **Communication**:
   - Team briefing on new architecture
   - Update agent development guidelines
   - Create troubleshooting guide