import { useQuery } from "@tanstack/react-query";
import { apiCallWithFallback } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

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
  const { user } = useAuth();
  // This logic for getting the client ID is a placeholder and may need to be adjusted
  const clientId = user?.client_accounts?.[0]?.id;

  return useQuery<Engagement[]>({
    queryKey: ["engagements", clientId],
    queryFn: async (): Promise<Engagement[]> => {
      try {
        if (!clientId) {
          // Try to get default client first
          const defaultClient = await apiCallWithFallback("/context/clients/default");
          if (!defaultClient) return [];
          
          // Then try to get default engagement
          const defaultEngagement = await apiCallWithFallback(`/context/clients/${defaultClient.id}/engagements/default`);
          return defaultEngagement ? [defaultEngagement] : [];
        }

        // If we have a client ID, try to get all engagements
        const engagements = await apiCallWithFallback(`/admin/clients/${clientId}/engagements`);
        if (engagements && engagements.length > 0) return engagements;

        // If no engagements found, try to get default engagement
        const defaultEngagement = await apiCallWithFallback(`/context/clients/${clientId}/engagements/default`);
        return defaultEngagement ? [defaultEngagement] : [];
      } catch (error) {
        console.error("Error fetching engagements:", error);
        return [];
      }
    },
    enabled: true, // Always enabled to handle default client/engagement
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};