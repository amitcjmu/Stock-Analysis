/**
 * Demo Context Service
 * Dynamically fetches demo IDs from the backend instead of using hardcoded values
 * 
 * This service ensures the frontend always uses the correct demo IDs that exist in the database,
 * preventing foreign key errors when database is rebuilt or deployed to new environments.
 */

import { apiCall } from '@/config/api';

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
      console.log('🔄 Fetching demo context from backend...');
      
      // Fetch demo context from a new endpoint
      const response = await apiCall('/context/demo', {}, false);
      
      if (response && response.client && response.engagement) {
        console.log('✅ Demo context fetched successfully:', {
          client: response.client.name,
          clientId: response.client.id,
          engagement: response.engagement.name,
          engagementId: response.engagement.id
        });
        
        return {
          client: response.client,
          engagement: response.engagement,
          users: response.users || []
        };
      }
      
      // Fallback: Try to find demo data manually
      console.log('⚠️ Demo context endpoint not available, trying fallback method...');
      return await this.fetchDemoContextFallback();
      
    } catch (error) {
      console.error('❌ Failed to fetch demo context:', error);
      
      // Try fallback method
      try {
        return await this.fetchDemoContextFallback();
      } catch (fallbackError) {
        console.error('❌ Fallback method also failed:', fallbackError);
        return null;
      }
    }
  }

  /**
   * Fallback method to find demo data by querying clients and engagements
   */
  private async fetchDemoContextFallback(): Promise<DemoContext | null> {
    try {
      // Fetch all clients and find the demo one (contains 'def0-def0-def0' in UUID)
      const clientsResponse = await apiCall('/admin/clients', {}, false);
      
      if (clientsResponse && Array.isArray(clientsResponse)) {
        // Find demo client (UUID contains 'def0-def0-def0')
        const demoClient = clientsResponse.find((client: any) => 
          client.id && client.id.includes('def0-def0-def0')
        );
        
        if (demoClient) {
          // Fetch engagements for this client
          const engagementsResponse = await apiCall(
            `/admin/engagements?client_account_id=${demoClient.id}`,
            {},
            false
          );
          
          if (engagementsResponse && Array.isArray(engagementsResponse)) {
            // Find demo engagement
            const demoEngagement = engagementsResponse.find((eng: any) =>
              eng.id && eng.id.includes('def0-def0-def0')
            );
            
            if (demoEngagement) {
              console.log('✅ Demo context found via fallback:', {
                client: demoClient.name,
                clientId: demoClient.id,
                engagement: demoEngagement.name,
                engagementId: demoEngagement.id
              });
              
              return {
                client: {
                  id: demoClient.id,
                  name: demoClient.name || 'Demo Client'
                },
                engagement: {
                  id: demoEngagement.id,
                  name: demoEngagement.name || 'Demo Engagement'
                },
                users: []
              };
            }
          }
        }
      }
      
      console.warn('⚠️ No demo data found in database');
      return null;
      
    } catch (error) {
      console.error('❌ Fallback method failed:', error);
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