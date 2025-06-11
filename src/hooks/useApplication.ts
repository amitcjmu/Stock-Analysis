import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface Application {
  id: string;
  name: string;
  techStack: string;
  criticality: string;
  dept: string;
  treatment: string;
  group: string;
  complexity: string;
  scope: string;
  appStrategy: string;
  grTreatment: string;
  wave: string;
  function: string;
  type: string;
  piiData: boolean;
  businessCritical: boolean;
  appOwner: string;
  email: string;
}

export const useApplication = (applicationId: string) => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<Application>({
    queryKey: ['application', applicationId],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/discovery/applications/${applicationId}`, {
        headers: getAuthHeaders()
      });
      return response.data;
    },
    enabled: !!applicationId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateApplication = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ applicationId, data }: { applicationId: string; data: Partial<Application> }) => {
      const response = await apiCall(`/api/v1/discovery/applications/${applicationId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      return response.data;
    },
    onSuccess: (_, { applicationId }) => {
      // Invalidate the application query to trigger a refetch
      queryClient.invalidateQueries({ queryKey: ['application', applicationId] });
      queryClient.invalidateQueries({ queryKey: ['applications'] }); // Also invalidate the list if it exists
    }
  });
}; 