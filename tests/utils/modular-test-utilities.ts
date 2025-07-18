/**
 * Modular Architecture Test Utilities
 * 
 * Comprehensive utilities for testing modular components, lazy loading,
 * and module boundaries in the modularized platform architecture.
 */

import { vi } from 'vitest';
import React from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { LoadingPriority } from '@/types/lazy';

// Types for modular testing
export interface LazyComponentTestConfig {
  componentName: string;
  importPath: string;
  mockImplementation?: React.ComponentType<unknown>;
  shouldFail?: boolean;
  loadDelay?: number;
  priority?: LoadingPriority;
}

export interface ModuleBoundaryTestConfig {
  moduleName: string;
  dependencies: string[];
  exports: string[];
  mockDependencies?: Record<string, unknown>;
}

export interface PerformanceTestConfig {
  componentName: string;
  maxLoadTime: number;
  maxBundleSize?: number;
  measureMetrics?: string[];
}

// Mock Implementations for Lazy Components
export class LazyComponentMocker {
  private mocks = new Map<string, React.ComponentType>();
  private importPromises = new Map<string, Promise<{ default: React.ComponentType }>>();

  createMockComponent(
    testId: string, 
    content: string = 'Mock Component',
    props: Record<string, unknown> = {}
  ): React.ComponentType {
    return React.forwardRef<HTMLDivElement, Record<string, unknown>>((componentProps, ref) => 
      React.createElement('div', {
        'data-testid': testId,
        ref,
        ...props,
        ...componentProps
      }, content)
    );
  }

  mockLazyImport(
    config: LazyComponentTestConfig
  ): () => Promise<{ default: React.ComponentType }> {
    const { componentName, mockImplementation, shouldFail, loadDelay = 0 } = config;
    
    if (this.importPromises.has(componentName)) {
      return () => this.importPromises.get(componentName)!;
    }

    const importPromise = new Promise<{ default: React.ComponentType }>((resolve, reject) => {
      setTimeout(() => {
        if (shouldFail) {
          reject(new Error(`Failed to load ${componentName}`));
        } else {
          const component = mockImplementation || 
            this.createMockComponent(`${componentName.toLowerCase()}-component`);
          this.mocks.set(componentName, component);
          resolve({ default: component });
        }
      }, loadDelay);
    });

    this.importPromises.set(componentName, importPromise);
    return () => importPromise;
  }

  getMockComponent(componentName: string): React.ComponentType | undefined {
    return this.mocks.get(componentName);
  }

  clearMocks(): void {
    this.mocks.clear();
    this.importPromises.clear();
  }
}

// Module Boundary Testing
export class ModuleBoundaryTester {
  private originalModules = new Map<string, unknown>();

  async mockModule(modulePath: string, mockImplementation: unknown): Promise<void> {
    // Store original module for restoration
    if (!this.originalModules.has(modulePath)) {
      try {
        const original = await import(modulePath);
        this.originalModules.set(modulePath, original);
      } catch {
        // Module doesn't exist yet
      }
    }

    vi.doMock(modulePath, () => mockImplementation);
  }

  async testModuleBoundary(config: ModuleBoundaryTestConfig): Promise<{
    isIsolated: boolean;
    circularDependencies: string[];
    unexpectedDependencies: string[];
  }> {
    const { moduleName, dependencies, exports } = config;
    
    // Mock all dependencies
    await Promise.all(dependencies.map(async dep => {
      if (config.mockDependencies?.[dep]) {
        await this.mockModule(dep, config.mockDependencies[dep]);
      } else {
        await this.mockModule(dep, { default: vi.fn() });
      }
    }));

    try {
      const module = await import(moduleName);
      
      // Check exports
      const actualExports = Object.keys(module);
      const unexpectedExports = actualExports.filter(exp => !exports.includes(exp));
      
      return {
        isIsolated: unexpectedExports.length === 0,
        circularDependencies: [], // Would need dependency graph analysis
        unexpectedDependencies: unexpectedExports
      };
    } catch (error) {
      throw new Error(`Failed to test module ${moduleName}: ${error}`);
    }
  }

  restoreModules(): void {
    this.originalModules.forEach((original, modulePath) => {
      vi.doUnmock(modulePath);
    });
    this.originalModules.clear();
  }
}

// Performance Testing Utilities
export class PerformanceTester {
  private metrics = new Map<string, number>();

  measureComponentLoad(componentName: string): {
    start: () => void;
    end: () => number;
    assert: (maxTime: number) => void;
  } {
    let startTime: number;

    return {
      start: () => {
        startTime = performance.now();
        global.performance.mark(`${componentName}-load-start`);
      },
      end: () => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        global.performance.mark(`${componentName}-load-end`);
        global.performance.measure(
          `${componentName}-load-duration`,
          `${componentName}-load-start`,
          `${componentName}-load-end`
        );
        this.metrics.set(componentName, duration);
        return duration;
      },
      assert: (maxTime: number) => {
        const duration = this.metrics.get(componentName);
        if (duration === undefined) {
          throw new Error(`No performance data for ${componentName}`);
        }
        if (duration > maxTime) {
          throw new Error(
            `Component ${componentName} took ${duration}ms to load, exceeding limit of ${maxTime}ms`
          );
        }
      }
    };
  }

  measureBundleSize(bundleName: string): {
    size: number;
    assert: (maxSize: number) => void;
  } {
    // Mock bundle size measurement (in real implementation, this would
    // analyze webpack bundle stats or use bundlesize tool)
    const mockSize = Math.floor(Math.random() * 500000); // 0-500KB

    return {
      size: mockSize,
      assert: (maxSize: number) => {
        if (mockSize > maxSize) {
          throw new Error(
            `Bundle ${bundleName} is ${mockSize} bytes, exceeding limit of ${maxSize} bytes`
          );
        }
      }
    };
  }

  getMetrics(): Record<string, number> {
    return Object.fromEntries(this.metrics);
  }

  clearMetrics(): void {
    this.metrics.clear();
  }
}

// Viewport Testing for Lazy Loading
export class ViewportTester {
  private observer: IntersectionObserver;
  private observedElements = new Set<Element>();

  constructor() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const element = entry.target as Element & { _intersectionCallback?: (entries: IntersectionObserverEntry[]) => void };
        if (element._intersectionCallback) {
          element._intersectionCallback([entry]);
        }
      });
    });
  }

  mockIntersectionObserver(): void {
    global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
      observe: vi.fn((element) => {
        this.observedElements.add(element);
        (element as Element & { _intersectionCallback?: (entries: IntersectionObserverEntry[]) => void })._intersectionCallback = callback;
      }),
      unobserve: vi.fn((element) => {
        this.observedElements.delete(element);
        delete (element as Element & { _intersectionCallback?: (entries: IntersectionObserverEntry[]) => void })._intersectionCallback;
      }),
      disconnect: vi.fn(() => {
        this.observedElements.clear();
      })
    }));
  }

  triggerIntersection(element: Element, isIntersecting: boolean = true): void {
    const callback = (element as Element & { _intersectionCallback?: (entries: IntersectionObserverEntry[]) => void })._intersectionCallback;
    if (callback) {
      callback([{
        target: element,
        isIntersecting,
        boundingClientRect: element.getBoundingClientRect(),
        intersectionRatio: isIntersecting ? 1 : 0,
        intersectionRect: isIntersecting ? element.getBoundingClientRect() : null,
        rootBounds: null,
        time: Date.now()
      }]);
    }
  }

  getObservedElements(): Element[] {
    return Array.from(this.observedElements);
  }
}

// Error Boundary Testing
export class ErrorBoundaryTester {
  static createTestError(message: string = 'Test error'): Error {
    const error = new Error(message);
    error.name = 'TestError';
    return error;
  }

  static createAsyncLoadError(componentName: string): Error {
    const error = new Error(`Failed to load component: ${componentName}`);
    error.name = 'ChunkLoadError';
    return error;
  }

  static createNetworkError(): Error {
    const error = new Error('Network request failed');
    error.name = 'NetworkError';
    return error;
  }

  static suppressConsoleError(callback: () => void): void {
    const originalError = console.error;
    console.error = vi.fn();
    
    try {
      callback();
    } finally {
      console.error = originalError;
    }
  }
}

// Custom Render Function for Modular Components
export interface ModularRenderOptions extends RenderOptions {
  mocks?: LazyComponentTestConfig[];
  viewport?: { width: number; height: number };
  performance?: boolean;
}

export function renderModularComponent(
  ui: React.ReactElement,
  options: ModularRenderOptions = {}
): RenderResult & {
  lazyMocker: LazyComponentMocker;
  performanceTester: PerformanceTester;
  viewportTester: ViewportTester;
} {
  const lazyMocker = new LazyComponentMocker();
  const performanceTester = new PerformanceTester();
  const viewportTester = new ViewportTester();

  // Setup mocks
  if (options.mocks) {
    options.mocks.forEach(mockConfig => {
      lazyMocker.mockLazyImport(mockConfig);
    });
  }

  // Setup viewport testing
  viewportTester.mockIntersectionObserver();

  // Setup performance monitoring
  if (options.performance) {
    // Enable performance monitoring
  }

  const result = render(ui, options);

  return {
    ...result,
    lazyMocker,
    performanceTester,
    viewportTester
  };
}

// Test Assertions for Modular Architecture
export const modularAssertions = {
  toLoadLazily: (component: Element, timeout: number = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const checkLoaded = () => {
        if (component.getAttribute('data-lazy-loaded') === 'true') {
          resolve(true);
        } else if (Date.now() - startTime > timeout) {
          reject(new Error(`Component did not load within ${timeout}ms`));
        } else {
          setTimeout(checkLoaded, 100);
        }
      };
      
      checkLoaded();
    });
  },

  toHaveModuleBoundary: async (modulePath: string, expectedExports: string[]) => {
    try {
      const module = await import(modulePath);
      const actualExports = Object.keys(module);
      const hasAllExports = expectedExports.every(exp => actualExports.includes(exp));
      
      return {
        pass: hasAllExports,
        message: () => hasAllExports
          ? `Expected module ${modulePath} not to have exports: ${expectedExports.join(', ')}`
          : `Expected module ${modulePath} to have exports: ${expectedExports.join(', ')}, but got: ${actualExports.join(', ')}`
      };
    } catch (error) {
      return {
        pass: false,
        message: () => `Failed to load module ${modulePath}: ${error}`
      };
    }
  },

  toBeWithinPerformanceBudget: (duration: number, budget: number) => {
    return {
      pass: duration <= budget,
      message: () => duration <= budget
        ? `Expected ${duration}ms not to be within budget of ${budget}ms`
        : `Expected ${duration}ms to be within budget of ${budget}ms`
    };
  }
};

// Export utilities
export {
  LazyComponentMocker,
  ModuleBoundaryTester,
  PerformanceTester,
  ViewportTester,
  ErrorBoundaryTester
};

// Global test setup for modular architecture
export const setupModularTesting = () => {
  const lazyMocker = new LazyComponentMocker();
  const boundaryTester = new ModuleBoundaryTester();
  const performanceTester = new PerformanceTester();
  const viewportTester = new ViewportTester();

  beforeEach(() => {
    lazyMocker.clearMocks();
    performanceTester.clearMetrics();
    viewportTester.mockIntersectionObserver();
  });

  afterEach(() => {
    lazyMocker.clearMocks();
    boundaryTester.restoreModules();
    performanceTester.clearMetrics();
  });

  return {
    lazyMocker,
    boundaryTester,
    performanceTester,
    viewportTester
  };
};