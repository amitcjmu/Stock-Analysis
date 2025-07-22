/**
 * Reusable Filter Management Hook
 * Common pattern for filter state management across components
 */

import { useState, useMemo, useCallback } from 'react';

type FilterValue = string | number | boolean | string[] | number[] | null | undefined;

export interface FilterConfig<T = Record<string, FilterValue>> {
  [key: string]: {
    type: 'string' | 'select' | 'multi-select' | 'date-range';
    defaultValue: FilterValue;
    options?: Array<{ value: string; label: string }>;
  };
}

export interface UseFiltersResult<T> {
  filters: T;
  setFilter: (key: keyof T, value: FilterValue) => void;
  setFilters: (filters: Partial<T>) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
}

export function useFilters<T extends Record<string, FilterValue>>(
  config: FilterConfig<T>
): UseFiltersResult<T> {
  // Initialize filters with default values
  const defaultFilters = useMemo(() => {
    const defaults = {} as T;
    Object.keys(config).forEach(key => {
      defaults[key as keyof T] = config[key].defaultValue;
    });
    return defaults;
  }, [config]);

  const [filters, setFiltersState] = useState<T>(defaultFilters);

  const setFilter = useCallback((key: keyof T, value: FilterValue) => {
    setFiltersState(prev => ({ ...prev, [key]: value }));
  }, []);

  const setFilters = useCallback((newFilters: Partial<T>) => {
    setFiltersState(prev => ({ ...prev, ...newFilters }));
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState(defaultFilters);
  }, [defaultFilters]);

  const hasActiveFilters = useMemo(() => {
    return Object.keys(filters).some(key => {
      const currentValue = filters[key as keyof T];
      const defaultValue = defaultFilters[key as keyof T];
      return currentValue !== defaultValue;
    });
  }, [filters, defaultFilters]);

  return {
    filters,
    setFilter,
    setFilters,
    clearFilters,
    hasActiveFilters
  };
}