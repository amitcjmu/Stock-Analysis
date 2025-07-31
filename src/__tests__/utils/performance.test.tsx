import React from 'react';
import { render, act, waitFor } from '@testing-library/react';
import { performanceMonitor, measureAsync, measureSync } from '../../utils/performance/monitoring';
import {
  useRenderPerformance,
  useApiPerformance,
  useCachePerformance
} from '../../utils/performance/hooks';
import {
  performantMemo,
  smartMemo,
  useStableCallback,
  useExpensiveMemo,
  useDebouncedValue
} from '../../utils/performance/memoization';
import {
  featureFlagsManager,
  useFeatureFlags,
  useFeatureFlag
} from '../../utils/performance/featureFlags';
import type { FeatureFlags } from '../../contexts/GlobalContext/types';

// Mock performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByName: jest.fn(() => [{ duration: 10, startTime: 100 }]),
  clearMarks: jest.fn(),
  clearMeasures: jest.fn(),
};

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true,
});

// Mock PerformanceObserver
global.PerformanceObserver = jest.fn().mockImplementation((callback) => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
}));

describe('Performance Monitoring', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    performanceMonitor.clear();
  });

  describe('performanceMonitor', () => {
    it('should record events correctly', () => {
      const event = {
        name: 'test-event',
        duration: 100,
        timestamp: Date.now(),
        metadata: { test: true },
      };

      performanceMonitor.recordEvent(event);
      const report = performanceMonitor.getReport();

      expect(report.events).toHaveLength(1);
      expect(report.events[0]).toEqual(event);
    });

    it('should mark start and end correctly', () => {
      const label = 'test-operation';

      performanceMonitor.markStart(label);
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${label}-start`);

      const duration = performanceMonitor.markEnd(label);
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${label}-end`);
      expect(mockPerformance.measure).toHaveBeenCalledWith(label, `${label}-start`, `${label}-end`);
      expect(duration).toBe(10); // Mocked duration
    });

    it('should subscribe to metrics updates', () => {
      const callback = jest.fn();
      const unsubscribe = performanceMonitor.subscribe(callback);

      // Should be a function
      expect(typeof unsubscribe).toBe('function');

      // Unsubscribe should work
      unsubscribe();
    });

    it('should limit events history', () => {
      const maxEvents = 100;

      // Add more events than the limit
      for (let i = 0; i < maxEvents + 10; i++) {
        performanceMonitor.recordEvent({
          name: `event-${i}`,
          duration: i,
          timestamp: Date.now(),
        });
      }

      const report = performanceMonitor.getReport();
      expect(report.events.length).toBeLessThanOrEqual(maxEvents);
    });
  });

  describe('measureAsync', () => {
    it('should measure async operation duration', async () => {
      const operation = jest.fn().mockResolvedValue('result');

      const result = await measureAsync('async-test', operation);

      expect(result).toBe('result');
      expect(operation).toHaveBeenCalled();
      expect(mockPerformance.mark).toHaveBeenCalledWith('async-test-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('async-test-end');
    });

    it('should handle async operation errors', async () => {
      const error = new Error('Test error');
      const operation = jest.fn().mockRejectedValue(error);

      await expect(measureAsync('async-error-test', operation)).rejects.toThrow('Test error');

      expect(mockPerformance.mark).toHaveBeenCalledWith('async-error-test-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('async-error-test-end');
    });
  });

  describe('measureSync', () => {
    it('should measure sync operation duration', () => {
      const operation = jest.fn().mockReturnValue('sync-result');

      const result = measureSync('sync-test', operation);

      expect(result).toBe('sync-result');
      expect(operation).toHaveBeenCalled();
      expect(mockPerformance.mark).toHaveBeenCalledWith('sync-test-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('sync-test-end');
    });

    it('should handle sync operation errors', () => {
      const error = new Error('Sync error');
      const operation = jest.fn().mockImplementation(() => {
        throw error;
      });

      expect(() => measureSync('sync-error-test', operation)).toThrow('Sync error');

      expect(mockPerformance.mark).toHaveBeenCalledWith('sync-error-test-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('sync-error-test-end');
    });
  });
});

describe('Performance Hooks', () => {
  const TestComponent: React.FC<{ componentName: string }> = ({ componentName }) => {
    const { renderCount, markStart, markEnd } = useRenderPerformance(componentName);

    React.useEffect(() => {
      markStart('effect');
      markEnd('effect');
    }, [markStart, markEnd]);

    return <div data-testid="render-count">{renderCount}</div>;
  };

  it('should track render performance', () => {
    const { rerender } = render(<TestComponent componentName="test-component" />);

    // Initial render count should be 1
    expect(screen.getByTestId('render-count')).toHaveTextContent('1');

    // Re-render should increment count
    rerender(<TestComponent componentName="test-component" />);
    expect(screen.getByTestId('render-count')).toHaveTextContent('2');
  });

  describe('useApiPerformance', () => {
    const ApiTestComponent: React.FC = () => {
      const { trackApiCall, apiCallCount } = useApiPerformance();
      const [result, setResult] = React.useState<string>('');

      const handleApiCall = async () => {
        const mockApiCall = () => Promise.resolve('api-result');
        const result = await trackApiCall('test-api', mockApiCall);
        setResult(result);
      };

      return (
        <div>
          <div data-testid="api-call-count">{apiCallCount}</div>
          <div data-testid="api-result">{result}</div>
          <button data-testid="api-button" onClick={handleApiCall}>Call API</button>
        </div>
      );
    };

    it('should track API call performance', async () => {
      render(<ApiTestComponent />);

      const button = screen.getByTestId('api-button');

      await act(async () => {
        await userEvent.click(button);
      });

      await waitFor(() => {
        expect(screen.getByTestId('api-call-count')).toHaveTextContent('1');
        expect(screen.getByTestId('api-result')).toHaveTextContent('api-result');
      });
    });
  });

  describe('useCachePerformance', () => {
    const CacheTestComponent: React.FC = () => {
      const { trackCacheHit, trackCacheMiss, hitRate } = useCachePerformance();

      const handleCacheHit = () => trackCacheHit('test-key');
      const handleCacheMiss = () => trackCacheMiss('test-key');

      return (
        <div>
          <div data-testid="hit-rate">{(hitRate * 100).toFixed(1)}%</div>
          <button data-testid="hit-button" onClick={handleCacheHit}>Cache Hit</button>
          <button data-testid="miss-button" onClick={handleCacheMiss}>Cache Miss</button>
        </div>
      );
    };

    it('should calculate cache hit rate correctly', async () => {
      render(<CacheTestComponent />);

      const hitButton = screen.getByTestId('hit-button');
      const missButton = screen.getByTestId('miss-button');

      // 2 hits, 1 miss = 66.7% hit rate
      await act(async () => {
        await userEvent.click(hitButton);
        await userEvent.click(hitButton);
        await userEvent.click(missButton);
      });

      expect(screen.getByTestId('hit-rate')).toHaveTextContent('66.7%');
    });
  });
});

describe('Memoization Utilities', () => {
  describe('performantMemo', () => {
    let renderCount = 0;

    const TestComponent: React.FC<{ value: string; ignored: number }> = ({ value }) => {
      renderCount++;
      return <div data-testid="value">{value}</div>;
    };

    const MemoizedComponent = performantMemo(TestComponent);

    beforeEach(() => {
      renderCount = 0;
    });

    it('should prevent unnecessary re-renders', () => {
      const { rerender } = render(<MemoizedComponent value="test" ignored={1} />);
      expect(renderCount).toBe(1);

      // Same props should not trigger re-render
      rerender(<MemoizedComponent value="test" ignored={1} />);
      expect(renderCount).toBe(1);

      // Different props should trigger re-render
      rerender(<MemoizedComponent value="changed" ignored={1} />);
      expect(renderCount).toBe(2);
    });
  });

  describe('smartMemo', () => {
    let renderCount = 0;

    const TestComponent: React.FC<{ value: string; metadata: object; ignored: number }> = ({ value }) => {
      renderCount++;
      return <div data-testid="value">{value}</div>;
    };

    const SmartMemoComponent = smartMemo(TestComponent, {
      ignoreKeys: ['ignored'],
      deep: true,
    });

    beforeEach(() => {
      renderCount = 0;
    });

    it('should ignore specified keys', () => {
      const metadata = { test: true };
      const { rerender } = render(
        <SmartMemoComponent value="test" metadata={metadata} ignored={1} />
      );
      expect(renderCount).toBe(1);

      // Changing ignored prop should not trigger re-render
      rerender(<SmartMemoComponent value="test" metadata={metadata} ignored={2} />);
      expect(renderCount).toBe(1);

      // Changing non-ignored prop should trigger re-render
      rerender(<SmartMemoComponent value="changed" metadata={metadata} ignored={2} />);
      expect(renderCount).toBe(2);
    });
  });

  describe('useStableCallback', () => {
    const TestComponent: React.FC<{ value: string }> = ({ value }) => {
      const [count, setCount] = React.useState(0);

      const stableCallback = useStableCallback(() => {
        setCount(prev => prev + 1);
      }, []);

      const unstableCallback = React.useCallback(() => {
        setCount(prev => prev + 1);
      }, []); // Changed to not depend on value to avoid unnecessary recreations

      return (
        <div>
          <div data-testid="count">{count}</div>
          <button data-testid="stable-button" onClick={stableCallback}>Stable</button>
          <button data-testid="unstable-button" onClick={unstableCallback}>Unstable</button>
        </div>
      );
    };

    it('should provide stable callback reference', () => {
      const { rerender } = render(<TestComponent value="initial" />);

      const stableButton = screen.getByTestId('stable-button');
      const initialStableCallback = stableButton.onclick;

      // Re-render with different value
      rerender(<TestComponent value="changed" />);

      const newStableButton = screen.getByTestId('stable-button');
      const newStableCallback = newStableButton.onclick;

      // Stable callback should maintain same reference
      expect(newStableCallback).toBe(initialStableCallback);
    });
  });

  describe('useExpensiveMemo', () => {
    const TestComponent: React.FC<{ data: number[] }> = ({ data }) => {
      const expensiveResult = useExpensiveMemo(() => {
        return data.reduce((sum, item) => sum + item, 0);
      }, [data], {
        debugLabel: 'sum-calculation',
        perfThreshold: 0, // Always log for testing
      });

      return <div data-testid="result">{expensiveResult}</div>;
    };

    it('should memoize expensive computations', () => {
      const data = [1, 2, 3, 4, 5];
      const { rerender } = render(<TestComponent data={data} />);

      expect(screen.getByTestId('result')).toHaveTextContent('15');

      // Same data should use memoized result
      rerender(<TestComponent data={data} />);
      expect(screen.getByTestId('result')).toHaveTextContent('15');

      // Different data should recompute
      const newData = [1, 2, 3, 4, 5, 6];
      rerender(<TestComponent data={newData} />);
      expect(screen.getByTestId('result')).toHaveTextContent('21');
    });
  });

  describe('useDebouncedValue', () => {
    const TestComponent: React.FC<{ value: string }> = ({ value }) => {
      const debouncedValue = useDebouncedValue(value, 100);

      return <div data-testid="debounced-value">{debouncedValue}</div>;
    };

    it('should debounce value changes', async () => {
      jest.useFakeTimers();

      const { rerender } = render(<TestComponent value="initial" />);
      expect(screen.getByTestId('debounced-value')).toHaveTextContent('initial');

      // Change value rapidly
      rerender(<TestComponent value="changed1" />);
      rerender(<TestComponent value="changed2" />);
      rerender(<TestComponent value="final" />);

      // Should still show initial value immediately
      expect(screen.getByTestId('debounced-value')).toHaveTextContent('initial');

      // After debounce delay, should show final value
      act(() => {
        jest.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(screen.getByTestId('debounced-value')).toHaveTextContent('final');
      });

      jest.useRealTimers();
    });
  });
});

describe('Feature Flags', () => {
  beforeEach(() => {
    featureFlagsManager.reset();
  });

  describe('featureFlagsManager', () => {
    it('should get and update flags correctly', () => {
      const initialFlags = featureFlagsManager.getFlags();
      expect(typeof initialFlags.useRedisCache).toBe('boolean');

      featureFlagsManager.updateFlags({ useRedisCache: true });
      expect(featureFlagsManager.getFlag('useRedisCache')).toBe(true);
    });

    it('should subscribe to flag changes', () => {
      const callback = jest.fn();
      const unsubscribe = featureFlagsManager.subscribe(callback);

      featureFlagsManager.updateFlags({ useRedisCache: true });
      expect(callback).toHaveBeenCalled();

      unsubscribe();
      featureFlagsManager.updateFlags({ useRedisCache: false });
      expect(callback).toHaveBeenCalledTimes(1); // Should not be called after unsubscribe
    });
  });

  describe('useFeatureFlags hook', () => {
    const TestComponent: React.FC = () => {
      const { flags, getFlag, updateFlags } = useFeatureFlags();

      return (
        <div>
          <div data-testid="redis-cache-flag">
            {getFlag('useRedisCache').toString()}
          </div>
          <button
            data-testid="toggle-button"
            onClick={() => updateFlags({ useRedisCache: !flags.useRedisCache })}
          >
            Toggle
          </button>
        </div>
      );
    };

    it('should provide current flags and update function', async () => {
      render(<TestComponent />);

      const flag = screen.getByTestId('redis-cache-flag');
      const button = screen.getByTestId('toggle-button');

      const initialValue = flag.textContent;

      await act(async () => {
        await userEvent.click(button);
      });

      await waitFor(() => {
        expect(flag.textContent).not.toBe(initialValue);
      });
    });
  });

  describe('useFeatureFlag hook', () => {
    const TestComponent: React.FC<{ flagKey: keyof FeatureFlags }> = ({ flagKey }) => {
      const isEnabled = useFeatureFlag(flagKey);

      return <div data-testid="flag-status">{isEnabled.toString()}</div>;
    };

    it('should return specific flag value', () => {
      featureFlagsManager.updateFlags({ enablePerformanceMonitoring: true });

      render(<TestComponent flagKey="enablePerformanceMonitoring" />);

      expect(screen.getByTestId('flag-status')).toHaveTextContent('true');
    });
  });
});

// Import missing modules for tests
import { screen, userEvent } from '@testing-library/react';
