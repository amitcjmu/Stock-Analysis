/**
 * Client Context Provider
 * Manages client state and selection
 */

import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { apiCall } from '@/lib/api';
import type { Client, ClientContextType } from './types';
import { ClientContext } from './context';

const CLIENT_KEY = 'current_client';

export const ClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentClient, setCurrentClient] = useState<Client | null>(null);
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { user, client: authClient, engagement: authEngagement, session: authSession, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Don't hardcode client for demo user - let them choose from available demo clients
    // The -def0-def0-def0- pattern identifies demo data

    const initializeClient = async (): Promise<void> => {
      try {
        // Skip client initialization for admin routes
        if (user?.role === 'admin' && window.location.pathname.startsWith('/admin')) {
          setIsLoading(false);
          return;
        }

        const clientId = sessionStorage.getItem(CLIENT_KEY);

        if (clientId) {
          // Try to get the specific client
          const response = await apiCall(`/api/v1/context-establishment/clients/${clientId}`);

        if (response.client) {
          setCurrentClient(response.client);
            setIsLoading(false);
            return;
          }
        }

        // If no client ID in session or client not found, fetch all clients to get first one
        const response = await apiCall('/api/v1/context-establishment/clients', {}, false);

        if (response.clients && response.clients.length > 0) {
          const firstClient = response.clients[0];
          sessionStorage.setItem(CLIENT_KEY, firstClient.id);
          setCurrentClient(firstClient);
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

    // Load clients when user is available - don't wait for full auth context
    // The auth context depends on ClientContext, so we can't wait for it
    if (user && !authLoading) {
      console.log('🔄 ClientContext: User available, fetching clients');
      const fetchClients = async (): Promise<void> => {
        setIsLoading(true);
        try {
          // Skip default client fetch - endpoint doesn't exist
          // We'll set the first available client as default instead

          // Also fetch all available clients
          const response = await apiCall('/api/v1/context-establishment/clients', {}, false); // Don't include context headers when fetching clients
          if (response.clients) {
            setAvailableClients(response.clients);

            // If we didn't get a default client, use stored or first available
            if (!currentClient) {
              const storedClientId = sessionStorage.getItem(CLIENT_KEY);
              if (storedClientId) {
                const client = response.clients.find((c: Client) => c.id === storedClientId);
                if (client) {
                  setCurrentClient(client);
                }
              } else if (response.clients.length > 0) {
                // select the first client if none is stored
                setCurrentClient(response.clients[0]);
                sessionStorage.setItem(CLIENT_KEY, response.clients[0].id);
              }
            }
          }
        } catch (err) {
          console.error('Failed to fetch clients:', err);
          setError(err instanceof Error ? err : new Error('Failed to fetch clients'));
        } finally {
          setIsLoading(false);
        }
      };
      fetchClients();
    } else if (authLoading) {
      // Waiting for auth to load - removed console.log to prevent infinite spam
    } else {
      // No user available - removed console.log to prevent spam
      setIsLoading(false);
      setCurrentClient(null);
      setAvailableClients([]);
    }
  }, [user, authLoading, navigate, currentClient]);

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

      const response = await apiCall(`/api/v1/context-establishment/clients/${id}`);

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

  const clearClient = (): unknown => {
    sessionStorage.removeItem(CLIENT_KEY);
    setCurrentClient(null);
  };

  const getClientId = (): string | null => {
    return sessionStorage.getItem(CLIENT_KEY);
  };

  const setDemoClient = (client: Client): unknown => {
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
