import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

// Placeholder type, replace with actual Engagement type
export interface Engagement {
  id: string;
  name: string;
  client_id: string;
}

const engagementsQueryKey = (clientId: string | null) => ['engagements', clientId];

export const useEngagements = () => {
  const { user } = useAuth();
  // This logic for getting the client ID is a placeholder and may need to be adjusted
  const clientId = user?.client_accounts?.[0]?.id;

  return useQuery<Engagement[]>({
    queryKey: engagementsQueryKey(clientId),
    queryFn: async (): Promise<Engagement[]> => {
      if (!clientId) return [];
      // Replace with your actual API endpoint for listing engagements
      return await apiCall(`/api/v1/admin/clients/${clientId}/engagements`);
    },
    enabled: !!clientId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}; 