import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface ChatMessage {
  id: string;
  text: string;
  type: 'user' | 'agent' | 'system';
  created_at: string;
  user: {
    id: string;
    name: string;
    role: string;
  };
  reactions: Array<{
    type: '👍' | '👎' | '❤️' | '🚀' | '🤔';
    count: number;
    user_has_reacted: boolean;
  }>;
  thread?: Array<{
    id: string;
    text: string;
    created_at: string;
    user: {
      id: string;
      name: string;
      role: string;
    };
  }>;
}

export interface ChatStats {
  total_messages: number;
  active_users: number;
  response_rate: number;
  average_response_time: number;
}

export interface ChatData {
  messages: ChatMessage[];
  stats: ChatStats;
}

export const useGlobalChat = () => {
  const { getContextHeaders } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<ChatData>({
    queryKey: ['global-chat'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/chat/global', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 5 * 1000, // 5 seconds
    refetchInterval: 5 * 1000, // Poll every 5 seconds
    refetchOnWindowFocus: true
  });

  const sendMessage = useMutation({
    mutationFn: async (text: string) => {
      const response = await apiCall('/api/v1/chat/global', {
        method: 'POST',
        headers: getContextHeaders(),
        body: JSON.stringify({ text })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['global-chat'] });
    }
  });

  const replyToMessage = useMutation({
    mutationFn: async ({ messageId, text }: { messageId: string; text: string }) => {
      const response = await apiCall(`/api/v1/chat/global/${messageId}/reply`, {
        method: 'POST',
        headers: getContextHeaders(),
        body: JSON.stringify({ text })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['global-chat'] });
    }
  });

  const reactToMessage = useMutation({
    mutationFn: async ({ messageId, reaction }: { messageId: string; reaction: ChatMessage['reactions'][0]['type'] }) => {
      const response = await apiCall(`/api/v1/chat/global/${messageId}/react`, {
        method: 'POST',
        headers: getContextHeaders(),
        body: JSON.stringify({ reaction })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['global-chat'] });
    }
  });

  return {
    ...query,
    sendMessage: sendMessage.mutate,
    isSending: sendMessage.isPending,
    sendError: sendMessage.error,
    replyToMessage: replyToMessage.mutate,
    isReplying: replyToMessage.isPending,
    replyError: replyToMessage.error,
    reactToMessage: reactToMessage.mutate,
    isReacting: reactToMessage.isPending,
    reactError: reactToMessage.error
  };
}; 