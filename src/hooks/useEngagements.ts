import { useQuery } from "@tanstack/react-query";
import { apiCallWithFallback } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// Placeholder type, replace with actual Engagement type
export interface Engagement {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

const engagementsQueryKey = (clientId: string | null) => ["engagements", clientId];

export const useEngagements = () => {
  const { user, client, isDemoMode } = useAuth();
  const clientId = client?.id;

  return useQuery<Engagement[]>({
    queryKey: engagementsQueryKey(clientId),
    queryFn: async (): Promise<Engagement[]> => {
      // This function should not run in demo mode
      if (!clientId) return [];
      
      try {
        const response = await apiCallWithFallback(`/admin/engagements/?client_account_id=${clientId}`);
        const engagements = response?.items || response || [];
        // Filter by client_account_id to ensure we only get engagements for this client
        return engagements.filter((engagement: unknown) => engagement.client_account_id === clientId);
      } catch (error) {
        console.error("Error fetching engagements:", error);
        return [];
      }
    },
    enabled: !!clientId && !isDemoMode,
    staleTime: 5 * 60 * 1000,
  });
};