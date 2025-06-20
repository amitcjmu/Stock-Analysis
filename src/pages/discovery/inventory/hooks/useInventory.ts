import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { InventoryResponse, InventoryFilters, BulkUpdateVariables } from '../types';

export const useInventoryData = (filters: InventoryFilters) => {
  return useQuery<InventoryResponse, Error>({
    queryKey: ['inventory', filters],
    queryFn: async () => {
      // Convert filters to query params, excluding 'all' values
      const params: Record<string, string> = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== 'all') {
          params[key] = String(value);
        }
      });
      
      // Make the API call with params
      return apiCall<InventoryResponse>('/assets/list/paginated', {
        params,
      });
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useBulkUpdateAssets = () => {
  const queryClient = useQueryClient();
  
  return useMutation<Response, Error, BulkUpdateVariables>({
    mutationFn: async ({ assetIds, updateData }) => {
      return apiCall<Response>('/assets/bulk-update-plan', {
        method: 'POST',
        data: {
          asset_ids: assetIds,
          ...updateData
        }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    }
  });
};
