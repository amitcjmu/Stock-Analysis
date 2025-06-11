import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { apiCall, API_CONFIG, updateApiContext } from '../config/api';

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
  session_display_name: string;
  engagement_id: string;
  status: string;
}

export interface AppContext {
  client: ClientContext | null;
  engagement: EngagementContext | null;
  session: SessionContext | null;
  viewMode: 'session_view' | 'engagement_view';
}

interface AppContextType {
  // Direct access to context values
  client: ClientContext | null;
  engagement: EngagementContext | null;
  session: SessionContext | null;
  viewMode: 'session_view' | 'engagement_view';
  
  // State and error handling
  isLoading: boolean;
  error: string | null;
  
  // Data fetching
  fetchClients: () => Promise<ClientContext[]>;
  fetchEngagements: (clientId: string) => Promise<EngagementContext[]>;
  fetchSessions: (engagementId: string) => Promise<SessionContext[]>;
  
  // State setters
  setClient: (client: ClientContext | null) => void;
  setEngagement: (engagement: EngagementContext | null) => void;
  setSession: (session: SessionContext | null) => void;
  setViewMode: (viewMode: 'session_view' | 'engagement_view', source?: string) => void;
  
  // Context utilities
  updateContext: (updates: Partial<AppContext>) => void;
  getContextHeaders: () => Record<string, string>;
  getBreadcrumbs: () => Array<{ 
    id: string; 
    label: string; 
    type: 'client' | 'engagement' | 'session'; 
    active: boolean 
  }>;
  resetToDemo: () => void;
  clearError: () => void;
  
  // For backward compatibility
  context: AppContext;
}

const STORAGE_KEY = 'aiforce_context';
const DEFAULT_DEMO_CLIENT: ClientContext = {
  id: 'd838573d-f461-44e4-81b5-5af510ef83b7',
  name: 'Acme Corporation',
  slug: 'acme-corp'
};

const DEFAULT_DEMO_ENGAGEMENT: EngagementContext = {
  id: 'd1a93e23-719d-4dad-8bbf-b66ab9de2b94',
  name: 'Cloud Migration Initiative 2024',
  slug: 'cloud-migration-initiative-2024',
  client_account_id: 'd838573d-f461-44e4-81b5-5af510ef83b7'
};

const DEFAULT_DEMO_SESSION: SessionContext = {
  id: 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
  session_name: 'default-session',
  session_display_name: 'Default Session',
  engagement_id: 'd1a93e23-719d-4dad-8bbf-b66ab9de2b94',
  status: 'active'
};

// Create the context
const AppContextContext = createContext<AppContextType | undefined>(undefined);

// Context Provider
export const AppContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  console.log('AppContextProvider - Initial render');
  const location = useLocation();
  const [context, setContext] = useState<AppContext>(() => {
    console.log('Initializing context state');
    return {
      client: DEFAULT_DEMO_CLIENT,
      engagement: DEFAULT_DEMO_ENGAGEMENT,
      session: DEFAULT_DEMO_SESSION,
      viewMode: 'session_view' as const
    };
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

// Sync context with API module
useEffect(() => {
  try {
    updateApiContext({
      client: context.client,
      engagement: context.engagement,
      session: context.session
    });
  } catch (error) {
    console.error('Failed to update API context:', error);
  }
}, [context.client, context.engagement, context.session]);

  // Log context changes
  useEffect(() => {
    console.group('AppContext - Context Update');
    console.log('Current context state:', {
      client: context.client ? { id: context.client.id, name: context.client.name } : null,
      engagement: context.engagement ? { id: context.engagement.id, name: context.engagement.name } : null,
      session: context.session ? { 
        id: context.session.id, 
        name: context.session.session_display_name || context.session.session_name 
      } : null,
      viewMode: context.viewMode
    });
    console.trace('Context update stack trace');
    console.groupEnd();
  }, [context]);

  // Load context from localStorage on mount
  useEffect(() => {
    console.log('Loading context from localStorage');
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsedContext = JSON.parse(stored);
        console.log('Found stored context:', parsedContext);
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
    } else {
      console.log('No stored context found, using defaults');
    }
  }, []);

  // Save context to localStorage when it changes
  useEffect(() => {
    console.log('Saving context to localStorage');
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(context));
    } catch (error) {
      console.error('Error saving context to localStorage:', error);
    }
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
        name: client.account_name, // API returns account_name
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
        name: engagement.engagement_name, // API returns engagement_name
        slug: engagement.slug || engagement.engagement_name?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''), // Generate slug if not provided
        client_account_id: engagement.client_account_id
      })) || [];
      
      return engagements;
    } catch (err) {
      console.warn('Failed to fetch engagements:', err);
      setError('Failed to load engagements');
      return [];
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

  // Update context with change checks
  const updateContext = (updates: Partial<AppContext>) => {
    console.log('Updating context with:', updates);
    setContext(prev => {
      // Check if any values actually changed
      const changes: Partial<AppContext> = {};
      let hasChanges = false;
      
      // Check client changes
      if ('client' in updates) {
        const clientChanged = updates.client?.id !== prev.client?.id;
        if (clientChanged) {
          changes.client = updates.client;
          hasChanges = true;
          
          // If client changes, clear engagement and session
          changes.engagement = null;
          changes.session = null;
        }
      }
      
      // Check engagement changes (if client didn't change)
      if ('engagement' in updates && !changes.engagement) {
        const engagementChanged = updates.engagement?.id !== prev.engagement?.id;
        if (engagementChanged) {
          changes.engagement = updates.engagement;
          hasChanges = true;
          
          // If engagement changes, clear session
          changes.session = null;
        }
      }
      
      // Check session changes (if engagement didn't change)
      if ('session' in updates && !changes.session) {
        const sessionChanged = updates.session?.id !== prev.session?.id;
        if (sessionChanged) {
          changes.session = updates.session;
          hasChanges = true;
        }
      }
      
      // Check view mode changes
      if ('viewMode' in updates && updates.viewMode !== prev.viewMode) {
        changes.viewMode = updates.viewMode;
        hasChanges = true;
      }
      
      // Only return a new object if there are actual changes
      if (!hasChanges) {
        console.log('No context changes, skipping update');
        return prev;
      }
      
      console.log('Applying context changes:', changes);
      return { ...prev, ...changes };
    });
  };

  // Set client context with change check
  const setClient = (client: ClientContext | null) => {
    console.log('Setting client:', client?.id);
    setContext(prev => {
      if ((!client && !prev.client) || (client?.id === prev.client?.id)) {
        console.log('Client unchanged, skipping update');
        return prev;
      }
      return { ...prev, client };
    });
  };

  // Set engagement context with change check
  const setEngagement = (engagement: EngagementContext | null) => {
    console.log('Setting engagement:', engagement?.id);
    setContext(prev => {
      if ((!engagement && !prev.engagement) || (engagement?.id === prev.engagement?.id)) {
        console.log('Engagement unchanged, skipping update');
        return prev;
      }
      return { ...prev, engagement };
    });
  };

  // Set session context with change check
  const setSession = (session: SessionContext | null) => {
    console.log('Setting session:', session?.id);
    setContext(prev => {
      if ((!session && !prev.session) || (session?.id === prev.session?.id)) {
        console.log('Session unchanged, skipping update');
        return prev;
      }
      return { ...prev, session };
    });
  };

  // Set view mode with change check and stack trace
  const setViewMode = (viewMode: 'session_view' | 'engagement_view', source = 'unknown') => {
    console.group('setViewMode');
    console.log('Requested view mode:', viewMode, 'from:', source);
    console.trace('Stack trace');
    
    setContext(prev => {
      if (prev.viewMode === viewMode) {
        console.log('View mode unchanged, skipping update');
        console.groupEnd();
        return prev;
      }
      
      console.log(`View mode changing from ${prev.viewMode} to ${viewMode}`);
      console.groupEnd();
      return { ...prev, viewMode };
    });
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
  const getBreadcrumbs = (): Array<{
    id: string;
    label: string;
    type: 'client' | 'engagement' | 'session';
    active: boolean;
  }> => {
    const breadcrumbs: Array<{
      id: string;
      label: string;
      type: 'client' | 'engagement' | 'session';
      active: boolean;
    }> = [];
    
    if (context.client) {
      breadcrumbs.push({
        id: `client-${context.client.id}`,
        label: context.client.name,
        type: 'client',
        active: !context.engagement
      });
    }
    
    if (context.engagement) {
      breadcrumbs.push({
        id: `engagement-${context.engagement.id}`,
        label: context.engagement.name,
        type: 'engagement',
        active: !context.session || context.viewMode === 'engagement_view'
      });
    }
    
    if (context.session && context.viewMode === 'session_view') {
      breadcrumbs.push({
        id: `session-${context.session.id}`,
        label: context.session.session_display_name || context.session.session_name,
        type: 'session',
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

  // Clear error
  const clearError = () => setError(null);

  // Create the context value with direct property access
  const contextValue: AppContextType = {
    // Direct properties
    client: context.client,
    engagement: context.engagement,
    session: context.session,
    viewMode: context.viewMode,
    
    // State and error handling
    isLoading,
    error,
    
    // Methods
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
    clearError,
    
    // For backward compatibility
    context: {
      client: context.client,
      engagement: context.engagement,
      session: context.session,
      viewMode: context.viewMode
    },
  };

  return (
    <AppContextContext.Provider value={contextValue}>
      {children}
    </AppContextContext.Provider>
  );
};

// Hook to use the context
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContextContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppContextProvider');
  }
  return context;
}; 