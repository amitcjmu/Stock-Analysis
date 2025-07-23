/**
 * Loading Manager - Core lazy loading infrastructure
 * Handles component loading, caching, and performance monitoring
 */

import type { LazyComponentOptions, LoadingState, LazyComponentImport } from '@/types/lazy'
import { LoadingPriority, LazyLoadingMetrics } from '@/types/lazy'

class LoadingManager {
  private static instance: LoadingManager;
  private loadingStates = new Map<string, LoadingState>();
  private componentCache = new Map<string, React.ComponentType>();
  private loadingQueue = new Map<LoadingPriority, Set<string>>();
  private metrics: LazyLoadingMetrics[] = [];
  private observers = new Map<string, IntersectionObserver>();

  private constructor() {
    // Initialize priority queues
    Object.values(LoadingPriority)
      .filter(v => typeof v === 'number')
      .forEach(priority => {
        this.loadingQueue.set(priority as LoadingPriority, new Set());
      });
  }

  static getInstance(): LoadingManager {
    if (!LoadingManager.instance) {
      LoadingManager.instance = new LoadingManager();
    }
    return LoadingManager.instance;
  }

  /**
   * Load a component with specified options
   */
  async loadComponent(
    componentId: string,
    importFn: LazyComponentImport,
    options: LazyComponentOptions = {}
  ): Promise<React.ComponentType> {
    const {
      priority = LoadingPriority.NORMAL,
      timeout = 30000,
      retryAttempts = 3,
      cacheStrategy = 'memory'
    } = options;

    // Check cache first
    const cached = this.getCachedComponent(componentId, cacheStrategy);
    if (cached) {
      this.recordMetric(componentId, 0, 0, true, priority);
      return cached;
    }

    // Initialize loading state
    const loadStartTime = performance.now();
    this.setLoadingState(componentId, {
      isLoading: true,
      error: null,
      retryCount: 0,
      loadStartTime,
      component: null
    });

    // Add to priority queue
    this.loadingQueue.get(priority)?.add(componentId);

    try {
      const component = await this.loadWithRetry(
        componentId,
        importFn,
        retryAttempts,
        timeout,
        loadStartTime,
        priority
      );

      // Cache the component
      this.cacheComponent(componentId, component, cacheStrategy);

      // Update loading state
      this.setLoadingState(componentId, {
        isLoading: false,
        error: null,
        retryCount: 0,
        loadStartTime,
        component
      });

      return component;
    } catch (error) {
      const loadingState = this.loadingStates.get(componentId);
      this.setLoadingState(componentId, {
        ...loadingState!,
        isLoading: false,
        error: error as Error,
        retryCount: loadingState?.retryCount || 0
      });
      throw error;
    } finally {
      this.loadingQueue.get(priority)?.delete(componentId);
    }
  }

  /**
   * Load component with retry logic
   */
  private async loadWithRetry(
    componentId: string,
    importFn: LazyComponentImport,
    maxRetries: number,
    timeout: number,
    loadStartTime: number,
    priority: LoadingPriority
  ): Promise<React.ComponentType> {
    let lastError: Error;
    let retryCount = 0;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const componentModule = await Promise.race([
          importFn(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Load timeout')), timeout)
          )
        ]);

        const loadEndTime = performance.now();
        const loadDuration = loadEndTime - loadStartTime;

        this.recordMetric(componentId, loadStartTime, loadEndTime, false, priority, retryCount);

        return componentModule.default;
      } catch (error) {
        lastError = error as Error;
        retryCount = attempt;

        // Update loading state with retry count
        const currentState = this.loadingStates.get(componentId);
        if (currentState) {
          this.setLoadingState(componentId, {
            ...currentState,
            retryCount: attempt + 1
          });
        }

        // Exponential backoff for retries
        if (attempt < maxRetries) {
          await this.delay(Math.pow(2, attempt) * 1000);
        }
      }
    }

    throw lastError!;
  }

  /**
   * Preload components based on strategy
   */
  preloadComponent(
    componentId: string,
    importFn: LazyComponentImport,
    options: LazyComponentOptions = {}
  ): void {
    // Don't preload if already loading or loaded
    if (this.loadingStates.has(componentId) || this.componentCache.has(componentId)) {
      return;
    }

    const priority = options.priority || LoadingPriority.LOW;
    
    // Use requestIdleCallback for low priority preloads
    if (priority === LoadingPriority.LOW && 'requestIdleCallback' in window) {
      requestIdleCallback(() => {
        this.loadComponent(componentId, importFn, options).catch(() => {
          // Ignore preload failures
        });
      });
    } else {
      // Load immediately for higher priorities
      this.loadComponent(componentId, importFn, options).catch(() => {
        // Ignore preload failures
      });
    }
  }

  /**
   * Set up intersection observer for viewport-based loading
   */
  observeForViewport(
    elementId: string,
    componentId: string,
    importFn: LazyComponentImport,
    options: LazyComponentOptions = {}
  ): void {
    const element = document.getElementById(elementId);
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            this.loadComponent(componentId, importFn, options);
            observer.disconnect();
            this.observers.delete(elementId);
          }
        });
      },
      { threshold: 0.1 }
    );

    observer.observe(element);
    this.observers.set(elementId, observer);
  }

  /**
   * Get loading state for a component
   */
  getLoadingState(componentId: string): LoadingState | null {
    return this.loadingStates.get(componentId) || null;
  }

  /**
   * Cache component based on strategy
   */
  private cacheComponent(
    componentId: string,
    component: React.ComponentType,
    strategy: 'memory' | 'session' | 'persistent'
  ): void {
    this.componentCache.set(componentId, component);

    if (strategy === 'session') {
      sessionStorage.setItem(`lazy_component_${componentId}`, 'cached');
    } else if (strategy === 'persistent') {
      localStorage.setItem(`lazy_component_${componentId}`, 'cached');
    }
  }

  /**
   * Get cached component
   */
  private getCachedComponent(
    componentId: string,
    strategy: 'memory' | 'session' | 'persistent'
  ): React.ComponentType | null {
    // Check memory cache first
    const memoryCache = this.componentCache.get(componentId);
    if (memoryCache) return memoryCache;

    // Check storage caches
    if (strategy === 'session') {
      return sessionStorage.getItem(`lazy_component_${componentId}`) ? null : null;
    } else if (strategy === 'persistent') {
      return localStorage.getItem(`lazy_component_${componentId}`) ? null : null;
    }

    return null;
  }

  /**
   * Record loading metrics
   */
  private recordMetric(
    componentName: string,
    loadStartTime: number,
    loadEndTime: number,
    cacheHit: boolean,
    priority: LoadingPriority,
    retryCount = 0
  ): void {
    const metric: LazyLoadingMetrics = {
      componentName,
      loadStartTime,
      loadEndTime,
      loadDuration: loadEndTime - loadStartTime,
      cacheHit,
      retryCount,
      priority,
      userAgent: navigator.userAgent,
      connectionType: (navigator as Navigator & { connection?: { effectiveType: string } }).connection?.effectiveType
    };

    this.metrics.push(metric);

    // Keep only last 1000 metrics to prevent memory leaks
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }
  }

  /**
   * Get performance metrics
   */
  getMetrics(): LazyLoadingMetrics[] {
    return [...this.metrics];
  }

  /**
   * Clear all caches
   */
  clearCaches(): void {
    this.componentCache.clear();
    this.loadingStates.clear();
    
    // Clear storage caches
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith('lazy_component_')) {
        sessionStorage.removeItem(key);
      }
    });

    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('lazy_component_')) {
        localStorage.removeItem(key);
      }
    });
  }

  /**
   * Get cache effectiveness
   */
  getCacheEffectiveness(): number {
    const totalLoads = this.metrics.length;
    if (totalLoads === 0) return 0;

    const cacheHits = this.metrics.filter(m => m.cacheHit).length;
    return (cacheHits / totalLoads) * 100;
  }

  /**
   * Set loading state
   */
  private setLoadingState(componentId: string, state: LoadingState): void {
    this.loadingStates.set(componentId, state);
  }

  /**
   * Utility delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }
}

export const loadingManager: LoadingManager = LoadingManager.getInstance();