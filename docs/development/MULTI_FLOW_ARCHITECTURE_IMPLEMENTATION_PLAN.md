# 🚀 Discovery Flow Fresh Architecture Implementation Plan

**Date:** January 27, 2025  
**Priority:** CRITICAL - Discovery Flow Foundation  
**Estimated Timeline:** 10 days  
**Scope:** Discovery Flow only with fresh database architecture

## 🎯 Objective

Implement a clean, unified architecture for the Discovery Flow using fresh database tables while maintaining existing test data during transition. Focus on getting Discovery Flow fully working before touching other flows.

## 📋 Current State & Strategy

### **Current State Reality**
- **Discovery Flow**: Only implemented flow, needs architectural cleanup
- **Other Flows**: UI concepts only, not implemented yet
- **Database**: Disposable test data from seeding scripts
- **CrewAI**: Working integration that should be maintained
- **Priority**: Get Discovery Flow working perfectly first

### **Fresh Start Strategy**
1. **Parallel Development**: Build new tables alongside existing ones
2. **Legacy Marking**: Clearly mark old tables as legacy
3. **Page-by-Page Migration**: Connect Discovery flow pages one at a time
4. **Preserve Test Data**: Keep existing data until switchover
5. **Docker-First**: All development and testing in containers

## 🏗️ Simplified Database Architecture

### **Core Discovery Tables Only**
```python
# Master flow entity - Discovery focused
class DiscoveryFlow(Base):
    __tablename__ = "discovery_flows"
    
    id = Column(UUID, primary_key=True)
    
    # Multi-tenant isolation (reuse demo constants)
    client_account_id = Column(UUID, default="11111111-1111-1111-1111-111111111111")  # Demo Client
    engagement_id = Column(UUID, default="22222222-2222-2222-2222-222222222222")     # Demo Engagement
    user_id = Column(UUID, default="33333333-3333-3333-3333-333333333333")          # Demo User
    
    # Discovery flow state
    current_phase = Column(String(100), default="data_import")
    progress_percentage = Column(Float, default=0.0)
    status = Column(String(20), default="active")  # active, completed, failed
    
    # CrewAI integration
    crewai_flow_id = Column(UUID, index=True)
    
    # Import connection
    import_session_id = Column(UUID, index=True)  # Links to import data
    
    # Discovery results
    raw_data = Column(JSON)              # Imported raw data
    field_mappings = Column(JSON)        # Attribute mapping results
    cleaned_data = Column(JSON)          # Data cleansing results
    asset_inventory = Column(JSON)       # Discovered assets
    dependencies = Column(JSON)          # Dependency analysis
    tech_debt = Column(JSON)             # Tech debt analysis
    
    # Phase completion tracking
    data_import_completed = Column(Boolean, default=False)
    attribute_mapping_completed = Column(Boolean, default=False)
    data_cleansing_completed = Column(Boolean, default=False)
    inventory_completed = Column(Boolean, default=False)
    dependencies_completed = Column(Boolean, default=False)
    tech_debt_completed = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Discovery assets - normalized
class DiscoveryAsset(Base):
    __tablename__ = "discovery_assets"
    
    id = Column(UUID, primary_key=True)
    discovery_flow_id = Column(UUID, ForeignKey('discovery_flows.id'), nullable=False)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID, default="11111111-1111-1111-1111-111111111111")
    engagement_id = Column(UUID, default="22222222-2222-2222-2222-222222222222")
    
    # Asset data
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100))  # server, database, application, etc.
    asset_data = Column(JSON, nullable=False)  # All asset attributes
    
    # Discovery phase tracking
    discovered_in_phase = Column(String(50))  # which phase discovered this asset
    quality_score = Column(Float)
    validation_status = Column(String(20), default="pending")
```

## 📅 Implementation Timeline

### **Phase 1: Fresh Database Foundation (Days 1-3)**

#### **Day 1: Core Tables & Migration Setup**
**Files Created:**
- `backend/app/models/discovery_flow.py`
- `backend/app/models/discovery_asset.py`
- `backend/alembic/versions/[timestamp]_create_discovery_flow_tables.py`

**Tasks:**
- [ ] Create new DiscoveryFlow and DiscoveryAsset models
- [ ] Create Alembic migration for new tables
- [ ] Mark existing tables as legacy in comments
- [ ] Test migration in Docker container

#### **Day 2: Repository & Service Layer**
**Files Created:**
- `backend/app/repositories/discovery_flow_repository.py`
- `backend/app/services/discovery_flow_service.py`

**Repository Pattern:**
```python
class DiscoveryFlowRepository(ContextAwareRepository):
    """Repository for new discovery flow tables"""
    
    async def create_discovery_flow(self, import_session_id: str, crewai_flow_id: str):
        """Create new discovery flow"""
        flow = DiscoveryFlow(
            import_session_id=import_session_id,
            crewai_flow_id=crewai_flow_id,
            current_phase="data_import"
        )
        self.db.add(flow)
        await self.db.commit()
        return flow
    
    async def update_phase_completion(self, flow_id: str, phase: str, data: dict):
        """Update phase completion and store results"""
        flow = await self.get_by_id(flow_id)
        setattr(flow, f"{phase}_completed", True)
        setattr(flow, phase.replace("_", ""), data)  # Store phase data
        await self.db.commit()
        return flow
```

**Tasks:**
- [ ] Create discovery flow repository with CRUD operations
- [ ] Create discovery flow service layer
- [ ] Add proper error handling and validation
- [ ] Test repository operations in Docker

#### **Day 3: Seeding Scripts for New Tables**
**Files Created:**
- `backend/scripts/seed_discovery_flow_tables.py`

**Seeding Strategy:**
```python
# Reuse existing demo constants
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "33333333-3333-3333-3333-333333333333"

async def seed_discovery_flow_data():
    """Seed new tables with test data"""
    # Create sample discovery flows
    # Populate with realistic test data
    # Ensure CrewAI integration works
```

**Tasks:**
- [ ] Create seeding script for new tables
- [ ] Populate with realistic discovery flow test data
- [ ] Validate data in Docker container
- [ ] Document seeding process

### **Phase 2: Discovery Flow Page Migration (Days 4-8)**

#### **Day 4: Data Import Page Migration**
**Files Updated:**
- `src/pages/discovery/DataImport.tsx`
- `backend/app/api/v1/discovery/data_import.py`

**API Updates:**
```python
@router.post("/api/v1/discovery/flows")
async def create_discovery_flow(request: CreateDiscoveryFlowRequest):
    """Create new discovery flow using new tables"""
    # Create in new DiscoveryFlow table
    # Maintain backward compatibility with old endpoints
    # Return flow_id for navigation
```

**Tasks:**
- [ ] Update data import API to use new tables
- [ ] Modify frontend to call new endpoints
- [ ] Test data import with new architecture
- [ ] Validate CrewAI integration still works

#### **Day 5: Attribute Mapping Page Migration**
**Files Updated:**
- `src/pages/discovery/AttributeMapping.tsx`
- `backend/app/api/v1/discovery/attribute_mapping.py`

**Navigation Fix:**
```typescript
// Use discovery_flow_id consistently
const { discovery_flow_id } = useParams();
const { flow, updatePhase } = useDiscoveryFlow(discovery_flow_id);

const handleMappingComplete = async (mappings: any) => {
  await updatePhase('attribute_mapping', mappings);
  // Navigate to next phase
};
```

**Tasks:**
- [ ] Update attribute mapping to use new flow tables
- [ ] Fix navigation to use discovery_flow_id
- [ ] Test field mapping functionality
- [ ] Validate phase progression

#### **Day 6: Data Cleansing Page Migration**
**Files Updated:**
- `src/pages/discovery/DataCleansing.tsx`
- `backend/app/api/v1/discovery/data_cleansing.py`

**Tasks:**
- [ ] Migrate data cleansing to new architecture
- [ ] Test data quality validation
- [ ] Ensure cleaned data stored properly
- [ ] Validate phase completion tracking

#### **Day 7: Inventory & Dependencies Pages**
**Files Updated:**
- `src/pages/discovery/Inventory.tsx`
- `src/pages/discovery/Dependencies.tsx`
- `backend/app/api/v1/discovery/inventory.py`
- `backend/app/api/v1/discovery/dependencies.py`

**Asset Creation:**
```python
async def create_assets_from_discovery(flow_id: str):
    """Create DiscoveryAsset records from flow results"""
    flow = await discovery_repo.get_by_id(flow_id)
    
    for asset_data in flow.asset_inventory:
        asset = DiscoveryAsset(
            discovery_flow_id=flow_id,
            asset_name=asset_data['name'],
            asset_type=asset_data['type'],
            asset_data=asset_data,
            discovered_in_phase='inventory'
        )
        db.add(asset)
```

**Tasks:**
- [ ] Migrate inventory page to new tables
- [ ] Create automatic asset creation from discovery
- [ ] Migrate dependencies page
- [ ] Test asset and dependency creation

#### **Day 8: Tech Debt Page & Flow Completion**
**Files Updated:**
- `src/pages/discovery/TechDebt.tsx`
- `backend/app/api/v1/discovery/tech_debt.py`

**Flow Completion:**
```python
async def complete_discovery_flow(flow_id: str):
    """Mark discovery flow as completed and prepare for assessment"""
    flow = await discovery_repo.get_by_id(flow_id)
    flow.status = "completed"
    flow.progress_percentage = 100.0
    
    # Prepare assessment handoff data
    assessment_package = {
        "assets": await get_discovery_assets(flow_id),
        "summary": create_discovery_summary(flow),
        "ready_for_assessment": True
    }
    
    return assessment_package
```

**Tasks:**
- [ ] Migrate tech debt analysis page
- [ ] Implement flow completion logic
- [ ] Create assessment handoff preparation
- [ ] Test complete discovery flow

### **Phase 3: Testing & Validation (Days 9-10)**

#### **Day 9: End-to-End Testing**
**Files Created:**
- `tests/integration/test_new_discovery_flow.py`

**Complete Flow Test:**
```python
async def test_complete_discovery_flow():
    """Test complete discovery flow with new architecture"""
    # Create discovery flow
    # Execute all phases in sequence
    # Validate data at each step
    # Verify asset creation
    # Test assessment readiness
```

**Tasks:**
- [ ] Create comprehensive integration tests
- [ ] Test complete discovery flow end-to-end
- [ ] Validate all phase transitions
- [ ] Test CrewAI integration throughout

#### **Day 10: Performance & Cleanup**
**Tasks:**
- [ ] Performance testing in Docker containers
- [ ] Database query optimization
- [ ] Clean up any remaining issues
- [ ] Prepare for legacy table removal
- [ ] Document new architecture

## 🧪 Testing Strategy

### **Docker-First Testing**
```bash
# All testing in Docker containers
docker-compose up -d --build
docker-compose exec backend python -m pytest tests/integration/
docker-compose exec frontend npm run test
```

### **Page-by-Page Validation**
- [ ] Test each page individually after migration
- [ ] Validate data flow between pages
- [ ] Ensure CrewAI integration works at each step
- [ ] Test navigation and error handling

### **Legacy Compatibility**
- [ ] Maintain old endpoints during transition
- [ ] Test that old data doesn't interfere
- [ ] Validate clean switchover process

## 🚨 Risk Mitigation

### **Minimal Risk Approach**
- **Parallel Development**: New tables alongside old ones
- **Incremental Migration**: One page at a time
- **Preserve Test Data**: Keep existing data until ready
- **Docker Isolation**: All development in containers

### **Rollback Strategy**
- **Simple Rollback**: Just switch back to old endpoints
- **No Data Loss**: Old tables remain untouched
- **Quick Recovery**: Minimal complexity for rollback

## 📊 Success Criteria

### **Technical Success**
- ✅ Complete Discovery Flow working with new architecture
- ✅ All phases (Data Import → Tech Debt) functional
- ✅ CrewAI integration maintained and working
- ✅ Asset creation automated from discovery results
- ✅ Clean navigation between all discovery phases

### **User Experience Success**
- ✅ Smooth flow progression without errors
- ✅ No "cannot find session" or navigation issues
- ✅ Clear progress indicators throughout
- ✅ Fast page loads and responsive UI

### **Business Success**
- ✅ Discovery Flow ready for production use
- ✅ Foundation for future Assessment Flow development
- ✅ Clean architecture for scaling to other flows
- ✅ Reliable platform for customer demos

## 🔄 Legacy Cleanup Plan

### **After Successful Migration**
1. **Mark Legacy Tables**: Add comments marking old tables as deprecated
2. **Update Documentation**: Document new architecture
3. **Remove Old Endpoints**: Clean up unused API endpoints
4. **Drop Legacy Tables**: After validation period (30 days)

---

**This simplified, focused approach gets Discovery Flow working perfectly with clean architecture, setting the foundation for future flows while minimizing risk and complexity.** 