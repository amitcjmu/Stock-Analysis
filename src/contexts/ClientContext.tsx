import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { apiCall } from '@/lib/api';

export interface Client {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  type: 'enterprise' | 'mid-market' | 'startup';
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

interface ClientContextType {
  currentClient: Client | null;
  availableClients: Client[];
  isLoading: boolean;
  error: Error | null;
  selectClient: (id: string) => Promise<void>;
  switchClient: (id: string) => Promise<void>;
  clearClient: () => void;
  getClientId: () => string | null;
  setDemoClient: (client: Client) => void;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

const CLIENT_KEY = 'current_client';

export const ClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentClient, setCurrentClient] = useState<Client | null>(null);
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user && user.id === '44444444-4444-4444-4444-444444444444') {
      setCurrentClient({
        id: '11111111-1111-1111-1111-111111111111',
        name: 'Democorp',
        status: 'active',
        type: 'enterprise',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        metadata: {
          industry: 'Technology',
          size: 'Enterprise',
          location: 'Global'
        }
      });
      setIsLoading(false);
      setError(null);
      return;
    }

    const initializeClient = async () => {
      try {
        // Skip client initialization for admin routes
        if (user?.role === 'admin' && window.location.pathname.startsWith('/admin')) {
          setIsLoading(false);
          return;
        }

        const clientId = sessionStorage.getItem(CLIENT_KEY);
        
        if (clientId) {
          // Try to get the specific client
          const response = await apiCall(`/clients/${clientId}`);

        if (response.client) {
          setCurrentClient(response.client);
            setIsLoading(false);
            return;
          }
        }

        // If no client ID in session or client not found, get default client
        const defaultResponse = await apiCall('/clients/default');

        if (defaultResponse) {
          sessionStorage.setItem(CLIENT_KEY, defaultResponse.id);
          setCurrentClient(defaultResponse);
        } else {
          sessionStorage.removeItem(CLIENT_KEY);
          setCurrentClient(null);
          
          // If no default client found, redirect to appropriate page
          if (user?.role === 'admin') {
            navigate('/admin/dashboard');
          } else {
            navigate('/session/select');
          }
        }
      } catch (err) {
        console.error('Client initialization error:', err);
        sessionStorage.removeItem(CLIENT_KEY);
        setCurrentClient(null);
        setError(err instanceof Error ? err : new Error('Client initialization failed'));
        
        // On error, redirect to appropriate page
        if (user?.role === 'admin') {
          navigate('/admin/dashboard');
        } else {
          navigate('/session/select');
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      const fetchClients = async () => {
        setIsLoading(true);
        try {
          const response = await apiCall('/api/v1/clients'); 
          if (response.items) {
            setAvailableClients(response.items);
            const storedClientId = sessionStorage.getItem(CLIENT_KEY);
            if (storedClientId) {
              const client = response.items.find((c: Client) => c.id === storedClientId);
              if (client) {
                setCurrentClient(client);
              }
            } else if (response.items.length > 0) {
              // select the first client if none is stored
              setCurrentClient(response.items[0]);
              sessionStorage.setItem(CLIENT_KEY, response.items[0].id);
            }
          }
        } catch (err) {
          setError(err instanceof Error ? err : new Error('Failed to fetch clients'));
        } finally {
          setIsLoading(false);
        }
      };
      fetchClients();
    } else {
      setIsLoading(false);
      setCurrentClient(null);
      setAvailableClients([]);
    }
  }, [user, navigate]);

  const switchClient = async (id: string): Promise<void> => {
    const client = availableClients.find(c => c.id === id);
    if (client) {
      setCurrentClient(client);
      sessionStorage.setItem(CLIENT_KEY, id);
    } else {
      throw new Error('Client not found');
    }
  };

  const selectClient = async (id: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall(`/api/v1/clients/${id}`);

      if (response.client) {
        sessionStorage.setItem(CLIENT_KEY, id);
        setCurrentClient(response.client);
      } else {
        throw new Error('Client not found');
      }
    } catch (err) {
      console.error('Select client error:', err);
      setError(err instanceof Error ? err : new Error('Failed to select client'));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearClient = () => {
    sessionStorage.removeItem(CLIENT_KEY);
    setCurrentClient(null);
  };

  const getClientId = (): string | null => {
    return sessionStorage.getItem(CLIENT_KEY);
  };

  const setDemoClient = (client: Client) => {
    setCurrentClient(client);
    setIsLoading(false);
    setError(null);
  };

  const value = {
    currentClient,
    availableClients,
    isLoading,
    error,
    selectClient,
    switchClient,
    clearClient,
    getClientId,
    setDemoClient
  };

  return <ClientContext.Provider value={value}>{children}</ClientContext.Provider>;
};

export const useClient = () => {
  const context = useContext(ClientContext);
  if (context === undefined) {
    throw new Error('useClient must be used within a ClientProvider');
  }
  return context;
};

export const withClient = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requireClient: boolean = true
) => {
  return function WithClientComponent(props: P) {
    const { currentClient, isLoading } = useClient();
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && requireClient && !currentClient) {
        // Skip client requirement for admin routes
        if (user?.role === 'admin' && window.location.pathname.startsWith('/admin')) {
          return;
        }

        // For non-admin users or admin users on non-admin routes
        if (!currentClient) {
          navigate('/session/select');
        }
      }
    }, [currentClient, isLoading, navigate, user?.role]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Loading client...</p>
          </div>
        </div>
      );
    }

    // Skip client requirement for admin routes
    if (requireClient && !currentClient && !(user?.role === 'admin' && window.location.pathname.startsWith('/admin'))) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}; 