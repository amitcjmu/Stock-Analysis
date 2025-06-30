/**
 * Authentication Interceptor for API v3
 * Handles automatic token injection and refresh
 */

import { getAuthToken, removeAuthToken } from '../utils/requestConfig';

export interface AuthConfig {
  tokenKey?: string;
  headerName?: string;
  tokenPrefix?: string;
  autoRefresh?: boolean;
  onTokenExpired?: () => void;
  onAuthError?: (error: any) => void;
}

const DEFAULT_AUTH_CONFIG: Required<AuthConfig> = {
  tokenKey: 'auth_token',
  headerName: 'Authorization',
  tokenPrefix: 'Bearer',
  autoRefresh: false,
  onTokenExpired: () => {
    console.warn('Auth token expired');
    removeAuthToken();
  },
  onAuthError: (error) => {
    console.error('Authentication error:', error);
  }
};

/**
 * Request interceptor to add authentication headers
 */
export function createAuthRequestInterceptor(config: AuthConfig = {}) {
  const authConfig = { ...DEFAULT_AUTH_CONFIG, ...config };

  return (request: Request): Request => {
    const token = getAuthToken();
    
    if (token) {
      const headers = new Headers(request.headers);
      headers.set(authConfig.headerName, `${authConfig.tokenPrefix} ${token}`);
      
      return new Request(request, { headers });
    }
    
    return request;
  };
}

/**
 * Response interceptor to handle auth errors
 */
export function createAuthResponseInterceptor(config: AuthConfig = {}) {
  const authConfig = { ...DEFAULT_AUTH_CONFIG, ...config };

  return (response: Response): Response => {
    // Check for authentication errors
    if (response.status === 401) {
      authConfig.onTokenExpired();
      authConfig.onAuthError({
        status: 401,
        message: 'Authentication token expired or invalid'
      });
    }

    return response;
  };
}

/**
 * Check if token is expired (client-side check)
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= exp;
  } catch (error) {
    console.warn('Failed to parse token:', error);
    return true; // Assume expired if we can't parse
  }
}

/**
 * Get time until token expires
 */
export function getTokenExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    return exp - Date.now();
  } catch (error) {
    console.warn('Failed to parse token:', error);
    return null;
  }
}

/**
 * Refresh token if needed
 */
export async function refreshTokenIfNeeded(
  refreshEndpoint: string,
  refreshToken?: string
): Promise<string | null> {
  const currentToken = getAuthToken();
  
  if (!currentToken) {
    return null;
  }

  // Check if token needs refresh (refresh if expires within 5 minutes)
  const timeUntilExpiry = getTokenExpiry(currentToken);
  if (timeUntilExpiry && timeUntilExpiry > 5 * 60 * 1000) {
    return currentToken; // Token is still valid
  }

  try {
    const response = await fetch(refreshEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentToken}`
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      const newToken = data.access_token || data.token;
      
      if (newToken) {
        localStorage.setItem('auth_token', newToken);
        return newToken;
      }
    }
  } catch (error) {
    console.error('Failed to refresh token:', error);
  }

  return null;
}

/**
 * Default auth interceptor with standard configuration
 */
export const authInterceptor = createAuthRequestInterceptor();

/**
 * Auth response interceptor with standard configuration
 */
export const authResponseInterceptor = createAuthResponseInterceptor();

/**
 * Combined auth interceptor for both request and response
 */
export function createAuthInterceptor(config: AuthConfig = {}) {
  return {
    request: createAuthRequestInterceptor(config),
    response: createAuthResponseInterceptor(config)
  };
}

/**
 * Validate auth token format
 */
export function validateTokenFormat(token: string): boolean {
  // Basic JWT format validation
  const parts = token.split('.');
  return parts.length === 3;
}

/**
 * Extract user info from token
 */
export function extractUserFromToken(token: string): any {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.sub || payload.user_id,
      email: payload.email,
      role: payload.role,
      permissions: payload.permissions || [],
      exp: payload.exp,
      iat: payload.iat
    };
  } catch (error) {
    console.warn('Failed to extract user from token:', error);
    return null;
  }
}

/**
 * Check if user has permission
 */
export function hasPermission(token: string, permission: string): boolean {
  const user = extractUserFromToken(token);
  return user && user.permissions && user.permissions.includes(permission);
}

/**
 * Get user role from token
 */
export function getUserRole(token: string): string | null {
  const user = extractUserFromToken(token);
  return user ? user.role : null;
}