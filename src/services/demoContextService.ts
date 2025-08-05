/**
 * Demo Context Service
 * Dynamically fetches demo IDs from the backend instead of using hardcoded values
 *
 * This service ensures the frontend always uses the correct demo IDs that exist in the database,
 * preventing foreign key errors when database is rebuilt or deployed to new environments.
 */

import { apiCall } from '@/config/api';
import type { ApiError } from '../types/shared/api-types';

/**
 * External client data from backend API
 */
export interface ExternalClientData {
  id: string;
  name: string;
  status?: string;
  metadata?: Record<string, unknown>;
}

/**
 * External engagement data from backend API
 */
export interface ExternalEngagementData {
  id: string;
  name: string;
  client_id?: string;
  status?: string;
  metadata?: Record<string, unknown>;
}

export interface DemoContext {
  client: {
    id: string;
    name: string;
  };
  engagement: {
    id: string;
    name: string;
  };
  users: Array<{
    id: string;
    email: string;
    role: string;
  }>;
}

class DemoContextService {
  private static instance: DemoContextService;
  private demoContext: DemoContext | null = null;
  private initialized = false;
  private initializationPromise: Promise<DemoContext | null> | null = null;

  private constructor() {}

  static getInstance(): DemoContextService {
    if (!DemoContextService.instance) {
      DemoContextService.instance = new DemoContextService();
    }
    return DemoContextService.instance;
  }

  /**
   * Initialize demo context by fetching from backend
   * This should be called once when the app loads
   */
  async initialize(): Promise<DemoContext | null> {
    // If already initialized, return cached context
    if (this.initialized && this.demoContext) {
      return this.demoContext;
    }

    // If initialization is in progress, return the existing promise
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    // Start initialization
    this.initializationPromise = this.fetchDemoContext();

    try {
      this.demoContext = await this.initializationPromise;
      this.initialized = true;
      return this.demoContext;
    } finally {
      this.initializationPromise = null;
    }
  }

  /**
   * Fetch demo context from backend
   * The backend will return entities with 'def0-def0-def0' pattern in their UUIDs
   */
  private async fetchDemoContext(): Promise<DemoContext | null> {
    try {
      // Check if user is authenticated
      const authToken = localStorage.getItem('auth-token');
      if (!authToken) {
        console.log('⚠️ No authentication token, cannot fetch demo context'); // nosec - operational log, no token data exposed
        return null;
      }

      console.log('🔄 Fetching demo context from backend...');

      // Try to fetch user's available contexts
      const clientsResponse = await apiCall('/api/v1/context-establishment/clients', {}, false);

      if (clientsResponse && Array.isArray(clientsResponse)) {
        // Check if user has access to demo client
        const demoClient = (clientsResponse as ExternalClientData[]).find((client: ExternalClientData) =>
          client.id && client.id.includes('def0-def0-def0')
        );

        if (demoClient) {
          // User has access to demo data
          console.log('✅ User has access to demo client:', demoClient.name);

          // Fetch engagements for demo client
          const engagementsResponse = await apiCall(
            `/api/v1/context-establishment/engagements?client_id=${demoClient.id}`,
            {},
            false
          );

          if (engagementsResponse && Array.isArray(engagementsResponse)) {
            const demoEngagement = (engagementsResponse as ExternalEngagementData[]).find((eng: ExternalEngagementData) =>
              eng.id && eng.id.includes('def0-def0-def0')
            );

            if (demoEngagement) {
              console.log('✅ Demo context found:', {
                client: demoClient.name,
                engagement: demoEngagement.name
              });

              return {
                client: {
                  id: demoClient.id,
                  name: demoClient.name
                },
                engagement: {
                  id: demoEngagement.id,
                  name: demoEngagement.name
                },
                users: []
              };
            }
          }
        } else {
          console.log('ℹ️ User does not have access to demo data');
        }
      }

      return null;

    } catch (error) {
      const apiError = error as ApiError;
      if (apiError.status === 401) {
        console.log('⚠️ User not authenticated');
      } else if (apiError.status === 403) {
        console.log('⚠️ User not authorized for demo data');
      } else {
        console.error('❌ Failed to fetch demo context:', apiError.message || 'Unknown error');
      }
      return null;
    }
  }


  /**
   * Get cached demo context
   */
  getContext(): DemoContext | null {
    return this.demoContext;
  }

  /**
   * Get demo client ID
   */
  getClientId(): string | null {
    return this.demoContext?.client?.id || null;
  }

  /**
   * Get demo engagement ID
   */
  getEngagementId(): string | null {
    return this.demoContext?.engagement?.id || null;
  }

  /**
   * Check if a UUID is a demo UUID (contains 'def0-def0-def0')
   */
  isDemoId(id: string): boolean {
    return id && id.includes('def0-def0-def0');
  }

  /**
   * Clear cached context (useful for testing or when data changes)
   */
  clearCache(): void {
    this.demoContext = null;
    this.initialized = false;
    this.initializationPromise = null;
  }
}

// Export singleton instance
export const demoContextService = DemoContextService.getInstance();
