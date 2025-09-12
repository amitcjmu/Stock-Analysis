# Discovery Flow Phase Progression Fix Implementation (November 2025)

## Safe Implementation Approach (GPT5 Validated)

### Fix Location
`backend/app/api/v1/endpoints/flow_processing.py` - `continue_flow_processing` endpoint

### Implementation Pattern

```python
# After determining next_phase in BOTH branches (fast-path and simple-logic)
# Around lines 250-260 and 310-320

if next_phase and next_phase != current_phase:  # Guard against redundant writes
    from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
        FlowPhaseManagementCommands
    )

    # Use existing tenant-scoped context
    phase_mgmt = FlowPhaseManagementCommands(
        db,
        context.client_account_id,
        context.engagement_id
    )

    # Update ONLY current_phase, not completion flags
    await phase_mgmt.update_phase_completion(
        flow_id=flow_id,
        phase=next_phase,
        completed=False,  # Critical: Don't mark complete prematurely
        data=None,
        agent_insights=None
    )

    logger.info(f"✅ Advanced current_phase from {current_phase} to {next_phase}")
```

### Key Safety Points

1. **completed=False**: Prevents corrupting progress flags
2. **Tenant-scoped**: Uses existing context for multi-tenant safety
3. **Guard condition**: `next_phase != current_phase` avoids redundant writes
4. **Both branches**: Apply in fast-path AND simple-logic paths
5. **No AI changes**: Leave Intelligent Flow Agent path unchanged

### Where to Add Code

**Branch 1 - Fast Path** (around line 250):
```python
# After: if validation_passed and next_phase:
#        result = {"next_phase": next_phase, ...}
# Add update here before returning result
```

**Branch 2 - Simple Logic** (around line 310):
```python
# After: next_phase = self._get_next_phase_simple(current_phase)
# Add update here if next_phase exists
```

**Branch 3 - AI Path** (optional, around line 340):
```python
# If AI returns next_phase in agent_result
# Add same update pattern before returning
```

### What NOT to Change

- ❌ Don't modify Intelligent Flow Agent logic
- ❌ Don't change phase names anywhere
- ❌ Don't use raw SQL - use repository pattern
- ❌ Don't mark phases as completed
- ❌ Don't update completion boolean flags

### Testing Checklist

1. **Upload CSV** → Creates flow at initialization
2. **Complete field mapping** → field_mapping_completed = true
3. **Click Continue** → Should update current_phase to 'data_cleansing'
4. **Verify database**:
   ```sql
   SELECT flow_id, current_phase, field_mapping_completed
   FROM migration.discovery_flows
   WHERE flow_id = 'YOUR_FLOW_ID';
   -- Should show: current_phase='data_cleansing', field_mapping_completed=true
   ```
5. **Continue through phases** → Each Continue should advance current_phase
6. **Asset inventory** → Assets should be created when phase executes

### Rollback Safety

If issues occur:
- The change is isolated to one endpoint
- Only affects current_phase field
- Doesn't modify completion flags
- Easy to comment out the update block

### Expected Behavior After Fix

- Navigation continues to work as before
- Database state stays synchronized with UI
- Phases advance properly: initialization → data_import → field_mapping → data_cleansing → asset_inventory → dependency_analysis
- Assets get created because flow reaches asset_inventory phase
