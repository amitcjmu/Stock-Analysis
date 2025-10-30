/**
 * Token Refresh Utility
 * Handles automatic access token refresh when it expires
 */

import { authApi } from './api/auth';
import { tokenStorage } from '@/contexts/AuthContext/storage';

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

/**
 * Refresh the access token using the refresh token
 * @returns Promise<string | null> - New access token or null if refresh failed
 */
export async function refreshAccessToken(): Promise<string | null> {
  // If already refreshing, return the existing promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;

  refreshPromise = (async () => {
    try {
      const refreshToken = tokenStorage.getRefreshToken();

      if (!refreshToken) {
        console.warn('No refresh token available');
        return null;
      }

      console.log('🔄 Refreshing access token...');

      const response = await authApi.refreshToken(refreshToken);

      if (response.status === 'success' && response.token) {
        // Store new tokens
        tokenStorage.setToken(response.token.access_token);
        if (response.token.refresh_token) {
          tokenStorage.setRefreshToken(response.token.refresh_token);
        }

        console.log('✅ Access token refreshed successfully');
        return response.token.access_token;
      }

      console.warn('Token refresh failed: Invalid response');
      return null;
    } catch (error) {
      console.error('Token refresh error:', error);

      // If refresh token is expired or invalid, clear tokens and redirect to login
      if (error instanceof Error && (error as Error & { status?: number }).status === 401) {
        console.log('🔄 Refresh token expired, clearing authentication');
        tokenStorage.removeToken();
        tokenStorage.removeRefreshToken();
        tokenStorage.removeUser();

        // Redirect to login
        window.location.href = '/login';
      }

      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/**
 * Fetch wrapper that automatically refreshes token on 401
 * @param url - Request URL
 * @param options - Fetch options
 * @returns Promise<Response>
 */
export async function fetchWithTokenRefresh(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // Skip token refresh for auth endpoints
  if (url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/refresh')) {
    return fetch(url, options);
  }

  // First attempt
  let response = await fetch(url, options);

  // If 401, try refreshing token and retry
  if (response.status === 401) {
    console.log('🔄 Received 401, attempting token refresh...');

    const newToken = await refreshAccessToken();

    if (newToken) {
      // Retry request with new token
      const headers = new Headers(options.headers);
      headers.set('Authorization', `Bearer ${newToken}`);

      response = await fetch(url, {
        ...options,
        headers,
      });

      console.log('🔄 Retried request with refreshed token');
    }
  }

  return response;
}

/**
 * Check if token is close to expiration and refresh proactively
 * @param tokenExpirationBuffer - Minutes before expiration to refresh (default: 5)
 */
export function checkTokenExpiration(tokenExpirationBuffer: number = 5): void {
  const token = tokenStorage.getToken();

  if (!token || !token.includes('.')) {
    // Not a JWT token or no token
    return;
  }

  try {
    const tokenData = JSON.parse(atob(token.split('.')[1]));
    const expirationTime = tokenData.exp * 1000; // Convert to milliseconds
    const now = Date.now();
    const timeUntilExpiration = expirationTime - now;
    const bufferTime = tokenExpirationBuffer * 60 * 1000; // Convert to milliseconds

    // If token will expire within the buffer time, refresh it proactively
    if (timeUntilExpiration < bufferTime && timeUntilExpiration > 0) {
      console.log(`🔄 Token expires in ${Math.round(timeUntilExpiration / 1000)}s, refreshing proactively...`);
      refreshAccessToken().catch(error => {
        console.error('Proactive token refresh failed:', error);
      });
    }
  } catch (error) {
    console.error('Error checking token expiration:', error);
  }
}

/**
 * Start background timer for proactive token refresh
 * @param checkIntervalMinutes - How often to check (default: 1 minute)
 * @param expirationBufferMinutes - Minutes before expiration to refresh (default: 5)
 * @returns Timer ID that can be used to stop the background refresh
 */
export function startBackgroundTokenRefresh(
  checkIntervalMinutes: number = 1,
  expirationBufferMinutes: number = 5
): NodeJS.Timeout {
  const intervalId = setInterval(() => {
    checkTokenExpiration(expirationBufferMinutes);
  }, checkIntervalMinutes * 60 * 1000);

  console.log('✅ Background token refresh started');

  return intervalId;
}

/**
 * Stop background token refresh
 * @param timerId - Timer ID returned by startBackgroundTokenRefresh
 */
export function stopBackgroundTokenRefresh(timerId: NodeJS.Timeout): void {
  clearInterval(timerId);
  console.log('🛑 Background token refresh stopped');
}
