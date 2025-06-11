import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Session as SessionServiceSession, sessionService } from '@/services/sessionService';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from './AuthContext'; // Import useAuth to get engagementId
import { apiCall } from '@/lib/api';

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
  switchSession: (id: string) => Promise<void>;
  endSession: () => Promise<void>;
  getSessionId: () => string | null;
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
      queryClient.invalidateQueries({ queryKey: ['sessions', currentEngagementId] });
      setCurrentSessionId(newSession.id); // Set as current session upon creation
      toast({ title: 'Success', description: `Successfully created session "${newSession.name}"`, variant: 'default' });
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
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
      toast({ variant: 'default', title: 'Success', description: 'Successfully updated session' });
    },
    onError: (error: Error) => {
      toast({ variant: 'destructive', title: 'Error', description: error.message });
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
      toast({ variant: 'default', title: 'Success', description: 'Session deleted successfully' });
    },
    onError: (error: Error) => {
      toast({ variant: 'destructive', title: 'Error', description: error.message });
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
      toast({ variant: 'default', title: 'Success', description: `"${updatedSession.name}" is now the default session` });
    },
    onError: (error: Error) => {
      toast({ variant: 'destructive', title: 'Error', description: error.message });
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
      toast({ variant: 'default', title: 'Success', description: 'Sessions merged successfully' });
    },
    onError: (error: Error) => {
      toast({ variant: 'destructive', title: 'Error', description: error.message });
    },
  });
};

// Provider component
interface SessionProviderProps {
  children: React.ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const { currentEngagementId, currentSessionId, setCurrentSessionId } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const router = useRouter();

  // Query to fetch sessions
  const { 
    data: sessions = [], 
    isLoading: isSessionsLoading, 
    error: sessionsError, 
    refetch: refetchSessions 
  } = useSessions();

  // Find the current session
  const currentSession = useMemo(
    () => sessions.find(session => session.id === currentSessionId) || null,
    [sessions, currentSessionId]
  );

  // Check if current session is the default session
  const isDefaultSession = useMemo(
    () => sessions.some(session => session.is_default && session.id === currentSessionId),
    [sessions, currentSessionId]
  );

  // Create session mutation
  const createSessionMutation = useCreateSession();
  
  // Update session mutation
  const updateSessionMutation = useUpdateSession();
  
  // Delete session mutation
  const deleteSessionMutation = useDeleteSession();
  
  // Set default session mutation
  const setDefaultSessionMutation = useSetDefaultSession();
  
  // Merge sessions mutation
  const mergeSessionsMutation = useMergeSessions();

  // Set current session
  const setCurrentSession = useCallback(async (session: UISession | null) => {
    if (session) {
      setCurrentSessionId(session.id);
    } else {
      setCurrentSessionId(null);
    }
  }, [setCurrentSessionId]);

  // Refresh sessions
  const refreshSessions = useCallback(async () => {
    try {
      await refetchSessions();
      toast({ variant: 'default', title: 'Success', description: 'Sessions refreshed successfully' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh sessions';
      toast({ variant: 'destructive', title: 'Error', description: errorMessage });
    }
  }, [refetchSessions, toast]);

  // Create session wrapper
  const createSession = useCallback(async (name: string, isDefault = false): Promise<UISession> => {
    const newSession = await createSessionMutation.mutateAsync({ name, isDefault });
    return newSession;
  }, [createSessionMutation]);

  // Update session wrapper
  const updateSession = useCallback(async (sessionId: string, updates: Partial<UISession>): Promise<UISession> => {
    const updatedSession = await updateSessionMutation.mutateAsync({ sessionId, updates });
    return updatedSession;
  }, [updateSessionMutation]);

  // Delete session wrapper
  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    await deleteSessionMutation.mutateAsync(sessionId);
  }, [deleteSessionMutation]);

  // Set default session wrapper
  const setDefaultSession = useCallback(async (sessionId: string): Promise<UISession> => {
    const updatedSession = await setDefaultSessionMutation.mutateAsync(sessionId);
    return updatedSession;
  }, [setDefaultSessionMutation]);

  // Merge sessions wrapper
  const mergeSessions = useCallback(async (
    sourceSessionId: string, 
    targetSessionId: string, 
    strategy: 'preserve_target' | 'overwrite' | 'merge' = 'merge'
  ): Promise<void> => {
    await mergeSessionsMutation.mutateAsync({ sourceSessionId, targetSessionId, strategy });
  }, [mergeSessionsMutation]);

  // Context value
  const contextValue = useMemo((): SessionContextType => ({
    currentSession,
    sessions,
    isLoading: isSessionsLoading,
    isCreating: createSessionMutation.isPending,
    isUpdating: updateSessionMutation.isPending,
    isSettingDefault: setDefaultSessionMutation.isPending,
    error: sessionsError || null,
    isDefaultSession,
    setCurrentSession,
    createSession,
    updateSession,
    deleteSession,
    setDefaultSession,
    refreshSessions,
    switchSession: async (id: string) => {
      // Implementation of switchSession
    },
    endSession: async () => {
      // Implementation of endSession
    },
    getSessionId: () => {
      // Implementation of getSessionId
      return null;
    },
  }), [
    currentSession,
    sessions,
    isSessionsLoading,
    createSessionMutation.isPending,
    updateSessionMutation.isPending,
    setDefaultSessionMutation.isPending,
    sessionsError,
    isDefaultSession,
    setCurrentSession,
    createSession,
    updateSession,
    deleteSession,
    setDefaultSession,
    refreshSessions,
  ]);

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

// Export the context for testing or direct usage if needed
export { SessionContext };
