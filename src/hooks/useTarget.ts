import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
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
  const { getContextHeaders } = useAuth();

  return useQuery<TargetData>({
    queryKey: ['target'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/plan/target', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
}; 