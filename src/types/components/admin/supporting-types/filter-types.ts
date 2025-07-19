/**
 * Filter Types
 * 
 * Filter configuration, search settings, and filtering-related
 * type definitions.
 */

export interface FilterConfig {
  filters: Filter[];
  search?: SearchConfig;
  sorting?: SortConfig;
  grouping?: GroupConfig;
}

export interface Filter {
  key: string;
  label: string;
  type: FilterType;
  field: string;
  operator?: FilterOperator;
  value?: any;
  options?: FilterOption[];
  multiple?: boolean;
  clearable?: boolean;
  searchable?: boolean;
}

export interface SearchConfig {
  enabled: boolean;
  fields: string[];
  placeholder?: string;
  fuzzy?: boolean;
  minLength?: number;
  debounce?: number;
}

export interface SortConfig {
  field: string;
  direction: SortDirection;
  multiple?: boolean;
  priority?: number;
}

export interface GroupConfig {
  field: string;
  label?: string;
  direction?: SortDirection;
  collapsed?: boolean;
}

export interface FilterOption {
  label: string;
  value: any;
  count?: number;
  disabled?: boolean;
  description?: string;
}

// Enum and union types
export type FilterType = 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'numberrange' | 'boolean' | 'search';
export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_null' | 'is_not_null';
export type SortDirection = 'asc' | 'desc';