import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
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
        
        // Use master flow service to get active flows
        const response = await masterFlowServiceExtended.getActiveFlows(
          client.id,
          engagement.id,
          'discovery'
        );
        
        console.log('✅ Raw discovery flows response:', response);
        
        // Transform to expected format
        const transformedFlows = response.map(flow => ({
          flow_id: flow.flowId,
          status: flow.status,
          current_phase: flow.currentPhase || '',
          created_at: flow.createdAt,
          updated_at: flow.updatedAt,
          // Map phase completion from metadata if available
          data_import_completed: flow.metadata?.phases?.data_import === true,
          attribute_mapping_completed: flow.metadata?.phases?.attribute_mapping === true,
          data_cleansing_completed: flow.metadata?.phases?.data_cleansing === true,
          inventory_completed: flow.metadata?.phases?.inventory === true,
          dependencies_completed: flow.metadata?.phases?.dependencies === true,
          tech_debt_completed: flow.metadata?.phases?.tech_debt === true,
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
    retry: (failureCount, error: any) => {
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
    
    const response = await masterFlowServiceExtended.getActiveFlows(
      clientId,
      engagementId,
      'discovery'
    );
    
    console.log('✅ getFlows utility - Raw response:', response);
    
    // Transform to legacy format for compatibility
    const transformedFlows = response.map(flow => ({
      flow_id: flow.flowId,
      status: flow.status,
      current_phase: flow.currentPhase || '',
      created_at: flow.createdAt,
      updated_at: flow.updatedAt
    }));
    
    console.log('✅ getFlows utility - Transformed flows:', transformedFlows);
    return transformedFlows;
  } catch (error) {
    console.error('❌ getFlows utility - Failed to fetch discovery flows:', error);
    return [];
  }
};