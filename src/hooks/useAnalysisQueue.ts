import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AnalysisQueueItem } from '@/types/assessment';
import { apiCall } from '@/lib/api';

interface CreateQueueRequest {
  name: string;
  applicationIds: string[];
}

export function useAnalysisQueue() {
  const queryClient = useQueryClient();

  const { data: queues = [], isLoading } = useQuery<AnalysisQueueItem[]>({
    queryKey: ['analysis-queues'],
    queryFn: () => apiCall('analysis/queues'),
  });

  const createQueue = async (request: CreateQueueRequest) => {
    const response = await apiCall('analysis/queues', { method: 'POST', body: JSON.stringify(request) });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
    return response.data;
  };

  const addToQueue = async (queueId: string, applicationId: string) => {
    await apiCall(`/api/v1/analysis/queues/${queueId}/items`, { 
      method: 'POST',
      body: JSON.stringify({ applicationId }) 
    });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const startQueue = async (id: string) => {
    await apiCall(`/api/v1/analysis/queues/${id}/start`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const pauseQueue = async (id: string) => {
    await apiCall(`/api/v1/analysis/queues/${id}/pause`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const cancelQueue = async (id: string) => {
    await apiCall(`/api/v1/analysis/queues/${id}/cancel`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const retryQueue = async (id: string) => {
    await apiCall(`/api/v1/analysis/queues/${id}/retry`, { method: 'POST' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const deleteQueue = async (queueId: string) => {
    await apiCall(`/api/v1/analysis/queues/${queueId}`, { method: 'DELETE' });
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const exportQueue = async (id: string, format: 'csv' | 'json' = 'csv') => {
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