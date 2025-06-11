import { useQuery } from '@tanstack/react-query';
import { clientService, Client } from '@/services/clientService';

const clientQueryKey = () => ['clients'];

export const useClients = () => {
    return useQuery<Client[]>({
        queryKey: clientQueryKey(),
        queryFn: async (): Promise<Client[]> => {
            return await clientService.listClients();
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}; 