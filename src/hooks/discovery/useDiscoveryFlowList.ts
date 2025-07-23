import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';

export interface DiscoveryFlow {
  flow_id: string;
  status: string;
  current_phase: string;
  next_phase?: string;
  phases?: Record<string, boolean>;
  data_import_completed?: boolean;
  attribute_mapping_completed?: boolean;
  data_cleansing_completed?: boolean;
  inventory_completed?: boolean;
  dependencies_completed?: boolean;
  tech_debt_completed?: boolean;
  created_at: string;
  updated_at: string;
}

export const useDiscoveryFlowList = () => {
  const { client, engagement } = useAuth();
  
  return useQuery<DiscoveryFlow[]>({
    queryKey: ['discovery-flows', client?.id, engagement?.id],
    queryFn: async () => {
      try {
        // Context validation - should not reach here due to enabled flag, but defensive programming
        if (!client?.id || !engagement?.id) {
          console.warn('⚠️ Missing client or engagement context for discovery flows:', { client: client?.id, engagement: engagement?.id });
          return []; // Return empty array instead of throwing to prevent infinite retries
        }
        
        console.log('🔍 Fetching discovery flows for:', { clientId: client.id, engagementId: engagement.id });
        
        // Use the same endpoint as dashboard for consistency
        const response = await apiCall('/api/v1/discovery/flows/active', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-Client-Account-ID': client.id,
            'X-Engagement-ID': engagement.id
          }
        });
        
        console.log('✅ Raw discovery flows response:', response);
        
        // Handle both array response and object with flows array (same as dashboard)
        let flowsToProcess = [];
        
        if (Array.isArray(response)) {
          // Direct array response from /api/v1/discovery/flows/active
          flowsToProcess = response;
        } else if (response.flows && Array.isArray(response.flows)) {
          // Object with flows array
          flowsToProcess = response.flows;
        } else if (response.flow_details && Array.isArray(response.flow_details)) {
          // Legacy structure
          flowsToProcess = response.flow_details;
        }
        
        console.log(`✅ Processing ${flowsToProcess.length} flows from discovery API...`);
        
        // Transform to expected format (matching the dashboard flow structure)
        const transformedFlows = flowsToProcess.map(flow => ({
          id: flow.flow_id, // Add id field for compatibility
          flow_id: flow.flow_id,
          status: flow.status,
          current_phase: flow.current_phase || '',
          next_phase: flow.next_phase || flow.current_phase || '',
          created_at: flow.created_at,
          updated_at: flow.updated_at,
          // Use the existing phase completion flags from the flow
          phases: {},
          data_import_completed: flow.data_import_completed === true,
          attribute_mapping_completed: flow.attribute_mapping_completed === true,
          data_cleansing_completed: flow.data_cleansing_completed === true,
          inventory_completed: flow.inventory_completed === true,
          dependencies_completed: flow.dependencies_completed === true,
          tech_debt_completed: flow.tech_debt_completed === true,
        }));
        
        console.log('✅ Transformed discovery flows:', transformedFlows);
        return transformedFlows;
      } catch (error) {
        console.error('❌ Failed to fetch discovery flows:', error);
        return [];
      }
    },
    enabled: !!client?.id && !!engagement?.id, // Only enable when we have context to prevent errors
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes to reduce API calls (increased from 2)
    cacheTime: 15 * 60 * 1000, // Keep in cache for 15 minutes (increased from 10)
    refetchInterval: false, // No auto-refresh
    refetchOnMount: false, // Don't refetch on mount if data is stale but within cache time
    refetchOnWindowFocus: false, // Don't refetch on window focus to reduce calls
    retry: (failureCount, error: unknown) => {
      // Prevent infinite retries - max 2 attempts total
      if (failureCount >= 2) {
        console.log(`❌ Max retries reached for discovery flows (${failureCount}), stopping`);
        return false;
      }
      
      // Only retry for specific conditions
      if (error?.message === 'Missing client or engagement context') {
        console.log(`🔄 Retrying discovery flows fetch (attempt ${failureCount + 1}) - waiting for context...`);
        return true;
      }
      
      // Retry 429 rate limit errors with exponential backoff
      if (error?.status === 429) {
        console.log(`🔄 Rate limited, retrying discovery flows fetch (attempt ${failureCount + 1})...`);
        return true;
      }
      
      // Don't retry other errors
      console.log(`❌ Not retrying discovery flows fetch - error: ${error?.message || error}`);
      return false;
    },
    retryDelay: (attemptIndex) => {
      // Exponential backoff: 3s, 6s, 12s
      const delay = Math.min(3000 * Math.pow(2, attemptIndex), 12000);
      console.log(`⏱️ Retrying discovery flows in ${delay}ms`);
      return delay;
    }
  });
};

// Re-export for backward compatibility
export { useDiscoveryFlowList as useDiscoveryFlowListV2 };

// Utility function to get flows (used by auto-detection)
export const getFlows = async (clientId?: string, engagementId?: string) => {
  try {
    // Require auth context to be passed in
    if (!clientId || !engagementId) {
      console.warn('getFlows utility requires client and engagement context');
      return [];
    }
    
    console.log('🔍 getFlows utility - Fetching discovery flows for:', { clientId, engagementId });
    
    // Use the same endpoint as main hook for consistency
    const response = await apiCall('/api/v1/discovery/flows/active', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Account-ID': clientId,
        'X-Engagement-ID': engagementId
      }
    });
    
    console.log('✅ getFlows utility - Raw response:', response);
    
    // Handle response format (same as main hook)
    let flowsToProcess = [];
    if (Array.isArray(response)) {
      flowsToProcess = response;
    } else if (response.flows && Array.isArray(response.flows)) {
      flowsToProcess = response.flows;
    } else if (response.flow_details && Array.isArray(response.flow_details)) {
      flowsToProcess = response.flow_details;
    }
    
    // Transform to legacy format for compatibility
    const transformedFlows = flowsToProcess.map(flow => ({
      flow_id: flow.flow_id,
      status: flow.status,
      current_phase: flow.current_phase || '',
      created_at: flow.created_at,
      updated_at: flow.updated_at
    }));
    
    console.log('✅ getFlows utility - Transformed flows:', transformedFlows);
    return transformedFlows;
  } catch (error) {
    console.error('❌ getFlows utility - Failed to fetch discovery flows:', error);
    return [];
  }
};