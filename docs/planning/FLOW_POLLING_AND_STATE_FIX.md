# Flow Polling and State Management Fix

## Issues Addressed

### 1. Frontend Polling Interval
**Problem**: Frontend was polling every 3-5 seconds, causing excessive backend load.

**Solution**: Updated all polling intervals to 30 seconds minimum:
- `/src/hooks/useFlow.ts` - Changed default `refreshInterval` from 5000ms to 30000ms
- `/src/components/discovery/AgentClarificationPanel.tsx` - Changed from 20s to 30s
- `/src/components/discovery/DataClassificationDisplay.tsx` - Changed from 8s to 30s  
- `/src/pages/discovery/CMDBImport/index.tsx` - Changed from 3s to 30s

The global polling manager already had a 30-second minimum, but some components were using hardcoded intervals.

### 2. Empty flow_id in State Management
**Problem**: Flow state was losing its IDs (flow_id, client_account_id, engagement_id, user_id) during execution.

**Root Causes**:
1. CrewAI base class initialization was accessing the state property before context was set
2. The state property might return different objects during flow execution
3. State synchronization between our managed state and CrewAI's internal state

**Solutions**:
1. **Fixed initialization order**: Moved context assignment before `super().__init__()` call
2. **Improved state property**: 
   - Always returns the managed `_flow_state` when available
   - Creates and stores a default state with proper IDs if needed
   - Ensures state consistency throughout flow lifecycle
3. **Added debug logging**: 
   - Log state IDs after initialization
   - Log state IDs at critical points (phase updates, pausing)
   - Track when state loses its IDs

## Code Changes

### Backend
- Fixed UnifiedDiscoveryFlow initialization order
- Enhanced state property to maintain ID consistency
- Added comprehensive debug logging for state tracking
- Improved error handling in import storage handler

### Frontend
- Standardized all polling intervals to 30 seconds minimum
- Ensures consistent polling behavior across all components

## Impact
- Reduced backend load from constant polling
- Fixed UUID validation errors in database operations
- Improved flow state consistency
- Better debugging capabilities for state management issues

## Testing
1. Upload a CSV file and monitor backend logs
2. Check that polling happens every 30 seconds, not more frequently
3. Verify no empty UUID errors in logs
4. Confirm flow progresses through phases with proper state IDs