import { useRef } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { getUserContext } from '@/lib/api/context';
import type { User, Client, Engagement, Flow } from '../types';
import { tokenStorage, clearInvalidContextData, syncContextToIndividualKeys } from '../storage';

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

// Add a global counter to debug re-initialization
let initializationCount = 0;

// Add session storage to persist initialization state across page refreshes
const AUTH_INIT_KEY = 'auth_initialization_complete';
const AUTH_INIT_TIMESTAMP_KEY = 'auth_initialization_timestamp';

const getInitializationState = (): boolean => {
  try {
    const completed = sessionStorage.getItem(AUTH_INIT_KEY) === 'true';
    const timestamp = sessionStorage.getItem(AUTH_INIT_TIMESTAMP_KEY);

    // Check if initialization was completed within the last 5 minutes
    if (completed && timestamp) {
      const elapsed = Date.now() - parseInt(timestamp, 10);
      if (elapsed < 5 * 60 * 1000) { // 5 minutes
        return true;
      }
    }
    return false;
  } catch {
    return false;
  }
};

const setInitializationState = (completed: boolean): unknown => {
  try {
    if (completed) {
      sessionStorage.setItem(AUTH_INIT_KEY, 'true');
      sessionStorage.setItem(AUTH_INIT_TIMESTAMP_KEY, Date.now().toString());
    } else {
      sessionStorage.removeItem(AUTH_INIT_KEY);
      sessionStorage.removeItem(AUTH_INIT_TIMESTAMP_KEY);
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
}: UseAuthInitializationProps): void => {
  const navigate = useNavigate();
  const initRef = useRef(false);
  const hasInitializedRef = useRef(false);
  const fallbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    initializationCount++;
    console.log(`🔍 useAuthInitialization effect triggered (count: ${initializationCount})`);

    // Fallback timeout to ensure isLoading gets set to false
    if (!fallbackTimeoutRef.current) {
      fallbackTimeoutRef.current = setTimeout(() => {
        console.warn('⚠️ Auth initialization fallback timeout triggered');
        setIsLoading(false);
      }, 5000); // 5 second timeout
    }

    // Critical: Check if we're in an infinite loop
    if (initializationCount > 10) {
      console.error('🚨 Auth initialization loop detected! Stopping to prevent infinite loop.');
      setIsLoading(false);
      // Clear all initialization state to allow fresh start
      globalAuthInitialized = false;
      isAuthInitializing = false;
      setInitializationState(false);
      if (fallbackTimeoutRef.current) {
        clearTimeout(fallbackTimeoutRef.current);
        fallbackTimeoutRef.current = null;
      }
      return;
    }

    // Guard against multiple initializations
    if (hasInitializedRef.current) {
      console.log('🔍 Auth initialization already completed by this instance, skipping');
      return;
    }

    // Check session state first - this is the most reliable check
    if (getInitializationState()) {
      console.log('🔍 Auth already initialized in this session (from sessionStorage), skipping');
      hasInitializedRef.current = true;
      setIsLoading(false);
      return;
    }

    // Check global initialization state
    if (globalAuthInitialized) {
      console.log('🔍 Auth already initialized globally, skipping');
      setIsLoading(false);
      return;
    }

    // Check if already initializing
    if (isAuthInitializing) {
      console.log('🔍 Auth initialization already in progress, skipping');
      return;
    }

    hasInitializedRef.current = true;

    let isMounted = true;

    const initializeAuth = async (): Promise<void> => {
      // Add a small delay to ensure React has fully mounted
      await new Promise(resolve => setTimeout(resolve, 100));

      // Check token and user first
      const token = tokenStorage.getToken();
      const storedUser = tokenStorage.getUser();

      if (!token || !storedUser) {
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

      // Conservative session guard: only skip if we have stored user and complete context
      if (getInitializationState() && storedUser) {
        console.log('🔍 Auth previously completed, restoring context from session');
        // Restore user from storage
        setUser(storedUser);

        // Always fetch fresh context from API to ensure we have client/engagement
        try {
          console.log('🔄 Fetching fresh context to restore client/engagement...');
          const contextPromise = fetchDefaultContext();
          const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('fetchDefaultContext timeout')), 10000);
          });

          await Promise.race([contextPromise, timeoutPromise]);
          console.log('✅ Context restored successfully');

          // CRITICAL: Sync context to individual localStorage keys for new API client
          syncContextToIndividualKeys();

          setIsLoading(false);
          // Mark initialization as complete again
          globalAuthInitialized = true;
          return;
        } catch (error) {
          console.warn('⚠️ Failed to restore context, clearing session and continuing with full init:', error);
          // Clear invalid context data from localStorage
          clearInvalidContextData();
          setClient(null);
          setEngagement(null);
          // Clear session state and continue with full initialization
          setInitializationState(false);
          globalAuthInitialized = false;
          isAuthInitializing = false; // Reset this to allow reinit
          // Don't return, let it fall through to full initialization
        }
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

        // Check if token is expired before making API calls (only for JWT tokens)
        try {
          // Only attempt JWT parsing if token has the right format
          if (token.includes('.') && token.split('.').length === 3) {
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
          }
          // For non-JWT tokens, skip expiration check and proceed with API validation
        } catch (tokenParseError) {
          // Non-JWT tokens or parsing errors - proceed with API validation
        }

        // Try to get user context from the modern API
        try {
          console.log('🔍 Starting getUserContext API call...');

          // First verify we have a valid token before making API calls
          const currentToken = tokenStorage.getToken();
          if (!currentToken) {
            console.warn('⚠️ No token available, skipping getUserContext');
            throw new Error('No authentication token');
          }

          const userContext = await getUserContext();
          console.log('🔍 getUserContext API call completed:', userContext);
          console.log('🔍 Auth Init - Detailed context analysis:', {
            hasUserContext: !!userContext,
            hasUser: !!userContext?.user,
            hasClient: !!userContext?.client,
            hasEngagement: !!userContext?.engagement,
            hasFlow: !!userContext?.flow,
            userEmail: userContext?.user?.email,
            clientName: userContext?.client?.name,
            engagementName: userContext?.engagement?.name,
            flowName: userContext?.flow?.name
          });

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
            } else {
              console.warn('⚠️ No client in getUserContext response - this may cause context issues');
            }

            if (userContext.engagement) {
              console.log('🔍 Setting engagement from API response:', userContext.engagement);
              setEngagement(userContext.engagement);
            } else {
              console.warn('⚠️ No engagement in getUserContext response - this may cause context issues');
            }

            if (userContext.flow) {
              console.log('🔍 Setting flow from API response:', userContext.flow);
              setFlow(userContext.flow);
            }

            // Check if we got complete context
            if (userContext.client && userContext.engagement) {
              console.log('✅ Complete user context loaded from API - auth initialization successful');
              // CRITICAL: Sync context to individual localStorage keys for new API client
              syncContextToIndividualKeys();
            } else {
              console.warn('⚠️ Incomplete user context from API, missing client or engagement');
              console.log('🔍 User context missing client/engagement, fetching defaults');
              try {
                // Add timeout to fetchDefaultContext to prevent hanging
                const contextPromise = fetchDefaultContext();
                const timeoutPromise = new Promise((_, reject) => {
                  setTimeout(() => reject(new Error('fetchDefaultContext timeout')), 10000);
                });

                await Promise.race([contextPromise, timeoutPromise]);
                console.log('🔍 fetchDefaultContext completed for user context');
                // CRITICAL: Sync context to individual localStorage keys for new API client
                syncContextToIndividualKeys();
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
                // CRITICAL: Sync context to individual localStorage keys for new API client
                syncContextToIndividualKeys();
              } catch (contextError) {
                console.warn('⚠️ fetchDefaultContext failed but continuing with stored user:', contextError);
                // Continue with just the stored user - don't fail the entire auth flow
              }
            } else {
              throw new Error('No user data available');
            }
          }
        } catch (error) {
          if (!isMounted) return;

          const apiError = error as { status?: number; message?: string };
          if (apiError.status === 401) {
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
            console.error('🔄 Error getting user context:', apiError.message || 'Unknown error');
            // Try to use stored user as fallback but be more lenient with errors
            const storedUser = tokenStorage.getUser();
            if (storedUser) {
              console.log('🔄 Using stored user as fallback due to context API error');
              setUser(storedUser);
              try {
                await fetchDefaultContext();
                // CRITICAL: Sync context to individual localStorage keys for new API client
                syncContextToIndividualKeys();
              } catch (contextError) {
                console.warn('⚠️ Default context fetch failed, continuing with stored user only:', contextError);
                // Continue with just the stored user - don't fail the entire auth flow
              }
            } else {
              throw error;
            }
          }
        }
      } catch (error) {
        if (!isMounted) return;

        const authError = error as { message?: string };
        console.error('Auth initialization error:', authError.message || 'Unknown error');
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
      // Don't reset hasInitializedRef on unmount - keep it true to prevent re-initialization
      console.log('🔍 useAuthInitialization unmounting');

      // Clean up fallback timeout
      if (fallbackTimeoutRef.current) {
        clearTimeout(fallbackTimeoutRef.current);
        fallbackTimeoutRef.current = null;
      }

      // Reset the initialization counter if it's too high to allow recovery
      if (initializationCount > 5) {
        console.log('🔍 Resetting initialization counter on unmount');
        initializationCount = 0;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - initialization should only run once per mount
  // Intentionally excluding dependencies to prevent re-initialization loops.
  // All functions (setUser, setClient, etc.) are stable from parent context and
  // this effect is designed to run exactly once on mount for authentication setup.
};
