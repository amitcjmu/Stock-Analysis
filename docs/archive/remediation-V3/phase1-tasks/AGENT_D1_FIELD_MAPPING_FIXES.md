# Phase 1 - Agent D1: Field Mapping Quick Fixes

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track D of Phase 1, focusing on immediate user-facing field mapping issues that are blocking productivity.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `docs/troubleshooting/discovery-flow-sync-issues.md` - Current issues
- Review recent commits related to field mapping fixes

### Phase 1 Goal
Stabilize the field mapping functionality to unblock users while other agents work on the broader architectural improvements. These are tactical fixes that will be properly refactored in Phase 2.

## Your Specific Tasks

### 1. Fix Dropdown Close Behavior
**File**: `src/components/discovery/attribute-mapping/FieldMappingsTab.tsx`

Current Issue: Dropdowns don't close when clicking outside
```typescript
// Add proper click-outside detection
useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as Element;
    // Check if click is outside all dropdown containers
    if (!target.closest('.dropdown-container')) {
      setOpenDropdowns({});
    }
  };
  
  document.addEventListener('mousedown', handleClickOutside);
  return () => {
    document.removeEventListener('mousedown', handleClickOutside);
  };
}, []);
```

Ensure:
- All dropdowns have the `dropdown-container` class
- Event listeners are properly cleaned up
- No memory leaks
- Works with multiple dropdowns

### 2. Fix Approve/Reject API Errors
**Files to modify**:
- `src/hooks/discovery/useAttributeMappingLogic.ts`
- `backend/app/api/v1/endpoints/data_import/field_mapping.py`

Current Issue: 500 errors due to ID mismatches

Frontend fix:
```typescript
// Update handleApproveMapping to use correct IDs
const handleApproveMapping = useCallback(async (mappingId: string) => {
  try {
    // Ensure we're using the database mapping ID, not temp IDs
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping || mapping.id.startsWith('mapping-')) {
      console.error('Invalid mapping ID:', mappingId);
      return;
    }
    
    const result = await apiCall(`/data-import/mappings/${mappingId}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        import_id: flow?.data_import_id // Use correct import ID
      })
    });
    
    // Handle success
  } catch (error) {
    // Proper error handling
  }
}, [fieldMappings, flow, getAuthHeaders]);
```

Backend fix:
```python
@router.post("/mappings/{mapping_id}/approve")
async def approve_field_mapping(
    mapping_id: str,
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Approve with proper context checking"""
    try:
        # Verify mapping exists and belongs to current context
        mapping = await db.get(ImportFieldMapping, mapping_id)
        if not mapping:
            raise HTTPException(404, "Mapping not found")
        
        # Verify context access
        if mapping.client_account_id != context.client_account_id:
            raise HTTPException(403, "Access denied")
        
        # Update mapping
        mapping.status = "approved"
        mapping.validated_at = datetime.utcnow()
        mapping.validated_by = context.user_id
        
        await db.commit()
        return {"status": "success", "mapping_id": mapping_id}
        
    except Exception as e:
        logger.error(f"Failed to approve mapping: {e}")
        await db.rollback()
        raise HTTPException(500, str(e))
```

### 3. Fix Data Import ID Usage
**Issue**: Foreign key violations due to using flow_id instead of data_import_id

Files to check and fix:
- `src/hooks/discovery/useAttributeMappingLogic.ts`
- All API calls passing `import_id` parameter

Ensure:
```typescript
// Always use data_import_id from flow, not flow_id
const importId = flow?.data_import_id;
if (!importId) {
  console.error('No data_import_id available');
  return;
}
```

### 4. Add Comprehensive Error Handling
**All field mapping components and hooks**

Implement proper error boundaries and user feedback:
```typescript
// Error boundary for field mapping section
export class FieldMappingErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Field mapping error:', error, errorInfo);
    // Log to monitoring service
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <Alert severity="error">
          <AlertTitle>Field Mapping Error</AlertTitle>
          Something went wrong with field mappings. 
          <Button onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        </Alert>
      );
    }
    return this.props.children;
  }
}
```

### 5. Ensure Multi-Tenant Context
**Backend validation for all field mapping operations**

Add context checking to all endpoints:
```python
def validate_context_access(
    resource: Any, 
    context: RequestContext
) -> None:
    """Validate user has access to resource"""
    if hasattr(resource, 'client_account_id'):
        if resource.client_account_id != context.client_account_id:
            raise HTTPException(403, "Access denied")
    
    if hasattr(resource, 'engagement_id') and context.engagement_id:
        if resource.engagement_id != context.engagement_id:
            raise HTTPException(403, "Access denied")
```

### 6. Add Loading States and User Feedback
**Frontend components**

Improve UX with proper loading states:
```typescript
// Loading states for all async operations
const [approvingMappings, setApprovingMappings] = useState<Set<string>>(new Set());

const handleApproveMapping = async (mappingId: string) => {
  setApprovingMappings(prev => new Set(prev).add(mappingId));
  try {
    // ... approval logic
    showSuccessToast('Mapping approved successfully');
  } catch (error) {
    showErrorToast('Failed to approve mapping');
  } finally {
    setApprovingMappings(prev => {
      const next = new Set(prev);
      next.delete(mappingId);
      return next;
    });
  }
};

// In render
<Button 
  disabled={approvingMappings.has(mapping.id)}
  loading={approvingMappings.has(mapping.id)}
>
  {approvingMappings.has(mapping.id) ? 'Approving...' : 'Approve'}
</Button>
```

## Success Criteria
- [ ] Dropdowns close properly when clicking outside
- [ ] No 500 errors on approve/reject operations
- [ ] Correct data_import_id usage throughout
- [ ] Comprehensive error handling with user feedback
- [ ] All operations respect multi-tenant context
- [ ] Loading states for all async operations
- [ ] No console errors in browser
- [ ] All field mapping operations complete in <200ms

## Testing Checklist
```yaml
Manual Testing:
  - [ ] Create new field mapping
  - [ ] Open dropdown and click outside - should close
  - [ ] Open multiple dropdowns - only one at a time
  - [ ] Approve mapping - should succeed
  - [ ] Reject mapping - should succeed
  - [ ] Modify mapping - should update
  - [ ] Test with multiple browser tabs
  - [ ] Test with slow network (throttle to 3G)
  - [ ] Test error scenarios (offline, timeout)

Automated Testing:
  - [ ] Unit tests for all hooks
  - [ ] Integration tests for API endpoints
  - [ ] E2E test for complete flow
```

## Quick Fix Implementation Order
1. Fix dropdown behavior (1 hour)
2. Fix API errors (2 hours)
3. Fix data_import_id usage (1 hour)
4. Add error handling (2 hours)
5. Add loading states (1 hour)
6. Test everything (1 hour)

Total: ~8 hours

## Commands to Run
```bash
# Frontend testing
docker exec -it migration_frontend npm run test -- --watch
docker exec -it migration_frontend npm run lint

# Backend testing
docker exec -it migration_backend python -m pytest tests/api/test_field_mapping.py -v

# E2E testing
docker exec -it migration_frontend npm run test:e2e -- field-mapping.spec.ts
```

## Definition of Done
- [ ] All identified issues fixed
- [ ] No console errors in browser
- [ ] All API calls succeed
- [ ] User can complete field mapping workflow
- [ ] Tests updated and passing
- [ ] No regressions introduced
- [ ] PR created with title: "fix: [Phase1-D1] Field mapping stability fixes"
- [ ] Tested in Docker environment

## Coordination Notes
- These are tactical fixes - proper refactoring comes in Phase 2
- Coordinate with Agent C1 on state management changes
- Work with Agent B1 if API changes needed
- Keep fixes minimal and focused
- Document any workarounds for Phase 2

## Common Pitfalls to Avoid
1. Don't refactor the entire system - just fix the issues
2. Don't break existing functionality
3. Don't skip error handling
4. Don't forget loading states
5. Don't bypass context checks
6. Test in Docker, not local environment

## Notes
- Users are actively blocked by these issues
- Priority is stability over perfection
- Some technical debt is acceptable for now
- Focus on user experience
- Keep changes isolated and easy to revert