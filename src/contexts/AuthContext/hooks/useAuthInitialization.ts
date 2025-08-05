import { useRef } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { getUserContext } from '@/lib/api/context';
import type { User, Client, Engagement, Flow } from '../types';
import { tokenStorage, syncContextToIndividualKeys } from '../storage';

interface UseAuthInitializationProps {
  setUser: (user: User | null) => void;
  setClient: (client: Client | null) => void;
  setEngagement: (engagement: Engagement | null) => void;
  setFlow: (flow: Flow | null) => void;
  setIsLoading: (loading: boolean) => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  fetchDefaultContext: () => Promise<void>;
}

// Simplified initialization guards (removed module-level variable - moved to hook scope)
const AUTH_INIT_KEY = 'auth_init_completed';
const AUTH_INIT_TTL = 30 * 1000; // 30 seconds TTL for session cache (reduced from 2 minutes to prevent stale state)

// Cache-aware initialization state management
const getSessionInitState = (): { completed: boolean; fresh: boolean } => {
  try {
    const data = sessionStorage.getItem(AUTH_INIT_KEY);
    if (!data) return { completed: false, fresh: false };

    const { timestamp } = JSON.parse(data);
    const fresh = (Date.now() - timestamp) < AUTH_INIT_TTL;
    return { completed: true, fresh };
  } catch {
    return { completed: false, fresh: false };
  }
};

const setSessionInitState = (completed: boolean): void => {
  try {
    if (completed) {
      sessionStorage.setItem(AUTH_INIT_KEY, JSON.stringify({ timestamp: Date.now() }));
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
}: UseAuthInitializationProps): void => {
  const navigate = useNavigate();
  const hasInitialized = useRef(false);
  const isAuthInitializing = useRef(false); // Convert to ref for proper scoping
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Prevent multiple initializations
    if (hasInitialized.current || isAuthInitializing.current) {
      return;
    }

    // Simplified auth initialization: Check for cached auth data first
    const storedUser = tokenStorage.getUser();
    const token = tokenStorage.getToken();

    // If we have auth data, restore it immediately
    if (storedUser && token) {
      // Set the auth data immediately
      setUser(storedUser);

      // Restore context from localStorage
      try {
        const cachedClient = localStorage.getItem('auth_client');
        const cachedEngagement = localStorage.getItem('auth_engagement');
        const cachedFlow = localStorage.getItem('auth_flow');

        if (cachedClient) setClient(JSON.parse(cachedClient));
        if (cachedEngagement) setEngagement(JSON.parse(cachedEngagement));
        if (cachedFlow) setFlow(JSON.parse(cachedFlow));

        // Sync context to individual keys for API client
        syncContextToIndividualKeys();
      } catch (error) {
        console.warn('Context restoration failed:', error);
      }

      // Complete initialization
      setIsLoading(false);
      hasInitialized.current = true;
      setSessionInitState(true);
      return;
    }

    // No cached auth data - redirect to login
    setUser(null);
    setClient(null);
    setEngagement(null);
    setFlow(null);

    // Clear any cached session state
    try {
      localStorage.removeItem('auth_client');
      localStorage.removeItem('auth_engagement');
      localStorage.removeItem('auth_flow');
      setSessionInitState(false);
    } catch (error) {
      console.warn('Failed to clear cached auth state:', error);
    }

    setIsLoading(false);
    hasInitialized.current = true;
    navigate('/login');
    return;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount for optimal performance
};
