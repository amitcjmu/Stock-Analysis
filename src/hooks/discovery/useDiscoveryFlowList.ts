import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

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
        // Use the active flows endpoint which is available
        const response = await apiCall('/api/v1/discovery/flows/active');
        // Handle both array response and object with flows array
        return Array.isArray(response) ? response : (response.flows || []);
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
export const getFlows = async () => {
  try {
    const response = await apiCall('/api/v1/discovery/flows/active');
    return Array.isArray(response) ? response : (response.flows || []);
  } catch (error) {
    console.warn('Failed to fetch discovery flows:', error);
    return [];
  }
};