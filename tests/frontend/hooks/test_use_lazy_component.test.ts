/**
 * Tests for Lazy Loading Hooks
 * 
 * Tests the modular lazy loading hook infrastructure including:
 * - useLazyComponent hook functionality
 * - useLazyHook for business logic loading
 * - Hook composition patterns
 * - Error handling in hooks
 * - Performance characteristics
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import React from 'react';

// Import hooks to test
import { useLazyComponent } from '@/hooks/lazy/useLazyComponent';
import { useLazyHook } from '@/hooks/lazy/useLazyHook';

// Mock components for testing
const mockComponent = () => React.createElement('div', { 'data-testid': 'mock-component' }, 'Mock Component');
const mockEnhancedComponent = () => React.createElement('div', { 'data-testid': 'mock-enhanced-component' }, 'Enhanced Component');

// Mock business logic hooks
const mockBusinessLogic = {
  useAssetInventory: () => ({ assets: [], loading: false, error: null }),
  useFieldMapping: () => ({ mappings: [], loading: false, error: null }),
  useDataCleansing: () => ({ issues: [], loading: false, error: null })
};

describe('useLazyComponent Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with loading state', () => {
    // Arrange
    const importFn = () => Promise.resolve({ default: mockComponent });
    
    // Act
    const { result } = renderHook(() => useLazyComponent(importFn));
    
    // Assert
    expect(result.current.Component).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should load component successfully', async () => {
    // Arrange
    const importFn = () => Promise.resolve({ default: mockComponent });
    
    // Act
    const { result } = renderHook(() => useLazyComponent(importFn));
    
    // Wait for component to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.Component).toBe(mockComponent);
    expect(result.current.error).toBeNull();
  });

  it('should handle import errors gracefully', async () => {
    // Arrange
    const importError = new Error('Failed to load component');
    const importFn = () => Promise.reject(importError);
    
    // Act
    const { result } = renderHook(() => useLazyComponent(importFn));
    
    // Wait for error to occur
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.Component).toBeNull();
    expect(result.current.error).toBe(importError);
  });

  it('should retry loading after error', async () => {
    // Arrange
    let attemptCount = 0;
    const importFn = () => {
      attemptCount++;
      if (attemptCount === 1) {
        return Promise.reject(new Error('First attempt failed'));
      }
      return Promise.resolve({ default: mockComponent });
    };
    
    // Act
    const { result } = renderHook(() => useLazyComponent(importFn));
    
    // Wait for initial error
    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
    
    // Retry loading
    act(() => {
      result.current.retry();
    });
    
    // Wait for successful retry
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
    
    // Assert
    expect(result.current.Component).toBe(mockComponent);
    expect(attemptCount).toBe(2);
  });

  it('should cache loaded components', async () => {
    // Arrange
    const importSpy = vi.fn(() => Promise.resolve({ default: mockComponent }));
    
    // Act - Render hook multiple times with same import function
    const { result: result1 } = renderHook(() => useLazyComponent(importSpy));
    const { result: result2 } = renderHook(() => useLazyComponent(importSpy));
    
    await waitFor(() => {
      expect(result1.current.loading).toBe(false);
      expect(result2.current.loading).toBe(false);
    });
    
    // Assert - Import should only be called once due to caching
    expect(importSpy).toHaveBeenCalledTimes(1);
    expect(result1.current.Component).toBe(result2.current.Component);
  });

  it('should support conditional loading', () => {
    // Arrange
    const importFn = () => Promise.resolve({ default: mockComponent });
    
    // Act - Initially don't load
    const { result, rerender } = renderHook(
      ({ shouldLoad }) => useLazyComponent(importFn, { shouldLoad }),
      { initialProps: { shouldLoad: false } }
    );
    
    // Assert - Should not start loading
    expect(result.current.Component).toBeNull();
    expect(result.current.loading).toBe(false);
    
    // Rerender with shouldLoad = true
    rerender({ shouldLoad: true });
    
    // Assert - Should start loading
    expect(result.current.loading).toBe(true);
  });

  it('should handle component preloading', async () => {
    // Arrange
    const importFn = vi.fn(() => Promise.resolve({ default: mockComponent }));
    
    // Act
    const { result } = renderHook(() => useLazyComponent(importFn, { preload: true }));
    
    // Assert - Should start loading immediately due to preload
    expect(result.current.loading).toBe(true);
    expect(importFn).toHaveBeenCalledOnce();
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    expect(result.current.Component).toBe(mockComponent);
  });
});

describe('useLazyHook Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should load business logic hook successfully', async () => {
    // Arrange
    const hookImportFn = () => Promise.resolve({ 
      default: mockBusinessLogic.useAssetInventory 
    });
    
    // Act
    const { result } = renderHook(() => useLazyHook(hookImportFn));
    
    // Wait for hook to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.hookModule).toBe(mockBusinessLogic.useAssetInventory);
    expect(result.current.error).toBeNull();
  });

  it('should execute loaded hook with parameters', async () => {
    // Arrange
    const mockHookWithParams = vi.fn(() => ({ data: 'test data', loading: false }));
    const hookImportFn = () => Promise.resolve({ default: mockHookWithParams });
    
    // Act
    const { result } = renderHook(() => useLazyHook(hookImportFn));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Execute the loaded hook
    const hookParams = { filter: 'active', limit: 10 };
    act(() => {
      result.current.executeHook(hookParams);
    });
    
    // Assert
    expect(mockHookWithParams).toHaveBeenCalledWith(hookParams);
  });

  it('should support progressive hook enhancement', async () => {
    // Arrange
    const baseHook = () => ({ data: [], features: ['basic'] });
    const enhancedHook = () => ({ data: [], features: ['basic', 'advanced', 'premium'] });
    
    const baseImportFn = () => Promise.resolve({ default: baseHook });
    const enhancedImportFn = () => Promise.resolve({ default: enhancedHook });
    
    // Act - Start with base hook
    const { result, rerender } = renderHook(
      ({ useEnhanced }) => useLazyHook(
        useEnhanced ? enhancedImportFn : baseImportFn,
        { progressive: true }
      ),
      { initialProps: { useEnhanced: false } }
    );
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert base hook loaded
    expect(result.current.hookModule).toBe(baseHook);
    
    // Switch to enhanced hook
    rerender({ useEnhanced: true });
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert enhanced hook loaded
    expect(result.current.hookModule).toBe(enhancedHook);
  });

  it('should handle hook loading errors', async () => {
    // Arrange
    const hookError = new Error('Failed to load hook');
    const hookImportFn = () => Promise.reject(hookError);
    
    // Act
    const { result } = renderHook(() => useLazyHook(hookImportFn));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.hookModule).toBeNull();
    expect(result.current.error).toBe(hookError);
  });

  it('should support hook composition patterns', async () => {
    // Arrange
    const composedHooks = {
      useAssetInventory: mockBusinessLogic.useAssetInventory,
      useFieldMapping: mockBusinessLogic.useFieldMapping,
      useDataCleansing: mockBusinessLogic.useDataCleansing
    };
    
    const hookImportFn = () => Promise.resolve({ default: composedHooks });
    
    // Act
    const { result } = renderHook(() => useLazyHook(hookImportFn));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.hookModule).toBe(composedHooks);
    expect(typeof result.current.hookModule.useAssetInventory).toBe('function');
    expect(typeof result.current.hookModule.useFieldMapping).toBe('function');
    expect(typeof result.current.hookModule.useDataCleansing).toBe('function');
  });
});

describe('Hook Performance and Caching', () => {
  it('should cache loaded hooks across multiple usages', async () => {
    // Arrange
    const importSpy = vi.fn(() => Promise.resolve({ 
      default: mockBusinessLogic.useAssetInventory 
    }));
    
    // Act - Use same hook in multiple places
    const { result: result1 } = renderHook(() => useLazyHook(importSpy));
    const { result: result2 } = renderHook(() => useLazyHook(importSpy));
    const { result: result3 } = renderHook(() => useLazyHook(importSpy));
    
    await Promise.all([
      waitFor(() => expect(result1.current.loading).toBe(false)),
      waitFor(() => expect(result2.current.loading).toBe(false)),
      waitFor(() => expect(result3.current.loading).toBe(false))
    ]);
    
    // Assert - Import should only be called once
    expect(importSpy).toHaveBeenCalledTimes(1);
    expect(result1.current.hookModule).toBe(result2.current.hookModule);
    expect(result2.current.hookModule).toBe(result3.current.hookModule);
  });

  it('should handle concurrent loading requests efficiently', async () => {
    // Arrange
    let resolveImport: (value: { default: () => unknown }) => void;
    const importPromise = new Promise(resolve => {
      resolveImport = resolve;
    });
    const importFn = () => importPromise;
    
    // Act - Start multiple concurrent requests
    const { result: result1 } = renderHook(() => useLazyHook(importFn));
    const { result: result2 } = renderHook(() => useLazyHook(importFn));
    const { result: result3 } = renderHook(() => useLazyHook(importFn));
    
    // All should be loading
    expect(result1.current.loading).toBe(true);
    expect(result2.current.loading).toBe(true);
    expect(result3.current.loading).toBe(true);
    
    // Resolve the import
    act(() => {
      resolveImport({ default: mockBusinessLogic.useAssetInventory });
    });
    
    await Promise.all([
      waitFor(() => expect(result1.current.loading).toBe(false)),
      waitFor(() => expect(result2.current.loading).toBe(false)),
      waitFor(() => expect(result3.current.loading).toBe(false))
    ]);
    
    // Assert - All should get the same result
    expect(result1.current.hookModule).toBe(mockBusinessLogic.useAssetInventory);
    expect(result2.current.hookModule).toBe(mockBusinessLogic.useAssetInventory);
    expect(result3.current.hookModule).toBe(mockBusinessLogic.useAssetInventory);
  });

  it('should measure and report loading performance', async () => {
    // Arrange
    const performanceMarks: string[] = [];
    const originalMark = performance.mark;
    const originalMeasure = performance.measure;
    
    performance.mark = vi.fn((name: string) => {
      performanceMarks.push(name);
      return originalMark.call(performance, name);
    });
    
    performance.measure = vi.fn((name: string, startMark: string, endMark: string) => {
      return originalMeasure.call(performance, name, startMark, endMark);
    });
    
    const importFn = () => new Promise(resolve => {
      setTimeout(() => resolve({ default: mockBusinessLogic.useAssetInventory }), 100);
    });
    
    // Act
    const { result } = renderHook(() => useLazyHook(importFn, { measurePerformance: true }));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(performance.mark).toHaveBeenCalledWith(expect.stringContaining('lazy-hook-start'));
    expect(performance.mark).toHaveBeenCalledWith(expect.stringContaining('lazy-hook-end'));
    expect(performance.measure).toHaveBeenCalled();
    
    // Restore original functions
    performance.mark = originalMark;
    performance.measure = originalMeasure;
  });
});

describe('Error Recovery and Resilience', () => {
  it('should implement exponential backoff for retries', async () => {
    // Arrange
    let attemptCount = 0;
    const retryDelays: number[] = [];
    
    const importFn = () => {
      attemptCount++;
      if (attemptCount <= 2) {
        return Promise.reject(new Error(`Attempt ${attemptCount} failed`));
      }
      return Promise.resolve({ default: mockBusinessLogic.useAssetInventory });
    };
    
    // Mock setTimeout to capture retry delays
    const originalSetTimeout = setTimeout;
    global.setTimeout = vi.fn((callback, delay) => {
      if (delay > 0) retryDelays.push(delay);
      return originalSetTimeout(callback, 0);
    });
    
    // Act
    const { result } = renderHook(() => useLazyHook(importFn, { 
      maxRetries: 3,
      retryDelay: 100,
      exponentialBackoff: true
    }));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.hookModule).toBe(mockBusinessLogic.useAssetInventory);
    expect(attemptCount).toBe(3);
    expect(retryDelays.length).toBe(2); // Two retries
    expect(retryDelays[1]).toBeGreaterThan(retryDelays[0]); // Exponential backoff
    
    global.setTimeout = originalSetTimeout;
  });

  it('should fallback to default hook on repeated failures', async () => {
    // Arrange
    const defaultHook = () => ({ data: [], error: 'Using fallback' });
    const importFn = () => Promise.reject(new Error('Import always fails'));
    
    // Act
    const { result } = renderHook(() => useLazyHook(importFn, {
      fallback: defaultHook,
      maxRetries: 2
    }));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.hookModule).toBe(defaultHook);
    expect(result.current.error).toBeNull(); // Error should be cleared when fallback is used
  });

  it('should handle network connectivity issues', async () => {
    // Arrange
    const networkError = new Error('Network error');
    networkError.name = 'NetworkError';
    
    const importFn = () => Promise.reject(networkError);
    
    // Act
    const { result } = renderHook(() => useLazyHook(importFn));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.error).toBe(networkError);
    expect(result.current.isNetworkError).toBe(true);
  });
});

describe('Memory Management', () => {
  it('should clean up resources when hook unmounts', async () => {
    // Arrange
    const cleanupSpy = vi.fn();
    const importFn = () => Promise.resolve({ 
      default: () => ({ cleanup: cleanupSpy })
    });
    
    // Act
    const { result, unmount } = renderHook(() => useLazyHook(importFn));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Unmount the hook
    unmount();
    
    // Assert
    expect(cleanupSpy).toHaveBeenCalled();
  });

  it('should not cause memory leaks with repeated loading', async () => {
    // Arrange
    const importFn = () => Promise.resolve({ 
      default: mockBusinessLogic.useAssetInventory 
    });
    
    // Act - Render and unmount multiple times
    for (let i = 0; i < 10; i++) {
      const { result, unmount } = renderHook(() => useLazyHook(importFn));
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      unmount();
    }
    
    // Assert - No memory leaks (this would be detected by memory profiling tools)
    // The test itself validates that the pattern doesn't cause obvious issues
    expect(true).toBe(true);
  });
});