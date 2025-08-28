# Questionnaire Persistence Issue Investigation Summary

## Problem Statement
Users cannot save and retrieve questionnaire responses in the Adaptive Data Collection feature. Data entered in forms is not persisting to the database, and previously entered data is not loading when users return to the form.

## Root Causes Identified

### 1. Missing Backend Implementation
- The `submit_questionnaire_response` function was missing after code modularization
- When pre-commit checks found collection_crud.py was too large, the function got lost during refactoring
- Function has been re-implemented in `collection_crud_update_commands.py`

### 2. Frontend-Backend Endpoint Mismatch
- Frontend calls: `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses`
- Backend had: `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/submit`
- Added `/responses` endpoint to match frontend expectations

### 3. Frontend Not Making Real API Calls
- The `handleSave` function in `useAdaptiveFormFlow.ts` was only simulating API calls with setTimeout
- Modified to use actual `apiCall` function but Save Progress button still not triggering API calls

### 4. Database Schema Mismatches
- CollectionFlow table has both `id` (primary key) and `flow_id` (UUID) columns
- Queries were using wrong column names causing 500 errors
- Fixed queries to use `flow_id` for lookups

## Files Modified

### Backend Changes
1. **Created:** `backend/app/api/v1/endpoints/collection_crud_update_commands.py`
   - Implements submit_questionnaire_response()
   - Implements get_questionnaire_responses()
   - Implements batch_update_questionnaire_responses()

2. **Modified:** `backend/app/api/v1/endpoints/collection.py`
   - Added POST `/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` endpoint
   - Kept legacy `/submit` endpoint for backward compatibility

3. **Modified:** `backend/app/api/v1/endpoints/collection_crud.py`
   - Imports functions from collection_crud_update_commands
   - Exports them in __all__ list

### Frontend Changes
1. **Modified:** `src/hooks/collection/useAdaptiveFormFlow.ts`
   - Updated handleSave to make actual API calls
   - Added logic to fetch saved responses on load
   - Fixed applicationId references

2. **Modified:** `src/services/api/collection-flow.ts`
   - Added getQuestionnaireResponses() method

## Current Status

### What's Working
- Collection flow creation and initialization
- Application selection for collection flows
- Questionnaire form rendering with CrewAI-generated fields
- Form validation and field completion tracking

### What's NOT Working
- **Save Progress button doesn't trigger API calls** (critical issue)
- **Save Draft button also non-functional**
- **No data being saved to collection_questionnaire_responses table**
- **Form data not persisting between sessions**

## Testing Performed
1. Created collection flow: a498f8a9-32a5-4e80-bd68-3d2b9bc5980e
2. Selected application: crm-system
3. Filled form fields:
   - Application Name: "Test Application December 2025"
   - Type: "Web"
   - Criticality: "Critical"
   - Primary Users: "Internal employees and external customers"
4. Clicked Save Progress - button appears active but no API call made
5. Database check: 0 rows in collection_questionnaire_responses table

## Remaining Issues to Fix

### Priority 1: Save Button Connection
- The Save Progress button onClick handler is not properly connected to handleSave
- Need to check AdaptiveForms.tsx to ensure button is wired correctly
- Verify handleSave is properly exposed from the useAdaptiveFormFlow hook

### Priority 2: Database Foreign Key Issues
- The submit_questionnaire_response uses flow.id (integer primary key)
- But frontend might be sending flow_id (UUID string)
- Need to ensure consistent ID usage throughout

### Priority 3: Application ID Validation
- PR #253 mentioned issues with adhoc app names not matching assets table
- Need to validate application IDs against actual assets before saving

### Priority 4: Response Loading
- Even if save works, need to verify responses load when returning to form
- The getQuestionnaireResponses might need flow_id parameter fixes

## Next Steps for Resolution

1. **Immediate Fix Required:**
   ```typescript
   // In AdaptiveForms.tsx or relevant component
   // Find the Save Progress button and ensure it's connected:
   <button onClick={handleSave}>Save Progress</button>
   ```

2. **Verify Hook Export:**
   ```typescript
   // In useAdaptiveFormFlow.ts
   // Ensure handleSave is in the return statement
   return {
     handleSave,  // Must be exported
     // ... other exports
   }
   ```

3. **Database Verification:**
   ```sql
   -- Check if any data exists after save attempt
   SELECT * FROM collection_questionnaire_responses
   WHERE collection_flow_id IN (
     SELECT id FROM collection_flows
     WHERE flow_id = 'a498f8a9-32a5-4e80-bd68-3d2b9bc5980e'
   );
   ```

4. **Add Logging:**
   - Add console.log in handleSave to verify it's called
   - Add console.log in API endpoint to verify requests arrive
   - Check browser Network tab for actual API calls

## Related Context
- User explicitly requested: "ensure that you go through a collection flow, where you submit the questionnaire for a single application and then are able to retrieve the info later"
- This is critical functionality for the Adaptive Data Collection System (ADCS)
- Multi-tenant isolation must be maintained (engagement_id filtering)
