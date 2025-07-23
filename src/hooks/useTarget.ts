import type { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface TargetEnvironment {
  id: string;
  name: string;
  type: 'AWS' | 'Azure' | 'GCP' | 'Private Cloud' | 'Hybrid';
  status: 'Planning' | 'In Progress' | 'Ready' | 'Active';
  readiness: number;
  components: Array<{
    name: string;
    status: 'Not Started' | 'In Progress' | 'Complete';
    dependencies: string[];
  }>;
  compliance: Array<{
    framework: string;
    status: 'Compliant' | 'In Progress' | 'Non-Compliant';
    gaps: string[];
  }>;
  costs: {
    estimated_monthly: number;
    actual_monthly?: number;
    savings_potential: number;
  };
}

export interface TargetMetrics {
  environments_count: number;
  average_readiness: number;
  compliance_rate: number;
  total_monthly_cost: number;
}

export interface TargetData {
  environments: TargetEnvironment[];
  metrics: TargetMetrics;
  recommendations: Array<{
    category: string;
    description: string;
    priority: 'High' | 'Medium' | 'Low';
  }>;
}

export const useTarget = () => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<TargetData>({
    queryKey: ['target'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/plan/target');
        return response;
      } catch (error: unknown) {
        // Handle errors gracefully - return mock data for development
        if (error.status === 404 || error.status === 403) {
          console.log('Target endpoint not available, returning mock data');
          return {
            environments: [],
            metrics: {
              environments_count: 0,
              average_readiness: 0,
              compliance_rate: 0,
              total_monthly_cost: 0
            },
            recommendations: []
          };
        }
        throw error;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2;
    }
  });
}; 