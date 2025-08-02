/**
 * Enhanced Lazy Components
 *
 * React components for enhanced lazy loading functionality.
 * Factory functions and utilities are in separate files for react-refresh compatibility.
 */

import React from 'react';
import type { ComponentType } from 'react';
import { useBundlePerformance } from '../../utils/performance/hooks';
import { LoadingPriority } from './lazyUtils';
import { createEnhancedLazy, createProgressiveLazy } from './lazyFactories';

// Bundle analyzer component (development only)
export const BundleAnalyzer: React.FC = () => {
  const { loadingStats } = useBundlePerformance();
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 left-4 bg-purple-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Bundle Analyzer"
      >
        📦
      </button>

      {isVisible && (
        <div className="fixed bottom-16 left-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50">
          <h3 className="font-semibold mb-2">Bundle Loading Stats</h3>
          <div className="text-sm space-y-1">
            <div>Total Bundles: {loadingStats.totalBundles}</div>
            <div>Loaded: {loadingStats.loadedBundles}</div>
            <div>Failed: {loadingStats.failedBundles}</div>
            <div>Avg Load Time: {loadingStats.averageLoadTime.toFixed(2)}ms</div>
            <div className="mt-2 pt-2 border-t">
              Success Rate: {loadingStats.totalBundles > 0
                ? ((loadingStats.loadedBundles / loadingStats.totalBundles) * 100).toFixed(1)
                : 0}%
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Route preloader utility
export const RoutePreloader: React.FC<{
  routes: Array<{
    path: string;
    importFn: () => Promise<{ default: ComponentType<unknown> }>;
  }>;
}> = ({ routes }) => {
  const { trackBundleLoad } = useBundlePerformance();

  React.useEffect(() => {
    routes.forEach(route => {
      trackBundleLoad(route.path, route.importFn);
    });
  }, [routes, trackBundleLoad]);

  return null; // This component doesn't render anything
};

// Enhanced lazy loading components exported individually
// For grouped exports, use ./enhancedLazyExports
