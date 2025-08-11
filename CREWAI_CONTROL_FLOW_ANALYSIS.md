# CrewAI Control Flow Analysis: Data Import to Attribute Mapping

## Executive Summary
The flow is broken at the phase execution level. The `FlowTypeConfig` object is missing the `is_phase_valid` attribute, causing flow execution to fail immediately when trying to generate field mappings.

## Current Flow Sequence (From Investigation)

### 1. Data Import Phase
**Location**: `/api/v1/data-import/store-import`
**Process**:
1. User uploads CSV file from Data Import page
2. Backend creates records in atomic transaction:
   - `data_imports` record with ID `ea00b3a6-0960-478d-9f4d-c56a0e5da76a`
   - `raw_import_records` (11 records)
   - Master flow in `crewai_flow_state_extensions` (flow_id: `8f0da8e1-0715-4f4c-a896-686c01a3f527`)
   - Discovery flow in `discovery_flows` table
3. Flow status set to "running"

### 2. Field Mapping Generation (BROKEN)
**Expected Process**:
1. PhaseController should execute `field_mapping` phase
2. UnifiedDiscoveryFlow's `generate_field_mapping_suggestions` should run
3. Field mappings should be created in `import_field_mappings` table
4. Flow should pause with status `waiting_for_approval`

**Actual Behavior**:
- No field mappings created (0 records in `import_field_mappings`)
- Flow stuck in "running" status
- Flow execution fails with: `'FlowTypeConfig' object has no attribute 'is_phase_valid'`

### 3. Attribute Mapping Page Load
**Location**: `/pages/discovery/AttributeMapping`
**Process**:
1. Page loads and detects flow ID `8f0da8e1-0715-4f4c-a896-686c01a3f527`
2. Calls `/api/v1/flows/{flowId}/status` - gets flow data
3. Calls `/api/v1/data-import/flow/{flowId}/import-data` - gets import data
4. Shows "No field mappings available" because none exist

### 4. "Trigger Analysis" Button Action
**Location**: `handleTriggerFieldMappingCrew` in `useAttributeMappingActions.ts`
**Process**:
1. Button calls `/discovery/flow/{flow_id}/resume` endpoint
2. Backend calls `MasterFlowOrchestrator.resume_flow()`
3. Should trigger field mapping generation
4. BUT: Flow can't execute due to configuration error

## Root Cause Analysis

### Primary Issue: FlowTypeConfig Missing Attribute
The `FlowTypeConfig` object is missing the `is_phase_valid` attribute that the phase execution logic expects. This happens in:
- File: Backend flow execution logic
- Error: `'FlowTypeConfig' object has no attribute 'is_phase_valid'`

### Secondary Issues:
1. **Field Mappings Never Generated**:
   - The flow never progresses past initialization
   - No CrewAI agents are executed
   - No field mapping suggestions are created

2. **Flow Status Incorrect**:
   - Flow shows "running" but isn't actually executing
   - Should be "waiting_for_approval" after field mapping generation

3. **Discovery Flow Record Incomplete**:
   - `master_flow_id` is NULL (should reference the master flow)
   - `field_mapping_completed` is FALSE
   - Status shows "initialized" not synced with master

## Control Flow Breakdown

### Data Import → Field Mapping Transition
```
1. Data Import Completion
   ├── Creates master flow record
   ├── Creates discovery flow record
   ├── Stores raw data in flow persistence
   └── Should trigger background execution
       └── FAILS: FlowTypeConfig.is_phase_valid missing

2. Field Mapping Generation (Never Reached)
   ├── PhaseController.execute_phase('field_mapping')
   ├── UnifiedDiscoveryFlow.generate_field_mapping_suggestions()
   ├── CrewAI agents analyze data
   ├── Create records in import_field_mappings
   └── Pause flow with 'waiting_for_approval'

3. User Approval Flow (Never Reached)
   ├── User reviews mappings on UI
   ├── Clicks "Approve Mappings"
   ├── Frontend calls /resume endpoint
   ├── Flow continues to data_cleansing phase
   └── Field mappings marked as approved
```

## Why "Trigger Analysis" Button Doesn't Work

The button attempts to resume the flow, but:
1. Flow can't execute due to missing `is_phase_valid` attribute
2. Even if fixed, there's no paused state to resume from
3. Field mappings were never generated in the first place

## Solution Required

### Immediate Fix Needed:
1. Fix the `FlowTypeConfig` to include `is_phase_valid` attribute
2. Ensure flow execution can proceed through phases
3. Generate field mappings during the field_mapping phase
4. Properly pause flow for user approval

### Verification Steps:
1. Flow should execute field_mapping phase after data import
2. Field mappings should be created in database
3. Flow should pause with `waiting_for_approval` status
4. UI should display the generated mappings
5. "Trigger Analysis" should resume the paused flow
