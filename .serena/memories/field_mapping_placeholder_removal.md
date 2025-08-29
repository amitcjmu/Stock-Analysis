# Field Mapping Placeholder/Fallback Removal Pattern

## Context
Field mapping system had placeholder and fallback logic that created confusion about data state and made debugging difficult.

## Decision: Complete Removal (Aug 2025)
Removed all placeholder/fallback logic to make the system cleaner and more transparent.

## Files Modified

### Frontend Changes

#### 1. useFieldMappings.ts
```typescript
// REMOVED: Placeholder creation logic
// Before: Created placeholder mappings for unmapped fields
const additionalMappings = missingFields.map(sourceField => ({
  id: crypto.randomUUID(),
  source_field: sourceField,
  target_field: 'UNMAPPED',
  is_placeholder: true
}));

// After: Just log unmapped fields
if (missingFields.length > 0) {
  console.warn(`⚠️ Found ${missingFields.length} unmapped CSV fields`, missingFields);
}
```

#### 2. Type Definitions
```typescript
// REMOVED from FieldMapping interface:
is_placeholder?: boolean;
is_fallback?: boolean;
```

#### 3. UI Components
```typescript
// REMOVED validation checks
if (mapping && (mapping.is_placeholder || mapping.is_fallback)) {
  console.warn('Cannot approve placeholder mapping');
  return;
}

// ADDED user feedback
if (!mapping) {
  if (window.showWarningToast) {
    window.showWarningToast('Selected mapping could not be found. Please refresh.');
  }
  return;
}
```

## Benefits of Removal
1. **Transparency**: Clear data state without hidden placeholders
2. **Simplicity**: Reduced conditional logic throughout codebase
3. **Debuggability**: Easier to trace mapping issues
4. **Backend Authority**: Backend handles all mapping generation

## Implementation Pattern

### State Cleanup with Finally Blocks
```typescript
const handleApprove = async (mappingId: string): void => {
  setProcessingMappings(prev => new Set(prev).add(mappingId));

  try {
    await onMappingAction(mappingId, 'approve');
    // Success logic
  } catch (error) {
    console.error('Error:', error);
  } finally {
    // Always cleanup state
    setTimeout(() => {
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        newSet.delete(mappingId);
        return newSet;
      });
    }, 300);
  }
};
```

## Return Type Consistency
```typescript
// Ensure void return for event handlers
const handleRefresh = (): void => {  // NOT JSX.Element
  // ...
};

const toggleExpansion = (id: string): void => {  // NOT unknown
  // ...
};
```

## Key Principle
Let the backend be the single source of truth for field mappings. Frontend only displays and manages user interactions, never creates synthetic data.
