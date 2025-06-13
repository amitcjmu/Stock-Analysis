import { useQuery } from "@tanstack/react-query";
import { apiCall } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export interface Client {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  type: 'enterprise' | 'mid-market' | 'startup';
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export const useClients = () => {
  const { user, isDemoMode } = useAuth();

  return useQuery<Client[]>({
    queryKey: ["clients", user?.id],
    queryFn: async (): Promise<Client[]> => {
      try {
        // If user is admin, get all clients
        if (user?.role === "admin") {
          const clients = await apiCall("/admin/clients");
          if (clients && clients.length > 0) return clients;
        }

        // For non-admin users or if no clients found, get default client
        const defaultClient = await apiCall("/clients/default");
        return defaultClient ? [defaultClient] : [];
      } catch (error) {
        console.error("Error fetching clients:", error);
        throw error; // Let React Query handle the error
      }
    },
    enabled: !isDemoMode, // Only run the query if not in demo mode
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2, // Retry failed requests twice
    refetchOnWindowFocus: false // Don't refetch when window regains focus
  });
}; 