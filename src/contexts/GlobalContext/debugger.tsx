import React, { useState, useEffect } from 'react';
import { useGlobalContext } from './index';
import { performanceMonitor } from '../../utils/performance/monitoring';
import { featureFlagsManager } from '../../utils/performance/featureFlags';
import type { GlobalState } from './types';
import type { FeatureFlags } from './types';

// Context debugging interface
interface ContextDebugInfo {
  timestamp: number;
  state: GlobalState;
  lastAction: string;
  performanceMetrics: Record<string, unknown>;
  featureFlags: FeatureFlags;
  cacheStatus: Record<string, unknown>;
}

// Debug log entry
interface DebugLogEntry {
  timestamp: number;
  type: 'action' | 'render' | 'error' | 'cache' | 'api';
  message: string;
  data?: unknown;
  duration?: number;
}

/**
 * Context debugger component for development
 */
export const ContextDebugger: React.FC = () => {
  const { state, dispatch } = useGlobalContext();
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'state' | 'logs' | 'performance' | 'flags'>('state');
  const [logs, setLogs] = useState<DebugLogEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);

  // Log state changes
  useEffect(() => {
    if (!isPaused) {
      setLogs(prev => [...prev.slice(-99), {
        timestamp: Date.now(),
        type: 'render',
        message: 'Global state updated',
        data: {
          auth: state.auth,
          context: state.context,
          ui: state.ui,
          cache: state.cache,
        }
      }]);
    }
  }, [state, isPaused]);

  // Subscribe to performance events
  useEffect(() => {
    const unsubscribe = performanceMonitor.subscribe((metrics) => {
      if (!isPaused) {
        setLogs(prev => [...prev.slice(-99), {
          timestamp: Date.now(),
          type: 'performance',
          message: 'Performance metrics updated',
          data: metrics,
        }]);
      }
    });

    return unsubscribe;
  }, [isPaused]);

  const clearLogs = () => setLogs([]);

  const exportDebugData = () => {
    const debugData = {
      timestamp: new Date().toISOString(),
      state,
      logs,
      performanceReport: performanceMonitor.getReport(),
      featureFlags: featureFlagsManager.getDebugInfo(),
    };

    const blob = new Blob([JSON.stringify(debugData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `context-debug-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const triggerTestAction = () => {
    dispatch({ type: 'UI_TOGGLE_SIDEBAR' });
  };

  const clearCache = () => {
    dispatch({ type: 'CACHE_CLEAR_PENDING_INVALIDATIONS' });
  };

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg z-50 hover:bg-blue-700 transition-colors"
        title="Open Context Debugger"
      >
        🐛
      </button>
    );
  }

  return (
    <div className="fixed inset-4 bg-white border border-gray-300 rounded-lg shadow-2xl z-50 flex flex-col max-h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold">Context Debugger</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`px-3 py-1 rounded text-sm ${
                isPaused
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            <button
              onClick={clearLogs}
              className="px-3 py-1 bg-gray-100 text-gray-800 rounded text-sm hover:bg-gray-200"
            >
              Clear Logs
            </button>
            <button
              onClick={exportDebugData}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200"
            >
              Export
            </button>
          </div>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-500 hover:text-gray-700 text-xl"
        >
          ×
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {(['state', 'logs', 'performance', 'flags'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'state' && (
          <div className="space-y-4">
            <div className="flex space-x-2 mb-4">
              <button
                onClick={triggerTestAction}
                className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm hover:bg-green-200"
              >
                Test Action (Toggle Sidebar)
              </button>
              <button
                onClick={clearCache}
                className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
              >
                Clear Cache
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium mb-2">Auth State</h3>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                  {JSON.stringify(state.auth, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-medium mb-2">Context State</h3>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                  {JSON.stringify(state.context, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-medium mb-2">UI State</h3>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                  {JSON.stringify(state.ui, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-medium mb-2">Cache State</h3>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                  {JSON.stringify(state.cache, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="space-y-2">
            <div className="text-sm text-gray-600 mb-2">
              Showing last {logs.length} events
            </div>
            {logs.slice(-50).reverse().map((log, index) => (
              <div
                key={index}
                className={`p-2 rounded text-xs border-l-4 ${
                  log.type === 'error' ? 'border-red-500 bg-red-50' :
                  log.type === 'performance' ? 'border-blue-500 bg-blue-50' :
                  log.type === 'cache' ? 'border-green-500 bg-green-50' :
                  log.type === 'api' ? 'border-yellow-500 bg-yellow-50' :
                  'border-gray-500 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium capitalize">{log.type}</span>
                  <span className="text-gray-500">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-700">{log.message}</div>
                {log.data && (
                  <details className="mt-1">
                    <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                      Show data
                    </summary>
                    <pre className="mt-1 p-2 bg-white rounded text-xs overflow-auto max-h-32">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-3 rounded">
                <div className="text-sm text-gray-600">Render Count</div>
                <div className="text-xl font-semibold">{state.performance.renderCount}</div>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <div className="text-sm text-gray-600">Avg Render Time</div>
                <div className="text-xl font-semibold">
                  {state.performance.averageRenderTime.toFixed(2)}ms
                </div>
              </div>
              <div className="bg-yellow-50 p-3 rounded">
                <div className="text-sm text-gray-600">Cache Hit Rate</div>
                <div className="text-xl font-semibold">
                  {(state.performance.cacheHitRate * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-purple-50 p-3 rounded">
                <div className="text-sm text-gray-600">API Calls</div>
                <div className="text-xl font-semibold">{state.performance.apiCallCount}</div>
              </div>
            </div>

            <div>
              <h3 className="font-medium mb-2">Performance Report</h3>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                {JSON.stringify(performanceMonitor.getReport(), null, 2)}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'flags' && (
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-2">Current Feature Flags</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.entries(state.featureFlags).map(([key, value]) => (
                  <div
                    key={key}
                    className={`p-2 rounded flex items-center justify-between ${
                      value ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                    }`}
                  >
                    <span className="text-sm font-mono">{key}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {value ? 'ON' : 'OFF'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-medium mb-2">Debug Info</h3>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                {JSON.stringify(featureFlagsManager.getDebugInfo(), null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Performance metrics display component
 */
export const PerformanceMetrics: React.FC<{
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}> = ({ position = 'top-right' }) => {
  const { state } = useGlobalContext();
  const [isVisible, setIsVisible] = useState(false);

  if (process.env.NODE_ENV !== 'development' || !state.featureFlags.enablePerformanceMonitoring) {
    return null;
  }

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-40`}>
      {!isVisible ? (
        <button
          onClick={() => setIsVisible(true)}
          className="bg-green-600 text-white p-2 rounded-full shadow-lg hover:bg-green-700 transition-colors text-sm"
          title="Show Performance Metrics"
        >
          ⚡
        </button>
      ) : (
        <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm min-w-48">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Performance</span>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span>Renders:</span>
              <span>{state.performance.renderCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Avg Render:</span>
              <span>{state.performance.averageRenderTime.toFixed(2)}ms</span>
            </div>
            <div className="flex justify-between">
              <span>Cache Hit:</span>
              <span>{(state.performance.cacheHitRate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span>API Calls:</span>
              <span>{state.performance.apiCallCount}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Cache status indicator
 */
export const CacheStatusIndicator: React.FC = () => {
  const { state } = useGlobalContext();

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 z-40">
      <div className={`px-2 py-1 rounded text-xs font-medium ${
        state.cache.isConnected
          ? 'bg-green-100 text-green-800'
          : 'bg-red-100 text-red-800'
      }`}>
        Cache: {state.cache.isConnected ? 'Connected' : 'Disconnected'}
        {state.cache.pendingInvalidations.length > 0 && (
          <span className="ml-1 bg-yellow-200 text-yellow-800 px-1 rounded">
            {state.cache.pendingInvalidations.length}
          </span>
        )}
      </div>
    </div>
  );
};
