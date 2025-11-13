import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Hook for fetching Replace strategy data (COTS/SaaS replacement or application rewrite)
 *
 * Note: This hook is named useRewrite for backward compatibility but handles the
 * consolidated "replace" strategy which includes both COTS/SaaS replacement and
 * custom application rewrites.
 */

export interface RewriteProject {
  id: string;
  name: string;
  status: 'Planning' | 'In Progress' | 'Completed' | 'On Hold';
  progress: number;
  technology: {
    current: string;
    target: string;
  };
  team: {
    size: number;
    skills: string[];
  };
  timeline: {
    start: string;
    estimated_completion: string;
  };
  metrics: {
    code_coverage: number;
    test_coverage: number;
    performance_improvement: number;
  };
  risks: Array<{
    type: string;
    severity: 'High' | 'Medium' | 'Low';
    mitigation: string;
  }>;
}

export interface RewriteMetrics {
  total_projects: number;
  completed_projects: number;
  in_progress: number;
  average_completion: number;
  overall_success_rate: number;
}

export interface RewriteData {
  projects: RewriteProject[];
  metrics: RewriteMetrics;
  ai_insights: {
    recommendations: string[];
    last_updated: string;
    key_findings: string[];
  };
}

export const useRewrite = (filter?: string): JSX.Element => {
  const { getContextHeaders } = useAuth();

  return useQuery<RewriteData>({
    queryKey: ['replace', filter], // Updated to 'replace' for consistency
    queryFn: async () => {
      // API endpoint will be updated to support both 'replace' and 'rewrite' for backward compatibility
      const response = await apiCall('modernize/replace', {
        method: 'GET',
        headers: {
          ...getContextHeaders(),
          ...(filter && { 'x-filter': filter })
        }
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
};
