import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface RoadmapPhase {
  name: string;
  start: string;
  end: string;
  status: 'completed' | 'in-progress' | 'planned';
}

export interface RoadmapWave {
  wave: string;
  phases: RoadmapPhase[];
}

export interface RoadmapData {
  waves: RoadmapWave[];
  totalApps: number;
  plannedApps: number;
}

export const useRoadmap = (): JSX.Element => {
  const { getAuthHeaders } = useAuth();

  return useQuery<RoadmapData>({
    queryKey: ['roadmap'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('assess/roadmap', { headers });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateRoadmap = (): any => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (data: RoadmapData) => {
      const headers = getAuthHeaders();
      return apiCall('assess/roadmap', {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmap'] });
    },
  });
};
