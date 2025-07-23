import type { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface ComplianceMetric {
  label: string;
  value: string;
  color: string;
  icon: string;
}

export interface ComplianceRequirement {
  id: string;
  name: string;
  description: string;
  framework: string;
  status: 'compliant' | 'non_compliant' | 'in_progress' | 'not_applicable';
  lastChecked: string;
  nextCheck: string;
  evidence?: string[];
  notes?: string;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  description: string;
  requirements: string[];
  status: 'active' | 'inactive';
  lastUpdated: string;
}

export interface ComplianceAudit {
  id: string;
  requirementId: string;
  type: 'automated' | 'manual';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  findings?: string[];
  evidence?: string[];
}

export interface ComplianceData {
  metrics: ComplianceMetric[];
  requirements: ComplianceRequirement[];
  frameworks: ComplianceFramework[];
  audits: ComplianceAudit[];
}

export const useCompliance = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<ComplianceData>({
    queryKey: ['compliance'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('decommission/compliance', { headers });
      return response.data;
    },
  });
};

export const useStartAudit = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (requirementId: string) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/compliance/audit/${requirementId}`, {
        method: 'POST',
        headers,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance'] });
    },
  });
};

export const useUpdateRequirement = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<ComplianceRequirement> & { id: string }) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/compliance/requirements/${data.id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance'] });
    },
  });
}; 