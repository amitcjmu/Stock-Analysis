import { apiCall } from './http';

// Default client for fallback
const DEFAULT_CLIENT = {
  id: "demo",
  name: "Pujyam Corp",
  status: "active",
  type: "enterprise",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  metadata: {
    industry: "Technology",
    size: "Enterprise",
    location: "Global"
  }
};

// Modified apiCall to handle default client case
export const apiCallWithFallback = async (endpoint: string, options?: RequestInit) => {
  try {
    // Handle default client case
    if (endpoint === '/api/v1/clients/default' || endpoint === '/clients/default') {
      return { client: DEFAULT_CLIENT };
    }
    
    // Try the actual API call
    return await apiCall(endpoint, options);
  } catch (error) {
    // If it's the clients endpoint and it fails, return default client
    if (endpoint === '/api/v1/admin/clients' || endpoint === '/admin/clients' || 
        endpoint === '/api/v1/clients/default' || endpoint === '/clients/default') {
      return { client: DEFAULT_CLIENT };
    }
    throw error;
  }
};

export { apiCall };
