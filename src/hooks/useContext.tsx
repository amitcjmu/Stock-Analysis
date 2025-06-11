import { useAuth } from '@/contexts/AuthContext';
import { useClient } from '@/contexts/ClientContext';
import { useEngagement } from '@/contexts/EngagementContext';
import { useSession } from '@/contexts/SessionContext';
import { useState, useCallback } from 'react';

// -----------------------------------------------------------------------------
//  Temporary compatibility layer
//  --------------------------------
//  This file re-introduces the legacy `useAppContext` API so that components
//  still depending on it compile and render without crashing.  The implementation
//  is intentionally minimal – it only stores data in React state and returns
//  no-op async helpers.  All real logic has moved to AuthContext, SessionContext
//  and other modern hooks.  Once every component is fully refactored, this file
//  should be deleted.
// -----------------------------------------------------------------------------

/** Basic client representation used by legacy components */
export interface ClientContext {
  id: string;
  name: string;
}

/** Basic engagement representation used by legacy components */
export interface EngagementContext {
  id: string;
  name: string;
  client_id?: string;
}

/** Basic session representation used by legacy components */
export interface SessionContext {
  id: string;
  session_display_name?: string;
  session_name?: string;
  engagement_id?: string;
}

/** View mode type used in the original implementation */
export type ViewMode = 'session_view' | 'engagement_view';

/** Shape returned by the legacy hook */
export interface LegacyAppContext {
  context: {
    client: ClientContext | null;
    engagement: EngagementContext | null;
    session: SessionContext | null;
    viewMode: ViewMode;
  };
  isLoading: boolean;
  error: string | null;
  // Data loaders
  fetchClients: () => Promise<ClientContext[]>;
  fetchEngagements: (clientId: string) => Promise<EngagementContext[]>;
  fetchSessions: (engagementId: string) => Promise<SessionContext[]>;
  // Mutators
  setClient: (client: ClientContext | null) => void;
  setEngagement: (engagement: EngagementContext | null) => void;
  setSession: (session: SessionContext | null) => void;
  setViewMode: (mode: ViewMode) => void;
  // Misc util functions preserved for compatibility
  resetToDemo: () => void;
  clearError: () => void;
  getContextHeaders: () => Record<string, string>;
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function useAppContext(): LegacyAppContext {
  // Minimal local state – this does *not* persist across components, but is
  // sufficient for rendering dropdowns etc. without API integration.
  const [client, setClient] = useState<ClientContext | null>(null);
  const [engagement, setEngagement] = useState<EngagementContext | null>(null);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('engagement_view');
  const [error, setError] = useState<string | null>(null);

  // ---------------------------
  //  Stubbed async loaders
  // ---------------------------
  const fetchClients = useCallback(async (): Promise<ClientContext[]> => {
    // In demo mode return a single placeholder client
    return Promise.resolve([{ id: 'demo-client', name: 'Demo Client' }]);
  }, []);

  const fetchEngagements = useCallback(async (_clientId: string): Promise<EngagementContext[]> => {
    return Promise.resolve([{ id: 'demo-engagement', name: 'Demo Engagement' }]);
  }, []);

  const fetchSessions = useCallback(async (_engagementId: string): Promise<SessionContext[]> => {
    return Promise.resolve([{ id: 'demo-session', session_display_name: 'Demo Session' }]);
  }, []);

  // ---------------------------
  //  Utility helpers
  // ---------------------------
  const resetToDemo = useCallback(() => {
    setClient({ id: 'demo-client', name: 'Demo Client' });
    setEngagement({ id: 'demo-engagement', name: 'Demo Engagement' });
    setSession({ id: 'demo-session', session_display_name: 'Demo Session' });
    setViewMode('engagement_view');
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const getContextHeaders = useCallback(() => {
    return {
      'X-Client-ID': client?.id ?? '',
      'X-Engagement-ID': engagement?.id ?? '',
      'X-Session-ID': session?.id ?? '',
    };
  }, [client?.id, engagement?.id, session?.id]);

  return {
    context: { client, engagement, session, viewMode },
    isLoading: false,
    error,
    fetchClients,
    fetchEngagements,
    fetchSessions,
    setClient,
    setEngagement,
    setSession,
    setViewMode,
    resetToDemo,
    clearError,
    getContextHeaders,
  };
}

export interface ContextData {
  auth: {
    userId: string | null;
    token: string | null;
  };
  client: {
    id: string | null;
    name: string | null;
  };
  engagement: {
    id: string | null;
    name: string | null;
  };
  session: {
    id: string | null;
    type: string | null;
  };
}

export const useContext = () => {
  const { user, getToken } = useAuth();
  const { currentClient } = useClient();
  const { currentEngagement } = useEngagement();
  const { currentSession } = useSession();

  const contextData: ContextData = {
    auth: {
      userId: user?.id || null,
      token: getToken() || null
    },
    client: {
      id: currentClient?.id || null,
      name: currentClient?.name || null
    },
    engagement: {
      id: currentEngagement?.id || null,
      name: currentEngagement?.name || null
    },
    session: {
      id: currentSession?.id || null,
      type: currentSession?.type || null
    }
  };

  return contextData;
};

export default useContext;

// -----------------------------------------------------------------------------
//  NOTE: This file is TEMPORARY.  Remove after all components are migrated to
//  the new Auth / Session / Engagement hooks & contexts.
// -----------------------------------------------------------------------------