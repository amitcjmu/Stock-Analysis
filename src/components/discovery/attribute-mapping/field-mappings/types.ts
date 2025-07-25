export interface FieldMapping {
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

export interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

export interface FilterOptions {
  showApproved: boolean;
  showRejected: boolean;
  showPending: boolean;
}

export interface RejectionDialogState {
  isOpen: boolean;
  mappingId: string;
  sourceField: string;
  targetField: string;
}

export interface FieldMappingsListProps {
  fieldMappings: FieldMapping[];
  currentPage: number;
  itemsPerPage: number;
  availableFields: TargetField[];
  openDropdowns: Record<string, boolean>;
  approvingMappings: Set<string>;
  rejectingMappings: Set<string>;
  onToggleDropdown: (mappingId: string) => void;
  onTargetFieldChange: (mappingId: string, newTarget: string) => void;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, sourceField: string, targetField: string) => void;
  selectedCategory: string;
  searchTerm: string;
  loadingFields: boolean;
  onCategoryChange: (category: string) => void;
  onSearchTermChange: (term: string) => void;
}

export interface FieldMappingItemProps {
  mapping: FieldMapping;
  availableFields: TargetField[];
  isDropdownOpen: boolean;
  isApproving: boolean;
  isRejecting: boolean;
  onToggleDropdown: () => void;
  onTargetFieldChange: (newTarget: string) => void;
  onApproveMapping: () => void;
  onRejectMapping: () => void;
  selectedCategory: string;
  searchTerm: string;
  loadingFields: boolean;
  onCategoryChange: (category: string) => void;
  onSearchTermChange: (term: string) => void;
}

export interface TargetFieldSelectorProps {
  mapping: FieldMapping;
  availableFields: TargetField[];
  isOpen: boolean;
  onToggle: () => void;
  onSelect: (fieldName: string) => void;
  selectedCategory: string;
  searchTerm: string;
  loadingFields: boolean;
  onCategoryChange: (category: string) => void;
  onSearchTermChange: (term: string) => void;
}

export interface ApprovalWorkflowProps {
  mapping: FieldMapping;
  isApproving: boolean;
  isRejecting: boolean;
  onApprove: () => void;
  onReject: () => void;
}

export interface RejectionDialogProps {
  isOpen: boolean;
  mappingId: string;
  sourceField: string;
  targetField: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}

export interface MappingPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  filteredItems: number;
  startIndex: number;
  endIndex: number;
  onPageChange: (page: number) => void;
}

export interface MappingFiltersProps {
  filterOptions: FilterOptions;
  onFilterChange: (filters: FilterOptions) => void;
  mappingCounts: {
    pending: number;
    approved: number;
    rejected: number;
  };
}

export interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
}

export interface CategoryColors {
  [key: string]: string;
}

export const CATEGORY_COLORS: CategoryColors = {
  identification: 'bg-blue-100 text-blue-800',
  technical: 'bg-green-100 text-green-800',
  network: 'bg-purple-100 text-purple-800',
  environment: 'bg-yellow-100 text-yellow-800',
  business: 'bg-orange-100 text-orange-800',
  application: 'bg-pink-100 text-pink-800',
  migration: 'bg-indigo-100 text-indigo-800',
  cost: 'bg-red-100 text-red-800',
  risk: 'bg-gray-100 text-gray-800',
  dependencies: 'bg-cyan-100 text-cyan-800',
  performance: 'bg-teal-100 text-teal-800',
  discovery: 'bg-lime-100 text-lime-800',
  ai_insights: 'bg-violet-100 text-violet-800'
};
