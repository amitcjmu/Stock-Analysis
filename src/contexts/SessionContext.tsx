import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Session as SessionServiceSession, sessionService, CreateSessionRequest } from '@/services/sessionService';
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
  setDemoSession: (session: UISession) => void;
}

// Create the context with default values
export const SessionContext = createContext<SessionContextType | undefined>(undefined);

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
    mutationFn: async (data: { name: string; isDefault?: boolean }) => {
      if (!currentEngagementId) throw new Error('No engagement ID available');
      const { user } = useAuth();
      if (!user) throw new Error('No user available');
      
      // Get client_account_id from the first client account association
      const clientAccountId = user.client_accounts?.[0]?.id;
      if (!clientAccountId) throw new Error('No client account available');
      
      const sessionData: CreateSessionRequest = {
        session_name: data.name.toLowerCase().replace(/\s+/g, '_'),
        session_display_name: data.name,
        engagement_id: currentEngagementId,
        client_account_id: clientAccountId,
        is_default: data.isDefault || false,
        session_type: 'analysis',
        status: 'active',
        auto_created: false,
        created_by: user.id,
      };
      
      const newSession = await sessionService.createSession(sessionData);
      return toUISession(newSession);
    },
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['sessions', currentEngagementId] });
      setCurrentSessionId(newSession.id);
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
    mutationFn: async (data: { sessionId: string; updates: Partial<UISession> }) => {
      const updated = await sessionService.updateSession(data.sessionId, toServiceSession(data.updates));
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
      await sessionService.deleteSession(sessionId);
      return sessionId;
    },
    onSuccess: (deletedSessionId) => {
      if (currentSessionId === deletedSessionId) {
        setCurrentSessionId(null);
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
      const updated = await sessionService.setDefaultSession(sessionId);
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

// Default export for the provider
const SessionProvider = ({ children }: SessionProviderProps) => {
  const { currentEngagementId, currentSessionId, setCurrentSessionId, user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Add these state hooks for demo mode
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

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
    if (!currentEngagementId) throw new Error('No engagement ID available');
    const { user } = useAuth();
    if (!user) throw new Error('No user available');
    
    // Get client_account_id from the first client account association
    const clientAccountId = user.client_accounts?.[0]?.id;
    if (!clientAccountId) throw new Error('No client account available');
    
    const sessionData: CreateSessionRequest = {
      session_name: name.toLowerCase().replace(/\s+/g, '_'),
      session_display_name: name,
      engagement_id: currentEngagementId,
      client_account_id: clientAccountId,
      is_default: isDefault,
      status: 'active',
      auto_created: false,
      created_by: user.id,
    };
    
    const newSession = await sessionService.createSession(sessionData);
    return toUISession(newSession);
  }, [currentEngagementId]);

  // Update session wrapper
  const updateSession = useCallback(async (sessionId: string, updates: Partial<UISession>): Promise<UISession> => {
    const updated = await sessionService.updateSession(sessionId, toServiceSession(updates));
    return toUISession(updated);
  }, []);

  // Delete session wrapper
  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    await sessionService.deleteSession(sessionId);
  }, []);

  // Set default session wrapper
  const setDefaultSession = useCallback(async (sessionId: string): Promise<UISession> => {
    const updated = await sessionService.setDefaultSession(sessionId);
    return toUISession(updated);
  }, []);

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
    isLoading: isSessionsLoading || isLoading,
    isCreating: createSessionMutation.isPending,
    isUpdating: updateSessionMutation.isPending,
    isSettingDefault: setDefaultSessionMutation.isPending,
    error: sessionsError || error,
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
    setDemoSession: (session: UISession) => {
      setCurrentSession(session);
      setIsLoading(false);
      setError(null);
    },
  }), [
    currentSession,
    sessions,
    isSessionsLoading,
    isLoading,
    createSessionMutation.isPending,
    updateSessionMutation.isPending,
    setDefaultSessionMutation.isPending,
    sessionsError,
    error,
    isDefaultSession,
    setCurrentSession,
    createSession,
    updateSession,
    deleteSession,
    setDefaultSession,
    refreshSessions,
  ]);

  useEffect(() => {
    // If demo user, set demo session and skip fetch
    const demoUserId = '44444444-4444-4444-4444-444444444444';
    const demoSession = {
      id: '33333333-3333-3333-3333-333333333333',
      name: 'Demo Session',
      session_name: 'demo_session',
      session_type: 'analysis', // Use a valid SessionType if needed
      engagement_id: '22222222-2222-2222-2222-222222222222',
      client_account_id: '11111111-1111-1111-1111-111111111111',
      is_default: true,
      status: 'active',
      auto_created: false,
      created_by: demoUserId,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };
    if (user && user.id === demoUserId) {
      setCurrentSession(demoSession);
      setIsLoading(false);
      setError(null);
      return;
    }
  }, [user, setCurrentSession, setIsLoading, setError]);

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

export { SessionProvider };

// Hook for using the session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

export default SessionProvider;
