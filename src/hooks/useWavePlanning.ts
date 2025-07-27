import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface WaveGroup {
  id: string;
  name: string;
}

export interface Wave {
  wave: string;
  startDate: string;
  targetDate: string;
  groups: string[];
  apps: number;
  status: 'Planning' | 'Scheduled' | 'Draft';
}

export interface WaveSummary {
  totalWaves: number;
  totalApps: number;
  totalGroups: number;
}

export interface WavePlanningData {
  waves: Wave[];
  summary: WaveSummary;
}

export const useWavePlanning = (): JSX.Element => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<WavePlanningData>({
    queryKey: ['wave-planning'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/wave-planning');
        return response;
      } catch (error: unknown) {
        // Handle 404 and 403 errors gracefully - endpoint may not exist yet
        if (error.status === 404 || error.response?.status === 404 || error.status === 403) {
          console.log('Wave planning endpoint not available yet');
          return { waves: [], summary: { totalWaves: 0, totalApps: 0, totalGroups: 0 } };
        }
        throw error;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateWavePlanning = (): unknown => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WavePlanningData) => {
      return apiCall('/api/v1/wave-planning', {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wave-planning'] });
    },
  });
};
