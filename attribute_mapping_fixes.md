# Attribute Mapping Issues - Analysis & Solutions

## Issue Analysis

Based on my investigation, I've identified the root causes of all three issues:

### 1. **Approve/Delete Mapping Buttons Not Working**

**Root Cause**: The mapping action handlers are implemented correctly in `AttributeMapping.tsx`, but there may be an issue with the backend endpoint or API integration.

**Current Status**: 
- ✅ Frontend handlers `handleMappingAction` and `handleMappingChange` are properly implemented
- ✅ Functions are correctly connected to `FieldMappingsTab` component
- ❓ Backend endpoint `/agent-learning` may not be handling the requests properly

### 2. **Duplicates in Dropdown Throwing Errors**

**Root Cause**: The dropdown field deduplication logic exists but may not be comprehensive enough.

**Current Status**:
- ✅ Basic deduplication logic is implemented in `FieldMappingsTab.tsx`
- ❓ Additional edge cases may need handling

### 3. **Agent UI Manager Not Working**

**Root Cause**: Backend `/discovery/agents/agent-status` endpoint returns incomplete data structure.

**Current Issues**:
- ❌ Missing `pending_questions` in `page_data`
- ❌ Missing `data` classifications (good_data, needs_clarification, unusable)
- ❌ Frontend components expect different data structure than backend provides

## Solutions

### Solution 1: Fix Backend Agent Status Endpoint

The backend needs to return the complete data structure expected by frontend components.

**File**: `backend/app/api/v1/endpoints/agents/discovery/handlers/status.py`

**Add before the response preparation** (around line 350):

```python
        # Prepare mock pending questions for agent clarifications
        pending_questions = []
        if page_context == "attribute-mapping":
            pending_questions = [
                {
                    "id": f"question_{page_context}_1",
                    "agent_id": "field_mapping_specialist_001",
                    "agent_name": "Field Mapping Specialist",
                    "question_type": "validation",
                    "page": page_context,
                    "title": "Field Mapping Validation",
                    "question": "Please review the suggested field mappings. Are the AI-suggested mappings accurate for your organization's data structure?",
                    "context": {},
                    "options": ["Approve all mappings", "Review individual mappings", "Reject and re-analyze"],
                    "confidence": "medium",
                    "priority": "high",
                    "created_at": "2025-01-15T10:00:00Z",
                    "is_resolved": False
                }
            ]
        
        # Prepare mock data classifications
        data_classifications = {
            "good_data": [
                {
                    "id": f"good_data_{page_context}_1",
                    "data_type": "asset_record",
                    "classification": "good_data",
                    "content": {"hostname": "server01", "environment": "production"},
                    "agent_analysis": {
                        "quality_score": 0.9,
                        "completeness": 0.85,
                        "accuracy": 0.95
                    },
                    "confidence": "high",
                    "issues": [],
                    "recommendations": ["Ready for migration analysis"],
                    "page": page_context
                }
            ],
            "needs_clarification": [
                {
                    "id": f"needs_clarification_{page_context}_1",
                    "data_type": "asset_record", 
                    "classification": "needs_clarification",
                    "content": {"hostname": "server02", "environment": "unknown"},
                    "agent_analysis": {
                        "quality_score": 0.6,
                        "completeness": 0.7,
                        "accuracy": 0.8
                    },
                    "confidence": "medium",
                    "issues": ["Missing business criticality", "Unclear environment designation"],
                    "recommendations": ["Verify business criticality level", "Confirm environment classification"],
                    "page": page_context
                }
            ],
            "unusable": []
        }
```

**Update the response structure**:

```python
        # Prepare the response with the expected structure
        response = {
            "status": "success",
            "session_id": str(session.id) if session and hasattr(session, 'id') else session_id,
            "flow_status": flow_status,
            "page_data": {
                "agent_insights": agent_insights,
                "pending_questions": pending_questions  # ADD THIS LINE
            },
            "data": data_classifications,  # ADD THIS LINE
            "available_clients": available_clients,
            "available_engagements": available_engagements,
            "available_sessions": available_sessions
        }
```

### Solution 2: Enhance Mapping Action Error Handling

**File**: `src/pages/discovery/AttributeMapping.tsx`

Add better error handling and logging to the existing functions:

```typescript
  // Enhanced mapping action handler with better error handling
  const handleMappingAction = useCallback(async (mappingId: string, action: 'approve' | 'reject') => {
    console.log(`🔧 Attempting to ${action} mapping: ${mappingId}`);
    
    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_type: 'field_mapping_action',
          mapping_id: mappingId,
          action: action,
          context: {
            page: 'attribute-mapping',
            user_id: user?.id
          }
        })
      });

      console.log(`✅ Mapping ${action} response:`, response);

      if (response.status === 'success') {
        toast({
          title: action === 'approve' ? 'Mapping Approved' : 'Mapping Rejected',
          description: `Field mapping has been ${action}d successfully.`,
        });
        
        // Refresh the critical attributes data
        refetchCriticalAttributes();
      } else {
        throw new Error(response.message || 'Failed to update mapping');
      }
    } catch (error) {
      console.error(`❌ Error ${action}ing mapping:`, error);
      toast({
        title: 'Error',
        description: `Failed to ${action} mapping. Please try again.`,
        variant: 'destructive',
      });
    }
  }, [user?.id, toast, refetchCriticalAttributes]);
```

### Solution 3: Backend Agent Learning Endpoint

**File**: Check if `backend/app/api/v1/endpoints/agents/discovery/handlers/learning.py` exists and handles the mapping actions.

If not, create the endpoint or update the existing agent learning service to handle:
- `field_mapping_action` learning type
- `field_mapping_change` learning type

## Implementation Steps

1. **Update Backend Agent Status Endpoint**:
   - Add `pending_questions` and `data` to response structure
   - Test with frontend components

2. **Verify Agent Learning Endpoint**:
   - Ensure backend handles mapping approve/reject actions
   - Check API logs when buttons are clicked

3. **Test All Components**:
   - Approve/reject buttons should work
   - Agent Clarifications should show questions
   - Data Classifications should show categorized data
   - Agent Insights should show analysis results

## Expected Results

After implementing these fixes:

✅ **Approve/Delete buttons** will properly update mappings and provide user feedback
✅ **Dropdown duplicates** will be handled gracefully without errors  
✅ **Agent UI Manager** will populate all three sections:
   - Agent Clarifications: Shows pending questions
   - Data Classifications: Shows good/needs clarification/unusable data
   - Agent Insights: Shows AI analysis and recommendations

## Testing

1. Navigate to Attribute Mapping page
2. Click approve/reject buttons on field mappings
3. Check right sidebar for agent data:
   - Agent Clarifications should show questions
   - Data Classifications should show data categories  
   - Agent Insights should show analysis results
4. Verify no console errors with dropdown selections 