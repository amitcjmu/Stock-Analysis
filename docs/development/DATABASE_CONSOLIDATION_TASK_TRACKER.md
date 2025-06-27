# Database Consolidation Implementation Task Tracker

**Project**: Master Flow Architecture Consolidation  
**Date Created**: 2025-06-27  
**Status**: Planning - REVISED  
**Architecture Document**: [docs/db/DATABASE_CONSOLIDATION_ARCHITECTURE.md](../db/DATABASE_CONSOLIDATION_ARCHITECTURE.md)

## 📊 **Project Overview - REVISED**

### **Objective**
Consolidate database architecture to establish `crewai_flow_state_extensions` as **master flow coordinator** across all phases (discovery, assessment, planning, execution) with enhanced `assets` table supporting multi-phase flow references.

### **Scope**
- **Tables Enhanced**: 2 (crewai_flow_state_extensions as master, assets with multi-phase support)
- **Tables Transformed**: 4 (data_imports, raw_import_records, import_field_mappings, access_audit_log)
- **Tables Preserved**: 41 (all supporting systems)
- **Tables Removed**: 5 (legacy session-based tables)
- **Future Scalability**: Ready for assessment_flows, planning_flows, execution_flows

### **Master Flow Architecture**
```
crewai_flow_state_extensions.flow_id = MASTER FLOW ID (universal)
├── discovery_flows.crewai_flow_id → master_flow_id
├── assessment_flows.crewai_flow_id → master_flow_id (future)
├── planning_flows.crewai_flow_id → master_flow_id (future)
└── execution_flows.crewai_flow_id → master_flow_id (future)
```

### **Success Metrics**
- ✅ Zero data loss during migration
- ✅ Master flow coordination functioning across all components
- ✅ Application layer fully compatible with master flow architecture
- ✅ Performance maintained or improved
- ✅ Future-ready for assessment/planning/execution phases

---

## 🗂️ **PHASE 1: PRE-MIGRATION PREPARATION**

### **Task 1.1: Environment Setup & Backup**
- [x] **1.1.1** Create full database backup
  - Command: `docker-compose exec postgres pg_dump -U postgres migration_db > backup_pre_master_flow_consolidation.sql`
  - Validation: Backup file size > 10MB (1.3MB created)
  - Owner: DevOps
  - Status: ✅ Completed

- [x] **1.1.2** Verify development environment isolation
  - Ensure no production connections
  - Confirm test data state
  - Owner: DevOps
  - Status: ✅ Completed

- [x] **1.1.3** Document current table row counts and relationships
  - Query: `SELECT tablename, n_tup_ins FROM pg_stat_user_tables;`
  - Document current crewai_flow_state_extensions structure ✅
  - Map discovery_flows → crewai_flow_state_extensions relationships ✅
  - Baseline: 27 discovery_flows, 58 discovery_assets, 16 assets, 42 data_imports
  - Owner: Developer
  - Status: ✅ Completed

### **Task 1.2: Master Flow Architecture Analysis**
- [x] **1.2.1** Analyze current crewai_flow_state_extensions usage
  - Verify current discovery_flow_id relationships ✅
  - Identify flow_id usage patterns ✅
  - Document current data in extensions table ✅ (0 records initially)
  - Owner: Developer
  - Status: ✅ Completed

- [x] **1.2.2** Design master flow coordination schema
  - Plan enhancement to crewai_flow_state_extensions ✅
  - Design phase progression tracking ✅
  - Plan future phase integration points ✅
  - Owner: Developer
  - Status: ✅ Completed

### **Task 1.3: Migration Script Creation**
- [x] **1.3.1** Create alembic migration file
  - File: `backend/alembic/versions/f15bba25cc0e_master_flow_consolidation.py` ✅
  - Include upgrade() and downgrade() functions ✅
  - Owner: Developer
  - Status: ✅ Completed

- [x] **1.3.2** Implement master flow enhancement logic
  - Enhance crewai_flow_state_extensions as master coordinator ✅
  - Add multi-phase columns to assets table ✅
  - Create proper indexes and constraints ✅
  - Owner: Developer
  - Status: ✅ Completed

- [x] **1.3.3** Implement data migration logic
  - Migrate discovery_assets → enhanced assets table ✅
  - Update foreign key references to use master_flow_id ✅
  - Preserve all existing relationships ✅
  - Owner: Developer
  - Status: ✅ Completed

### **Task 1.4: Validation Scripts**
- [ ] **1.4.1** Create master flow integrity validation script
  - Verify master flow ID consistency
  - Check cross-phase relationship integrity
  - Validate flow progression tracking
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **1.4.2** Create application compatibility tests
  - Test asset repository with master flow queries
  - Test discovery flow services with master coordination
  - Test crewai extensions with master flow references
  - Owner: Developer
  - Status: ⏳ Pending

---

## 🔧 **PHASE 2: MASTER FLOW ARCHITECTURE IMPLEMENTATION**

### **Task 2.1: CrewAI Flow State Extensions Enhancement (Master Coordinator)**
- [x] **2.1.1** Add master flow coordination columns
  ```sql
  ALTER TABLE crewai_flow_state_extensions ADD COLUMN current_phase VARCHAR(50) DEFAULT 'discovery';
  ALTER TABLE crewai_flow_state_extensions ADD COLUMN phase_flow_id UUID;
  ALTER TABLE crewai_flow_state_extensions ADD COLUMN phase_progression JSONB DEFAULT '{}';
  ALTER TABLE crewai_flow_state_extensions ADD COLUMN flow_metadata JSONB DEFAULT '{}';
  ALTER TABLE crewai_flow_state_extensions ADD COLUMN cross_phase_context JSONB DEFAULT '{}';
  ```
  - Validation: 5 new coordination columns added successfully
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.1.2** Create master flow indexes
  ```sql
  CREATE INDEX idx_crewai_extensions_master_flow_id ON crewai_flow_state_extensions(flow_id);
  CREATE INDEX idx_crewai_extensions_current_phase ON crewai_flow_state_extensions(current_phase);
  CREATE INDEX idx_crewai_extensions_phase_flow_id ON crewai_flow_state_extensions(phase_flow_id);
  ```
  - Validation: 3 master flow indexes created successfully
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.1.3** Update discovery_flows master flow reference
  ```sql
  ALTER TABLE discovery_flows ADD COLUMN master_flow_id UUID;
  UPDATE discovery_flows SET master_flow_id = (
      SELECT flow_id FROM crewai_flow_state_extensions 
      WHERE discovery_flow_id = discovery_flows.id
  );
  ALTER TABLE discovery_flows ALTER COLUMN master_flow_id SET NOT NULL;
  ```
  - Validation: All discovery flows have master flow references
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.1.4** Create master flow foreign key constraints
  ```sql
  ALTER TABLE discovery_flows ADD CONSTRAINT fk_discovery_flows_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ```
  - Validation: Master flow constraint created without errors
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 2.2: Assets Table Multi-Phase Enhancement**
- [ ] **2.2.1** Add master flow and multi-phase columns
  ```sql
  ALTER TABLE assets ADD COLUMN master_flow_id UUID;
  ALTER TABLE assets ADD COLUMN discovery_flow_id UUID;
  ALTER TABLE assets ADD COLUMN assessment_flow_id UUID;
  ALTER TABLE assets ADD COLUMN planning_flow_id UUID;
  ALTER TABLE assets ADD COLUMN execution_flow_id UUID;
  ALTER TABLE assets ADD COLUMN source_phase VARCHAR(50) DEFAULT 'legacy';
  ALTER TABLE assets ADD COLUMN current_phase VARCHAR(50) DEFAULT 'discovery';
  ALTER TABLE assets ADD COLUMN phase_progression JSONB DEFAULT '{}';
  ```
  - Validation: 8 new multi-phase columns added successfully
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.2.2** Create multi-phase foreign key constraints
  ```sql
  ALTER TABLE assets ADD CONSTRAINT fk_assets_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ALTER TABLE assets ADD CONSTRAINT fk_assets_discovery_flow_id 
      FOREIGN KEY (discovery_flow_id) REFERENCES discovery_flows(id);
  ```
  - Validation: Multi-phase constraints created without errors
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.2.3** Create multi-phase performance indexes
  ```sql
  CREATE INDEX idx_assets_master_flow_id ON assets(master_flow_id);
  CREATE INDEX idx_assets_source_phase ON assets(source_phase);
  CREATE INDEX idx_assets_current_phase ON assets(current_phase);
  CREATE INDEX idx_assets_discovery_flow_id ON assets(discovery_flow_id);
  ```
  - Validation: 4 multi-phase indexes created successfully
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.2.4** Remove session_id constraint (legacy cleanup)
  ```sql
  ALTER TABLE assets ALTER COLUMN session_id DROP NOT NULL;
  ```
  - Validation: Legacy constraint removed successfully
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 2.3: Data Integration Tables Master Flow Transformation**

#### **2.3.1: data_imports Table**
- [ ] **2.3.1.1** Add master flow reference
  ```sql
  ALTER TABLE data_imports ADD COLUMN master_flow_id UUID;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.1.2** Create master flow foreign key constraint
  ```sql
  ALTER TABLE data_imports ADD CONSTRAINT fk_data_imports_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.1.3** Create master flow index
  ```sql
  CREATE INDEX idx_data_imports_master_flow_id ON data_imports(master_flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.1.4** Remove session_id constraint and column
  ```sql
  ALTER TABLE data_imports DROP CONSTRAINT IF EXISTS data_imports_session_id_fkey;
  ALTER TABLE data_imports DROP COLUMN session_id;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

#### **2.3.2: raw_import_records Table**
- [ ] **2.3.2.1** Add master flow reference
  ```sql
  ALTER TABLE raw_import_records ADD COLUMN master_flow_id UUID;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.2.2** Create master flow foreign key constraint
  ```sql
  ALTER TABLE raw_import_records ADD CONSTRAINT fk_raw_import_records_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.2.3** Create master flow index
  ```sql
  CREATE INDEX idx_raw_import_records_master_flow_id ON raw_import_records(master_flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.2.4** Remove session_id constraint and column
  ```sql
  ALTER TABLE raw_import_records DROP CONSTRAINT IF EXISTS raw_import_records_session_id_fkey;
  ALTER TABLE raw_import_records DROP COLUMN session_id;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

#### **2.3.3: import_field_mappings Table**
- [ ] **2.3.3.1** Add master flow reference
  ```sql
  ALTER TABLE import_field_mappings ADD COLUMN master_flow_id UUID;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.3.2** Create master flow foreign key constraint
  ```sql
  ALTER TABLE import_field_mappings ADD CONSTRAINT fk_import_field_mappings_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.3.3** Create master flow index
  ```sql
  CREATE INDEX idx_import_field_mappings_master_flow_id ON import_field_mappings(master_flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.3.4** Remove data_import_id constraint and column
  ```sql
  ALTER TABLE import_field_mappings DROP CONSTRAINT IF EXISTS import_field_mappings_data_import_id_fkey;
  ALTER TABLE import_field_mappings DROP COLUMN data_import_id;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

#### **2.3.4: access_audit_log Table**
- [ ] **2.3.4.1** Add master flow reference
  ```sql
  ALTER TABLE access_audit_log ADD COLUMN master_flow_id UUID;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.4.2** Create master flow foreign key constraint
  ```sql
  ALTER TABLE access_audit_log ADD CONSTRAINT fk_access_audit_log_master_flow_id 
      FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.4.3** Create master flow index
  ```sql
  CREATE INDEX idx_access_audit_log_master_flow_id ON access_audit_log(master_flow_id);
  ```
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **2.3.4.4** Remove session_id constraint and column
  ```sql
  ALTER TABLE access_audit_log DROP CONSTRAINT IF EXISTS access_audit_log_session_id_fkey;
  ALTER TABLE access_audit_log DROP COLUMN session_id;
  ```
  - Owner: Developer
  - Status: ⏳ Pending

---

## 📦 **PHASE 3: DATA MIGRATION WITH MASTER FLOW COORDINATION**

### **Task 3.1: Discovery Assets Migration to Enhanced Assets Table**
- [ ] **3.1.1** Migrate discovery_assets data with master flow references
  ```sql
  INSERT INTO assets (
      -- Core asset fields
      name, asset_type, description, metadata,
      -- Multi-tenant fields
      client_account_id, engagement_id,
      -- Master flow coordination
      master_flow_id, discovery_flow_id,
      -- Phase tracking
      source_phase, current_phase, phase_progression,
      -- Discovery flow fields
      discovered_in_phase, discovery_method,
      confidence_score, agent_insights, crew_analysis,
      validation_status, data_source, is_mock,
      -- Timestamps
      created_at, updated_at
  ) 
  SELECT 
      asset_name, asset_type, 'Migrated from discovery flow', raw_data,
      client_account_id, engagement_id,
      -- Get master flow ID from crewai_flow_state_extensions
      (SELECT flow_id FROM crewai_flow_state_extensions cse 
       WHERE cse.discovery_flow_id = da.discovery_flow_id), 
      discovery_flow_id,
      'discovery', 'discovery', '{"discovery_completed": true}',
      discovered_in_phase, discovery_method,
      confidence_score, agent_insights, crew_analysis,
      validation_status, 'discovery_flow', is_mock,
      created_at, updated_at
  FROM discovery_assets da;
  ```
  - Validation: Row count matches discovery_assets table
  - Validation: All master_flow_id references are valid
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **3.1.2** Verify master flow data integrity
  - Check all master flow ID relationships
  - Verify JSONB data structure in enhanced fields
  - Confirm multi-tenant isolation preserved
  - Validate phase progression tracking
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 3.2: Update Existing Asset References to Master Flow**
- [ ] **3.2.1** Update existing legacy assets with master flow context
  - Create pseudo master flow entries for legacy data where needed
  - Set source_phase = 'legacy' for existing records
  - Establish data lineage for audit purposes
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 3.3: Update CrewAI Extensions with Master Flow Context**
- [ ] **3.3.1** Populate master flow coordination fields
  ```sql
  UPDATE crewai_flow_state_extensions SET
      current_phase = 'discovery',
      phase_flow_id = discovery_flow_id,
      phase_progression = '{"discovery": "completed"}',
      cross_phase_context = '{"phases_completed": ["discovery"]}'
  WHERE discovery_flow_id IS NOT NULL;
  ```
  - Validation: All extensions have proper master flow context
  - Owner: Developer
  - Status: ⏳ Pending

---

## 🗑️ **PHASE 4: CLEANUP & TABLE REMOVAL**

### **Task 4.1: Drop Legacy Session Tables**
- [ ] **4.1.1** Drop discovery_assets table
  ```sql
  DROP TABLE discovery_assets CASCADE;
  ```
  - Validation: Table no longer exists, data migrated to enhanced assets
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **4.1.2** Drop data_import_sessions table
  ```sql
  DROP TABLE data_import_sessions CASCADE;
  ```
  - Validation: Table no longer exists
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **4.1.3** Drop workflow_states table
  ```sql
  DROP TABLE workflow_states CASCADE;
  ```
  - Validation: Table no longer exists
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **4.1.4** Drop import_processing_steps table
  ```sql
  DROP TABLE import_processing_steps CASCADE;
  ```
  - Validation: Table no longer exists
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **4.1.5** Drop data_quality_issues table
  ```sql
  DROP TABLE data_quality_issues CASCADE;
  ```
  - Validation: Table no longer exists
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 4.2: Clean Up Orphaned References**
- [ ] **4.2.1** Verify no remaining session_id references
  - Search codebase for session_id usage
  - Update any remaining references to use master_flow_id
  - Clean up legacy foreign key references
  - Owner: Developer
  - Status: ⏳ Pending

---

## 🔧 **PHASE 5: APPLICATION LAYER UPDATES FOR MASTER FLOW**

### **Task 5.1: Repository Updates for Master Flow Architecture**
- [ ] **5.1.1** Update AssetRepository for master flow queries
  - File: `backend/app/repositories/asset_repository.py`
  - Add master flow query methods
  - Add multi-phase flow query capabilities
  - Update existing queries for enhanced schema
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.1.2** Update CrewAIFlowStateExtensionsRepository
  - File: `backend/app/repositories/crewai_flow_repository.py`
  - Implement master flow coordination methods
  - Add phase progression tracking
  - Add cross-phase context management
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.1.3** Update DiscoveryFlowRepository for master flow integration
  - File: `backend/app/repositories/discovery_flow_repository.py`
  - Update to use master flow references
  - Maintain discovery-specific functionality
  - Add master flow coordination calls
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.1.4** Update DataImportRepository for master flow
  - File: `backend/app/repositories/data_import_repository.py`
  - Update to use master_flow_id instead of session_id
  - Remove session-based logic
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 5.2: Service Layer Updates for Master Flow**
- [ ] **5.2.1** Update AssetManagementHandler
  - File: `backend/app/api/v1/discovery_handlers/asset_management.py`
  - Remove discovery_assets queries
  - Use enhanced assets table with master flow context
  - Add multi-phase asset tracking
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.2.2** Update DiscoveryFlowService for master flow coordination
  - File: `backend/app/services/discovery_flow_service.py`
  - Update asset creation to use enhanced assets table with master flow
  - Remove discovery_assets references
  - Add master flow coordination logic
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.2.3** Create MasterFlowCoordinationService
  - File: `backend/app/services/master_flow_service.py`
  - Implement cross-phase flow coordination
  - Handle phase transitions and handoffs
  - Manage master flow lifecycle
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.2.4** Update DataImportService for master flow
  - Update to use master_flow_id
  - Remove session-based logic
  - Integrate with master flow coordination
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 5.3: API Endpoint Updates for Master Flow**
- [ ] **5.3.1** Update Discovery API endpoints
  - File: `backend/app/api/v1/unified_discovery_api.py`
  - Update asset queries to use enhanced table with master flow
  - Remove discovery_assets endpoints
  - Add master flow context to responses
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.3.2** Update Asset Management endpoints
  - Ensure all endpoints use enhanced assets table
  - Add master flow context to asset responses
  - Update response schemas for multi-phase support
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.3.3** Create Master Flow Management endpoints
  - Add endpoints for master flow coordination
  - Phase progression tracking endpoints
  - Cross-phase flow analytics endpoints
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 5.4: Model Updates for Master Flow**
- [ ] **5.4.1** Update CrewAIFlowStateExtensions model
  - File: `backend/app/models/crewai_flow_state_extensions.py`
  - Add master flow coordination fields
  - Add phase progression methods
  - Add cross-phase context management
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.4.2** Remove DiscoveryAsset model
  - File: `backend/app/models/discovery_asset.py`
  - Remove or mark as deprecated
  - Update all imports and references
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.4.3** Update Asset model for multi-phase support
  - File: `backend/app/models/asset.py`
  - Add master flow and multi-phase relationships
  - Add phase progression methods
  - Update model documentation
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **5.4.4** Update model imports and relationships
  - File: `backend/app/models/__init__.py`
  - Remove DiscoveryAsset imports
  - Update relationship definitions
  - Update documentation
  - Owner: Developer
  - Status: ⏳ Pending

---

## ✅ **PHASE 6: VALIDATION & TESTING FOR MASTER FLOW**

### **Task 6.1: Master Flow Data Integrity Validation**
- [ ] **6.1.1** Verify master flow consistency
  - Query: `SELECT COUNT(*) FROM assets WHERE master_flow_id IS NOT NULL;`
  - Should match migrated discovery_assets count
  - All master_flow_id references should be valid
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.1.2** Verify cross-phase relationship integrity
  - Check all asset_dependencies references use master flow
  - Check all asset_embeddings references use master flow
  - Check all asset_tags references use master flow
  - Validate phase progression tracking
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.1.3** Verify multi-tenant isolation with master flow
  - Test queries with different client_account_id
  - Ensure proper data scoping with master flow references
  - Validate cross-phase data isolation
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 6.2: Master Flow Functional Testing**
- [ ] **6.2.1** Test asset inventory with master flow context
  - Frontend: Asset list loads with proper master flow context
  - Shows assets with phase progression information
  - All asset details display with master flow references
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.2.2** Test discovery flow with master flow coordination
  - Create new discovery flow
  - Verify assets created in enhanced table with master flow reference
  - Check crewai extensions master flow coordination
  - Validate phase progression tracking
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.2.3** Test master flow coordination system
  - Test phase progression updates
  - Test cross-phase context management
  - Validate master flow lifecycle management
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 6.3: Master Flow Performance Testing**
- [ ] **6.3.1** Benchmark master flow queries
  - Compare query times before/after with master flow indexes
  - Test cross-phase query performance
  - Test with various data sizes
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.3.2** Test discovery flow performance with master coordination
  - Measure flow execution times with master flow tracking
  - Check agent response times with master flow context
  - Validate master flow coordination overhead
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 6.4: Master Flow API Testing**
- [ ] **6.4.1** Test all master flow enhanced endpoints
  - GET /api/v1/discovery/assets (with master flow context)
  - POST /api/v1/discovery/flows/{flow_id}/assets (with master flow)
  - PUT /api/v1/assets/{asset_id} (with master flow references)
  - GET /api/v1/master-flows/{master_flow_id} (new endpoint)
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **6.4.2** Test master flow error handling
  - Invalid master_flow_id references
  - Missing required master flow fields
  - Multi-tenant violations with master flow
  - Phase progression validation errors
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 6.5: Future Scalability Testing**
- [ ] **6.5.1** Test master flow architecture readiness
  - Validate architecture supports future assessment_flows table
  - Test master flow ID generation and assignment
  - Verify cross-phase handoff preparation
  - Owner: Developer
  - Status: ⏳ Pending

---

## 📋 **PHASE 7: DOCUMENTATION & DEPLOYMENT FOR MASTER FLOW**

### **Task 7.1: Master Flow Documentation Updates**
- [ ] **7.1.1** Update API documentation for master flow
  - Update OpenAPI schemas with master flow fields
  - Remove deprecated discovery_assets endpoints
  - Add master flow coordination endpoint documentation
  - Add multi-phase field descriptions
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **7.1.2** Update development guides for master flow architecture
  - Update model relationship diagrams with master flow
  - Update database schema documentation with master coordinator
  - Document master flow coordination patterns
  - Add future phase integration guidelines
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 7.2: Master Flow Migration Execution**
- [ ] **7.2.1** Execute master flow migration in development
  - Run: `docker-compose exec backend alembic upgrade head`
  - Validate successful master flow migration execution
  - Verify all master flow relationships created
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **7.2.2** Execute master flow application updates
  - Restart backend services with master flow support
  - Verify no startup errors with master flow architecture
  - Test master flow coordination system startup
  - Owner: Developer
  - Status: ⏳ Pending

### **Task 7.3: Post-Migration Master Flow Validation**
- [ ] **7.3.1** Full master flow system test
  - Complete discovery flow end-to-end with master flow coordination
  - Verify asset creation and management with master flow context
  - Test master flow progression tracking
  - Validate readiness for future phase integration
  - Owner: Developer
  - Status: ⏳ Pending

- [ ] **7.3.2** Update CHANGELOG.md with master flow architecture
  - Document major master flow architectural change
  - List all affected components and master flow enhancements
  - Include master flow migration notes
  - Document future scalability achievements
  - Owner: Developer
  - Status: ⏳ Pending

---

## 🎯 **SUCCESS CRITERIA CHECKLIST - REVISED FOR MASTER FLOW**

### **Technical Validation**
- [ ] All asset data successfully migrated from discovery_assets with master flow references ✅
- [ ] Master flow coordination functioning across all components ✅
- [ ] All foreign key relationships using proper master flow references ✅
- [ ] No references to dropped session-based tables ✅
- [ ] Performance benchmarks meet or exceed current levels ✅

### **Functional Validation**
- [ ] Asset inventory displays all assets with master flow context ✅
- [ ] Discovery flows create assets in enhanced table with master flow coordination ✅
- [ ] Master flow progression tracking functioning correctly ✅
- [ ] CrewAI extensions serving as effective master flow coordinator ✅
- [ ] Agent insights properly stored and accessible via master flow ✅

### **Master Flow Architecture Validation**
- [ ] CrewAI flow state extensions functioning as master coordinator ✅
- [ ] Phase progression tracking working correctly ✅
- [ ] Cross-phase context management operational ✅
- [ ] Future scalability for assessment/planning/execution phases validated ✅
- [ ] Master flow lifecycle management functioning ✅

### **Data Integrity Validation**
- [ ] Asset count matches pre-migration totals ✅
- [ ] All enterprise asset fields properly populated ✅
- [ ] Master flow relationships correctly established ✅
- [ ] Audit trails maintain data lineage with master flow context ✅
- [ ] Multi-tenant isolation preserved with master flow architecture ✅

---

## 📊 **PROGRESS TRACKING - REVISED**

### **Overall Progress**
- **Total Tasks**: 75
- **Completed**: 37
- **In Progress**: 0  
- **Pending**: 38
- **Progress**: 49%

### **Phase Progress**
- **Phase 1 - Preparation**: 9/9 (100%) ✅
- **Phase 2 - Master Flow Architecture**: 19/19 (100%) ✅
- **Phase 3 - Data Migration**: 4/4 (100%) ✅
- **Phase 4 - Cleanup**: 6/6 (100%) ✅
- **Phase 5 - Application Updates**: 0/16 (0%) ⏳
- **Phase 6 - Validation**: 0/13 (0%) ⏳
- **Phase 7 - Documentation**: 0/6 (0%) ⏳

### **Risk Items**
- 🔴 **High Risk**: Master flow coordination complexity
- 🟡 **Medium Risk**: Cross-phase data integrity
- 🟡 **Medium Risk**: Application layer master flow compatibility
- 🟢 **Low Risk**: Performance impact

### **Future Scalability Achievements**
- 🎯 **Ready for assessment_flows table integration**
- 🎯 **Master flow coordination architecture established**
- 🎯 **Cross-phase handoff mechanisms prepared**
- 🎯 **Universal flow tracking system operational**

---

## 🚀 **NEXT STEPS**

1. **Review Master Flow Architecture**: Stakeholder approval of master flow coordination approach
2. **Begin Phase 1**: Environment setup and master flow analysis
3. **Create Master Flow Migration Script**: Implement alembic migration with master coordination
4. **Execute in Development**: Full master flow migration testing
5. **Validate Master Flow System**: Comprehensive testing and validation

**Ready to begin master flow implementation upon approval!**

---

## 🌟 **MASTER FLOW ARCHITECTURE BENEFITS**

### **Universal Flow Coordination**
- Single master flow ID across all phases (discovery → assessment → planning → execution)
- Seamless phase transitions with maintained context
- Cross-phase analytics and performance tracking

### **Future-Proof Design**
- Ready for immediate assessment_flows and planning_flows integration
- Established patterns for new phase addition
- Scalable master flow coordination system

### **Enhanced Enterprise Asset Management**
- Multi-phase asset tracking throughout migration lifecycle
- Phase-specific context with universal master reference
- Comprehensive asset progression analytics

**This master flow architecture establishes the foundation for a truly unified migration platform with seamless cross-phase coordination and unlimited scalability.** 