# Discovery Flow - Architecture Summary

**Last Updated:** 2025-07-30  
**Purpose:** Quick reference guide for understanding the Discovery flow architecture before making code changes

## 🎯 Overview

The Discovery flow is a multi-phase, AI-powered process that imports, analyzes, and inventories IT assets for migration assessment. It uses CrewAI agents orchestrated by the MasterFlowOrchestrator to process data through six distinct phases.

## 🏗️ Core Architecture

### Master Flow Orchestrator (MFO) Integration (CRITICAL)
The Discovery flow is fully integrated with the **Master Flow Orchestrator** architecture:

1. **Master Flow Orchestrator (MFO)**
   - **Primary identifier**: `master_flow_id` is used for ALL operations
   - ALL flow operations (create, resume, pause, delete) go through MFO
   - **Unified API**: `/api/v1/master-flows/*` endpoints
   - Single source of truth for flow lifecycle management

2. **Master Flow Table** (`crewai_flow_state_extensions`)
   - Orchestration and coordination hub
   - Flow status and current phase tracking
   - Stores comprehensive flow state and metadata
   - **Primary Key**: `flow_id` (this IS the master_flow_id)

3. **Child Flow Table** (`discovery_flows`) 
   - Discovery-specific phase tracking (internal implementation detail)
   - Links to master via `master_flow_id` foreign key
   - Contains phase completion booleans for UI display
   - **NOT exposed to API consumers** - internal state only

⚠️ **CRITICAL**: The `master_flow_id` is the **primary identifier** for all Discovery flow operations. Child flow IDs are internal implementation details and should never be used directly by API consumers or UI components.

### Key Components

- **MasterFlowOrchestrator**: Coordinates all flows, manages lifecycle
- **PhaseController**: Manages sequential phase execution with pause/resume
- **UnifiedDiscoveryFlow**: The CrewAI flow implementation
- **Background Execution Service**: Runs flows asynchronously after data import

## 📊 Flow Phases

### 1. **Data Import** 
- Uploads and validates data files
- Creates atomic transaction for all records
- Triggers flow creation
- [Details →](./02_Data_Import.md)

### 2. **Attribute Mapping** (Requires User Input)
- AI suggests field mappings
- Pauses for user approval
- Currently broken due to missing child flow records
- [Details →](./03_Attribute_Mapping.md)

### 3. **Data Cleansing**
- Enriches data with AI intelligence
- Standardizes and validates records
- [Details →](./04_Data_Cleansing.md)

### 4. **Asset Inventory**
- Categorizes and deduplicates assets
- Multi-domain classification
- [Details →](./05_Inventory.md)

### 5. **Dependency Analysis** (Parallel with #6)
- Maps relationships between assets
- Network and infrastructure analysis
- [Details →](./06_Dependencies.md)

### 6. **Technical Debt Assessment** (Parallel with #5)
- Identifies outdated components
- Security vulnerability analysis
- [Details →](./07_Tech_Debt.md)

## 🔄 Data Flow Sequence (MFO-Aligned)

```
1. User uploads file → POST /api/v1/data-import/store-import
2. Backend creates flow through MasterFlowOrchestrator (atomic transaction):
   - MFO.create_flow() → returns master_flow_id
   - DataImport record (references master_flow_id)
   - RawImportRecords 
   - ImportFieldMappings
   - Master flow state (crewai_flow_state_extensions)
   - Child flow record (discovery_flows) - internal tracking only
3. MFO initiates BackgroundExecutionService with master_flow_id
4. PhaseController executes phases through MFO coordination
5. ALL phase updates go through MFO using master_flow_id
6. UI polls MFO endpoints with master_flow_id for updates
```

## 🚨 Recently Fixed Issues

### Critical Bug: Missing Child Flow Creation (FIXED)
- **Problem**: Commit da9b699c1 incorrectly removed discovery flow creation
- **Impact**: Attribute mapping page was broken, couldn't find flow records
- **Root Cause**: Misunderstanding of MFO two-table design pattern
- **Solution**: Restored child flow creation in flow_trigger_service.py to follow MFO pattern

### MFO Integration Pattern (Updated)
1. **MasterFlowOrchestrator is the single entry point** for all flow operations
2. MFO manages the master flow record with `master_flow_id` as primary identifier
3. Child flow records are created automatically but are internal implementation details
4. **APIs exclusively use master_flow_id** - child flow IDs are never exposed
5. **UI components only reference master_flow_id** for all operations

## 💾 Database Schema

### Essential Tables
- `data_imports` - File upload metadata
- `raw_import_records` - Uploaded data (JSONB)
- `import_field_mappings` - Field mapping suggestions
- `crewai_flow_state_extensions` - Master flow orchestration
- `discovery_flows` - Discovery-specific tracking (MUST EXIST)

### Foreign Key Relationships (MFO-Aligned)
```
# Primary relationships through master_flow_id
data_imports.master_flow_id → crewai_flow_state_extensions.flow_id (master_flow_id)
discovery_flows.master_flow_id → crewai_flow_state_extensions.flow_id (master_flow_id)
discovery_flows.data_import_id → data_imports.id

# Key Point: crewai_flow_state_extensions.flow_id IS the master_flow_id
# All external references use this as the primary identifier
```

## 🛠️ Critical Code Patterns

### ✅ Correct Patterns

```python
# MFO Flow Creation (Primary Pattern)
master_flow_id = await mfo.create_flow(
    flow_type="discovery",
    configuration=config,
    atomic=True  # MUST be true for imports
)

# Always use master_flow_id for operations
await mfo.execute_phase(master_flow_id, phase_input)
await mfo.get_flow_status(master_flow_id)
await mfo.pause_flow(master_flow_id)

# UUID Serialization (prevents JSON errors)
configuration = convert_uuids_to_str({...})
```

### ❌ Incorrect Patterns

```python
# DON'T use child flow IDs for operations
discovery_flow_id = get_discovery_flow_id()  # WRONG!
await some_operation(discovery_flow_id)      # WRONG!

# DON'T bypass MFO for flow operations
await direct_database_update(flow_id)        # WRONG!

# DON'T reference child flow IDs in APIs/UI
return {"discovery_flow_id": child_id}       # WRONG!

# Always use master_flow_id instead
return {"master_flow_id": master_flow_id}    # CORRECT!
```

## 📋 Implementation Checklist

Before modifying Discovery flow code:

- [ ] **CRITICAL**: Use master_flow_id for ALL external operations
- [ ] Route all flow operations through MasterFlowOrchestrator
- [ ] Never expose child flow IDs to API consumers or UI
- [ ] Use `/api/v1/master-flows/*` endpoints for flow operations
- [ ] Ensure child flow records are created for internal tracking
- [ ] Use atomic transactions for data import through MFO
- [ ] Handle UUID serialization for JSON storage
- [ ] Test full flow lifecycle using only master_flow_id
- [ ] Verify UI uses master_flow_id for all flow references

## 🔗 Quick References

| Topic | Details | Key File |
|-------|---------|----------|
| Flow Overview | [01_Overview.md](./01_Overview.md) | `/pages/discovery/EnhancedDiscoveryDashboard` |
| Data Import | [02_Data_Import.md](./02_Data_Import.md) | `/services/data_import/flow_trigger_service.py` |
| Attribute Mapping | [03_Attribute_Mapping.md](./03_Attribute_Mapping.md) | `/pages/discovery/AttributeMapping` |
| Phase Execution | [Phase Controller](./02_Data_Import.md#phase-controller-architecture) | `/services/crewai_flows/unified_discovery_flow/phase_controller.py` |
| Background Tasks | [Background Execution](./02_Data_Import.md#7-asynchronous-kickoff-backgroundexecutionservice) | `/services/data_import/background_execution_service.py` |

## ⚡ Emergency Fixes

### If Discovery Flow is Stuck:
1. Check `crewai_flow_state_extensions` for flow status
2. Verify `discovery_flows` record exists (if not, that's the problem)
3. Check phase_controller initialization logic
4. Review background execution logs

### If Attribute Mapping Fails:
1. Verify discovery flow lookup in import_storage_handler
2. Check if flow has `data_import_id` set
3. Ensure field mappings were created during import

---

**Remember**: The Discovery flow is the foundation for migration assessment. Breaking it prevents users from analyzing their infrastructure. Always test the complete flow after changes.