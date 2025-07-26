import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
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

export const useApplication = (applicationId: string): JSX.Element => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<Application>({
    queryKey: ['application', applicationId],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/discovery/applications/${applicationId}`);
        return response.data;
      } catch (error) {
        // Handle 404 and 403 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404 || errorObj.status === 403) {
          console.log('Discovery applications endpoint not available yet');
          return null;
        }
        throw error;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement && !!applicationId,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && typeof error === 'object' && 'status' in error &&
          (error.status === 404 || error.status === 403)) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateApplication = (): JSX.Element => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ applicationId, data }: { applicationId: string; data: Partial<Application> }) => {
      const response = await apiCall(`/api/v1/discovery/applications/${applicationId}`, {
        method: 'PUT',
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
