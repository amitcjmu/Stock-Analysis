/**
 * Lazy Loading - Main exports for the lazy loading system
 */

// Core infrastructure
export { LazyLoadingProvider } from './LazyLoadingProvider';
export { useLazyLoading } from '../../hooks/lazy/useLazyLoading';
export { LoadingFallback, ErrorFallback, SkeletonFallback, PreloadIndicator } from './LoadingFallback';
export { PerformanceDashboard } from './PerformanceDashboard';

// Route-level lazy loading
export * from './routes/LazyRoutes';

// Component-level lazy loading
export * from './components/LazyComponents';

// Hooks
export { useLazyComponent, useViewportLazyComponent, useHoverPreload } from '../../hooks/lazy/useLazyComponent';
export * from '../../hooks/lazy/LazyHooks';

// Utilities
export * from '../../utils/lazy/LazyUtilities';
export { loadingManager } from '../../utils/lazy/loadingManager';
export { routePreloader } from '../../utils/lazy/routePreloader';
export { performanceMonitor } from '../../utils/lazy/performanceMonitor';

// Types
export * from '../../types/lazy';
