import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface FeedbackItem {
  id: string;
  type: 'Bug' | 'Feature' | 'Improvement' | 'Other';
  title: string;
  description: string;
  status: 'New' | 'In Review' | 'Accepted' | 'Rejected' | 'Implemented';
  created_at: string;
  updated_at: string;
  votes: number;
  user_has_voted: boolean;
  comments: Array<{
    id: string;
    text: string;
    created_at: string;
    user: {
      name: string;
      role: string;
    };
  }>;
}

export interface FeedbackStats {
  total_items: number;
  implemented_items: number;
  pending_review: number;
  top_categories: Array<{
    type: string;
    count: number;
  }>;
}

export interface FeedbackData {
  items: FeedbackItem[];
  stats: FeedbackStats;
}

export interface CreateFeedbackInput {
  type: FeedbackItem['type'];
  title: string;
  description: string;
}

export const useFeedback = () => {
  const { getContextHeaders } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<FeedbackData>({
    queryKey: ['feedback'],
    queryFn: async () => {
      const response = await apiCall('feedback', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: true
  });

  const createMutation = useMutation({
    mutationFn: async (input: CreateFeedbackInput) => {
      const response = await apiCall('feedback', {
        method: 'POST',
        headers: getContextHeaders(),
        body: JSON.stringify(input)
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] });
    }
  });

  const voteMutation = useMutation({
    mutationFn: async (feedbackId: string) => {
      const response = await apiCall(`/api/v1/feedback/${feedbackId}/vote`, {
        method: 'POST',
        headers: getContextHeaders()
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] });
    }
  });

  const commentMutation = useMutation({
    mutationFn: async ({ feedbackId, text }: { feedbackId: string; text: string }) => {
      const response = await apiCall(`/api/v1/feedback/${feedbackId}/comment`, {
        method: 'POST',
        headers: getContextHeaders(),
        body: JSON.stringify({ text })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] });
    }
  });

  return {
    ...query,
    createFeedback: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    voteFeedback: voteMutation.mutate,
    isVoting: voteMutation.isPending,
    voteError: voteMutation.error,
    commentFeedback: commentMutation.mutate,
    isCommenting: commentMutation.isPending,
    commentError: commentMutation.error
  };
}; 