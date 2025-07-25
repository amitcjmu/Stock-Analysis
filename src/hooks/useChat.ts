import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useCallback } from 'react'
import type { apiCall } from '@/config/api';

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

// Mock data for development
const mockChatData: ChatData = {
  messages: [
    {
      id: '1',
      text: 'Hello! How can I help you today?',
      type: 'agent',
      user: { name: 'AI Assistant', role: 'agent' },
      created_at: new Date().toISOString(),
      reactions: [
        { type: '👍', count: 1, user_has_reacted: false },
        { type: '❤️', count: 0, user_has_reacted: false }
      ]
    }
  ],
  stats: {
    total_messages: 1,
    active_users: 1,
    response_rate: 100,
    average_response_time: 1
  }
};

export const useChat = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // For development, return mock data
  const {
    data = mockChatData,
    isLoading,
    isError,
    refetch: refetchChat
  } = useQuery<ChatData, Error>({
    queryKey: ['globalChat', conversationId],
    queryFn: async () => {
      // For development, return mock data
      return mockChatData;
    },
    enabled: true, // Always enabled for development
    retry: false
  });

  // Send message mutation - handles both one-off and conversation messages
  const {
    mutate: sendMessage,
    isPending: isSending,
    error: sendError
  } = useMutation<Message, Error, string>({
    mutationFn: async (text) => {
      // For development, simulate a response
      return {
        id: Date.now().toString(),
        text: `You said: ${text}. This is a mock response.`,
        type: 'agent',
        user: { name: 'AI Assistant', role: 'agent' },
        created_at: new Date().toISOString(),
        reactions: [
          { type: '👍', count: 0, user_has_reacted: false },
          { type: '❤️', count: 0, user_has_reacted: false }
        ]
      };
    },
    onSuccess: (newMessage) => {
      // Update mock data
      mockChatData.messages.push({
        id: Date.now().toString(),
        text: newMessage.text,
        type: 'agent',
        user: { name: 'AI Assistant', role: 'agent' },
        created_at: new Date().toISOString(),
        reactions: [
          { type: '👍', count: 0, user_has_reacted: false },
          { type: '❤️', count: 0, user_has_reacted: false }
        ]
      });
      queryClient.setQueryData(['globalChat', conversationId], mockChatData);
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
      // For development, simulate a reply
      return {
        id: Date.now().toString(),
        text: `Reply to ${messageId}: ${text}`,
        type: 'agent',
        user: { name: 'AI Assistant', role: 'agent' },
        created_at: new Date().toISOString(),
        reactions: []
      };
    },
    onSuccess: (newMessage) => {
      // Update mock data
      const parentMessage = mockChatData.messages.find(m => m.id === newMessage.id);
      if (parentMessage) {
        parentMessage.thread = parentMessage.thread || [];
        parentMessage.thread.push(newMessage);
        queryClient.setQueryData(['globalChat', conversationId], mockChatData);
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
      // For development, simulate reaction
      const message = mockChatData.messages.find(m => m.id === messageId);
      if (message) {
        const existingReaction = message.reactions.find(r => r.type === reaction);
        if (existingReaction) {
          existingReaction.count += 1;
          existingReaction.user_has_reacted = true;
        }
      }
    },
    onSuccess: () => {
      queryClient.setQueryData(['globalChat', conversationId], mockChatData);
    },
    onError: (error) => {
      setError(error);
    }
  });

  // Manual refresh function
  const refreshChat = useCallback(() => {
    queryClient.setQueryData(['globalChat', conversationId], mockChatData);
  }, [conversationId, queryClient]);

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
    hasActiveConversation: true // Always true for development
  };
};
