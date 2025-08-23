import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext';
import { tokenStorage } from '@/contexts/AuthContext/storage';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle } from 'lucide-react'
import { AlertCircle } from 'lucide-react'

export const DebugContext: React.FC = () => {
  const { user, client, engagement, flow } = useAuth();
  const [localStorage, setLocalStorage] = useState<Record<string, unknown>>({});
  const [apiResponse, setApiResponse] = useState<{
    error?: string;
    clients?: unknown[];
    [key: string]: unknown;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Read all auth-related localStorage items
    const authKeys = ['auth_token', 'user_data', 'auth_client', 'auth_engagement', 'auth_session', 'auth_client_id'];
    const data: Record<string, unknown> = {};

    authKeys.forEach(key => {
      const value = window.localStorage.getItem(key);
      if (value) {
        try {
          data[key] = JSON.parse(value);
        } catch {
          data[key] = value;
        }
      }
    });

    setLocalStorage(data);
  }, []);

  const clearLocalStorage = (): unknown => {
    window.localStorage.removeItem('auth_client');
    window.localStorage.removeItem('auth_engagement');
    window.localStorage.removeItem('auth_session');
    window.localStorage.removeItem('auth_client_id');
    window.location.reload();
  };

  const fetchClients = async (): Promise<void> => {
    setLoading(true);
    try {
      const token = tokenStorage.getToken();

      // Use proper URL construction for Docker development
      let apiUrl: string;
      if (typeof window !== 'undefined' && window.location.port === '8081') {
        // Force relative URL for Docker development to use Vite proxy
        apiUrl = '/api/v1/context-establishment/clients';
      } else {
        // For other environments, use the environment variable
        apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/context-establishment/clients`;
      }

      const response = await fetch(apiUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setApiResponse(data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      setApiResponse({ error: error instanceof Error ? error.message : String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      <h1 className="text-3xl font-bold">Debug Context & Authentication</h1>

      <Card>
        <CardHeader>
          <CardTitle>Current Auth Context</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold">User:</h3>
            <pre className="bg-gray-100 p-2 rounded text-sm">
              {user ? JSON.stringify(user, null, 2) : 'null'}
            </pre>
          </div>

          <div>
            <h3 className="font-semibold">Client:</h3>
            <pre className="bg-gray-100 p-2 rounded text-sm">
              {client ? JSON.stringify(client, null, 2) : 'null'}
            </pre>
            {client && typeof client.id !== 'string' && (
              <div className="flex items-center gap-2 mt-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>Client ID is not a string! Type: {typeof client.id}</span>
              </div>
            )}
            {client && client.id && client.id.length < 36 && (
              <div className="flex items-center gap-2 mt-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>Client ID appears to be numeric, not a UUID!</span>
              </div>
            )}
          </div>

          <div>
            <h3 className="font-semibold">Engagement:</h3>
            <pre className="bg-gray-100 p-2 rounded text-sm">
              {engagement ? JSON.stringify(engagement, null, 2) : 'null'}
            </pre>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LocalStorage Auth Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
            {JSON.stringify(localStorage, null, 2)}
          </pre>

          <div className="mt-4 space-x-2">
            <Button onClick={clearLocalStorage} variant="destructive">
              Clear Context Data
            </Button>
            <Button onClick={fetchClients} disabled={loading}>
              {loading ? 'Fetching...' : 'Fetch Clients from API'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {apiResponse && (
        <Card>
          <CardHeader>
            <CardTitle>API Response</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
              {JSON.stringify(apiResponse, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DebugContext;
