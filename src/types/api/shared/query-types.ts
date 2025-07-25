/**
 * Query API Types
 *
 * Types for filtering, sorting, searching, and data querying operations.
 */

import type { PrimitiveValue } from './value-types'
import type { FilterValue } from './value-types'

// Query parameters
export interface SortParameter {
  field: string;
  direction: 'asc' | 'desc';
  priority?: number;
  nullsFirst?: boolean;
}

export interface FilterParameter {
  field: string;
  operator: FilterOperator;
  value: FilterValue;
  values?: FilterValue[];
  caseSensitive?: boolean;
  negate?: boolean;
}

export interface SearchParameter {
  query: string;
  fields?: string[];
  operator?: 'and' | 'or';
  boost?: Record<string, number>;
  fuzzy?: boolean;
  exactMatch?: boolean;
  caseSensitive?: boolean;
}

export interface AppliedFilter {
  field: string;
  operator: FilterOperator;
  value: FilterValue;
  label?: string;
  count?: number;
}

export interface AppliedSort {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface Aggregation {
  name: string;
  type: string;
  field: string;
  buckets?: AggregationBucket[];
  value?: number;
  metrics?: Record<string, number>;
}

export interface AggregationBucket {
  key: PrimitiveValue | Record<string, PrimitiveValue>;
  label?: string;
  count: number;
  selected?: boolean;
  metrics?: Record<string, number>;
}

// Filter operators
export type FilterOperator =
  | 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte'
  | 'in' | 'nin' | 'contains' | 'ncontains'
  | 'startswith' | 'endswith' | 'regex'
  | 'exists' | 'nexists' | 'between'
  | 'isNull' | 'isNotNull' | 'isEmpty' | 'isNotEmpty';

// Time range for queries
export interface TimeRange {
  start: string;
  end: string;
  timezone?: string;
}

// Aggregation requests and results
export interface AggregationRequest {
  name: string;
  type: 'terms' | 'date_histogram' | 'range' | 'stats' | 'cardinality';
  field: string;
  size?: number;
  interval?: string;
  ranges?: AggregationRange[];
  nested?: AggregationRequest[];
}

export interface AggregationRange {
  from?: number;
  to?: number;
  key?: string;
}

export interface AggregationResult {
  name: string;
  buckets?: AggregationBucket[];
  value?: number;
  count?: number;
  stats?: AggregationStats;
}

export interface AggregationStats {
  count: number;
  min: number;
  max: number;
  avg: number;
  sum: number;
}
