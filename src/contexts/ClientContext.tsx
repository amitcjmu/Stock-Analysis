import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from './AuthContext';
import { apiCall } from '@/lib/api';

interface Client {
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
  isLoading: boolean;
  error: Error | null;
  selectClient: (id: string) => Promise<void>;
  clearClient: () => void;
  getClientId: () => string | null;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

const CLIENT_KEY = 'current_client';

export const ClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentClient, setCurrentClient] = useState<Client | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { getContextHeaders } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const initializeClient = async () => {
      try {
        const clientId = sessionStorage.getItem(CLIENT_KEY);
        if (!clientId) {
          setIsLoading(false);
          return;
        }

        const response = await apiCall(`/api/v1/clients/${clientId}`, {
          method: 'GET',
          headers: getContextHeaders()
        });

        if (response.client) {
          setCurrentClient(response.client);
        } else {
          sessionStorage.removeItem(CLIENT_KEY);
          setCurrentClient(null);
        }
      } catch (err) {
        console.error('Client initialization error:', err);
        sessionStorage.removeItem(CLIENT_KEY);
        setCurrentClient(null);
        setError(err instanceof Error ? err : new Error('Client initialization failed'));
      } finally {
        setIsLoading(false);
      }
    };

    initializeClient();
  }, [getContextHeaders]);

  const selectClient = async (id: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall(`/api/v1/clients/${id}`, {
        method: 'GET',
        headers: getContextHeaders()
      });

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

  const value = {
    currentClient,
    isLoading,
    error,
    selectClient,
    clearClient,
    getClientId
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
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && requireClient && !currentClient) {
        router.push('/clients');
      }
    }, [currentClient, isLoading, router]);

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

    if (requireClient && !currentClient) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}; 