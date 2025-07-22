/**
 * Performance Hook Types
 * 
 * Hook interfaces for performance optimization including memoization and virtualization.
 */

// Performance hooks
export interface UseMemoizedParams<T> {
  factory: () => T;
  deps: readonly unknown[];
  compare?: (prev: T, next: T) => boolean;
}

export interface UseMemoizedReturn<T> {
  value: T;
  reset: () => void;
  isStale: boolean;
}

export interface UseVirtualizedParams<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  containerHeight: number;
  overscan?: number;
  scrollTop?: number;
  onScroll?: (scrollTop: number) => void;
}

export interface UseVirtualizedReturn<T> {
  virtualItems: VirtualItem<T>[];
  totalHeight: number;
  startIndex: number;
  endIndex: number;
  scrollToIndex: (index: number, align?: 'start' | 'center' | 'end' | 'auto') => void;
  scrollToOffset: (offset: number) => void;
  measureElement: (index: number, element: HTMLElement) => void;
}

export interface VirtualItem<T> {
  index: number;
  start: number;
  end: number;
  size: number;
  item: T;
}