import { useQuery } from '@tanstack/react-query';
import { useAuth } from './AuthContext';
import { engagementService, Engagement } from '@/services/engagementService';

const engagementQueryKey = (clientId: string | null) => ['engagements', clientId];

export const useEngagements = () => {
    const { user } = useAuth(); // Assuming client is tied to user or another context
    // This is a simplification. In a real app, you might get the client ID
    // from a different context or user profile.
    const clientId = user?.client_accounts?.[0]; // Placeholder for client ID

    return useQuery<Engagement[]>({
        queryKey: engagementQueryKey(clientId),
        queryFn: async (): Promise<Engagement[]> => {
            if (!clientId) return [];
            return await engagementService.listEngagements(clientId);
        },
        enabled: !!clientId,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}; 