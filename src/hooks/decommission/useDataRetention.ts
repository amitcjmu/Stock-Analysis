import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface RetentionMetric {
  label: string;
  value: string;
  color: string;
  icon: string;
}

export interface RetentionPolicy {
  id: string;
  name: string;
  description: string;
  retentionPeriod: string;
  complianceReqs: string[];
  dataTypes: string[];
  storageLocation: string;
  status: string;
  affectedSystems: number;
}

export interface ArchiveJob {
  id: string;
  systemName: string;
  dataSize: string;
  status: 'In Progress' | 'Queued' | 'Completed';
  progress: number;
  startDate: string;
  estimatedCompletion: string;
  priority: 'High' | 'Medium' | 'Low';
  policy: string;
}

export interface RetentionStep {
  step: number;
  title: string;
  description: string;
  status: 'completed' | 'in-progress' | 'pending';
}

export interface DataRetentionData {
  metrics: RetentionMetric[];
  policies: RetentionPolicy[];
  archiveJobs: ArchiveJob[];
  retentionSteps: RetentionStep[];
}

export const useDataRetention = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<DataRetentionData>({
    queryKey: ['data-retention'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('decommission/data-retention', { headers });
      return response.data;
    },
  });
};

export const useCreateArchiveJob = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<ArchiveJob>) => {
      const headers = getAuthHeaders();
      const response = await apiCall('decommission/archive-jobs', {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-retention'] });
    },
  });
};

export const useUpdateRetentionPolicy = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<RetentionPolicy> & { id: string }) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/retention-policies/${data.id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-retention'] });
    },
  });
}; 