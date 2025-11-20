# AG Grid Column Selection Pattern with State Management

## Problem
Need selective bulk operations on AG Grid columns (e.g., approve/reject specific fields, not all mappings). Standard AG Grid row selection doesn't apply to column-level operations.

## Solution
Implement checkbox-based column selection using Set for state management, custom headerComponent for each column, and parent notification callbacks for coordinated bulk actions.

## Key Components

### 1. State Management (Set-based for O(1) lookups)
```typescript
const [selectedColumns, setSelectedColumns] = useState<Set<string>>(new Set());
```

### 2. "Select All" Header Checkbox with Indeterminate State
```typescript
headerComponent: () => {
  const allSelected = sourceFields.every((sf) => selectedColumns.has(sf));
  const someSelected = sourceFields.some((sf) => selectedColumns.has(sf)) && !allSelected;

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSelected = new Set(selectedColumns);
    if (e.target.checked) {
      sourceFields.forEach((sf) => newSelected.add(sf));
    } else {
      sourceFields.forEach((sf) => newSelected.delete(sf));
    }
    setSelectedColumns(newSelected);

    // Notify parent for bulk actions
    if (onSelectionChange) {
      onSelectionChange(Array.from(newSelected));
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={allSelected}
        ref={(input) => {
          if (input) input.indeterminate = someSelected;
        }}
        onChange={handleSelectAll}
        className="w-4 h-4 cursor-pointer"
        title="Select All Columns"
      />
      <span className="font-semibold">Row Type</span>
    </div>
  );
}
```

### 3. Individual Column Checkbox
```typescript
headerComponent: () => {
  const isSelected = selectedColumns.has(source_field);

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSelected = new Set(selectedColumns);
    if (e.target.checked) {
      newSelected.add(source_field);
    } else {
      newSelected.delete(source_field);
    }
    setSelectedColumns(newSelected);

    // Notify parent of selection change
    if (onSelectionChange) {
      onSelectionChange(Array.from(newSelected));
    }
  };

  return (
    <div className="flex items-center gap-2 w-full h-full">
      <input
        type="checkbox"
        checked={isSelected}
        onChange={handleCheckboxChange}
        className="w-4 h-4 cursor-pointer"
      />
      <span className="font-semibold">{source_field}</span>
    </div>
  );
}
```

### 4. Parent Component Integration
```typescript
interface Props {
  onSelectionChange?: (selectedSourceFields: string[]) => void;
}

// In parent component
const [selectedSourceFields, setSelectedSourceFields] = useState<string[]>([]);

const handleApproveSelected = async () => {
  const selectedMappings = fieldMappings.filter(m =>
    selectedSourceFields.includes(m.source_field)
  );

  for (const mapping of selectedMappings) {
    await onMappingAction(mapping.id, 'approve');
  }

  setSelectedSourceFields([]); // Clear selection
  queryClient.invalidateQueries({ queryKey: ['field-mappings'] });
};
```

## Benefits
- **Selective Operations**: Bulk approve/reject specific columns instead of all
- **Visual Feedback**: Indeterminate state shows "some selected"
- **Performance**: Set data structure provides O(1) lookup/add/delete
- **Coordinated Actions**: Parent receives selection updates for bulk operations

## Usage
Apply this pattern when:
- AG Grid needs column-level selection (not row selection)
- Bulk operations should apply to subset of columns
- Visual indication of selection state is important
- Parent component needs to coordinate actions based on selection

## Reference
- Implementation: `AttributeMappingAGGrid.tsx:148-304`
- Parent Integration: `FieldMappingsTab/index.tsx:98-248`
- Issue: #1076 (AG Grid Attribute Mapping) - Column Selection Feature
