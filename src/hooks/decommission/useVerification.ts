import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface VerificationMetric {
  label: string;
  value: string;
  color: string;
  icon: string;
}

export interface VerificationCheck {
  id: string;
  name: string;
  description: string;
  type: 'data_integrity' | 'compliance' | 'security' | 'accessibility';
  status: 'pending' | 'in_progress' | 'passed' | 'failed';
  lastRun?: string;
  nextRun?: string;
  findings?: string[];
  recommendations?: string[];
}

export interface VerificationReport {
  id: string;
  checkId: string;
  timestamp: string;
  status: 'passed' | 'failed';
  details: string[];
  evidence: string[];
}

export interface VerificationData {
  metrics: VerificationMetric[];
  checks: VerificationCheck[];
  reports: VerificationReport[];
}

export const useVerification = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<VerificationData>({
    queryKey: ['verification'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('decommission/verification', { headers });
      return response.data;
    },
  });
};

export const useRunVerification = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (checkId: string) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/verification/run/${checkId}`, {
        method: 'POST',
        headers,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification'] });
    },
  });
};

export const useGenerateReport = () => {
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (checkId: string) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/verification/report/${checkId}`, {
        method: 'POST',
        headers,
      });
      return response.data;
    },
  });
}; 