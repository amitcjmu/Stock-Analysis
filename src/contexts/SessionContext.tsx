import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Session as SessionServiceSession, sessionService } from '@/services/sessionService';
import { useToast } from '@/components/ui/use-toast';
import { useAppContext } from '@/hooks/useContext';
import { useAuth } from './AuthContext'; // Import useAuth to get engagementId

// Define our UI-specific session type that matches the service type but with name instead of session_display_name
interface UISession extends Omit<SessionServiceSession, 'session_display_name'> {
  name: string; // Alias for session_display_name
}

// SessionContext type
interface SessionContextType {
  currentSession: UISession | null;
  sessions: UISession[];
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isSettingDefault: boolean;
  error: Error | null;
  isDefaultSession: boolean;
  setCurrentSession: (session: UISession | null) => Promise<void>;
  createSession: (name: string, isDefault?: boolean) => Promise<UISession>;
  updateSession: (sessionId: string, updates: Partial<UISession>) => Promise<UISession>;
  deleteSession: (sessionId: string) => Promise<void>;
  setDefaultSession: (sessionId: string) => Promise<UISession>;
  refreshSessions: () => Promise<void>;
}

// Create the context with default values
const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Helper to convert service session to UI session
const toUISession = (session: SessionServiceSession): UISession => ({
  ...session,
  name: session.session_display_name,
});

// Helper to convert UI session to service session format
const toServiceSession = (uiSession: Partial<UISession>): Partial<SessionServiceSession> => {
  const { name, ...rest } = uiSession;
  return {
    ...rest,
    ...(name !== undefined && { session_display_name: name }),
  };
};

const sessionQueryKey = (engagementId: string | null) => ['sessions', engagementId];

/**
 * Hook to fetch the list of sessions for a given engagement.
 */
export const useSessions = () => {
  const { currentEngagementId } = useAuth();
  
  return useQuery<UISession[]>({
    queryKey: sessionQueryKey(currentEngagementId),
    queryFn: async (): Promise<UISession[]> => {
      if (!currentEngagementId) return [];
      const serviceSessions = await sessionService.listSessions(currentEngagementId);
      return serviceSessions.map(toUISession);
    },
    enabled: !!currentEngagementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to create a new session.
 */
export const useCreateSession = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { currentEngagementId, setCurrentSessionId } = useAuth();

  return useMutation({
    mutationFn: async ({ name, isDefault = false }: { name: string; isDefault?: boolean }) => {
      if (!currentEngagementId) throw new Error('No engagement ID available');
      const newSession = await sessionService.createSession(currentEngagementId, { session_display_name: name });
      if (isDefault) {
        await sessionService.setDefaultSession(currentEngagementId, newSession.id);
      }
      return toUISession(newSession);
    },
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: sessionQueryKey(currentEngagementId) });
      setCurrentSessionId(newSession.id); // Set as current session upon creation
      toast({
        title: 'Session created',
        description: `Successfully created session "${newSession.name}"`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error creating session',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Hook to update an existing session.
 */
export const useUpdateSession = () => {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const { currentEngagementId } = useAuth();

    return useMutation({
        mutationFn: async ({ sessionId, updates }: { sessionId: string; updates: Partial<UISession> }) => {
            if (!currentEngagementId) throw new Error('No engagement ID available');
            const updated = await sessionService.updateSession(currentEngagementId, sessionId, toServiceSession(updates));
            return toUISession(updated);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: sessionQueryKey(currentEngagementId) });
            toast({
                title: 'Session updated',
                description: `Successfully updated session.`,
            });
        },
        onError: (error: Error) => {
            toast({
                title: 'Error updating session',
                description: error.message,
                variant: 'destructive',
            });
        },
    });
};

/**
 * Hook to delete a session.
 */
export const useDeleteSession = () => {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const { currentEngagementId, currentSessionId, setCurrentSessionId } = useAuth();

    return useMutation({
        mutationFn: async (sessionId: string) => {
            if (!currentEngagementId) throw new Error('No engagement ID available');
            await sessionService.deleteSession(currentEngagementId, sessionId);
            return sessionId;
        },
        onSuccess: (deletedSessionId) => {
            if (currentSessionId === deletedSessionId) {
                setCurrentSessionId(null); // Clear current session if it was deleted
            }
            queryClient.invalidateQueries({ queryKey: sessionQueryKey(currentEngagementId) });
            toast({
                title: 'Session deleted',
                description: 'The session has been successfully deleted.',
            });
        },
        onError: (error: Error) => {
            toast({
                title: 'Error deleting session',
                description: error.message,
                variant: 'destructive',
            });
        },
    });
};

/**
 * Hook to set a session as the default for an engagement.
 */
export const useSetDefaultSession = () => {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const { currentEngagementId } = useAuth();

    return useMutation({
        mutationFn: async (sessionId: string) => {
            if (!currentEngagementId) throw new Error('No engagement ID available');
            const updated = await sessionService.setDefaultSession(currentEngagementId, sessionId);
            return toUISession(updated);
        },
        onSuccess: (updatedSession) => {
            queryClient.invalidateQueries({ queryKey: sessionQueryKey(currentEngagementId) });
            toast({
                title: 'Default session updated',
                description: `"${updatedSession.name}" is now the default session.`,
            });
        },
        onError: (error: Error) => {
            toast({
                title: 'Error setting default session',
                description: error.message,
                variant: 'destructive',
            });
        },
    });
};

/**
 * Hook to merge two sessions.
 */
export const useMergeSessions = () => {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const { currentEngagementId } = useAuth();

    return useMutation({
        mutationFn: async ({ sourceSessionId, targetSessionId, strategy }: { sourceSessionId: string; targetSessionId: string; strategy: 'preserve_target' | 'overwrite' | 'merge' }) => {
            if (!currentEngagementId) throw new Error('No engagement ID available');
            await sessionService.mergeSessions(currentEngagementId, sourceSessionId, targetSessionId, strategy);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: sessionQueryKey(currentEngagementId) });
            toast({
                title: 'Sessions Merged',
                description: 'The sessions have been merged successfully.',
            });
        },
        onError: (error: Error) => {
            toast({
                title: 'Error Merging Sessions',
                description: error.message,
                variant: 'destructive',
            });
        },
    });
};

// Provider component
export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { engagementId: urlEngagementId } = useParams<{ engagementId: string }>();
  const { context } = useAppContext();
  
  // State
  const [currentSession, setCurrentSessionState] = useState<UISession | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isSettingDefault, setIsSettingDefault] = useState(false);
  const [mutationError, setMutationError] = useState<Error | null>(null);
  
  // Get engagementId from URL or context
  const engagementId = urlEngagementId || context.engagement?.id;

  // Fetch sessions query
  const {
    data: sessions = [],
    isLoading: isSessionsLoading,
    error: sessionsError,
    refetch: refetchSessions,
  } = useQuery<UISession[]>({
    queryKey: ['sessions', engagementId],
    queryFn: async (): Promise<UISession[]> => {
      if (!engagementId) return [];
      const serviceSessions = await sessionService.listSessions(engagementId);
      return serviceSessions.map(toUISession);
    },
    enabled: !!engagementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Update app context when current session changes
  const updateAppContext = useCallback((session: UISession | null) => {
    // Implementation depends on your app context
    // This is a placeholder - replace with actual context update logic
    console.log('Updating app context with session:', session);
  }, []);

  // Set current session handler
  const handleSetCurrentSession = useCallback(async (session: UISession | null) => {
    setCurrentSessionState(session);
    updateAppContext(session);
  }, [updateAppContext]);

  // Handle refreshing sessions
  const handleRefreshSessions = useCallback(async () => {
    if (!engagementId) return;
    await queryClient.invalidateQueries({ queryKey: ['sessions', engagementId] });
  }, [engagementId, queryClient]);

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async ({ name, isDefault = false }: { name: string; isDefault?: boolean }) => {
      if (!engagementId) throw new Error('No engagement ID available');
      const newSession = await sessionService.createSession(engagementId, { session_display_name: name });
      if (isDefault) {
        await sessionService.setDefaultSession(engagementId, newSession.id);
      }
      return toUISession(newSession);
    },
    onSuccess: (newSession) => {
      toast({
        title: 'Session created',
        description: `Successfully created session "${newSession.name}"`,
      });
      handleRefreshSessions();
      handleSetCurrentSession(newSession);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error creating session',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Update session mutation
  const updateSessionMutation = useMutation({
    mutationFn: async ({ sessionId, updates }: { sessionId: string; updates: Partial<UISession> }) => {
      if (!engagementId) throw new Error('No engagement ID available');
      const updated = await sessionService.updateSession(engagementId, sessionId, toServiceSession(updates));
      return toUISession(updated);
    },
    onSuccess: (updatedSession) => {
      toast({
        title: 'Session updated',
        description: `Successfully updated session "${updatedSession.name}"`,
      });
      handleRefreshSessions();
      if (currentSession?.id === updatedSession.id) {
        handleSetCurrentSession(updatedSession);
      }
    },
    onError: (error: Error) => {
      toast({
        title: 'Error updating session',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Set default session mutation
  const setDefaultSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      if (!engagementId) throw new Error('No engagement ID available');
      const updated = await sessionService.setDefaultSession(engagementId, sessionId);
      return toUISession(updated);
    },
    onSuccess: (updatedSession) => {
      toast({
        title: 'Default session updated',
        description: `"${updatedSession.name}" is now the default session`,
      });
      handleRefreshSessions();
    },
    onError: (error: Error) => {
      toast({
        title: 'Error setting default session',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Delete session handler
  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (!engagementId) return;
    
    try {
      await sessionService.deleteSession(engagementId, sessionId);
      
      // If we're deleting the current session, clear it
      if (currentSession?.id === sessionId) {
        handleSetCurrentSession(null);
      }
      
      // Refresh the sessions list
      await handleRefreshSessions();
      
      toast({
        title: 'Session deleted',
        description: 'The session has been successfully deleted',
      });
      
      return true;
    } catch (error) {
      toast({
        title: 'Error deleting session',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        variant: 'destructive',
      });
      throw error;
    }
  }, [engagementId, currentSession, handleSetCurrentSession, handleRefreshSessions, toast]);

  // Set default session when sessions load or change
  useEffect(() => {
    if (sessions.length > 0) {
      const defaultSession = sessions.find(s => s.is_default) || sessions[0];
      if (defaultSession && (!currentSession || !sessions.some(s => s.id === currentSession.id))) {
        handleSetCurrentSession(defaultSession);
      }
    } else if (currentSession) {
      handleSetCurrentSession(null);
    }
  }, [sessions, currentSession, handleSetCurrentSession]);

  // Memoize the context value to prevent unnecessary re-renders
  const contextValue = useMemo<SessionContextType>(() => ({
    currentSession,
    sessions,
    isLoading: isSessionsLoading,
    isCreating: createSessionMutation.isPending,
    isUpdating: updateSessionMutation.isPending,
    isSettingDefault: setDefaultSessionMutation.isPending,
    error: sessionsError || mutationError,
    isDefaultSession: !!currentSession?.is_default,
    setCurrentSession: handleSetCurrentSession,
    createSession: (name: string, isDefault = false) => {
      return new Promise((resolve, reject) => {
        createSessionMutation.mutate(
          { name, isDefault },
          {
            onSuccess: (data) => resolve(data),
            onError: (error) => reject(error)
          }
        );
      });
    },
    updateSession: (sessionId: string, updates: Partial<UISession>) => {
      return new Promise((resolve, reject) => {
        updateSessionMutation.mutate(
          { sessionId, updates },
          {
            onSuccess: (data) => resolve(data),
            onError: (error) => reject(error)
          }
        );
      });
    },
    deleteSession: handleDeleteSession,
    setDefaultSession: (sessionId: string) => {
      return new Promise((resolve, reject) => {
        setDefaultSessionMutation.mutate(sessionId, {
          onSuccess: (data) => resolve(data),
          onError: (error) => reject(error)
        });
      });
    },
    refreshSessions: handleRefreshSessions,
  }), [
    currentSession,
    sessions,
    isSessionsLoading,
    createSessionMutation,
    updateSessionMutation,
    setDefaultSessionMutation,
    sessionsError,
    mutationError,
    handleSetCurrentSession,
    handleDeleteSession,
    handleRefreshSessions,
  ]);

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

// Custom hook to use the session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

// Export the context for testing or direct usage if needed
export { SessionContext };
