import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface RearchitectProject {
  id: string;
  application: string;
  currentArch: string;
  targetArch: string;
  status: string;
  progress: number;
  complexity: 'High' | 'Medium' | 'Low';
  aiRecommendation: string;
}

export interface ArchitecturalPattern {
  name: string;
  description: string;
  benefits: string[];
  complexity: 'High' | 'Medium' | 'Low';
  projects: number;
}

export interface AIInsights {
  recommendations: string[];
  analysis: string;
  lastUpdated: string;
  confidence: number;
}

export interface RearchitectData {
  projects: RearchitectProject[];
  patterns: ArchitecturalPattern[];
  aiInsights: AIInsights;
}

export const useRearchitect = (): JSX.Element => {
  const { getContextHeaders } = useAuth();

  return useQuery<RearchitectData>({
    queryKey: ['rearchitect'],
    queryFn: async () => {
      const response = await apiCall('modernize/rearchitect', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
};
