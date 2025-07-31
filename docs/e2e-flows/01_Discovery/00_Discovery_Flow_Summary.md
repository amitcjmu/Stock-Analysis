# Discovery Flow - Architecture Summary

**Last Updated:** 2025-07-30  
**Purpose:** Quick reference guide for understanding the Discovery flow architecture before making code changes

## 🎯 Overview

The Discovery flow is a multi-phase, AI-powered process that imports, analyzes, and inventories IT assets for migration assessment. It uses CrewAI agents orchestrated by the MasterFlowOrchestrator to process data through six distinct phases.

## 🏗️ Core Architecture

### Two-Table Design (CRITICAL)
The Discovery flow uses a **two-table architecture** that MUST be maintained:

1. **Master Flow Table** (`crewai_flow_state_extensions`)
   - Orchestration and coordination
   - Flow status and current phase
   - Managed by MasterFlowOrchestrator
   - Stores high-level flow state

2. **Child Flow Table** (`discovery_flows`) 
   - Discovery-specific phase tracking
   - Links to master via `master_flow_id`
   - Contains phase completion booleans
   - Used by UI for display logic

⚠️ **WARNING**: Both tables MUST have records for the flow to work properly. The MasterFlowOrchestrator creates the master flow record, but the flow-specific service must create the child flow record as part of the MFO two-table design pattern.

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

## 🔄 Data Flow Sequence

```
1. User uploads file → POST /api/v1/data-import/store-import
2. Backend creates (atomic transaction):
   - DataImport record
   - RawImportRecords 
   - ImportFieldMappings
   - Master flow (crewai_flow_state_extensions)
   - Child flow (discovery_flows) - Created by DiscoveryFlowService
3. BackgroundExecutionService starts UnifiedDiscoveryFlow
4. PhaseController executes phases sequentially
5. Each phase updates flow state
6. UI polls for updates via WebSocket/polling
```

## 🚨 Recently Fixed Issues

### Critical Bug: Missing Child Flow Creation (FIXED)
- **Problem**: Commit da9b699c1 incorrectly removed discovery flow creation
- **Impact**: Attribute mapping page was broken, couldn't find flow records
- **Root Cause**: Misunderstanding of MFO two-table design pattern
- **Solution**: Restored child flow creation in flow_trigger_service.py to follow MFO pattern

### MFO Two-Table Design Pattern
1. MasterFlowOrchestrator creates the master flow record
2. Flow-specific services (e.g., DiscoveryFlowService) create child flow records
3. Both records are required for proper flow operation
4. UI and APIs depend on both tables existing

## 💾 Database Schema

### Essential Tables
- `data_imports` - File upload metadata
- `raw_import_records` - Uploaded data (JSONB)
- `import_field_mappings` - Field mapping suggestions
- `crewai_flow_state_extensions` - Master flow orchestration
- `discovery_flows` - Discovery-specific tracking (MUST EXIST)

### Foreign Key Relationships
```
data_imports.master_flow_id → crewai_flow_state_extensions.flow_id
discovery_flows.master_flow_id → crewai_flow_state_extensions.flow_id
discovery_flows.data_import_id → data_imports.id
```

## 🛠️ Critical Code Patterns

### ✅ Correct Patterns

```python
# UUID Serialization (prevents JSON errors)
configuration = convert_uuids_to_str({...})

# Atomic Flow Creation
flow_result = await orchestrator.create_flow(
    flow_type="discovery",
    atomic=True,  # MUST be true for imports
)

# Phase Status Checking
is_successful = isinstance(result, dict) and \
                result.get("status") in ["initialized", "initialization_completed"]
```

### ❌ Incorrect Patterns

```python
# DON'T compare status as string
if result == "initialization_completed":  # WRONG!

# DON'T assume MFO creates child flows
# Just creating master flow is NOT enough
```

## 📋 Implementation Checklist

Before modifying Discovery flow code:

- [ ] Understand two-table architecture requirement
- [ ] Ensure child flow records are created
- [ ] Use atomic transactions for data import
- [ ] Handle UUID serialization for JSON storage
- [ ] Check phase status as dictionary, not string
- [ ] Test full flow from import through all phases
- [ ] Verify UI can find and display flow data

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