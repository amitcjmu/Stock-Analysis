import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

export const useWavePlanning = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<WavePlanningData>({
    queryKey: ['wave-planning'],
    queryFn: async () => {
      try {
        const headers = getAuthHeaders();
        const response = await apiCall('ave-planning', { headers });
        return response;
      } catch (error: any) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        if (error.status === 404 || error.response?.status === 404) {
          console.log('Wave planning endpoint not available yet');
          return { waves: [], summary: { totalWaves: 0, totalApps: 0, totalGroups: 0 } };
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateWavePlanning = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (data: WavePlanningData) => {
      const headers = getAuthHeaders();
      return apiCall('ave-planning', {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wave-planning'] });
    },
  });
}; 