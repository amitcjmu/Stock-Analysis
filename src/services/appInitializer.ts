/**
 * App Initializer Service
 * Handles initialization tasks that should run once when the app loads
 *
 * This ensures critical data like demo context is loaded before any components
 * need it, preventing hardcoded ID issues.
 */

import type { DemoContext } from './demoContextService'
import { demoContextService } from './demoContextService'

export class AppInitializer {
  private static initialized = false;
  private static initializationPromise: Promise<void> | null = null;

  /**
   * Initialize the app
   * This should be called once in the main App component or before ReactDOM.render
   */
  static async initialize(): Promise<void> {
    // If already initialized, return immediately
    if (this.initialized) {
      return;
    }

    // If initialization is in progress, return the existing promise
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    // Start initialization
    this.initializationPromise = this.runInitialization();

    try {
      await this.initializationPromise;
      this.initialized = true;
    } finally {
      this.initializationPromise = null;
    }
  }

  /**
   * Run all initialization tasks
   */
  private static async runInitialization(): Promise<void> {
    try {
      // Task 1: Initialize demo context (only if user has access)
      const authToken = localStorage.getItem('auth-token');
      if (authToken) {
        try {
          const demoContext = await demoContextService.initialize();
          if (demoContext) {
            // Store demo context in sessionStorage for quick access
            sessionStorage.setItem('demo_client_id', demoContext.client.id);
            sessionStorage.setItem('demo_engagement_id', demoContext.engagement.id);
            sessionStorage.setItem('demo_context', JSON.stringify(demoContext));
          }
        } catch (error) {
          // Demo context not accessible - expected for non-demo users
        }
      }

      // Task 2: Check API health
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/health`);
        // API health check completed (no need to log success)
      } catch (error) {
        // API health check failed (silent - don't spam console)
      }

    } catch (error) {
      // App initialization failed (silent - don't spam console)
    }
  }

  /**
   * Get initialization status
   */
  static isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Reset initialization (useful for testing)
   */
  static reset(): void {
    this.initialized = false;
    this.initializationPromise = null;
    demoContextService.clearCache();
    sessionStorage.removeItem('demo_client_id');
    sessionStorage.removeItem('demo_engagement_id');
    sessionStorage.removeItem('demo_context');
  }
}

// Helper function to get demo IDs from session storage
export function getDemoClientId(): string | null {
  return sessionStorage.getItem('demo_client_id') || demoContextService.getClientId();
}

export function getDemoEngagementId(): string | null {
  return sessionStorage.getItem('demo_engagement_id') || demoContextService.getEngagementId();
}

export function getDemoContext(): DemoContext | null {
  const stored = sessionStorage.getItem('demo_context');
  if (stored) {
    try {
      return JSON.parse(stored) as DemoContext;
    } catch {
      // Ignore parse errors
    }
  }
  return demoContextService.getContext();
}
