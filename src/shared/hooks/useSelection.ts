/**
 * Reusable Selection Management Hook
 * Common pattern for item selection across components
 */

import type { useState } from 'react'
import { useCallback, useMemo } from 'react'

export interface UseSelectionResult<T = number | string> {
  selectedItems: T[];
  isSelected: (item: T) => boolean;
  isAllSelected: (items: T[]) => boolean;
  selectItem: (item: T) => void;
  selectAll: (items: T[]) => void;
  deselectAll: () => void;
  toggleSelection: (item: T) => void;
  toggleSelectAll: (items: T[]) => void;
  setSelectedItems: (items: T[]) => void;
}

export interface UseSelectionOptions {
  maxSelections?: number;
  initialSelection?: Array<number | string>;
}

export function useSelection<T = number | string>(
  options: UseSelectionOptions = {}
): UseSelectionResult<T> {
  const { maxSelections, initialSelection = [] } = options;
  
  const [selectedItems, setSelectedItems] = useState<T[]>(initialSelection as T[]);

  const isSelected = useCallback((item: T): boolean => {
    return selectedItems.includes(item);
  }, [selectedItems]);

  const isAllSelected = useCallback((items: T[]): boolean => {
    return items.length > 0 && items.every(item => selectedItems.includes(item));
  }, [selectedItems]);

  const selectItem = useCallback((item: T) => {
    setSelectedItems(prev => {
      if (prev.includes(item)) return prev;
      const newSelection = [...prev, item];
      return maxSelections ? newSelection.slice(0, maxSelections) : newSelection;
    });
  }, [maxSelections]);

  const deselectItem = useCallback((item: T) => {
    setSelectedItems(prev => prev.filter(selected => selected !== item));
  }, []);

  const selectAll = useCallback((items: T[]) => {
    const itemsToSelect = maxSelections ? items.slice(0, maxSelections) : items;
    setSelectedItems(itemsToSelect);
  }, [maxSelections]);

  const deselectAll = useCallback(() => {
    setSelectedItems([]);
  }, []);

  const toggleSelection = useCallback((item: T) => {
    if (isSelected(item)) {
      deselectItem(item);
    } else {
      selectItem(item);
    }
  }, [isSelected, selectItem, deselectItem]);

  const toggleSelectAll = useCallback((items: T[]) => {
    if (isAllSelected(items)) {
      deselectAll();
    } else {
      selectAll(items);
    }
  }, [isAllSelected, selectAll, deselectAll]);

  return {
    selectedItems,
    isSelected,
    isAllSelected,
    selectItem,
    selectAll,
    deselectAll,
    toggleSelection,
    toggleSelectAll,
    setSelectedItems
  };
}