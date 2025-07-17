# 📋 **LEGACY CODE CLEANUP MANIFEST**

*AI Modernize Migration Platform - Discovery Flow Remediation*

**Manifest Date:** January 2025  
**Scope:** File-by-file legacy cleanup action plan  
**Total Files Affected:** 147 files across 6 legacy categories  

---

## **📊 CLEANUP SUMMARY**

| Category | Files | Lines of Code | Priority | Risk Level |
|----------|-------|---------------|----------|------------|
| Session ID References | 79 | ~15,000 | 🔴 Critical | High |
| Pseudo-Agent Architecture | 8 | ~3,500 | 🔴 Critical | High |
| Legacy API Patterns | 25 | ~8,000 | 🟡 High | Medium |
| Broken Imports | 12 | ~2,000 | 🔴 Critical | High |
| Legacy Files (*_legacy.py) | 8 | ~4,000 | 🟡 High | Low |
| Documentation/Comments | 35+ | ~1,500 | 🟢 Medium | Low |
| **TOTAL** | **147** | **~34,000** | | |

---

## **🗂️ CATEGORY 1: SESSION ID REFERENCES**

### **🔴 CRITICAL - Database Schema (5 files)**

#### **File: `alembic/versions/remove_session_id_final_cleanup.py`**
- **Action**: Execute migration
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: High - Database integrity
- **Lines**: 49 lines
- **Dependencies**: None (migration script)
- **Command**: `alembic upgrade remove_session_id_cleanup`
- **Backup Required**: Yes - Full database backup
- **Testing**: Staging environment first

#### **File: `app/models/data_import_session.py`**
- **Action**: Update to remove `parent_session_id` column reference
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: High - Model integrity
- **Lines**: 73 lines affected
- **Dependencies**: Data import flows
- **Changes Required**:
  ```python
  # REMOVE:
  parent_session_id: str = Column(String, nullable=True)
  # UPDATE foreign key relationships to use flow_id
  ```

#### **File: `app/models/asset.py`**
- **Action**: Remove session_id comments and references
- **Priority**: 🟡 High (Week 2)
- **Risk**: Low - Comment cleanup only
- **Lines**: 91 lines (comments only)
- **Dependencies**: None
- **Changes Required**: Update migration comments

### **🔴 CRITICAL - Active Service Logic (12 files)**

#### **File: `app/services/data_import_validation_service.py`**
- **Action**: Migrate from session-based to flow-based validation
- **Priority**: 🔴 Critical (Week 2)
- **Risk**: High - Active validation logic
- **Lines**: ~200 lines affected
- **Dependencies**: Data import handlers, file validation
- **Changes Required**:
  ```python
  # REPLACE:
  def validate_session_data(session_id: str)
  # WITH:
  def validate_flow_data(flow_id: str)
  
  # UPDATE file storage paths from session-based to flow-based
  ```

#### **File: `app/utils/session_manager.py`**
- **Action**: Remove entire file or convert to flow manager
- **Priority**: 🔴 Critical (Week 2)
- **Risk**: High - Core session functionality
- **Lines**: ~150 lines
- **Dependencies**: Multiple services reference this
- **Decision Required**: Remove vs Convert
- **Alternative**: Create `flow_manager.py` with equivalent functionality

#### **File: `app/services/crewai_flows/event_listeners/discovery_flow_listener.py`**
- **Action**: Remove session_id fallback logic
- **Priority**: 🟡 High (Week 3)
- **Risk**: Medium - Event handling
- **Lines**: ~50 lines affected
- **Dependencies**: CrewAI flow events
- **Changes Required**:
  ```python
  # REMOVE session_id fallback patterns
  # UPDATE to use flow_id exclusively
  ```

#### **File: `app/services/migration/session_to_flow.py`**
- **Action**: KEEP as compatibility service
- **Priority**: 🟢 Low (Keep)
- **Risk**: Low - Compatibility layer
- **Lines**: 284 lines
- **Dependencies**: Migration scenarios
- **Rationale**: Needed for emergency rollback scenarios

### **🟡 HIGH - API Handlers (15 files)**

#### **File: `app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`**
- **Action**: Remove `validation_session_id` usage
- **Priority**: 🟡 High (Week 2)
- **Risk**: Medium - Import processing
- **Lines**: ~100 lines affected (9 references)
- **Dependencies**: Data import validation
- **Changes Required**:
  ```python
  # REPLACE:
  validation_session_id: str
  # WITH:
  validation_flow_id: str
  ```

#### **File: `app/schemas/data_import_schemas.py`**
- **Action**: Remove legacy session_id fields
- **Priority**: 🟡 High (Week 2)
- **Risk**: Medium - API contracts
- **Lines**: ~30 lines affected
- **Dependencies**: Frontend API calls
- **Changes Required**: Update Pydantic models

#### **File: `app/schemas/auth_schemas.py`**
- **Action**: Remove optional session_id field
- **Priority**: 🟢 Medium (Week 3)
- **Risk**: Low - Optional field only
- **Lines**: 5 lines
- **Dependencies**: Authentication flows

---

## **🗂️ CATEGORY 2: PSEUDO-AGENT ARCHITECTURE**

### **🔴 CRITICAL - Agent Conversions (5 files)**

#### **File: `app/services/agents/data_import_validation_agent.py`**
- **Action**: Convert from pseudo-agent to CrewAI agent
- **Priority**: 🔴 Critical (Week 3)
- **Risk**: High - Business logic accuracy
- **Lines**: ~200 lines
- **Dependencies**: Data import flows, validation logic
- **Conversion Requirements**:
  ```python
  # CURRENT: Pseudo-agent pattern
  class DataImportValidationAgent(BaseDiscoveryAgent):
      def execute(self, data) -> AgentResult:
  
  # TARGET: CrewAI pattern  
  class DataImportValidationAgent(Agent):
      @tool
      def validate_import_data(self, data):
  ```
- **Testing Required**: Parallel validation of outputs

#### **File: `app/services/agents/attribute_mapping_agent.py`**
- **Action**: Convert from pseudo-agent to CrewAI agent
- **Priority**: 🔴 Critical (Week 3)
- **Risk**: High - Field mapping accuracy
- **Lines**: ~180 lines
- **Dependencies**: Field mapping UI, schema analysis
- **Business Logic**: Complex attribute matching rules
- **Testing Required**: A/B testing against current logic

#### **File: `app/services/agents/tech_debt_analysis_agent.py`**
- **Action**: Convert from pseudo-agent to CrewAI agent
- **Priority**: 🔴 Critical (Week 4)
- **Risk**: High - Technical debt scoring
- **Lines**: ~220 lines
- **Dependencies**: Asset analysis, modernization recommendations
- **Testing Required**: Scoring accuracy validation

#### **File: `app/services/agents/dependency_analysis_agent.py`**
- **Action**: Convert from pseudo-agent to CrewAI agent
- **Priority**: 🔴 Critical (Week 4)
- **Risk**: High - Dependency mapping
- **Lines**: ~190 lines
- **Dependencies**: Asset relationships, topology analysis
- **Testing Required**: Dependency graph validation

### **🟡 HIGH - Dual Implementation Cleanup (3 files)**

#### **File: `app/services/agents/data_cleansing_agent.py`**
- **Action**: DELETE (keep CrewAI version only)
- **Priority**: 🟡 High (Week 3)
- **Risk**: Low - CrewAI version already exists
- **Lines**: 158 lines
- **Dependencies**: Check for any remaining references
- **Alternative**: `app/services/agents/data_cleansing_agent_crewai.py`

#### **File: `app/services/agents/asset_inventory_agent.py`**
- **Action**: DELETE (keep CrewAI version only)
- **Priority**: 🟡 High (Week 3)
- **Risk**: Low - CrewAI version already exists
- **Lines**: ~150 lines
- **Dependencies**: Asset inventory flows
- **Alternative**: `app/services/agents/asset_inventory_agent_crewai.py`

#### **File: `app/services/agents/base_discovery_agent.py`**
- **Action**: DELETE after all conversions complete
- **Priority**: 🟢 Medium (Week 4)
- **Risk**: Medium - Base class for multiple agents
- **Lines**: ~100 lines
- **Dependencies**: All pseudo-agents inherit from this
- **Prerequisite**: Convert all child agents first

---

## **🗂️ CATEGORY 3: LEGACY API PATTERNS**

### **🔴 CRITICAL - Legacy File Removal (4 files)**

#### **File: `app/api/v1/admin/session_comparison_original.py`**
- **Action**: DELETE immediately
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: Zero - No dependencies found
- **Lines**: 713 lines
- **Dependencies**: None (session-based comparison service not used)
- **Verification**: Confirmed no imports in codebase
- **Command**: `rm app/api/v1/admin/session_comparison_original.py`

#### **File: `app/utils/vector_utils_old.py`**
- **Action**: DELETE immediately
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: Zero - Replaced by stubbed version
- **Lines**: 317 lines
- **Dependencies**: None (references removed)
- **Alternative**: `app/utils/vector_utils.py` (stubbed version)
- **Command**: `rm app/utils/vector_utils_old.py`

### **🟡 HIGH - API Consolidation (21 files)**

#### **Directory: `/app/api/v2/`**
- **Action**: DELETE empty directory
- **Priority**: 🟡 High (Week 2)
- **Risk**: Low - Contains only `__init__.py`
- **Lines**: 1 line
- **Dependencies**: Check for any v2 imports in test files
- **Command**: `rm -rf app/api/v2/`

#### **File: `app/api/v1/api.py`**
- **Action**: Clean up v2 references and comments
- **Priority**: 🟡 High (Week 2)
- **Risk**: Low - Comment and import cleanup
- **Lines**: ~50 lines affected (comments about v2)
- **Dependencies**: Router configuration
- **Changes Required**: Remove v2 import attempts

---

## **🗂️ CATEGORY 4: BROKEN IMPORTS & MISSING MODELS**

### **🔴 CRITICAL - Missing Model Resolution (3 models)**

#### **Model: `MappingLearningPattern`**
- **Referenced In**: 7 files
- **Action Decision Required**: Restore vs Remove
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: High - Vector functionality affected
- **Files Affected**:
  - `app/services/agent_learning_system.py` (line 19 - commented)
  - `app/services/embedding_service.py` (line 23 - commented)  
  - `app/utils/vector_utils.py` (stubbed methods)
  - `app/utils/vector_utils_old.py` (DELETE)

**Option 1: Restore Model**
```python
# Recreate model in app/models/learning_patterns.py
class MappingLearningPattern(Base):
    __tablename__ = "mapping_learning_patterns"
    # ... field definitions
```

**Option 2: Complete Removal**
```python
# Remove all references and keep stubbed functionality
# Pros: Cleaner architecture
# Cons: Loss of pattern learning capability
```

#### **Model: `AssetClassificationPattern`**
- **Referenced In**: 3 files
- **Action**: Remove references (unused)
- **Priority**: 🟡 High (Week 2)
- **Risk**: Low - Not actively used
- **Files Affected**:
  - `app/services/agent_learning_system.py` (line 1043)
  - `app/services/embedding_service.py` (line 24 - commented)

#### **Model: `User`**
- **Referenced In**: 5 files
- **Action**: Update context management to handle gracefully
- **Priority**: 🟡 High (Week 2)
- **Risk**: Medium - Context management
- **Files Affected**:
  - `app/core/context.py` (line 39 - has try/except handling)

### **🟡 HIGH - Import Chain Repair (9 files)**

#### **File: `app/services/agent_learning_system.py`**
- **Action**: Fix missing imports and restore functionality
- **Priority**: 🟡 High (Week 2)
- **Risk**: Medium - Learning system functionality
- **Lines**: Multiple import issues
- **Issues**:
  - Missing `AsyncSessionLocal` import (line 1042)
  - Commented out `MappingLearningPattern` import (line 19)
  - Commented out `AssetClassificationPattern` import (line 1043)

---

## **🗂️ CATEGORY 5: LEGACY FILES WITH SUFFIXES**

### **🔴 CRITICAL - Immediate Removal (4 files)**

#### **File: `app/api/v1/endpoints/data_import/field_mapping_legacy.py`**
- **Action**: DELETE immediately
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: Zero - No dependencies
- **Lines**: 1,702 lines
- **Dependencies**: None found
- **Verification**: No imports detected
- **Command**: `rm app/api/v1/endpoints/data_import/field_mapping_legacy.py`

#### **File: `app/api/v1/endpoints/data_import/agentic_critical_attributes_legacy.py`**
- **Action**: DELETE immediately  
- **Priority**: 🔴 Critical (Week 1)
- **Risk**: Zero - No dependencies
- **Lines**: 1,290 lines
- **Dependencies**: None found
- **Command**: `rm app/api/v1/endpoints/data_import/agentic_critical_attributes_legacy.py`

### **🟡 HIGH - Review Required (4 files)**

#### **File: `app/services/discovery_flow_cleanup_service_v2.py`**
- **Action**: Review for active usage before removal
- **Priority**: 🟡 High (Week 2)
- **Risk**: Medium - May have cleanup logic
- **Lines**: ~200 lines
- **Dependencies**: Check for scheduler jobs or cleanup tasks
- **Decision**: Keep if actively used, otherwise DELETE

#### **File: `scripts/archive_legacy_session_handlers.py`**
- **Action**: Move to archive directory
- **Priority**: 🟢 Medium (Week 3)
- **Risk**: Low - Archive script
- **Lines**: ~50 lines
- **Dependencies**: None (historical)

---

## **🗂️ CATEGORY 6: DOCUMENTATION & COMMENTS**

### **🟢 MEDIUM - Documentation Updates (35+ files)**

#### **Phase References (Multiple files)**
- **Action**: Remove "Phase 2" and "Phase 3" architectural comments
- **Priority**: 🟢 Medium (Week 5)
- **Risk**: Zero - Documentation only
- **Files**: Throughout codebase
- **Pattern**: `# Phase 2 - Deprecated`, `# Phase 3 implementation`

#### **Session ID Examples (Multiple files)**
- **Action**: Update examples to use flow_id
- **Priority**: 🟢 Medium (Week 5)
- **Risk**: Zero - Documentation only
- **Pattern**: `session_id = "disc_session_12345"`
- **Replacement**: `flow_id = str(uuid.uuid4())`

#### **TODO Cleanup Items (Multiple files)**
- **Action**: Resolve or remove TODO comments about legacy cleanup
- **Priority**: 🟢 Medium (Week 6)
- **Risk**: Zero - Comments only
- **Pattern**: `# TODO: Remove session_id references`

---

## **📋 EXECUTION CHECKLIST**

### **Week 1: Foundation**
- [ ] Execute database backup
- [ ] Run database migration: `alembic upgrade remove_session_id_cleanup`
- [ ] DELETE: `session_comparison_original.py` (713 lines)
- [ ] DELETE: `vector_utils_old.py` (317 lines)
- [ ] DELETE: `field_mapping_legacy.py` (1,702 lines)
- [ ] DELETE: `agentic_critical_attributes_legacy.py` (1,290 lines)
- [ ] **Total Removed**: 4,022 lines

### **Week 2: Service Layer**
- [ ] Update `data_import_validation_service.py` for flow-based validation
- [ ] Remove/convert `session_manager.py`
- [ ] Fix `import_storage_handler.py` validation_session_id usage
- [ ] Update schema files: `data_import_schemas.py`, `auth_schemas.py`
- [ ] Resolve missing model imports decision

### **Week 3: Agent Conversions**
- [ ] Convert `data_import_validation_agent.py` to CrewAI
- [ ] Convert `attribute_mapping_agent.py` to CrewAI
- [ ] DELETE pseudo versions: `data_cleansing_agent.py`, `asset_inventory_agent.py`
- [ ] Update flow integration for new agent patterns

### **Week 4: Final Agents**
- [ ] Convert `tech_debt_analysis_agent.py` to CrewAI
- [ ] Convert `dependency_analysis_agent.py` to CrewAI
- [ ] DELETE: `base_discovery_agent.py`
- [ ] Validate all agent conversions

### **Week 5: API & Documentation**
- [ ] DELETE: `/app/api/v2/` directory
- [ ] Clean v2 references in `api.py`
- [ ] Update documentation and comments (Phase references)
- [ ] Review and clean session_id examples

### **Week 6: Final Validation**
- [ ] Remove TODO cleanup comments
- [ ] Run comprehensive test suite
- [ ] Validate no session_id references remain
- [ ] Performance testing and optimization

---

## **🎯 SUCCESS METRICS**

### **Quantitative Targets**
- **Files Reduced**: 147 → 0 legacy files
- **Lines Removed**: ~34,000 lines of legacy code
- **Session ID References**: 237 → 0 active references
- **Import Errors**: 12 → 0 broken imports
- **API Endpoints**: 50% reduction in deprecated endpoints

### **Validation Commands**
```bash
# Verify no session_id references in active code
grep -r "session_id" app/ --include="*.py" | grep -v "# " | wc -l
# Expected: 0

# Verify no broken imports
python -m py_compile $(find app/ -name "*.py")
# Expected: No errors

# Verify all agents are CrewAI-based
grep -r "BaseDiscoveryAgent" app/services/agents/ --include="*.py"
# Expected: No results

# Verify no legacy files remain
find app/ -name "*_legacy.py" -o -name "*_old.py" -o -name "*_v2.py"
# Expected: No results
```

---

## **⚠️ ROLLBACK PROCEDURES**

### **Database Rollback**
```bash
# If migration fails
alembic downgrade -1
# Restore from backup
pg_restore --clean --if-exists migration_backup.sql
```

### **Code Rollback**
```bash
# Feature flag rollback
export LEGACY_CLEANUP_ENABLED=false
# Git branch rollback
git checkout legacy-cleanup-rollback
```

### **Service Rollback**
```bash
# Restore compatibility services
export USE_SESSION_COMPATIBILITY=true
# Re-enable legacy endpoints
export LEGACY_ENDPOINTS_ENABLED=true
```

---

**This manifest provides the complete action plan for systematic legacy code removal while maintaining system stability and functionality.**

**Last Updated:** January 2025  
**Next Review:** After each weekly milestone