import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { apiCall, API_CONFIG } from '../config/api';

export interface ClientContext {
  id: string;
  name: string;
  slug: string;
}

export interface EngagementContext {
  id: string;
  name: string;
  slug: string;
  client_account_id: string;
}

export interface SessionContext {
  id: string;
  session_name: string;
  session_display_name?: string;
  engagement_id: string;
  status: string;
}

export interface AppContext {
  client: ClientContext | null;
  engagement: EngagementContext | null;
  session: SessionContext | null;
  viewMode: 'session_view' | 'engagement_view';
}

const STORAGE_KEY = 'aiforce_context';
const DEFAULT_DEMO_CLIENT: ClientContext = {
  id: 'cc92315a-4bae-469d-9550-46d1c6e5ab68',
  name: 'Pujyam Corp',
  slug: 'pujyam-corp'
};

const DEFAULT_DEMO_ENGAGEMENT: EngagementContext = {
  id: '3d4e572d-46b1-4b3c-bfb4-99c50e9aa6ec',
  name: 'Digital Transformation 2025',
  slug: 'digital-transformation-2025',
  client_account_id: 'cc92315a-4bae-469d-9550-46d1c6e5ab68'
};

export const useAppContext = () => {
  const location = useLocation();
  const [context, setContext] = useState<AppContext>({
    client: DEFAULT_DEMO_CLIENT,
    engagement: DEFAULT_DEMO_ENGAGEMENT,
    session: null,
    viewMode: 'engagement_view'
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load context from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsedContext = JSON.parse(stored);
        setContext(prev => ({
          ...prev,
          ...parsedContext,
          // Always ensure we have demo defaults if stored context is incomplete
          client: parsedContext.client || DEFAULT_DEMO_CLIENT,
          engagement: parsedContext.engagement || DEFAULT_DEMO_ENGAGEMENT
        }));
      } catch (err) {
        console.warn('Failed to parse stored context, using defaults');
      }
    }
  }, []);

  // Save context to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(context));
  }, [context]);

  // Fetch available clients
  const fetchClients = async (): Promise<ClientContext[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.ADMIN.CLIENTS}/?page_size=100`, {
        headers: {
          // Add current context headers
          ...(context.client && { 'X-Client-Account-Id': context.client.id }),
          ...(context.engagement && { 'X-Engagement-Id': context.engagement.id }),
          ...(context.session && { 'X-Session-Id': context.session.id })
        }
      });
      
      const clients = response.items?.map((client: any) => ({
        id: client.id,
        name: client.account_name, // Map account_name to name
        slug: client.slug
      })) || [];
      
      // Always include demo client if not already present
      const hasDemo = clients.some((c: ClientContext) => c.id === DEFAULT_DEMO_CLIENT.id);
      if (!hasDemo) {
        clients.unshift(DEFAULT_DEMO_CLIENT);
      }
      
      return clients;
    } catch (err) {
      console.warn('Failed to fetch clients:', err);
      setError('Failed to load clients');
      return [DEFAULT_DEMO_CLIENT];
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch engagements for a client
  const fetchEngagements = async (clientId: string): Promise<EngagementContext[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.ADMIN.ENGAGEMENTS}/?client_account_id=${clientId}&page_size=100`, {
        headers: {
          'X-Client-Account-Id': clientId,
          ...(context.engagement && { 'X-Engagement-Id': context.engagement.id }),
          ...(context.session && { 'X-Session-Id': context.session.id })
        }
      });
      
      const engagements = response.items?.map((engagement: any) => ({
        id: engagement.id,
        name: engagement.name,
        slug: engagement.slug,
        client_account_id: engagement.client_account_id
      })) || [];
      
      // For demo client, ensure demo engagement is included
      if (clientId === DEFAULT_DEMO_CLIENT.id) {
        const hasDemo = engagements.some((e: EngagementContext) => e.id === DEFAULT_DEMO_ENGAGEMENT.id);
        if (!hasDemo) {
          engagements.unshift(DEFAULT_DEMO_ENGAGEMENT);
        }
      }
      
      return engagements;
    } catch (err) {
      console.warn('Failed to fetch engagements:', err);
      setError('Failed to load engagements');
      // Return demo engagement for demo client
      return clientId === DEFAULT_DEMO_CLIENT.id ? [DEFAULT_DEMO_ENGAGEMENT] : [];
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch sessions for an engagement
  const fetchSessions = async (engagementId: string): Promise<SessionContext[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.ADMIN.ENGAGEMENTS}/${engagementId}/sessions`, {
        headers: {
          ...(context.client && { 'X-Client-Account-Id': context.client.id }),
          'X-Engagement-Id': engagementId,
          ...(context.session && { 'X-Session-Id': context.session.id })
        }
      });
      
      return response.items?.map((session: any) => ({
        id: session.id,
        session_name: session.session_name,
        session_display_name: session.session_display_name,
        engagement_id: session.engagement_id,
        status: session.status
      })) || [];
    } catch (err) {
      console.warn('Failed to fetch sessions:', err);
      setError('Failed to load sessions');
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  // Update context
  const updateContext = (updates: Partial<AppContext>) => {
    setContext(prev => {
      const newContext = { ...prev, ...updates };
      
      // If client changes, clear engagement and session
      if (updates.client && updates.client.id !== prev.client?.id) {
        newContext.engagement = null;
        newContext.session = null;
      }
      
      // If engagement changes, clear session
      if (updates.engagement && updates.engagement.id !== prev.engagement?.id) {
        newContext.session = null;
      }
      
      return newContext;
    });
  };

  // Set client context
  const setClient = (client: ClientContext | null) => {
    updateContext({ client });
  };

  // Set engagement context
  const setEngagement = (engagement: EngagementContext | null) => {
    updateContext({ engagement });
  };

  // Set session context
  const setSession = (session: SessionContext | null) => {
    updateContext({ session });
  };

  // Set view mode
  const setViewMode = (viewMode: 'session_view' | 'engagement_view') => {
    updateContext({ viewMode });
  };

  // Get current context as HTTP headers
  const getContextHeaders = () => {
    const headers: Record<string, string> = {};
    
    if (context.client) {
      headers['X-Client-Account-Id'] = context.client.id;
    }
    
    if (context.engagement) {
      headers['X-Engagement-Id'] = context.engagement.id;
    }
    
    if (context.session && context.viewMode === 'session_view') {
      headers['X-Session-Id'] = context.session.id;
    }
    
    headers['X-View-Mode'] = context.viewMode;
    
    return headers;
  };

  // Get context breadcrumb path
  const getBreadcrumbs = () => {
    const breadcrumbs = [];
    
    if (context.client) {
      breadcrumbs.push({
        label: context.client.name,
        type: 'client' as const,
        active: !context.engagement
      });
    }
    
    if (context.engagement) {
      breadcrumbs.push({
        label: context.engagement.name,
        type: 'engagement' as const,
        active: !context.session || context.viewMode === 'engagement_view'
      });
    }
    
    if (context.session && context.viewMode === 'session_view') {
      breadcrumbs.push({
        label: context.session.session_display_name || context.session.session_name,
        type: 'session' as const,
        active: true
      });
    }
    
    return breadcrumbs;
  };

  // Reset to demo context
  const resetToDemo = () => {
    setContext({
      client: DEFAULT_DEMO_CLIENT,
      engagement: DEFAULT_DEMO_ENGAGEMENT,
      session: null,
      viewMode: 'engagement_view'
    });
  };

  return {
    context,
    isLoading,
    error,
    fetchClients,
    fetchEngagements,
    fetchSessions,
    setClient,
    setEngagement,
    setSession,
    setViewMode,
    updateContext,
    getContextHeaders,
    getBreadcrumbs,
    resetToDemo,
    clearError: () => setError(null)
  };
}; 