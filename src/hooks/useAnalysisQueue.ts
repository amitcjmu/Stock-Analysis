import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AnalysisQueueItem } from '@/types/assessment';
import { api } from '@/lib/api';

interface CreateQueueRequest {
  name: string;
  applicationIds: string[];
}

export function useAnalysisQueue() {
  const queryClient = useQueryClient();

  const { data: queues = [], isLoading } = useQuery<AnalysisQueueItem[]>({
    queryKey: ['analysis-queues'],
    queryFn: () => api.get('/api/v1/analysis/queues').then(res => res.data),
  });

  const createQueue = async (request: CreateQueueRequest) => {
    const response = await api.post('/api/v1/analysis/queues', request);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
    return response.data;
  };

  const startQueue = async (id: string) => {
    await api.post(`/api/v1/analysis/queues/${id}/start`);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const pauseQueue = async (id: string) => {
    await api.post(`/api/v1/analysis/queues/${id}/pause`);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const cancelQueue = async (id: string) => {
    await api.post(`/api/v1/analysis/queues/${id}/cancel`);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const retryQueue = async (id: string) => {
    await api.post(`/api/v1/analysis/queues/${id}/retry`);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const deleteQueue = async (id: string) => {
    await api.delete(`/api/v1/analysis/queues/${id}`);
    await queryClient.invalidateQueries({ queryKey: ['analysis-queues'] });
  };

  const exportResults = async (id: string, format: 'csv' | 'pdf' | 'json') => {
    const response = await api.get(`/api/v1/analysis/queues/${id}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
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
    exportResults
  };
} 