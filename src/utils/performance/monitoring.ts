import React from 'react';
import { PerformanceConfig, PerformanceMetrics } from '../../contexts/GlobalContext/types';

// Performance monitoring configuration
const DEFAULT_CONFIG: PerformanceConfig = {
  enabled: process.env.NODE_ENV === 'development',
  sampleRate: 0.1, // Sample 10% of events in production
  reportInterval: 10000, // Report every 10 seconds
  maxMetricsHistory: 100,
};

// Performance event types
export interface PerformanceEvent {
  name: string;
  duration: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Render performance tracker
export interface RenderPerformance {
  componentName: string;
  renderTime: number;
  propsChanged: boolean;
  stateChanged: boolean;
  timestamp: number;
}

/**
 * Performance monitoring utility class
 */
class PerformanceMonitor {
  private config: PerformanceConfig;
  private events: PerformanceEvent[] = [];
  private renderHistory: RenderPerformance[] = [];
  private observers: ((metrics: PerformanceMetrics) => void)[] = [];
  private reportTimer: NodeJS.Timer | null = null;

  constructor(config: Partial<PerformanceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };

    if (this.config.enabled && typeof window !== 'undefined') {
      this.setupPerformanceObserver();
      this.startReporting();
    }
  }

  /**
   * Set up performance observer for Web APIs
   */
  private setupPerformanceObserver(): void {
    if (!window.PerformanceObserver) return;

    try {
      // Observe navigation timing
      const navigationObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordEvent({
            name: 'navigation',
            duration: entry.duration,
            timestamp: entry.startTime,
            metadata: {
              type: entry.entryType,
              name: entry.name,
            },
          });
        }
      });
      navigationObserver.observe({ entryTypes: ['navigation'] });

      // Observe resource loading
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (Math.random() <= this.config.sampleRate) {
            this.recordEvent({
              name: 'resource',
              duration: entry.duration,
              timestamp: entry.startTime,
              metadata: {
                name: entry.name,
                size: (entry as any).transferSize,
              },
            });
          }
        }
      });
      resourceObserver.observe({ entryTypes: ['resource'] });

      // Observe long tasks
      if ('PerformanceObserver' in window) {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordEvent({
              name: 'long-task',
              duration: entry.duration,
              timestamp: entry.startTime,
              metadata: {
                name: entry.name,
              },
            });
          }
        });
        try {
          longTaskObserver.observe({ entryTypes: ['longtask'] });
        } catch (e) {
          // longtask not supported in all browsers
        }
      }
    } catch (error) {
      console.warn('Failed to setup performance observer:', error);
    }
  }

  /**
   * Start automatic metrics reporting
   */
  private startReporting(): void {
    if (this.reportTimer) return;

    this.reportTimer = setInterval(() => {
      const metrics = this.getMetrics();
      this.observers.forEach(observer => observer(metrics));
    }, this.config.reportInterval);
  }

  /**
   * Stop automatic metrics reporting
   */
  stopReporting(): void {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }
  }

  /**
   * Record a performance event
   */
  recordEvent(event: PerformanceEvent): void {
    if (!this.config.enabled) return;

    this.events.push(event);

    // Keep only recent events
    if (this.events.length > this.config.maxMetricsHistory) {
      this.events = this.events.slice(-this.config.maxMetricsHistory);
    }
  }

  /**
   * Record render performance
   */
  recordRender(performance: RenderPerformance): void {
    if (!this.config.enabled) return;

    this.renderHistory.push(performance);

    // Keep only recent render history
    if (this.renderHistory.length > this.config.maxMetricsHistory) {
      this.renderHistory = this.renderHistory.slice(-this.config.maxMetricsHistory);
    }
  }

  /**
   * Mark the start of a performance measurement
   */
  markStart(label: string): void {
    if (!this.config.enabled || typeof window === 'undefined') return;

    if (window.performance && window.performance.mark) {
      window.performance.mark(`${label}-start`);
    }
  }

  /**
   * Mark the end of a performance measurement and record the event
   */
  markEnd(label: string, metadata?: Record<string, any>): number | null {
    if (!this.config.enabled || typeof window === 'undefined') return null;

    if (window.performance && window.performance.mark && window.performance.measure) {
      try {
        window.performance.mark(`${label}-end`);
        window.performance.measure(label, `${label}-start`, `${label}-end`);

        const measures = window.performance.getEntriesByName(label, 'measure');
        if (measures.length > 0) {
          const measure = measures[measures.length - 1];

          this.recordEvent({
            name: label,
            duration: measure.duration,
            timestamp: measure.startTime,
            metadata,
          });

          // Clean up marks and measures
          window.performance.clearMarks(`${label}-start`);
          window.performance.clearMarks(`${label}-end`);
          window.performance.clearMeasures(label);

          return measure.duration;
        }
      } catch (error) {
        console.warn(`Failed to measure performance for ${label}:`, error);
      }
    }

    return null;
  }

  /**
   * Get current performance metrics
   */
  getMetrics(): PerformanceMetrics {
    const now = Date.now();
    const recentEvents = this.events.filter(e => now - e.timestamp < 60000); // Last minute
    const recentRenders = this.renderHistory.filter(r => now - r.timestamp < 60000);

    const renderTimes = recentRenders.map(r => r.renderTime);
    const avgRenderTime = renderTimes.length > 0
      ? renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
      : 0;

    // Calculate cache hit rate from events (if available)
    const cacheEvents = recentEvents.filter(e => e.name.includes('cache'));
    const cacheHits = cacheEvents.filter(e => e.metadata?.hit).length;
    const cacheHitRate = cacheEvents.length > 0 ? cacheHits / cacheEvents.length : 0;

    // Count API calls
    const apiCalls = recentEvents.filter(e =>
      e.name.includes('api') || e.name.includes('fetch') || e.name.includes('xhr')
    ).length;

    return {
      renderCount: recentRenders.length,
      lastRenderTime: renderTimes[renderTimes.length - 1] || 0,
      averageRenderTime: avgRenderTime,
      cacheHitRate,
      apiCallCount: apiCalls,
    };
  }

  /**
   * Subscribe to performance metrics updates
   */
  subscribe(observer: (metrics: PerformanceMetrics) => void): () => void {
    this.observers.push(observer);

    return () => {
      const index = this.observers.indexOf(observer);
      if (index > -1) {
        this.observers.splice(index, 1);
      }
    };
  }

  /**
   * Get detailed performance report
   */
  getReport(): {
    events: PerformanceEvent[];
    renders: RenderPerformance[];
    metrics: PerformanceMetrics;
    config: PerformanceConfig;
  } {
    return {
      events: [...this.events],
      renders: [...this.renderHistory],
      metrics: this.getMetrics(),
      config: this.config,
    };
  }

  /**
   * Clear all performance data
   */
  clear(): void {
    this.events = [];
    this.renderHistory = [];
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<PerformanceConfig>): void {
    this.config = { ...this.config, ...updates };

    if (this.config.enabled && !this.reportTimer) {
      this.startReporting();
    } else if (!this.config.enabled && this.reportTimer) {
      this.stopReporting();
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopReporting();
    this.clear();
    this.observers = [];
  }
}

// Create global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * React Hook for component render performance tracking
 */
export const useRenderPerformance = (componentName: string) => {
  const startTime = performance.now();

  React.useEffect(() => {
    const endTime = performance.now();
    const renderTime = endTime - startTime;

    performanceMonitor.recordRender({
      componentName,
      renderTime,
      propsChanged: false, // This would need prop comparison logic
      stateChanged: false, // This would need state comparison logic
      timestamp: startTime,
    });
  });

  return {
    markStart: (label: string) => performanceMonitor.markStart(`${componentName}-${label}`),
    markEnd: (label: string) => performanceMonitor.markEnd(`${componentName}-${label}`),
  };
};

/**
 * Decorator for measuring function performance
 */
export function measurePerformance(label?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    const measureLabel = label || `${target.constructor.name}.${propertyKey}`;

    descriptor.value = async function (...args: any[]) {
      performanceMonitor.markStart(measureLabel);
      try {
        const result = await originalMethod.apply(this, args);
        performanceMonitor.markEnd(measureLabel);
        return result;
      } catch (error) {
        performanceMonitor.markEnd(measureLabel, { error: error.message });
        throw error;
      }
    };

    return descriptor;
  };
}

/**
 * Utility to measure async operations
 */
export async function measureAsync<T>(
  label: string,
  operation: () => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> {
  performanceMonitor.markStart(label);
  try {
    const result = await operation();
    performanceMonitor.markEnd(label, metadata);
    return result;
  } catch (error) {
    performanceMonitor.markEnd(label, { ...metadata, error: error.message });
    throw error;
  }
}

/**
 * Utility to measure synchronous operations
 */
export function measureSync<T>(
  label: string,
  operation: () => T,
  metadata?: Record<string, any>
): T {
  performanceMonitor.markStart(label);
  try {
    const result = operation();
    performanceMonitor.markEnd(label, metadata);
    return result;
  } catch (error) {
    performanceMonitor.markEnd(label, { ...metadata, error: error.message });
    throw error;
  }
}

// Export for debugging in development
if (process.env.NODE_ENV === 'development') {
  (window as any).__performanceMonitor = performanceMonitor;
}
