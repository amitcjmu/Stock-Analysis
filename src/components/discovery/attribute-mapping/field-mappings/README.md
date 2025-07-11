# Modular Field Mappings Components

This directory contains the modular field mappings components that were refactored from the original monolithic `FieldMappingsTab.tsx` component (676 LOC).

## Architecture Overview

The field mappings system has been decomposed into 7 specialized components, each handling specific aspects of the field mapping functionality:

```
FieldMappingsTab (Main Composition)
├── MappingFilters (Filter Controls)
├── FieldMappingsList (List Container)
│   └── FieldMappingItem (Individual Mapping)
│       ├── TargetFieldSelector (Field Selection)
│       └── ApprovalWorkflow (Approve/Reject)
├── MappingPagination (Pagination Controls)
└── RejectionDialog (Rejection Modal)
```

## Component Breakdown

### 1. MappingFilters
**File:** `MappingFilters.tsx`  
**Purpose:** Filter controls for mapping status  
**Features:**
- Checkbox filters for pending, approved, rejected
- Live count display for each status
- Filter state management
- Clean filter UI layout

### 2. FieldMappingsList
**File:** `FieldMappingsList.tsx`  
**Purpose:** Container for mapping items with virtualization  
**Features:**
- Scrollable list container
- Pagination support
- Empty state handling
- Efficient rendering of large lists

### 3. FieldMappingItem
**File:** `FieldMappingItem.tsx`  
**Purpose:** Individual mapping row component  
**Features:**
- Mapping information display
- Status indicators and styling
- Integration with selector and approval components
- Confidence level visualization
- AI reasoning display

### 4. TargetFieldSelector
**File:** `TargetFieldSelector.tsx`  
**Purpose:** Dropdown with search and filter for field selection  
**Features:**
- Advanced dropdown with search
- Category-based filtering
- Field requirement indicators
- Custom field support
- Real-time search functionality

### 5. ApprovalWorkflow
**File:** `ApprovalWorkflow.tsx`  
**Purpose:** Approve/reject buttons and workflow logic  
**Features:**
- Approve and reject buttons
- Loading states during operations
- Status-based conditional rendering
- Bulk action support potential

### 6. MappingPagination
**File:** `MappingPagination.tsx`  
**Purpose:** Pagination controls and navigation  
**Features:**
- Previous/next navigation
- Item count display
- Filtered vs total count display
- Accessible pagination controls

### 7. RejectionDialog
**File:** `RejectionDialog.tsx`  
**Purpose:** Modal for rejection reasons and confirmation  
**Features:**
- Pre-defined rejection reasons
- Custom reason input
- Form validation
- Modal overlay and escape handling

## TypeScript Types

All components use strict TypeScript typing defined in `types.ts`:

```typescript
interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  action?: 'ignore' | 'delete';
}

interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

interface FilterOptions {
  showApproved: boolean;
  showRejected: boolean;
  showPending: boolean;
}
```

## Main FieldMappingsTab Component

The main `FieldMappingsTab.tsx` component serves as the composition root:

```typescript
const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onMappingChange
}) => {
  // State management
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({...});
  
  // Event handlers
  const handleApproveMapping = async (mappingId: string) => {...};
  const handleRejectMapping = async (mappingId: string, reason?: string) => {...};
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <MappingFilters {...filterProps} />
      <FieldMappingsList {...listProps} />
      <MappingPagination {...paginationProps} />
      <RejectionDialog {...dialogProps} />
    </div>
  );
};
```

## Usage

### Basic Usage
```typescript
import { FieldMappingsTab } from './components/discovery/attribute-mapping/field-mappings';

function AttributeMappingPage() {
  return (
    <FieldMappingsTab
      fieldMappings={mappings}
      isAnalyzing={false}
      onMappingAction={handleMappingAction}
      onMappingChange={handleMappingChange}
    />
  );
}
```

### Individual Component Usage
```typescript
import { 
  FieldMappingItem, 
  TargetFieldSelector, 
  ApprovalWorkflow 
} from './components/discovery/attribute-mapping/field-mappings';

// Use components individually if needed
<FieldMappingItem 
  mapping={mapping}
  availableFields={fields}
  onApproveMapping={handleApprove}
  onRejectMapping={handleReject}
/>
```

## State Management

The field mappings system manages several types of state:

1. **Data State**: Field mappings and available target fields
2. **UI State**: Pagination, filters, dropdown states
3. **Loading State**: API calls and async operations
4. **Modal State**: Dialog visibility and form data

## API Integration

The system integrates with the backend API for:

- **Available Fields**: Fetching target field options
- **Mapping Actions**: Approve/reject operations
- **Field Changes**: Updating target field selections
- **Authentication**: Multi-tenant header management

## Performance Considerations

- **Debounced API Calls**: Prevents excessive API requests
- **Memoization**: Efficient re-rendering with React hooks
- **Pagination**: Handles large datasets efficiently
- **Virtualization**: Scrollable containers for performance
- **Caching**: Available fields caching to reduce API calls

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support for all controls
- **Screen Reader Support**: Proper ARIA labels and roles
- **Focus Management**: Logical tab order and focus trapping
- **Color Coding**: Meaningful color usage with sufficient contrast
- **Loading States**: Clear loading indicators

## Category System

The system supports a comprehensive category system for field organization:

```typescript
const CATEGORY_COLORS: CategoryColors = {
  identification: 'bg-blue-100 text-blue-800',
  technical: 'bg-green-100 text-green-800',
  network: 'bg-purple-100 text-purple-800',
  environment: 'bg-yellow-100 text-yellow-800',
  business: 'bg-orange-100 text-orange-800',
  application: 'bg-pink-100 text-pink-800',
  migration: 'bg-indigo-100 text-indigo-800',
  // ... more categories
};
```

## Migration Notes

The original `FieldMappingsTab.tsx` (676 LOC) has been completely refactored into this modular system while maintaining:

- **✅ 100% Functional Parity**: All original functionality preserved
- **✅ Same Component API**: Drop-in replacement
- **✅ Identical Styling**: CSS classes and styles maintained
- **✅ State Management**: All state behavior preserved
- **✅ API Integration**: All API calls working
- **✅ TypeScript Safety**: Improved type safety

## Benefits of Modularization

1. **Maintainability**: Each component has a single responsibility
2. **Reusability**: Components can be used independently
3. **Testability**: Easier to unit test individual components
4. **Readability**: Smaller, focused components are easier to understand
5. **Scalability**: Easy to add new features to specific components
6. **Performance**: Better optimization opportunities
7. **Type Safety**: Better TypeScript inference and error detection

## File Structure

```
src/components/discovery/attribute-mapping/field-mappings/
├── index.ts                    # Main exports
├── types.ts                    # TypeScript type definitions
├── FieldMappingsTab.tsx        # Main composition component
├── MappingFilters.tsx          # Filter controls
├── FieldMappingsList.tsx       # List container
├── FieldMappingItem.tsx        # Individual mapping item
├── TargetFieldSelector.tsx     # Field selection dropdown
├── ApprovalWorkflow.tsx        # Approve/reject workflow
├── MappingPagination.tsx       # Pagination controls
├── RejectionDialog.tsx         # Rejection modal
└── README.md                   # This documentation
```

## Advanced Features

### Smart Field Matching
- AI-powered field suggestions
- Confidence scoring
- Sample value analysis
- Reasoning explanations

### Bulk Operations
- Multi-select support (future enhancement)
- Batch approve/reject operations
- Bulk field reassignment

### Advanced Filtering
- Search across multiple field properties
- Category-based filtering
- Confidence level filtering
- Status-based filtering

## Testing

Each component should be tested individually:

```typescript
// Example test for FieldMappingItem
import { render, screen } from '@testing-library/react';
import { FieldMappingItem } from './FieldMappingItem';

test('renders mapping with correct confidence level', () => {
  render(
    <FieldMappingItem 
      mapping={mockMapping}
      availableFields={mockFields}
      onApproveMapping={jest.fn()}
      onRejectMapping={jest.fn()}
    />
  );
  
  expect(screen.getByText('85% confidence')).toBeInTheDocument();
});
```

## Contributing

When adding new features:

1. **Single Responsibility**: Keep each component focused
2. **Type Safety**: Add proper TypeScript types
3. **Accessibility**: Ensure ARIA compliance
4. **Performance**: Consider virtualization for large datasets
5. **Documentation**: Update README and inline docs
6. **Testing**: Add appropriate tests
7. **Consistency**: Follow existing patterns and conventions

## Common Patterns

### Error Handling
```typescript
try {
  await onMappingAction(mappingId, 'approve');
} catch (error) {
  console.error('Failed to approve mapping:', error);
  // Handle error appropriately
}
```

### Loading States
```typescript
const [isLoading, setIsLoading] = useState(false);

const handleAction = async () => {
  setIsLoading(true);
  try {
    await performAction();
  } finally {
    setIsLoading(false);
  }
};
```

### Conditional Rendering
```typescript
{mapping.status === 'pending' && (
  <ApprovalWorkflow 
    onApprove={handleApprove}
    onReject={handleReject}
  />
)}
```