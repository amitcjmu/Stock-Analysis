import { QueryClient } from '@tanstack/react-query';

// Create a basic query client without error handling
// The error handling will be added in the App component where we have access to navigation
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false, // Optional: disable refetching on window focus
      retry: (failureCount: number, error: unknown) => {
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
  },
}); 