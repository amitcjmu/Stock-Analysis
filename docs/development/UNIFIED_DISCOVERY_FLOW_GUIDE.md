# 🎯 Unified Discovery Flow - Master Guide

**Version:** 1.0  
**Date:** January 2025  
**Status:** Active  

## 📋 Overview

The Unified Discovery Flow is the single source of truth for all discovery-related functionality in the AI Modernize Migration Platform. This guide consolidates all previous documentation and provides comprehensive guidance for developers working with the discovery flow system.

## 🏗️ Architecture Overview

### **Core Components**

1. **Backend Flow Engine** (`backend/app/services/crewai_flows/unified_discovery_flow.py`)
   - Single CrewAI Flow implementation
   - Manages all discovery phases with proper state persistence
   - Follows official CrewAI Flow documentation patterns

2. **Unified State Model** (`backend/app/models/unified_discovery_flow_state.py`)
   - Comprehensive state management for all discovery phases
   - Multi-tenant support with proper data isolation
   - Real-time progress tracking and error handling

3. **Frontend Integration** (`src/hooks/useUnifiedDiscoveryFlow.ts`)
   - Single React hook for all discovery flow interactions
   - Real-time state synchronization with backend
   - Consistent API across all discovery pages

4. **Database Persistence** (`backend/app/models/workflow_state.py`)
   - Enhanced workflow state model with unified flow support
   - Multi-tenant repository pattern
   - Proper data isolation and context management

## 🔄 Discovery Flow Phases

### **Phase 1: Data Import** ✅ Connected
- **Purpose**: Import CMDB data from various sources
- **Page**: `src/pages/discovery/CMDBImport.tsx`
- **Status**: Fully integrated with unified flow

### **Phase 2: Field Mapping** ✅ Connected  
- **Purpose**: Map imported fields to critical attributes
- **Page**: `src/pages/discovery/AttributeMapping.tsx`
- **Status**: Fully integrated with unified flow

### **Phase 3: Data Cleansing** ✅ Connected
- **Purpose**: Clean and validate imported data
- **Page**: `src/pages/discovery/DataCleansing.tsx`
- **Status**: Recently connected to unified flow

### **Phase 4: Asset Inventory** ✅ Connected
- **Purpose**: Analyze and categorize assets
- **Page**: `src/pages/discovery/AssetInventoryRedesigned.tsx`
- **Status**: Recently connected to unified flow

### **Phase 5: Dependency Analysis** ✅ Connected
- **Purpose**: Analyze asset dependencies and relationships
- **Page**: `src/pages/discovery/DependencyAnalysis.tsx`
- **Status**: Recently connected to unified flow

### **Phase 6: Tech Debt Analysis** ✅ Connected
- **Purpose**: Identify technical debt and end-of-life components
- **Page**: `src/pages/discovery/TechDebtAnalysis.tsx`
- **Status**: Recently connected to unified flow

## 🚀 CrewAI Flow Implementation

### **Flow Class Structure**

```python
@persist()
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    Single Discovery Flow following CrewAI documentation patterns.
    Handles all discovery phases with proper state management.
    """
    
    @start()
    def initialize_discovery(self):
        """Initialize discovery flow with proper state management"""
        self.state.status = "running"
        self.state.current_phase = "initialization"
        return {"status": "initialized", "flow_id": self.state.flow_id}
    
    @listen(initialize_discovery)
    def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping using CrewAI crews"""
        # Implementation details...
        
    @listen(execute_field_mapping_crew)
    def execute_data_cleansing_crew(self, previous_result):
        """Execute data cleansing using CrewAI crews"""
        # Implementation details...
        
    # Additional phases follow the same pattern...
```

### **State Management Patterns**

```python
class UnifiedDiscoveryFlowState(BaseModel):
    """Single source of truth for Discovery Flow state"""
    
    # Core identification
    flow_id: str = ""
    session_id: str = ""
    client_account_id: str = ""
    engagement_id: str = ""
    
    # CrewAI Flow state management
    current_phase: str = "initialization"
    phase_completion: Dict[str, bool] = Field(default_factory=dict)
    crew_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Phase-specific data storage
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    field_mappings: Dict[str, Any] = Field(default_factory=dict)
    cleaned_data: List[Dict[str, Any]] = Field(default_factory=list)
    asset_inventory: Dict[str, Any] = Field(default_factory=dict)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    technical_debt: Dict[str, Any] = Field(default_factory=dict)
```

## 🎨 Frontend Integration

### **Unified Hook Usage**

```typescript
// Single hook for all discovery flow interactions
const {
  flowState,
  isLoading,
  error,
  getPhaseData,
  isPhaseComplete,
  canProceedToPhase,
  executeFlowPhase,
  isExecutingPhase,
  refreshFlow
} = useUnifiedDiscoveryFlow();

// Get phase-specific data
const cleansingData = getPhaseData('data_cleansing');
const isCleansingComplete = isPhaseComplete('data_cleansing');
const canProceedToInventory = canProceedToPhase('asset_inventory');

// Execute flow phases
const handleExecuteCleansing = async () => {
  await executeFlowPhase('data_cleansing');
};
```

### **Page Connection Pattern**

All discovery pages follow the same integration pattern:

1. **Import unified hook**: `import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';`
2. **Get phase data**: `const phaseData = getPhaseData('phase_name');`
3. **Check completion**: `const isComplete = isPhaseComplete('phase_name');`
4. **Execute phase**: `await executeFlowPhase('phase_name');`
5. **Handle navigation**: Use `canProceedToPhase()` for flow-aware navigation

## 🔧 API Endpoints

### **Unified Discovery API** (`/api/v1/unified-discovery/`)

```python
# Flow initialization
POST /api/v1/unified-discovery/flow/initialize
{
  "client_account_id": "string",
  "engagement_id": "string",
  "user_id": "string"
}

# Flow status monitoring
GET /api/v1/unified-discovery/flow/status/{session_id}

# Phase execution
POST /api/v1/unified-discovery/flow/execute/{phase_name}

# Health check
GET /api/v1/unified-discovery/flow/health
```

## 🗄️ Database Schema

### **Enhanced Workflow State Model**

```python
class WorkflowState(Base):
    __tablename__ = 'workflow_states'
    
    # Core identification
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    client_account_id = Column(String, nullable=False)
    engagement_id = Column(String, nullable=False)
    
    # Unified flow state
    unified_flow_state = Column(JSON, nullable=True)
    current_phase = Column(String, default="initialization")
    phase_completion = Column(JSON, default=dict)
    
    # CrewAI Flow integration
    crew_status = Column(JSON, default=dict)
    flow_results = Column(JSON, default=dict)
    
    # Multi-tenant support
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=False)
```

## 🧪 Testing Patterns

### **Backend Testing**

```python
# Test flow execution
def test_unified_discovery_flow_execution():
    flow = UnifiedDiscoveryFlow()
    result = flow.initialize_discovery()
    assert result["status"] == "initialized"
    
# Test state persistence
def test_flow_state_persistence():
    state = UnifiedDiscoveryFlowState(flow_id="test-123")
    # Test state operations...
```

### **Frontend Testing**

```typescript
// Test hook integration
describe('useUnifiedDiscoveryFlow', () => {
  it('should fetch flow state correctly', async () => {
    const { result } = renderHook(() => useUnifiedDiscoveryFlow());
    // Test hook behavior...
  });
});
```

## 🚨 Error Handling

### **Backend Error Patterns**

```python
# Graceful degradation
try:
    crew_result = await execute_crew(crew_name)
    self.state.crew_status[crew_name] = {"status": "completed"}
except Exception as e:
    self.state.crew_status[crew_name] = {"status": "failed", "error": str(e)}
    # Continue with fallback logic
```

### **Frontend Error Patterns**

```typescript
// Consistent error handling
const handleExecutePhase = async (phase: string) => {
  try {
    await executeFlowPhase(phase);
    toast({ title: 'Success', description: `${phase} started successfully.` });
  } catch (error) {
    toast({ 
      title: 'Error', 
      description: `Failed to start ${phase}. Please try again.`,
      variant: 'destructive'
    });
  }
};
```

## 📊 Monitoring and Observability

### **Flow Monitoring**

- **Real-time status updates**: WebSocket connections for live progress
- **Phase completion tracking**: Detailed progress metrics per phase
- **Crew status monitoring**: Individual crew execution status
- **Error tracking**: Comprehensive error logging and recovery

### **Performance Metrics**

- **Flow execution time**: End-to-end discovery flow duration
- **Phase completion rates**: Success rates per discovery phase
- **Crew performance**: Individual crew execution metrics
- **Data quality scores**: Quality improvements through the flow

## 🔄 Migration Guide

### **From Legacy Implementations**

If you're migrating from old discovery implementations:

1. **Replace old hooks**: Remove `useDiscoveryFlowState` and individual phase hooks
2. **Update imports**: Use `useUnifiedDiscoveryFlow` instead
3. **Update data access**: Use `getPhaseData()` instead of direct state access
4. **Update navigation**: Use `canProceedToPhase()` for flow-aware navigation
5. **Update error handling**: Use consistent error patterns

### **Breaking Changes**

- **State structure**: New unified state model replaces old schemas
- **API endpoints**: New unified endpoints replace old discovery endpoints
- **Hook interface**: New hook interface replaces multiple competing hooks
- **Navigation patterns**: Flow-aware navigation replaces independent page navigation

## 🎯 Best Practices

### **Development Guidelines**

1. **Always use unified hook**: Never bypass the unified flow system
2. **Respect phase order**: Don't skip phases or break flow sequence
3. **Handle errors gracefully**: Implement proper error recovery
4. **Use flow-aware navigation**: Check phase completion before navigation
5. **Follow state patterns**: Use provided state access methods

### **Performance Optimization**

1. **Lazy loading**: Load phase data only when needed
2. **Caching**: Use React Query caching for flow state
3. **Real-time updates**: Use WebSocket for live status updates
4. **Background execution**: Use background tasks for long-running crews

## 📚 Additional Resources

### **Related Documentation**

- **CrewAI Flow Documentation**: https://docs.crewai.com/guides/flows/
- **Platform Architecture Summary**: `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md`
- **Consolidation Plan**: `docs/development/UNIFIED_DISCOVERY_FLOW_CONSOLIDATION_PLAN.md`

### **Code Examples**

- **Backend Flow**: `backend/app/services/crewai_flows/unified_discovery_flow.py`
- **Frontend Hook**: `src/hooks/useUnifiedDiscoveryFlow.ts`
- **Page Integration**: `src/pages/discovery/DataCleansing.tsx`

### **Testing Examples**

- **Backend Tests**: `tests/backend/flows/test_discovery_flow_sequence.py`
- **Frontend Tests**: `tests/frontend/discovery/`

---

## 🏁 Conclusion

The Unified Discovery Flow represents a complete consolidation of all discovery-related functionality into a single, maintainable, and properly documented system. By following this guide, developers can:

- **Understand the complete architecture** and how all components work together
- **Implement new features** using established patterns and best practices
- **Maintain and extend** the system with confidence
- **Debug and troubleshoot** issues effectively
- **Ensure consistency** across all discovery-related functionality

This unified approach eliminates code duplication, reduces maintenance overhead, and provides a solid foundation for future enhancements to the discovery flow system. 