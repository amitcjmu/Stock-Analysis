# Frontend State Management Patterns

## Collection Flow State Management
### Hook: useAdaptiveFormFlow
- Manages: Form data, validation, submission, completion state
- Key states: `isCompleted`, `flowId`, `questionnaires`, `formData`

### Completion State Pattern
```typescript
// Check for completion after submission
if (updatedQuestionnaires.length === 0) {
    setState(prev => ({ ...prev, isCompleted: true }));
}

// Component rendering based on completion
if (isCompleted) {
    return <CompletionScreen />;
}
```

## React Query Caching Patterns
### Questionnaire Fetching:
```typescript
const { data: questionnaires } = useQuery({
    queryKey: ['collection-questionnaires', flowId],
    staleTime: 30000, // 30 seconds to reduce refetch
    cacheTime: 5 * 60 * 1000, // 5 minutes
});
```

## Toast Notification Patterns
### Success States:
- Bootstrap submission: "Application Details Saved"
- Flow completion: "Collection Complete"
- Progress save: "Progress Saved"

### Error Handling:
- Always provide user-friendly messages
- Log detailed errors to console
- Offer fallback actions when possible

## Form Validation Integration
### Completion Percentage Calculation:
- Bootstrap forms: Force 100% on submission
- Regular forms: Calculate from field completion
- Store in `form_metadata.completion_percentage`

## WebSocket Integration Points
- Listen for: `questionnaire_ready` events
- Update on: `workflow_update` with status changes
- Trigger refetch on relevant events
