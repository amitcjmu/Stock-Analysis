/**
 * Custom hook for persisting AG Grid column state (visibility and order)
 *
 * This hook solves the issue where column rearrangement is lost when data
 * is refetched after row operations (delete, update, etc.)
 *
 * Features:
 * - Persists column visibility to localStorage
 * - Persists column order to localStorage
 * - Restores state on component mount
 * - Automatically saves state when columns are toggled or reordered
 */

import { useState, useEffect, useCallback } from 'react';
import type { ColumnState } from 'ag-grid-community';

const STORAGE_KEY_PREFIX = 'inventory-column-state';

interface UseColumnStateOptions {
  storageKey?: string;
  defaultColumns: string[];
}

interface UseColumnStateReturn {
  selectedColumns: string[];
  columnOrder: string[];
  setSelectedColumns: (columns: string[]) => void;
  setColumnOrder: (order: string[]) => void;
  toggleColumn: (column: string) => void;
  resetColumns: () => void;
  onColumnMoved: (newOrder: string[]) => void;
  saveColumnState: (columnState: ColumnState[]) => void;
  getColumnState: () => ColumnState[] | null;
}

export const useColumnState = ({
  storageKey = 'default',
  defaultColumns
}: UseColumnStateOptions): UseColumnStateReturn => {
  const fullStorageKey = `${STORAGE_KEY_PREFIX}-${storageKey}`;

  // Initialize state from localStorage or defaults
  const [selectedColumns, setSelectedColumnsInternal] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(`${fullStorageKey}-visibility`);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load column visibility from localStorage:', error);
    }
    return defaultColumns;
  });

  const [columnOrder, setColumnOrderInternal] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(`${fullStorageKey}-order`);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load column order from localStorage:', error);
    }
    return defaultColumns;
  });

  // Persist selected columns to localStorage
  const setSelectedColumns = useCallback((columns: string[]) => {
    setSelectedColumnsInternal(columns);
    try {
      localStorage.setItem(`${fullStorageKey}-visibility`, JSON.stringify(columns));
    } catch (error) {
      console.error('Failed to save column visibility to localStorage:', error);
    }
  }, [fullStorageKey]);

  // Persist column order to localStorage
  const setColumnOrder = useCallback((order: string[]) => {
    setColumnOrderInternal(order);
    try {
      localStorage.setItem(`${fullStorageKey}-order`, JSON.stringify(order));
    } catch (error) {
      console.error('Failed to save column order to localStorage:', error);
    }
  }, [fullStorageKey]);

  // Toggle column visibility
  const toggleColumn = useCallback((column: string) => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  }, [setSelectedColumns]);

  // Reset to defaults
  const resetColumns = useCallback(() => {
    setSelectedColumns(defaultColumns);
    setColumnOrder(defaultColumns);
    try {
      localStorage.removeItem(`${fullStorageKey}-visibility`);
      localStorage.removeItem(`${fullStorageKey}-order`);
      localStorage.removeItem(`${fullStorageKey}-state`);
    } catch (error) {
      console.error('Failed to clear column state from localStorage:', error);
    }
  }, [defaultColumns, fullStorageKey, setSelectedColumns, setColumnOrder]);

  // Handle column moved event from AG Grid
  const onColumnMoved = useCallback((newOrder: string[]) => {
    setColumnOrder(newOrder);
  }, [setColumnOrder]);

  // Save full AG Grid column state (includes width, sort, etc.)
  const saveColumnState = useCallback((columnState: ColumnState[]) => {
    try {
      localStorage.setItem(`${fullStorageKey}-state`, JSON.stringify(columnState));
    } catch (error) {
      console.error('Failed to save AG Grid column state to localStorage:', error);
    }
  }, [fullStorageKey]);

  // Get full AG Grid column state
  const getColumnState = useCallback((): ColumnState[] | null => {
    try {
      const stored = localStorage.getItem(`${fullStorageKey}-state`);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load AG Grid column state from localStorage:', error);
    }
    return null;
  }, [fullStorageKey]);

  return {
    selectedColumns,
    columnOrder,
    setSelectedColumns,
    setColumnOrder,
    toggleColumn,
    resetColumns,
    onColumnMoved,
    saveColumnState,
    getColumnState
  };
};
