# AG Grid Cell Renderers - Attribute Mapping

Custom cell renderers for the AG Grid-based attribute mapping interface. These renderers provide specialized UI components for different row types in the mapping grid.

## Overview

The attribute mapping grid uses three distinct renderers for different row types:

1. **MappingCellRenderer** (Row 1) - Interactive mapping dropdown
2. **ColumnHeaderRenderer** (Row 2) - Source field headers
3. **DataCellRenderer** (Rows 3-10) - Preview data values

## Components

### 1. MappingCellRenderer

**Purpose**: Provides an interactive dropdown for mapping source fields to target system fields.

**Features**:
- Searchable dropdown with typeahead filtering
- Status badges (Approved, Suggested, Needs Review, Unmapped)
- Confidence score display (High/Medium/Low with percentage)
- Approve/Reject action buttons
- Outside click detection to close dropdown
- Keyboard navigation (Escape to close)
- Disabled state for approved mappings

**Props**:
```typescript
interface MappingCellRendererProps extends ICellRendererParams {
  value: MappingCellValue;
  sourceField: string;
  availableTargetFields: string[];
  onSelect?: (sourceField: string, targetField: string) => void;
  onApprove?: (mappingId: string) => void;
  onReject?: (mappingId: string) => void;
}

interface MappingCellValue {
  target_field: string | null;
  status: FieldMappingStatus;
  confidence_score: number;
  mapping_id: string;
}
```

**Status Badge Colors**:
- **Approved** - Green with checkmark icon
- **Suggested** - Secondary (blue) with percentage
- **Needs Review** - Outline with yellow alert icon
- **Rejected** - Destructive (red) with X icon
- **Unmapped** - Gray outline with gray alert icon

**Confidence Levels**:
- **High**: >= 80%
- **Medium**: 50-79%
- **Low**: < 50%

**Usage Example**:
```typescript
const columnDef = {
  field: 'mapping',
  cellRenderer: MappingCellRenderer,
  cellRendererParams: {
    sourceField: 'customer_id',
    availableTargetFields: ['id', 'customer_number', 'client_id'],
    onSelect: (source, target) => handleMappingChange(source, target),
    onApprove: (mappingId) => handleApprove(mappingId),
    onReject: (mappingId) => handleReject(mappingId)
  }
};
```

---

### 2. ColumnHeaderRenderer

**Purpose**: Displays the original CSV/JSON column header names in a read-only format.

**Features**:
- FileText icon indicator
- Italicized styling for visual distinction
- Gray background for separation
- Automatic truncation for long names (> 40 chars)
- Tooltip on hover showing full name

**Props**:
```typescript
interface ColumnHeaderRendererProps extends ICellRendererParams {
  value: string;
}
```

**Usage Example**:
```typescript
const columnDef = {
  field: 'source_header',
  cellRenderer: ColumnHeaderRenderer
};
```

---

### 3. DataCellRenderer

**Purpose**: Displays preview data values from imported CSV/JSON files.

**Features**:
- Handles multiple data types (string, number, boolean, JSON objects)
- Null/undefined displayed as "-" in gray
- Automatic truncation for long values (> 50 chars)
- Tooltip on hover showing full value
- Type-specific formatting (boolean → "true"/"false")

**Props**:
```typescript
interface DataCellRendererProps extends ICellRendererParams {
  value: unknown;
}
```

**Usage Example**:
```typescript
const columnDef = {
  field: 'preview_data',
  cellRenderer: DataCellRenderer
};
```

---

## Integration with AG Grid

### Basic Setup

```typescript
import {
  MappingCellRenderer,
  ColumnHeaderRenderer,
  DataCellRenderer
} from '@/components/discovery/attribute-mapping/renderers';

const columnDefs = [
  {
    headerName: 'Mapping',
    field: 'mapping',
    cellRenderer: MappingCellRenderer,
    cellRendererParams: {
      sourceField: 'customer_name',
      availableTargetFields: targetFieldNames,
      onSelect: handleMappingChange,
      onApprove: handleApprove,
      onReject: handleReject
    },
    flex: 2
  },
  {
    headerName: 'Source Header',
    field: 'source_header',
    cellRenderer: ColumnHeaderRenderer,
    flex: 1
  },
  {
    headerName: 'Data Preview',
    field: 'preview',
    cellRenderer: DataCellRenderer,
    flex: 1
  }
];
```

### Dynamic Row Configuration

The renderers are designed to work with different row types in a single grid:

```typescript
const rowData = [
  // Row 1: Mapping controls
  {
    rowType: 'mapping',
    mapping: {
      target_field: 'customer_name',
      status: 'suggested',
      confidence_score: 0.85,
      mapping_id: 'uuid-123'
    }
  },
  // Row 2: Column headers
  {
    rowType: 'header',
    source_header: 'cust_name'
  },
  // Rows 3-10: Data preview
  {
    rowType: 'data',
    preview: 'Acme Corporation'
  },
  // ... more data rows
];
```

---

## Styling

All renderers use:
- **Tailwind CSS** for styling
- **Shadcn UI Badge** component for status indicators
- **Lucide React** icons (FileText, ChevronDown, Check, X, AlertCircle, CheckCircle)

### Customization

Modify Tailwind classes in component files:
- `className` properties for layout
- Badge `variant` prop for color schemes

---

## Accessibility

All renderers implement proper accessibility features:

### MappingCellRenderer
- `aria-label` on dropdown button
- `aria-expanded` for dropdown state
- `aria-haspopup="listbox"` for dropdown menu
- `role="listbox"` on dropdown container
- `role="option"` on field items
- `aria-selected` on selected items
- Keyboard navigation support

### ColumnHeaderRenderer
- `title` attribute for tooltips
- Semantic HTML structure

### DataCellRenderer
- `title` attribute for full value on hover
- Proper null/undefined handling with "-" indicator

---

## Performance Considerations

### MappingCellRenderer
- **Dropdown Optimization**: Only renders when open
- **Search Filtering**: Case-insensitive, client-side filtering
- **Event Cleanup**: Properly removes event listeners on unmount
- **Memoization**: Consider memoizing `filteredFields` for large datasets (50+ fields)

### ColumnHeaderRenderer
- **Lightweight**: Minimal re-renders
- **Static Content**: Header values rarely change

### DataCellRenderer
- **Type Checking**: Efficient value type detection
- **Truncation**: Pre-computed to avoid layout shifts

---

## Edge Cases Handled

### MappingCellRenderer
- Empty `availableTargetFields` array
- Null/undefined `target_field`
- Missing callback functions (graceful no-op)
- Rapid clicking (dropdown state management)
- Long field names in dropdown (scrollable container)
- Approved mappings (disabled state)

### ColumnHeaderRenderer
- Empty/null header values (displays "(empty)")
- Very long header names (truncated at 40 chars)

### DataCellRenderer
- Null/undefined values (displays "-")
- Boolean values (displays "true"/"false")
- JSON objects (stringified with fallback)
- Very long strings (truncated at 50 chars)

---

## Testing Recommendations

### Unit Tests
```typescript
describe('MappingCellRenderer', () => {
  it('should open dropdown on click', () => { /* ... */ });
  it('should filter fields on search', () => { /* ... */ });
  it('should call onSelect when field selected', () => { /* ... */ });
  it('should close dropdown on outside click', () => { /* ... */ });
  it('should close dropdown on Escape key', () => { /* ... */ });
  it('should disable dropdown for approved mappings', () => { /* ... */ });
});

describe('ColumnHeaderRenderer', () => {
  it('should display header with icon', () => { /* ... */ });
  it('should truncate long headers', () => { /* ... */ });
  it('should show tooltip for truncated headers', () => { /* ... */ });
});

describe('DataCellRenderer', () => {
  it('should display string values', () => { /* ... */ });
  it('should display boolean as "true"/"false"', () => { /* ... */ });
  it('should display null as "-"', () => { /* ... */ });
  it('should truncate long values', () => { /* ... */ });
});
```

### Manual Testing Checklist
- [ ] Dropdown opens/closes correctly
- [ ] Search filtering works (case-insensitive)
- [ ] Field selection updates mapping
- [ ] Approve/Reject buttons work
- [ ] Status badges show correct colors
- [ ] Confidence scores display correctly
- [ ] Outside click closes dropdown
- [ ] Escape key closes dropdown
- [ ] Approved mappings are disabled
- [ ] Long field names truncate properly
- [ ] Tooltips appear on hover

---

## Future Enhancements

Potential improvements for consideration:

1. **MappingCellRenderer**:
   - Category filtering in dropdown
   - Multi-select for bulk operations
   - Undo/redo support
   - Inline editing of confidence scores
   - Drag-and-drop support

2. **ColumnHeaderRenderer**:
   - Data type indicator (string, number, date)
   - Sample value count

3. **DataCellRenderer**:
   - Data type-specific formatting (dates, currencies)
   - Inline validation warnings
   - Copy-to-clipboard button

---

## Dependencies

- **react**: ^18.x
- **ag-grid-community**: Latest
- **lucide-react**: Icons
- **@/components/ui/badge**: Shadcn UI Badge component
- **@/types/api/discovery/field-mapping-types**: Type definitions
- **tailwindcss**: Styling

---

## Related Components

- **AG Grid Core Component** (Issue #1077)
- **ThreeColumnFieldMapper**: Reference implementation for dropdown patterns
- **TargetFieldSelector**: Similar dropdown implementation in field mappings

---

## Maintainer Notes

- Follow snake_case naming convention for all field names (per CLAUDE.md)
- No WebSocket usage - all updates via HTTP polling
- Ensure multi-tenant context in all API calls
- Add proper TypeScript types for all props
- Document any new status types in FieldMappingStatus enum

---

## Support

For questions or issues with these renderers:
1. Check Issue #1078 (implementation task)
2. Check Issue #1076 (parent task)
3. Review `/docs/analysis/Notes/coding-agent-guide.md`
4. Review `/docs/analysis/Notes/000-lessons.md`
