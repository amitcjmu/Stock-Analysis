/**
 * Data Fetching Hook Types
 *
 * Hook interfaces for data operations including pagination, sorting, filtering, and search functionality.
 */

import type { ReactNode } from 'react';

// Data fetching hooks
export interface UsePaginationParams {
  initialPage?: number;
  initialPageSize?: number;
  total?: number;
  onPageChange?: (page: number, pageSize: number) => void;
}

export interface UsePaginationReturn {
  currentPage: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  isFirstPage: boolean;
  isLastPage: boolean;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setTotal: (total: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  firstPage: () => void;
  lastPage: () => void;
  goToPage: (page: number) => void;
  getPageNumbers: (delta?: number) => number[];
}

export interface UseSortingParams<T> {
  initialSortBy?: string;
  initialSortOrder?: 'asc' | 'desc';
  onSort?: (sortBy: string, sortOrder: 'asc' | 'desc', data: T[]) => void;
}

export interface UseSortingReturn<T> {
  sortBy: string | null;
  sortOrder: 'asc' | 'desc';
  sort: (data: T[]) => T[];
  setSortBy: (field: string) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  toggleSortOrder: () => void;
  resetSort: () => void;
  isSorted: boolean;
  getSortedData: (data: T[]) => T[];
}

export interface UseFilteringParams<T> {
  initialFilters?: Record<string, string | number | boolean | null>;
  onFilter?: (filters: Record<string, string | number | boolean | null>, data: T[]) => void;
}

export interface UseFilteringReturn<T> {
  filters: Record<string, string | number | boolean | null>;
  setFilter: (key: string, value: unknown) => void;
  removeFilter: (key: string) => void;
  clearFilters: () => void;
  hasFilters: boolean;
  filter: (data: T[]) => T[];
  getFilteredData: (data: T[]) => T[];
}

export interface UseSearchParams<T> {
  searchFields?: string[];
  caseSensitive?: boolean;
  onSearch?: (query: string, results: T[]) => void;
}

export interface UseSearchReturn<T> {
  query: string;
  setQuery: (query: string) => void;
  clearQuery: () => void;
  hasQuery: boolean;
  search: (data: T[]) => T[];
  getSearchResults: (data: T[]) => T[];
  highlightMatches: (text: string) => ReactNode[];
}
