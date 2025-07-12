/**
 * Route Preloader - Intelligent preloading strategies for routes
 */

import { LoadingPriority } from '@/types/lazy';
import { loadingManager } from './loadingManager';

interface RouteConfig {
  path: string;
  importFn: () => Promise<{ default: React.ComponentType<any> }>;
  priority: LoadingPriority;
  preloadOn?: ('hover' | 'visible' | 'idle' | 'prefetch')[];
  dependencies?: string[];
}

interface PreloadStrategy {
  trigger: 'navigation' | 'idle' | 'viewport' | 'hover' | 'manual';
  routes: string[];
  delay?: number;
}

class RoutePreloader {
  private static instance: RoutePreloader;
  private routes = new Map<string, RouteConfig>();
  private preloadedRoutes = new Set<string>();
  private hoverTimeouts = new Map<string, NodeJS.Timeout>();
  private navigationHistory: string[] = [];

  private constructor() {
    this.setupNavigationTracking();
    this.setupIdlePreloading();
  }

  static getInstance(): RoutePreloader {
    if (!RoutePreloader.instance) {
      RoutePreloader.instance = new RoutePreloader();
    }
    return RoutePreloader.instance;
  }

  /**
   * Register a route for preloading
   */
  registerRoute(config: RouteConfig): void {
    this.routes.set(config.path, config);
  }

  /**
   * Preload routes based on current location and user behavior
   */
  preloadFromCurrentLocation(currentPath: string): void {
    const suggestedRoutes = this.getSuggestedRoutes(currentPath);
    
    suggestedRoutes.forEach(route => {
      this.preloadRoute(route.path, route.priority);
    });
  }

  /**
   * Get suggested routes based on current path and navigation patterns
   */
  private getSuggestedRoutes(currentPath: string): RouteConfig[] {
    const suggestions: RouteConfig[] = [];

    // Discovery flow suggestions
    if (currentPath.startsWith('/discovery')) {
      const discoveryRoutes = [
        '/discovery/cmdb-import',
        '/discovery/inventory',
        '/discovery/attribute-mapping',
        '/discovery/data-cleansing'
      ];
      
      discoveryRoutes.forEach(path => {
        const route = this.routes.get(path);
        if (route && !this.preloadedRoutes.has(path)) {
          suggestions.push(route);
        }
      });
    }

    // Assessment flow suggestions
    if (currentPath.startsWith('/assess') || currentPath.includes('assessment')) {
      const assessmentRoutes = [
        '/assessment/overview',
        '/assessment/initialize'
      ];
      
      assessmentRoutes.forEach(path => {
        const route = this.routes.get(path);
        if (route && !this.preloadedRoutes.has(path)) {
          suggestions.push(route);
        }
      });
    }

    // Sequential workflow suggestions
    const workflowOrder = ['/discovery', '/assess', '/plan', '/execute', '/modernize'];
    const currentIndex = workflowOrder.findIndex(p => currentPath.startsWith(p));
    
    if (currentIndex !== -1 && currentIndex < workflowOrder.length - 1) {
      const nextPath = workflowOrder[currentIndex + 1];
      const route = this.routes.get(nextPath);
      if (route && !this.preloadedRoutes.has(nextPath)) {
        suggestions.push(route);
      }
    }

    return suggestions.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Preload a specific route
   */
  preloadRoute(path: string, priority: LoadingPriority = LoadingPriority.LOW): void {
    const route = this.routes.get(path);
    if (!route || this.preloadedRoutes.has(path)) {
      return;
    }

    loadingManager.preloadComponent(
      `route_${path}`,
      route.importFn,
      { priority }
    );

    this.preloadedRoutes.add(path);
  }

  /**
   * Setup hover-based preloading for navigation links
   */
  setupHoverPreloading(): void {
    document.addEventListener('mouseover', (event) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a[href]') as HTMLAnchorElement;
      
      if (!link || link.hostname !== window.location.hostname) {
        return;
      }

      const href = link.getAttribute('href');
      if (!href || this.preloadedRoutes.has(href)) {
        return;
      }

      // Clear existing timeout for this route
      const existingTimeout = this.hoverTimeouts.get(href);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // Set new timeout for preloading
      const timeout = setTimeout(() => {
        this.preloadRoute(href, LoadingPriority.HIGH);
        this.hoverTimeouts.delete(href);
      }, 100); // Small delay to avoid preloading on quick hovers

      this.hoverTimeouts.set(href, timeout);
    });

    // Clear timeouts on mouse leave
    document.addEventListener('mouseout', (event) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a[href]') as HTMLAnchorElement;
      
      if (link) {
        const href = link.getAttribute('href');
        if (href) {
          const timeout = this.hoverTimeouts.get(href);
          if (timeout) {
            clearTimeout(timeout);
            this.hoverTimeouts.delete(href);
          }
        }
      }
    });
  }

  /**
   * Setup navigation tracking for intelligent preloading
   */
  private setupNavigationTracking(): void {
    // Track navigation history for pattern analysis
    const trackNavigation = () => {
      const currentPath = window.location.pathname;
      this.navigationHistory.push(currentPath);
      
      // Keep only last 10 navigations
      if (this.navigationHistory.length > 10) {
        this.navigationHistory = this.navigationHistory.slice(-10);
      }

      // Preload based on current location
      this.preloadFromCurrentLocation(currentPath);
    };

    // Track initial page load
    trackNavigation();

    // Track navigation changes
    window.addEventListener('popstate', trackNavigation);
    
    // Track programmatic navigation (for SPA routing)
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      setTimeout(trackNavigation, 0);
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      setTimeout(trackNavigation, 0);
    };
  }

  /**
   * Setup idle-time preloading
   */
  private setupIdlePreloading(): void {
    let idleTimer: NodeJS.Timeout;
    const idleTime = 2000; // 2 seconds of inactivity

    const resetIdleTimer = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        this.preloadIdleRoutes();
      }, idleTime);
    };

    // Reset timer on user activity
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
      document.addEventListener(event, resetIdleTimer, true);
    });

    // Start the timer
    resetIdleTimer();
  }

  /**
   * Preload routes during idle time
   */
  private preloadIdleRoutes(): void {
    const currentPath = window.location.pathname;
    const idleRoutes = this.getSuggestedRoutes(currentPath)
      .filter(route => !this.preloadedRoutes.has(route.path))
      .slice(0, 3); // Limit to 3 routes during idle time

    idleRoutes.forEach(route => {
      this.preloadRoute(route.path, LoadingPriority.LOW);
    });
  }

  /**
   * Preload routes based on viewport visibility
   */
  setupViewportPreloading(): void {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const element = entry.target as HTMLElement;
          const href = element.getAttribute('data-preload-route');
          
          if (href && !this.preloadedRoutes.has(href)) {
            this.preloadRoute(href, LoadingPriority.NORMAL);
          }
        }
      });
    }, { threshold: 0.1 });

    // Observe elements with preload attributes
    document.querySelectorAll('[data-preload-route]').forEach(el => {
      observer.observe(el);
    });
  }

  /**
   * Get preloading statistics
   */
  getPreloadingStats(): {
    totalRoutes: number;
    preloadedRoutes: number;
    preloadHitRate: number;
    navigationHistory: string[];
  } {
    const totalRoutes = this.routes.size;
    const preloadedCount = this.preloadedRoutes.size;
    
    return {
      totalRoutes,
      preloadedRoutes: preloadedCount,
      preloadHitRate: totalRoutes > 0 ? (preloadedCount / totalRoutes) * 100 : 0,
      navigationHistory: [...this.navigationHistory]
    };
  }

  /**
   * Clear all preloaded routes
   */
  clearPreloadedRoutes(): void {
    this.preloadedRoutes.clear();
    this.hoverTimeouts.forEach(timeout => clearTimeout(timeout));
    this.hoverTimeouts.clear();
  }
}

export const routePreloader = RoutePreloader.getInstance();