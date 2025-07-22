import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from '@/components/ui/use-toast';
import { tokenStorage } from '@/contexts/AuthContext/storage';
import { useAuth } from '@/contexts/AuthContext';

export const useGlobalErrorHandler = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { logout } = useAuth();

  useEffect(() => {
    // Set up global error handler for queries
    const unsubscribeQuery = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'error' && event.query.state.error) {
        const error = event.query.state.error as unknown;
        
        // Check if it's an authentication error
        if (error?.status === 401 || error?.isAuthError) {
          console.warn('🔐 Authentication error detected in query, logging out');
          
          // Clear all queries to stop retries
          queryClient.cancelQueries();
          queryClient.clear();
          
          // Use the logout function which handles navigation
          logout();
        }
      }
    });

    // Set up global error handler for mutations
    const unsubscribeMutation = queryClient.getMutationCache().subscribe((event) => {
      if (event.type === 'error' && event.mutation?.state.error) {
        const error = event.mutation.state.error as unknown;
        
        // Check if it's an authentication error
        if (error?.status === 401 || error?.isAuthError) {
          console.warn('🔐 Authentication error detected in mutation, logging out');
          
          // Clear all queries to stop retries
          queryClient.cancelQueries();
          queryClient.clear();
          
          // Use the logout function which handles navigation
          logout();
        }
      }
    });

    // Cleanup
    return () => {
      unsubscribeQuery();
      unsubscribeMutation();
    };
  }, [queryClient, logout]);
};