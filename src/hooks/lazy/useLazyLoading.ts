/**
 * Lazy Loading Hook - CC hook for accessing lazy loading context
 */

import type { useContext } from 'react';
import type { LazyLoadingContext } from '@/components/lazy/LazyLoadingProvider';

export const useLazyLoading = () => {
  const context = useContext(LazyLoadingContext);
  if (!context) {
    throw new Error('useLazyLoading must be used within a LazyLoadingProvider');
  }
  return context;
};