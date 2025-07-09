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
        // Ensure we have proper client and engagement context
        if (!client?.id || !engagement?.id) {
          console.warn('Missing client or engagement context for discovery flows');
          return [];
        }
        
        // Use master flow service to get active flows
        const response = await masterFlowServiceExtended.getActiveFlows(
          client.id,
          engagement.id,
          'discovery'
        );
        
        // Transform to expected format
        return response.map(flow => ({
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
      } catch (error) {
        console.warn('Failed to fetch discovery flows, returning empty list:', error);
        return [];
      }
    },
    enabled: !!client?.id && !!engagement?.id,
    staleTime: 30000, // 30 seconds
    refetchInterval: false // No auto-refresh
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
    
    const response = await masterFlowServiceExtended.getActiveFlows(
      clientId,
      engagementId,
      'discovery'
    );
    
    // Transform to legacy format for compatibility
    return response.map(flow => ({
      flow_id: flow.flowId,
      status: flow.status,
      current_phase: flow.currentPhase || '',
      created_at: flow.createdAt,
      updated_at: flow.updatedAt
    }));
  } catch (error) {
    console.warn('Failed to fetch discovery flows:', error);
    return [];
  }
};