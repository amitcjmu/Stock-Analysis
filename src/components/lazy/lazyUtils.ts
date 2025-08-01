/**
 * Lazy Loading Utilities
 * 
 * Non-component utilities for enhanced lazy loading functionality.
 * Separated from components to maintain react-refresh compatibility.
 */

import { createEnhancedLazy, createProgressiveLazy } from './lazyFactories';

// Progressive loading components with priority levels
export enum LoadingPriority {
  CRITICAL = 0,   // Load immediately
  HIGH = 1,       // Load when visible or on hover
  NORMAL = 2,     // Load when visible
  LOW = 3,        // Load when idle
}

// Export enhanced lazy loading utilities object
export const enhancedLazy = {
  create: createEnhancedLazy,
  progressive: createProgressiveLazy,
  LoadingPriority,
};