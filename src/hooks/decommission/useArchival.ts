import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface ArchivalMetric {
  label: string;
  value: string;
  color: string;
  icon: string;
}

export interface ArchivalSystem {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  dataSize: string;
  archiveLocation: string;
  lastBackup: string;
  retentionPolicy: string;
  dependencies: string[];
  archiveDate?: string;
  verificationStatus?: string;
  complianceStatus?: string;
}

export interface ArchivalTask {
  id: string;
  systemId: string;
  type: 'backup' | 'archive' | 'verify' | 'cleanup';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: string;
  endTime?: string;
  error?: string;
}

export interface ArchivalData {
  metrics: ArchivalMetric[];
  systems: ArchivalSystem[];
  tasks: ArchivalTask[];
}

export const useArchival = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<ArchivalData>({
    queryKey: ['archival'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('decommission/archival', { headers });
      return response.data;
    },
  });
};

export const useStartArchival = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (systemId: string) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/archival/${systemId}/start`, {
        method: 'POST',
        headers,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['archival'] });
    },
  });
};

export const useVerifyArchival = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (systemId: string) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/decommission/archival/${systemId}/verify`, {
        method: 'POST',
        headers,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['archival'] });
    },
  });
}; 