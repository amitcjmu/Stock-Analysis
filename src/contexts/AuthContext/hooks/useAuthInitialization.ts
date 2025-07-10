import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserContext } from '@/lib/api/context';
import { User, Client, Engagement, Flow } from '../types';
import { tokenStorage } from '../storage';

interface UseAuthInitializationProps {
  setUser: (user: User | null) => void;
  setClient: (client: Client | null) => void;
  setEngagement: (engagement: Engagement | null) => void;
  setFlow: (flow: Flow | null) => void;
  setIsLoading: (loading: boolean) => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  fetchDefaultContext: () => Promise<void>;
}

// Global initialization guard to prevent multiple simultaneous authentication attempts
// This is especially important in React Strict Mode which runs effects twice
let globalAuthInitialized = false;
let isAuthInitializing = false;

// Add session storage to persist initialization state across page refreshes
const AUTH_INIT_KEY = 'auth_initialization_complete';
const getInitializationState = () => {
  try {
    return sessionStorage.getItem(AUTH_INIT_KEY) === 'true';
  } catch {
    return false;
  }
};

const setInitializationState = (completed: boolean) => {
  try {
    if (completed) {
      sessionStorage.setItem(AUTH_INIT_KEY, 'true');
    } else {
      sessionStorage.removeItem(AUTH_INIT_KEY);
    }
  } catch {
    // Ignore storage errors
  }
};

export const useAuthInitialization = ({
  setUser,
  setClient,
  setEngagement,
  setFlow,
  setIsLoading,
  switchClient,
  fetchDefaultContext
}: UseAuthInitializationProps) => {
  const navigate = useNavigate();
  const initRef = useRef(false);

  useEffect(() => {
    let isMounted = true;
    
    const initializeAuth = async () => {
      // Session guard: if auth was already completed in this session, skip
      if (getInitializationState()) {
        console.log('🔍 Auth already initialized in this session, skipping');
        setIsLoading(false);
        return;
      }
      
      // Global guard: if auth was already initialized globally, skip
      if (globalAuthInitialized) {
        console.log('🔍 Auth already initialized globally, skipping');
        setIsLoading(false);
        return;
      }
      
      // Component guard: if this component already initialized, skip
      if (initRef.current) {
        console.log('🔍 This component already initialized, skipping');
        return;
      }
      
      // Concurrency guard: if initialization is in progress, skip
      if (isAuthInitializing) {
        console.log('🔍 Auth initialization already in progress, skipping');
        return;
      }
      
      console.log('🔍 Starting auth initialization...');
      isAuthInitializing = true;
      initRef.current = true;
      
      // Add timeout to prevent infinite hanging
      const timeoutId = setTimeout(() => {
        console.error('🚨 Authentication initialization timed out after 15 seconds');
        isAuthInitializing = false;
        if (isMounted) {
          setIsLoading(false);
        }
      }, 15000);
      try {
        if (!isMounted) return;
        setIsLoading(true);
        
        const token = tokenStorage.getToken();
        if (!token) {
          if (isMounted) {
            setUser(null);
            setClient(null);
            setEngagement(null);
            setFlow(null);
            setIsLoading(false);
            navigate('/login');
          }
          return;
        }

        // Check if token is expired before making API calls
        try {
          const tokenData = JSON.parse(atob(token.split('.')[1]));
          const now = Math.floor(Date.now() / 1000);
          
          if (tokenData.exp && tokenData.exp < now) {
            tokenStorage.removeToken();
            tokenStorage.setUser(null);
            if (isMounted) {
              setUser(null);
              setClient(null);
              setEngagement(null);
              setFlow(null);
              setIsLoading(false);
              navigate('/login');
            }
            return;
          }
        } catch (tokenParseError) {
          // Could not parse token, proceed with API validation
        }

        // Try to get user context from the modern API
        try {
          console.log('🔍 Starting getUserContext API call...');
          const userContext = await getUserContext();
          console.log('🔍 getUserContext API call completed:', userContext);
          
          if (!isMounted) {
            console.log('🔍 Component unmounted, stopping auth initialization');
            return;
          }
          
          if (userContext?.user) {
            console.log('🔍 Setting user from API response:', userContext.user);
            setUser(userContext.user);
            
            if (userContext.client) {
              console.log('🔍 Setting client from API response:', userContext.client);
              setClient(userContext.client);
            }
            
            if (userContext.engagement) {
              console.log('🔍 Setting engagement from API response:', userContext.engagement);
              setEngagement(userContext.engagement);
            }
            
            if (userContext.flow) {
              console.log('🔍 Setting flow from API response:', userContext.flow);
              setFlow(userContext.flow);
            }
            
            console.log('✅ User context loaded from API - auth initialization should complete now');
            
            // If we have user but no client/engagement, fetch defaults
            if (!userContext.client || !userContext.engagement) {
              console.log('🔍 User context missing client/engagement, fetching defaults');
              try {
                // Add timeout to fetchDefaultContext to prevent hanging
                const contextPromise = fetchDefaultContext();
                const timeoutPromise = new Promise((_, reject) => {
                  setTimeout(() => reject(new Error('fetchDefaultContext timeout')), 10000);
                });
                
                await Promise.race([contextPromise, timeoutPromise]);
                console.log('🔍 fetchDefaultContext completed for user context');
              } catch (contextError) {
                console.warn('⚠️ fetchDefaultContext failed but continuing with user-only context:', contextError);
                // Continue with just the user - don't fail the entire auth flow
              }
            }
          } else {
            console.log('🔍 No user in userContext, trying stored user. userContext:', userContext);
            // If no context from API, try to use stored user and fetch defaults
            const storedUser = tokenStorage.getUser();
            if (storedUser && isMounted) {
              console.log('🔍 Setting stored user and fetching default context');
              setUser(storedUser);
              console.log('🔄 Calling fetchDefaultContext...');
              try {
                // Add timeout to fetchDefaultContext to prevent hanging
                const contextPromise = fetchDefaultContext();
                const timeoutPromise = new Promise((_, reject) => {
                  setTimeout(() => reject(new Error('fetchDefaultContext timeout')), 10000);
                });
                
                await Promise.race([contextPromise, timeoutPromise]);
                console.log('🔄 fetchDefaultContext completed');
              } catch (contextError) {
                console.warn('⚠️ fetchDefaultContext failed but continuing with stored user:', contextError);
                // Continue with just the stored user - don't fail the entire auth flow
              }
            } else {
              throw new Error('No user data available');
            }
          }
        } catch (error: any) {
          if (!isMounted) return;
          
          if (error.status === 401) {
            console.log('🔄 Token is invalid, clearing authentication and redirecting to login');
            tokenStorage.removeToken();
            tokenStorage.setUser(null);
            setUser(null);
            setClient(null);
            setEngagement(null);
            setFlow(null);
            navigate('/login');
            return;
          } else {
            console.error('🔄 Error getting user context:', error);
            // Try to use stored user as fallback but be more lenient with errors
            const storedUser = tokenStorage.getUser();
            if (storedUser) {
              console.log('🔄 Using stored user as fallback due to context API error');
              setUser(storedUser);
              try {
                await fetchDefaultContext();
              } catch (contextError) {
                console.warn('⚠️ Default context fetch failed, continuing with stored user only:', contextError);
                // Continue with just the stored user - don't fail the entire auth flow
              }
            } else {
              throw error;
            }
          }
        }
      } catch (error: any) {
        if (!isMounted) return;
        
        console.error('Auth initialization error:', error);
        tokenStorage.removeToken();
        tokenStorage.setUser(null);
        setUser(null);
        setClient(null);
        setEngagement(null);
        setFlow(null);
        setInitializationState(false); // Clear initialization state on error
        navigate('/login');
      } finally {
        clearTimeout(timeoutId);
        isAuthInitializing = false;
        globalAuthInitialized = true; // Mark as globally initialized
        setInitializationState(true); // Persist across page refreshes
        console.log('✅ Auth initialization completed successfully');
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initializeAuth();
    
    return () => {
      isMounted = false;
    };
  }, []);
};