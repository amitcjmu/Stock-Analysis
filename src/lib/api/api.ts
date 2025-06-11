import { sixrApi } from './sixr';

// Access the http client from sixrApi instance
const httpClient = sixrApi['http'];

/**
 * A generic API call function that uses the http client from sixrApi
 * @param url The API endpoint URL
 * @param options Request options (method, headers, body, etc.)
 * @returns Promise with the response data
 */
export const apiCall = async <T = any>(
  url: string,
  options: RequestInit & { 
    params?: Record<string, any>;
    data?: any;
  } = {}
): Promise<T> => {
  try {
    // Ensure we don't duplicate the /api/v1 prefix that getApiBaseUrl already provides
    let endpoint = url.replace(/^\/api\/v1/, '');
    
    const { params, data, ...fetchOptions } = options;
    const method = (fetchOptions.method || 'GET').toUpperCase();
    
    // Add query parameters for GET requests
    if (method === 'GET' && params && Object.keys(params).length > 0) {
      const queryString = new URLSearchParams(
        Object.entries(params)
          .filter(([_, value]) => value !== undefined && value !== null)
          .map(([key, value]) => [key, String(value)])
      ).toString();
      endpoint = `${endpoint}?${queryString}`;
    }

    // Use the appropriate http client method based on the HTTP method
    switch (method) {
      case 'GET':
        return httpClient.get<T>(endpoint);
      case 'POST':
        return httpClient.post<T>(endpoint, data);
      case 'PUT':
        return httpClient.put<T>(endpoint, data);
      case 'DELETE':
        return httpClient.delete<T>(endpoint);
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

// Re-export the apiCall function as the default export
export default apiCall;
