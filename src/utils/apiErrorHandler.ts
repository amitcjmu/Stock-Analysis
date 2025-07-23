import type { QueryCache, MutationCache } from '@tanstack/react-query';
import { toast } from '@/components/ui/use-toast';
import { tokenStorage } from '@/contexts/AuthContext/storage';
import type { ApiError } from '@/types/shared/api-types';

// Create a function to handle API errors globally
export const handleApiError = (error: ApiError & { status?: number; isAuthError?: boolean }, navigate: (path: string) => void) => {
  // Check if it's an authentication error
  if (error?.status === 401 || error?.isAuthError) {
    console.warn('🔐 Authentication error detected, redirecting to login');
    
    // Clear the stored token
    tokenStorage.removeToken();
    tokenStorage.setUser(null);
    
    // Clear any stored context
    localStorage.removeItem('auth_client');
    localStorage.removeItem('auth_engagement');
    localStorage.removeItem('auth_flow');
    sessionStorage.removeItem('auth_initialization_complete');
    
    // Show toast notification
    toast({
      title: 'Session Expired',
      description: 'Please log in again to continue.',
      variant: 'destructive'
    });
    
    // Redirect to login
    navigate('/login');
    
    // Prevent further processing
    return true;
  }
  
  return false;
};

// Create query and mutation caches with global error handling
export const createQueryClient = (navigate: (path: string) => void) => {
  return {
    queryCache: new QueryCache({
      onError: (error: ApiError & { status?: number }) => {
        console.error('Query error:', error);
        
        // Handle authentication errors
        if (handleApiError(error, navigate)) {
          return;
        }
        
        // Handle other errors
        if (error?.status === 500) {
          toast({
            title: 'Server Error',
            description: 'An unexpected error occurred. Please try again later.',
            variant: 'destructive'
          });
        }
      }
    }),
    mutationCache: new MutationCache({
      onError: (error: ApiError & { status?: number }) => {
        console.error('Mutation error:', error);
        
        // Handle authentication errors
        if (handleApiError(error, navigate)) {
          return;
        }
        
        // Let individual mutations handle other errors
      }
    }),
    defaultOptions: {
      queries: {
        retry: (failureCount: number, error: ApiError & { status?: number; isAuthError?: boolean }) => {
          // Don't retry on authentication errors
          if (error?.status === 401 || error?.isAuthError) {
            return false;
          }
          
          // Don't retry on client errors (4xx except 429)
          if (error?.status >= 400 && error?.status < 500 && error?.status !== 429) {
            return false;
          }
          
          // Retry up to 3 times for other errors
          return failureCount < 3;
        },
        retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000)
      },
      mutations: {
        retry: false // Don't retry mutations by default
      }
    }
  };
};