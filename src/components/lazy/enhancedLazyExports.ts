/**
 * Enhanced Lazy Components Exports
 * 
 * Non-component exports for enhanced lazy loading functionality.
 * Separated from component file to maintain react-refresh compatibility.
 */

import { BundleAnalyzer, RoutePreloader } from './EnhancedLazyComponents';

// Export enhanced lazy loading components (utilities available from ./lazyUtils and ./lazyFactories)
export const enhancedLazyComponents = {
  BundleAnalyzer,
  RoutePreloader,
};