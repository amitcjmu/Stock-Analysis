/**
 * Compatibility components for GlobalContext
 */

import React from 'react';
import { useContextDebug } from './compatibilityHooks';

/**
 * Feature flag controlled context provider wrapper
 * This allows gradual rollout of the new GlobalContext
 */
interface ContextMigrationProviderProps {
  children: React.ReactNode;
  useGlobalContext?: boolean;
}

export const ContextMigrationProvider: React.FC<ContextMigrationProviderProps> = ({
  children,
  useGlobalContext = process.env.NODE_ENV === 'development',
}) => {
  if (useGlobalContext) {
    // Use the new GlobalContext system
    return <>{children}</>;
  } else {
    // Fall back to the original context providers
    // This would import and use the original providers
    return <>{children}</>;
  }
};

/**
 * Context debugging tools
 */
export const ContextDebugger: React.FC = () => {
  const { state } = useContextDebug();
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Context Debugger"
      >
        🐛
      </button>

      {isVisible && (
        <div className="fixed bottom-16 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md max-h-96 overflow-auto z-50">
          <h3 className="font-semibold mb-2">Context Debug Info</h3>
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify(state || {}, null, 2)}
          </pre>
        </div>
      )}
    </>
  );
};

/**
 * Performance debugging component
 */
export const PerformanceDebugger: React.FC = () => {
  const { metrics, enabled } = useContextDebug();
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development' || !enabled) {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 right-16 bg-green-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Performance Debugger"
      >
        ⚡
      </button>

      {isVisible && (
        <div className="fixed bottom-16 right-16 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md z-50">
          <h3 className="font-semibold mb-2">Performance Metrics</h3>
          <div className="text-sm space-y-1">
            <div>Render Count: {(metrics as Record<string, unknown>)?.renderCount || 0}</div>
            <div>Avg Render Time: {((metrics as Record<string, unknown>)?.averageRenderTime as number || 0).toFixed(2)}ms</div>
            <div>Cache Hit Rate: {(((metrics as Record<string, unknown>)?.cacheHitRate as number || 0) * 100).toFixed(1)}%</div>
            <div>API Calls: {(metrics as Record<string, unknown>)?.apiCallCount || 0}</div>
          </div>
        </div>
      )}
    </>
  );
};

/**
 * Migration status indicator
 */
export const MigrationStatusIndicator: React.FC = () => {
  const [migrationStatus] = React.useState({
    globalContext: true,
    performanceMonitoring: true,
    featureFlags: true,
    cacheIntegration: true,
  });

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const completedCount = Object.values(migrationStatus).filter(Boolean).length;
  const totalCount = Object.keys(migrationStatus).length;
  const percentage = (completedCount / totalCount) * 100;

  return (
    <div className="fixed top-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm z-50">
      <div className="font-semibold mb-1">Migration Status</div>
      <div className="flex items-center space-x-2">
        <div className="w-20 bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span>{completedCount}/{totalCount}</span>
      </div>
    </div>
  );
};