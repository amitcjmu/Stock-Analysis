/**
 * Performance Monitor - Advanced performance monitoring for lazy loading
 */

import type { BundleAnalysis, LoadingPriority } from '@/types/lazy'
import type { LazyLoadingMetrics } from '@/types/lazy'

interface PerformanceThresholds {
  excellentLoadTime: number;
  goodLoadTime: number;
  poorLoadTime: number;
  criticalLoadTime: number;
}

interface LoadingPattern {
  route: string;
  component: string;
  frequency: number;
  averageLoadTime: number;
  cacheHitRate: number;
  errorRate: number;
}

interface PerformanceInsight {
  type: 'optimization' | 'warning' | 'error' | 'info';
  category: 'bundle-size' | 'load-time' | 'cache-efficiency' | 'error-rate';
  message: string;
  impact: 'high' | 'medium' | 'low';
  suggestion: string;
  metrics?: {
    averageLoadTime?: number;
    cacheHitRate?: number;
    errorRate?: number;
    bundleSize?: number;
    componentName?: string;
    frequency?: number;
  };
}

class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: LazyLoadingMetrics[] = [];
  private bundleMetrics = new Map<string, number>();
  private loadingPatterns = new Map<string, LoadingPattern>();
  private performanceObserver: PerformanceObserver | null = null;
  private resourceObserver: PerformanceObserver | null = null;

  private thresholds: PerformanceThresholds = {
    excellentLoadTime: 100,   // < 100ms
    goodLoadTime: 300,        // < 300ms
    poorLoadTime: 1000,       // < 1s
    criticalLoadTime: 3000    // > 3s
  };

  private constructor() {
    this.setupPerformanceObservation();
    this.setupResourceObservation();
    this.setupMemoryMonitoring();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Record a lazy loading metric
   */
  recordMetric(metric: LazyLoadingMetrics): void {
    this.metrics.push(metric);

    // Update loading patterns
    this.updateLoadingPattern(metric);

    // Keep only last 1000 metrics to prevent memory leaks
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }

    // Real-time performance analysis
    this.analyzeRealTimePerformance(metric);
  }

  /**
   * Get comprehensive performance analysis
   */
  getPerformanceAnalysis(): {
    summary: {
      totalLoads: number;
      averageLoadTime: number;
      cacheHitRate: number;
      errorRate: number;
      performanceScore: number;
    };
    bundleAnalysis: BundleAnalysis;
    insights: PerformanceInsight[];
    patterns: LoadingPattern[];
  } {
    const summary = this.calculateSummaryMetrics();
    const bundleAnalysis = this.analyzeBundlePerformance();
    const insights = this.generatePerformanceInsights();
    const patterns = Array.from(this.loadingPatterns.values());

    return {
      summary,
      bundleAnalysis,
      insights,
      patterns
    };
  }

  /**
   * Calculate summary performance metrics
   */
  private calculateSummaryMetrics() {
    const totalLoads = this.metrics.length;
    if (totalLoads === 0) {
      return {
        totalLoads: 0,
        averageLoadTime: 0,
        cacheHitRate: 0,
        errorRate: 0,
        performanceScore: 100
      };
    }

    const averageLoadTime = this.metrics.reduce((sum, m) => sum + m.loadDuration, 0) / totalLoads;
    const cacheHits = this.metrics.filter(m => m.cacheHit).length;
    const cacheHitRate = (cacheHits / totalLoads) * 100;
    const errors = this.metrics.filter(m => m.retryCount > 0).length;
    const errorRate = (errors / totalLoads) * 100;

    const performanceScore = this.calculatePerformanceScore(averageLoadTime, cacheHitRate, errorRate);

    return {
      totalLoads,
      averageLoadTime: Math.round(averageLoadTime),
      cacheHitRate: Math.round(cacheHitRate * 100) / 100,
      errorRate: Math.round(errorRate * 100) / 100,
      performanceScore: Math.round(performanceScore)
    };
  }

  /**
   * Calculate overall performance score (0-100)
   */
  private calculatePerformanceScore(
    averageLoadTime: number,
    cacheHitRate: number,
    errorRate: number
  ): number {
    // Load time score (40% weight)
    let loadTimeScore = 100;
    if (averageLoadTime > this.thresholds.criticalLoadTime) {
      loadTimeScore = 0;
    } else if (averageLoadTime > this.thresholds.poorLoadTime) {
      loadTimeScore = 30;
    } else if (averageLoadTime > this.thresholds.goodLoadTime) {
      loadTimeScore = 70;
    } else if (averageLoadTime > this.thresholds.excellentLoadTime) {
      loadTimeScore = 90;
    }

    // Cache hit rate score (35% weight)
    const cacheScore = Math.min(100, cacheHitRate * 1.2);

    // Error rate score (25% weight)
    const errorScore = Math.max(0, 100 - (errorRate * 10));

    return (loadTimeScore * 0.4) + (cacheScore * 0.35) + (errorScore * 0.25);
  }

  /**
   * Analyze bundle performance
   */
  private analyzeBundlePerformance(): BundleAnalysis {
    const chunkSizes: Record<string, number> = {};
    let totalBundleSize = 0;
    let initialBundleSize = 0;

    // Collect chunk sizes from performance entries
    this.bundleMetrics.forEach((size, chunk) => {
      chunkSizes[chunk] = size;
      totalBundleSize += size;
      
      if (chunk.includes('main') || chunk.includes('vendor')) {
        initialBundleSize += size;
      }
    });

    const loadedChunks = Array.from(this.bundleMetrics.keys());
    const pendingChunks = this.getPendingChunks();
    const cacheEffectiveness = this.calculateCacheEffectiveness();

    return {
      totalBundleSize,
      initialBundleSize,
      chunkSizes,
      loadedChunks,
      pendingChunks,
      cacheEffectiveness,
      performanceScore: this.calculateSummaryMetrics().performanceScore
    };
  }

  /**
   * Generate performance insights and recommendations
   */
  private generatePerformanceInsights(): PerformanceInsight[] {
    const insights: PerformanceInsight[] = [];
    const summary = this.calculateSummaryMetrics();

    // Load time insights
    if (summary.averageLoadTime > this.thresholds.poorLoadTime) {
      insights.push({
        type: 'warning',
        category: 'load-time',
        message: `Average load time (${summary.averageLoadTime}ms) exceeds recommended threshold`,
        impact: 'high',
        suggestion: 'Consider implementing preloading strategies or reducing chunk sizes'
      });
    }

    // Cache efficiency insights
    if (summary.cacheHitRate < 60) {
      insights.push({
        type: 'optimization',
        category: 'cache-efficiency',
        message: `Cache hit rate (${summary.cacheHitRate}%) is below optimal`,
        impact: 'medium',
        suggestion: 'Review caching strategies and implement smarter preloading'
      });
    }

    // Error rate insights
    if (summary.errorRate > 5) {
      insights.push({
        type: 'error',
        category: 'error-rate',
        message: `High error rate (${summary.errorRate}%) detected`,
        impact: 'high',
        suggestion: 'Investigate network issues or implement better retry mechanisms'
      });
    }

    // Bundle size insights
    const bundleAnalysis = this.analyzeBundlePerformance();
    if (bundleAnalysis.initialBundleSize > 200 * 1024) { // 200KB
      insights.push({
        type: 'warning',
        category: 'bundle-size',
        message: `Initial bundle size (${Math.round(bundleAnalysis.initialBundleSize / 1024)}KB) is large`,
        impact: 'medium',
        suggestion: 'Consider splitting critical code into smaller chunks'
      });
    }

    // Performance patterns insights
    this.loadingPatterns.forEach((pattern, key) => {
      if (pattern.frequency > 10 && pattern.averageLoadTime > this.thresholds.goodLoadTime) {
        insights.push({
          type: 'optimization',
          category: 'load-time',
          message: `Frequently loaded component "${pattern.component}" has slow load times`,
          impact: 'high',
          suggestion: 'Consider preloading this component or optimizing its dependencies'
        });
      }
    });

    return insights.sort((a, b) => {
      const impactScore = { high: 3, medium: 2, low: 1 };
      return impactScore[b.impact] - impactScore[a.impact];
    });
  }

  /**
   * Update loading patterns for analysis
   */
  private updateLoadingPattern(metric: LazyLoadingMetrics): void {
    const key = `${metric.componentName}`;
    const existing = this.loadingPatterns.get(key);

    if (existing) {
      const newFrequency = existing.frequency + 1;
      const newAverageLoadTime = (existing.averageLoadTime * existing.frequency + metric.loadDuration) / newFrequency;
      const newCacheHitRate = ((existing.cacheHitRate * existing.frequency) + (metric.cacheHit ? 100 : 0)) / newFrequency;
      const newErrorRate = ((existing.errorRate * existing.frequency) + (metric.retryCount > 0 ? 100 : 0)) / newFrequency;

      this.loadingPatterns.set(key, {
        ...existing,
        frequency: newFrequency,
        averageLoadTime: newAverageLoadTime,
        cacheHitRate: newCacheHitRate,
        errorRate: newErrorRate
      });
    } else {
      this.loadingPatterns.set(key, {
        route: window.location.pathname,
        component: metric.componentName,
        frequency: 1,
        averageLoadTime: metric.loadDuration,
        cacheHitRate: metric.cacheHit ? 100 : 0,
        errorRate: metric.retryCount > 0 ? 100 : 0
      });
    }
  }

  /**
   * Setup performance observation
   */
  private setupPerformanceObservation(): void {
    if ('PerformanceObserver' in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            console.debug('Navigation performance:', entry);
          } else if (entry.entryType === 'measure') {
            console.debug('Custom measure:', entry.name, entry.duration);
          }
        }
      });

      this.performanceObserver.observe({ 
        entryTypes: ['navigation', 'measure'] 
      });
    }
  }

  /**
   * Setup resource observation for bundle analysis
   */
  private setupResourceObservation(): void {
    if ('PerformanceObserver' in window) {
      this.resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name.includes('.js') || entry.name.includes('chunk')) {
            const resourceEntry = entry as PerformanceResourceTiming;
            const size = resourceEntry.transferSize || resourceEntry.encodedBodySize || 0;
            const chunkName = this.extractChunkName(entry.name);
            this.bundleMetrics.set(chunkName, size);
          }
        }
      });

      this.resourceObserver.observe({ 
        entryTypes: ['resource'] 
      });
    }
  }

  /**
   * Setup memory monitoring
   */
  private setupMemoryMonitoring(): void {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as Performance & { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
        
        // Calculate percentages
        const usedPercentOfTotal = (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100;
        const usedPercentOfLimit = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
        
        // Only warn if BOTH conditions are true:
        // 1. Using >98% of current heap AND 
        // 2. Using >50% of the browser's memory limit (indicating actual pressure)
        const shouldWarn = usedPercentOfTotal > 98 && usedPercentOfLimit > 50;
        
        if (shouldWarn) {
          console.warn('High memory usage detected:', {
            used: Math.round(memory.usedJSHeapSize / 1024 / 1024) + 'MB',
            total: Math.round(memory.totalJSHeapSize / 1024 / 1024) + 'MB',
            limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024) + 'MB',
            usedPercent: Math.round(usedPercentOfTotal) + '% of heap',
            limitPercent: Math.round(usedPercentOfLimit) + '% of browser limit'
          });
        }
      }, 120000); // Check every 2 minutes to reduce noise
    }
  }

  /**
   * Real-time performance analysis
   */
  private analyzeRealTimePerformance(metric: LazyLoadingMetrics): void {
    // Alert for critical load times
    if (metric.loadDuration > this.thresholds.criticalLoadTime) {
      console.warn(`Critical load time detected for ${metric.componentName}: ${metric.loadDuration}ms`);
    }

    // Alert for excessive retries
    if (metric.retryCount > 2) {
      console.warn(`Excessive retries for ${metric.componentName}: ${metric.retryCount} attempts`);
    }

    // Memory pressure detection
    if ('memory' in performance) {
      const memory = (performance as Performance & { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
      const memoryUsagePercent = (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100;
      
      if (memoryUsagePercent > 85) {
        console.warn('High memory usage detected during lazy loading:', `${memoryUsagePercent.toFixed(1)}%`);
      }
    }
  }

  /**
   * Extract chunk name from resource URL
   */
  private extractChunkName(url: string): string {
    const parts = url.split('/');
    const filename = parts[parts.length - 1];
    return filename.split('?')[0]; // Remove query parameters
  }

  /**
   * Get pending chunks that should be loaded
   */
  private getPendingChunks(): string[] {
    // This would need to be integrated with the bundler's chunk manifest
    // For now, return an empty array
    return [];
  }

  /**
   * Calculate cache effectiveness
   */
  private calculateCacheEffectiveness(): number {
    const totalLoads = this.metrics.length;
    if (totalLoads === 0) return 0;

    const cacheHits = this.metrics.filter(m => m.cacheHit).length;
    return (cacheHits / totalLoads) * 100;
  }

  /**
   * Export performance data for analysis
   */
  exportPerformanceData(): string {
    const data = {
      timestamp: new Date().toISOString(),
      metrics: this.metrics,
      analysis: this.getPerformanceAnalysis(),
      userAgent: navigator.userAgent,
      connection: (navigator as Navigator & { connection?: { effectiveType: string; downlink: number; rtt: number } }).connection ? {
        effectiveType: (navigator as Navigator & { connection: { effectiveType: string; downlink: number; rtt: number } }).connection.effectiveType,
        downlink: (navigator as Navigator & { connection: { effectiveType: string; downlink: number; rtt: number } }).connection.downlink,
        rtt: (navigator as Navigator & { connection: { effectiveType: string; downlink: number; rtt: number } }).connection.rtt
      } : null
    };

    return JSON.stringify(data, null, 2);
  }

  /**
   * Clear all performance data
   */
  clearData(): void {
    this.metrics = [];
    this.bundleMetrics.clear();
    this.loadingPatterns.clear();
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }
    if (this.resourceObserver) {
      this.resourceObserver.disconnect();
    }
  }
}

export const performanceMonitor: PerformanceMonitor = PerformanceMonitor.getInstance();