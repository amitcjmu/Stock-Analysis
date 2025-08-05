import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import type { AnalysisQueueItem } from '@/types/assessment';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface CreateQueueRequest {
  name: string;
  applicationIds: string[];
}

export function useAnalysisQueue() {
  const queryClient = useQueryClient();
  const { isAuthenticated, client, engagement } = useAuth();

  const { data: queues = [], isLoading } = useQuery<AnalysisQueueItem[]>({
    queryKey: ['analysis-queues'],
    queryFn: async () => {
      return await apiCall('/api/v1/analysis/queues');
    },
    enabled: isAuthenticated && !!client && !!engagement,
    retry: 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const createQueue = async (request: CreateQueueRequest): Promise<AnalysisQueueItem> => {
    const response = await apiCall('/api/v1/analysis/queues', { method: 'POST', body: JSON.stringify(request) });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
    return response.data;
  };

  const addToQueue = async (queueId: string, applicationId: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${queueId}/items`, {
      method: 'POST',
      body: JSON.stringify({ applicationId })
    });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const startQueue = async (id: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${id}/start`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const pauseQueue = async (id: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${id}/pause`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const cancelQueue = async (id: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${id}/cancel`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const retryQueue = async (id: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${id}/retry`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const deleteQueue = async (queueId: string): Promise<void> => {
    await apiCall(`/api/v1/analysis/queues/${queueId}`, { method: 'DELETE' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const exportQueue = async (id: string, format: 'csv' | 'json' = 'csv'): Promise<unknown> => {
    const response = await apiCall(`/api/v1/analysis/queues/${id}/export?format=${format}`, {
      method: 'GET',
      headers: {
        'Accept': format === 'csv' ? 'text/csv' : 'application/json'
      }
    });
    return response;
  };

  return {
    queues,
    isLoading,
    createQueue,
    startQueue,
    pauseQueue,
    cancelQueue,
    retryQueue,
    deleteQueue,
    exportResults: exportQueue
  };
}
