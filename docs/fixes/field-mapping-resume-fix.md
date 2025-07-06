# Field Mapping Resume Fix

## Issue Description

The discovery flow gets stuck after field mapping suggestions are generated and the user clicks "Continue to Data Cleansing". The flow enters a `waiting_for_approval` state but doesn't properly resume when approval is given.

## Root Cause

1. **Flow Pauses for Approval**: The UnifiedDiscoveryFlow explicitly pauses at `pause_for_field_mapping_approval` and sets:
   - `status = "waiting_for_approval"`
   - `awaiting_user_approval = True`

2. **Resume Logic Issue**: The `/discovery/flow/{flow_id}/resume` endpoint was trying to execute the field_mapping phase again, but the flow needs to:
   - Mark field mapping as completed
   - Update the current phase to `data_cleansing`
   - Clear the `awaiting_user_approval` flag
   - Update progress percentage

3. **State Synchronization**: The fix ensures state is updated in both:
   - Master flow persistence (CrewAIFlowStateExtensions)
   - Discovery flow table (DiscoveryFlow)

## Solution Applied

Modified the resume endpoint in `backend/app/api/v1/endpoints/discovery_flows.py` to:

1. **Update Flow State Properly**:
   ```python
   # Mark field mapping as completed and advance to next phase
   current_state["phase_completion"]["field_mapping"] = True
   current_state["current_phase"] = "data_cleansing"
   current_state["progress_percentage"] = 33.3  # 2/6 phases complete
   ```

2. **Update Discovery Flow Table**:
   ```python
   discovery_flow.status = "processing"
   discovery_flow.current_phase = "data_cleansing"
   discovery_flow.field_mapping_completed = True
   discovery_flow.crewai_state_data["awaiting_user_approval"] = False
   ```

3. **Execute Next Phase**: Instead of re-executing field_mapping, execute the data_cleansing phase directly.

## Testing

1. **Run the test script**:
   ```bash
   cd /Users/chocka/CursorProjects/migrate-ui-orchestrator
   python test_field_mapping_resume.py
   ```

2. **Manual Testing**:
   - Start a discovery flow
   - Upload data
   - Wait for field mapping suggestions
   - Click "Continue to Data Cleansing"
   - Verify flow progresses to data cleansing phase

## Frontend Integration

The frontend already has the correct implementation in `useAttributeMappingNavigation.ts`:
- Detects when flow is in `waiting_for_approval` state
- Calls `/api/v1/discovery/flow/{flow_id}/resume` with field mappings
- Shows appropriate toast messages

## Additional Notes

- The flow uses CrewAI's `@listen` decorators for phase transitions
- Field mapping suggestions are stored in both flow persistence and discovery_flows table
- Progress is calculated as percentage of completed phases (6 total phases)
- The fix maintains backward compatibility with existing flows