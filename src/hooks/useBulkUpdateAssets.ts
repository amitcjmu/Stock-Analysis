import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';

interface BulkUpdatePayload {
  assetIds: string[];
  updates: Record<string, unknown>;
}

export function useBulkUpdateAssets() {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ assetIds, updates }: BulkUpdatePayload) => {
      const response = await fetch('/api/v1/inventory/bulk-update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ assetIds, updates })
      });

      if (!response.ok) {
        throw new Error('Failed to update assets');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    }
  });
}
