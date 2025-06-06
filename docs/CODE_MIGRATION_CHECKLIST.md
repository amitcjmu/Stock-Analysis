# Code Migration Checklist - Data Model Consolidation

## 📋 **Files Requiring cmdb_asset → asset Migration**

### **Backend Models & Core Files**
- [x] `backend/app/models/cmdb_asset.py` - **REMOVE ENTIRELY**
- [ ] `backend/app/models/__init__.py` - Remove CMDBAsset exports (lines 24, 97-101)
- [ ] `backend/app/models/data_import.py` - Update foreign key from cmdb_assets to assets (lines 118, 126)
- [ ] `backend/app/models/client_account.py` - Update relationship from cmdb_assets to assets (line 191)
- [ ] `backend/app/models/tags.py` - Update foreign keys from cmdb_assets to assets (lines 73, 106)

### **API Endpoints**
- [ ] `backend/app/api/v1/endpoints/data_import.py` - Replace CMDBAsset with Asset (lines 43, 1471, 1681, 1688, 1736-1741)
- [ ] `backend/app/api/v1/discovery/asset_management.py` - Replace CMDBAsset imports and usage (lines 15, 106, 1257)
- [ ] `backend/app/api/v1/endpoints/agent_discovery.py` - Replace CMDBAsset import (line 15)

### **Services & Business Logic**
- [ ] `backend/app/services/crewai_flow_modular_enhanced.py` - Replace CMDBAsset model and create_cmdb_assets method (lines 23, 72-132, 402)
- [ ] `backend/app/services/crewai_flow_data_processing.py` - Replace CMDBAsset and create_cmdb_assets method (lines 33, 251-321, 593-621)
- [ ] `backend/app/services/embedding_service.py` - Replace CMDBAsset import (line 12)
- [ ] `backend/app/services/session_comparison_service.py` - Replace CMDBAsset import (line 19)

### **Repositories**
- [ ] `backend/app/repositories/base_repository.py` - Replace all CMDBAsset imports (lines 326, 335, 344, 353, 362)
- [ ] `backend/app/repositories/demo_repository.py` - Replace CMDBAsset import (line 21)

### **Database & Initialization**
- [ ] `backend/app/core/database.py` - Remove cmdb_asset reference (line 81)
- [ ] `backend/init_db.py` - Remove CMDBAsset import and demo creation (lines 21, 60, 264, 760)
- [ ] `backend/app/scripts/init_db.py` - Replace CMDBAsset with Asset (lines 21, 114, 507-617, 785)

### **Debug & Test Files (Lower Priority)**
- [ ] `backend/railway_setup.py` - Replace CMDBAsset import (line 126)
- [ ] `backend/debug_asset_inventory.py` - Update table references (lines 39-131)
- [ ] `backend/debug_schema_analysis.py` - Update table analysis (lines 38-39)
- [ ] `backend/debug_asset_count.py` - Replace CMDBAsset import (line 10)
- [ ] `debug_asset_count.py` - Replace CMDBAsset import (line 10)
- [ ] `debug_schema_analysis.py` - Update table references (lines 38-39)

### **Broken/Backup Files (Can be ignored)**
- [ ] `backend/app/models/client_account_broken.py` - Contains old references but is backup file

## 🎯 **Migration Strategy**

### **Phase 1: Update Imports and References**
1. Replace all `from app.models.cmdb_asset import CMDBAsset` with `from app.models.asset import Asset`
2. Replace all `CMDBAsset` class references with `Asset`
3. Update relationship definitions in related models

### **Phase 2: Update Method Names**
1. Rename `create_cmdb_assets` methods to `create_assets`
2. Update foreign key references from `cmdb_asset_id` to `asset_id`
3. Update table relationship definitions

### **Phase 3: Database Schema Updates**
1. Migrate data from cmdb_assets to assets table
2. Update foreign key constraints
3. Drop cmdb_assets table

### **Phase 4: Validation**
1. Ensure all imports compile successfully
2. Test API endpoints return data correctly
3. Verify frontend displays unified asset data

## ✅ **Success Criteria**
- [ ] No references to `cmdb_asset` or `CMDBAsset` in codebase (except comments/docs)
- [ ] All services use unified Asset model
- [ ] Database contains only assets table with all data
- [ ] Frontend displays all asset data correctly
- [ ] All tests pass with unified model 