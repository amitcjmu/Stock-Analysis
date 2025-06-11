import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';

// This is a placeholder type. You should replace this with the actual Client type from your backend.
export interface Client {
  id: string;
  name: string;
}

const clientsQueryKey = () => ['clients'];

export const useClients = () => {
  return useQuery<Client[]>({
    queryKey: clientsQueryKey(),
    queryFn: async (): Promise<Client[]> => {
      // Replace with your actual API endpoint for listing clients
      return await apiCall('/api/v1/admin/clients');
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}; 