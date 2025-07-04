/**
 * App Initializer Service
 * Handles initialization tasks that should run once when the app loads
 * 
 * This ensures critical data like demo context is loaded before any components
 * need it, preventing hardcoded ID issues.
 */

import { demoContextService } from './demoContextService';

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
    console.log('🚀 Starting app initialization...');
    
    try {
      // Task 1: Initialize demo context (only if user has access)
      console.log('📋 Task 1: Checking for demo context access...');
      
      // Check if user has a valid auth token first
      const authToken = localStorage.getItem('auth-token');
      if (!authToken) {
        console.log('⚠️ No auth token found, skipping demo context initialization');
      } else {
        try {
          const demoContext = await demoContextService.initialize();
          
          if (demoContext) {
            console.log('✅ Demo context loaded successfully');
            
            // Store demo context in sessionStorage for quick access
            sessionStorage.setItem('demo_client_id', demoContext.client.id);
            sessionStorage.setItem('demo_engagement_id', demoContext.engagement.id);
            sessionStorage.setItem('demo_context', JSON.stringify(demoContext));
          } else {
            console.log('ℹ️ No demo context available for this user');
          }
        } catch (error) {
          console.log('ℹ️ Demo context not accessible:', error);
          // This is expected for non-demo users
        }
      }
      
      // Task 2: Check API health
      console.log('📋 Task 2: Checking API health...');
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/health`);
        if (response.ok) {
          console.log('✅ API is healthy');
        } else {
          console.warn('⚠️ API health check returned:', response.status);
        }
      } catch (error) {
        console.warn('⚠️ API health check failed:', error);
      }
      
      // Task 3: Load feature flags (if needed in future)
      console.log('📋 Task 3: Loading feature flags...');
      // Placeholder for feature flags
      console.log('✅ Feature flags loaded (none configured)');
      
      console.log('🎉 App initialization completed successfully');
      
    } catch (error) {
      console.error('❌ App initialization failed:', error);
      // Don't throw - allow app to continue even if initialization partially fails
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

export function getDemoContext(): any {
  const stored = sessionStorage.getItem('demo_context');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      // Ignore parse errors
    }
  }
  return demoContextService.getContext();
}