import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

// Backend API response types
interface BackendPhase {
  id: string;
  phase_name: string;
  planned_start_date: string | null;
  planned_end_date: string | null;
  status: string;
  wave_number: number | null;
}

interface BackendRoadmapResponse {
  timeline_id?: string;
  timeline_name?: string;
  overall_start_date?: string | null;
  overall_end_date?: string | null;
  phases?: BackendPhase[];
  milestones?: unknown[];
  roadmap_status?: string;
}

// Frontend display types
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

// Transform backend response to frontend format
const transformRoadmapData = (backendData: BackendRoadmapResponse): RoadmapData => {
  // Handle empty state
  if (!backendData.phases || backendData.phases.length === 0) {
    return {
      waves: [],
      totalApps: 0,
      plannedApps: 0
    };
  }

  // Group phases by wave_number
  const waveMap = new Map<number, BackendPhase[]>();

  backendData.phases.forEach(phase => {
    const waveNum = phase.wave_number || 1; // Default to wave 1 if not specified
    if (!waveMap.has(waveNum)) {
      waveMap.set(waveNum, []);
    }
    waveMap.get(waveNum)!.push(phase);
  });

  // Transform to frontend format
  const waves: RoadmapWave[] = Array.from(waveMap.entries())
    .sort(([a], [b]) => a - b) // Sort by wave number
    .map(([waveNum, phases]) => ({
      wave: `Wave ${waveNum}`,
      phases: phases.map(p => ({
        name: p.phase_name,
        start: p.planned_start_date || 'TBD',
        end: p.planned_end_date || 'TBD',
        status: (p.status === 'completed' || p.status === 'in-progress' || p.status === 'planned'
          ? p.status
          : 'planned') as 'completed' | 'in-progress' | 'planned'
      }))
    }));

  return {
    waves,
    totalApps: 0, // TODO: Calculate from actual app assignments
    plannedApps: 0 // TODO: Calculate from actual app assignments
  };
};

export const useRoadmap = (): JSX.Element => {
  const { getAuthHeaders } = useAuth();

  return useQuery<RoadmapData>({
    queryKey: ['roadmap'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('plan/roadmap', { headers });
      return transformRoadmapData(response as BackendRoadmapResponse);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateRoadmap = (): unknown => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (data: RoadmapData) => {
      const headers = getAuthHeaders();
      return apiCall('plan/roadmap', {
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
