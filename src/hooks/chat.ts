import type { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import type { useState } from 'react'
import { useCallback } from 'react'
import { apiCall } from '@/config/api';

interface User {
  name: string;
  role: string;
}

interface Reaction {
  type: string;
  count: number;
  user_has_reacted: boolean;
}

interface Message {
  id: string;
  text: string;
  type: string;
  user: User;
  created_at: string;
  reactions: Reaction[];
  thread?: Message[];
}

interface ChatStats {
  total_messages: number;
  active_users: number;
  response_rate: number;
  average_response_time: number;
}

interface ChatData {
  messages: Message[];
  stats: ChatStats;
}

interface SendMessageParams {
  text: string;
}

interface ReplyParams {
  messageId: string;
  text: string;
}

interface ReactionParams {
  messageId: string;
  reaction: string;
}

export const useChat = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Fetch chat data only when we have a conversation ID
  const {
    data = { messages: [], stats: { total_messages: 0, active_users: 0, response_rate: 0, average_response_time: 0 } },
    isLoading,
    isError,
    refetch: refetchChat
  } = useQuery<ChatData, Error>({
    queryKey: ['globalChat', conversationId],
    queryFn: async () => {
      if (!conversationId) {
        return {
          messages: [],
          stats: {
            total_messages: 0,
            active_users: 0,
            response_rate: 0,
            average_response_time: 0
          }
        };
      }

      try {
        const response = await apiCall(`/api/v1/chat/conversation/${conversationId}`);
        return response;
      } catch (err) {
        if (err.response?.status === 404) {
          return {
            messages: [],
            stats: {
              total_messages: 0,
              active_users: 0,
              response_rate: 0,
              average_response_time: 0
            }
          };
        }
        throw err;
      }
    },
    enabled: !!conversationId, // Only run query when we have a conversation ID
    retry: false
  });

  // Send message mutation - handles both one-off and conversation messages
  const {
    mutate: sendMessage,
    isPending: isSending,
    error: sendError
  } = useMutation<Message, Error, string>({
    mutationFn: async (text) => {
      // If we don't have a conversation ID, use one-off chat endpoint
      if (!conversationId) {
        const response = await apiCall('chat', {
          method: 'POST',
          body: JSON.stringify({
            message: text,
            conversation_history: data.messages.map(msg => ({
              role: msg.type === 'user' ? 'user' : 'assistant',
              content: msg.text
            }))
          })
        });

        // If this is our second message, create a conversation
        if (data.messages.length > 0) {
          const newConversationId = `global-${Date.now()}`;
          setConversationId(newConversationId);
        }

        return response;
      }

      // Use conversation endpoint if we have a conversation ID
      const response = await apiCall(`/api/v1/chat/conversation/${conversationId}`, {
        method: 'POST',
        body: JSON.stringify({
          message: text,
          conversation_history: data.messages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.text
          }))
        })
      });
      return response;
    },
    onSuccess: () => {
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['globalChat', conversationId] });
      }
    },
    onError: (error) => {
      setError(error);
    }
  });

  // Reply to message mutation
  const {
    mutate: replyToMessage,
    isPending: isReplying,
    error: replyError
  } = useMutation<Message, Error, ReplyParams>({
    mutationFn: async ({ messageId, text }) => {
      if (!conversationId) {
        throw new Error('Cannot reply without an active conversation');
      }

      const response = await apiCall(`/api/v1/chat/conversation/${conversationId}`, {
        method: 'POST',
        body: JSON.stringify({
          message: text,
          conversation_history: data.messages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.text
          }))
        })
      });
      return response;
    },
    onSuccess: () => {
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['globalChat', conversationId] });
      }
    },
    onError: (error) => {
      setError(error);
    }
  });

  // React to message mutation
  const {
    mutate: reactToMessage,
    isPending: isReacting,
    error: reactError
  } = useMutation<void, Error, ReactionParams>({
    mutationFn: async ({ messageId, reaction }) => {
      if (!conversationId) {
        throw new Error('Cannot react without an active conversation');
      }

      await apiCall(`/api/v1/chat/conversation/${conversationId}/react`, {
        method: 'POST',
        body: JSON.stringify({ reaction })
      });
    },
    onSuccess: () => {
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['globalChat', conversationId] });
      }
    },
    onError: (error) => {
      setError(error);
    }
  });

  // Manual refresh function
  const refreshChat = useCallback(() => {
    if (conversationId) {
      refetchChat();
    }
  }, [conversationId, refetchChat]);

  return {
    data,
    isLoading,
    isError: isError && error?.response?.status !== 404,
    error,
    sendMessage,
    isSending,
    sendError,
    replyToMessage,
    isReplying,
    replyError,
    reactToMessage,
    isReacting,
    reactError,
    refreshChat,
    hasActiveConversation: !!conversationId
  };
}; 