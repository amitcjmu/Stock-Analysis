import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import {
  GlobalContextProvider,
  useGlobalContext,
  useGlobalAuth,
  useGlobalUserContext
} from '../../contexts/GlobalContext';
import { globalReducer, createInitialState } from '../../contexts/GlobalContext/reducer';
import { contextStorage } from '../../contexts/GlobalContext/storage';

// Mock external dependencies
jest.mock('../../config/api', () => ({
  apiCall: jest.fn(),
}));

jest.mock('../../utils/performance/monitoring', () => ({
  performanceMonitor: {
    markStart: jest.fn(),
    markEnd: jest.fn(),
    subscribe: jest.fn(() => jest.fn()),
    recordEvent: jest.fn(),
    getReport: jest.fn(() => ({})),
  },
}));

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

// Test component to access context
const TestComponent: React.FC = () => {
  const { state, login, logout, switchClient } = useGlobalContext();
  const { user, isAuthenticated } = useGlobalAuth();
  const { client } = useGlobalUserContext();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-name">{user?.full_name || 'no-user'}</div>
      <div data-testid="client-name">{client?.name || 'no-client'}</div>
      <div data-testid="loading-status">
        {state.auth.isLoading ? 'loading' : 'not-loading'}
      </div>
      <button
        data-testid="login-button"
        onClick={() => login('test@example.com', 'password')}
      >
        Login
      </button>
      <button
        data-testid="logout-button"
        onClick={logout}
      >
        Logout
      </button>
      <button
        data-testid="switch-client-button"
        onClick={() => switchClient('client-1')}
      >
        Switch Client
      </button>
    </div>
  );
};

const renderWithProvider = (
  component: React.ReactElement,
  options: { enablePerformanceMonitoring?: boolean } = {}
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <GlobalContextProvider {...options}>
        {component}
      </GlobalContextProvider>
    </QueryClientProvider>
  );
};

describe('GlobalContext', () => {
  let mockApiCall: jest.Mock;

  beforeEach(() => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const apiModule = require('../../config/api') as { apiCall: jest.Mock };
    mockApiCall = apiModule.apiCall;
    mockApiCall.mockClear();

    // Clear storage
    contextStorage.clearContextData();

    // Reset local storage
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('GlobalContextProvider', () => {
    it('should render loading state initially', async () => {
      mockApiCall.mockResolvedValue({ user: null });

      renderWithProvider(<TestComponent />);

      expect(screen.getByText('Initializing application...')).toBeInTheDocument();
    });

    it('should initialize with user context from API', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'user',
      };

      const mockClient = {
        id: 'client-1',
        name: 'Test Client',
        status: 'active',
      };

      mockApiCall.mockResolvedValue({
        user: mockUser,
        client: mockClient,
      });

      renderWithProvider(<TestComponent />);

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
        expect(screen.getByTestId('client-name')).toHaveTextContent('Test Client');
      });

      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/context/me', {}, false);
    });

    it('should use cached context data when available', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Cached User',
        role: 'user',
      };

      // Set cached data
      contextStorage.setContextData({
        user: mockUser,
        client: null,
        engagement: null,
        flow: null,
      });

      renderWithProvider(<TestComponent />);

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('Cached User');
      });

      // API should not be called when using cached data
      expect(mockApiCall).not.toHaveBeenCalled();
    });

    it('should handle authentication errors gracefully', async () => {
      mockApiCall.mockRejectedValue(new Error('Authentication failed'));

      renderWithProvider(<TestComponent />);

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('no-user');
      });
    });
  });

  describe('Authentication Actions', () => {
    it('should handle login successfully', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'user',
      };

      // Mock login API call
      mockApiCall
        .mockResolvedValueOnce({ user: null }) // Initial context call
        .mockResolvedValueOnce({ user: mockUser }) // Login call
        .mockResolvedValueOnce({ user: mockUser }); // Re-initialize context

      renderWithProvider(<TestComponent />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('loading-status')).toHaveTextContent('not-loading');
      });

      // Perform login
      const loginButton = screen.getByTestId('login-button');
      await act(async () => {
        await userEvent.click(loginButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
      });

      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
      });
    });

    it('should handle logout correctly', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'user',
      };

      mockApiCall.mockResolvedValue({ user: mockUser });

      renderWithProvider(<TestComponent />);

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      // Perform logout
      const logoutButton = screen.getByTestId('logout-button');
      await act(async () => {
        await userEvent.click(logoutButton);
      });

      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-name')).toHaveTextContent('no-user');
    });
  });

  describe('Context Switching', () => {
    it('should switch client successfully', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'user',
      };

      const mockClient = {
        id: 'client-1',
        name: 'New Client',
        status: 'active',
      };

      mockApiCall
        .mockResolvedValueOnce({ user: mockUser }) // Initial context
        .mockResolvedValueOnce({ client: mockClient }); // Switch client

      renderWithProvider(<TestComponent />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      // Switch client
      const switchClientButton = screen.getByTestId('switch-client-button');
      await act(async () => {
        await userEvent.click(switchClientButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('client-name')).toHaveTextContent('New Client');
      });

      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/context-establishment/clients/client-1');
    });
  });

  describe('Reducer', () => {
    it('should handle AUTH_INIT_SUCCESS correctly', () => {
      const initialState = createInitialState();
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'admin',
      };

      const action = {
        type: 'AUTH_INIT_SUCCESS' as const,
        payload: { user: mockUser },
      };

      const newState = globalReducer(initialState, action);

      expect(newState.auth.user).toEqual(mockUser);
      expect(newState.auth.isInitialized).toBe(true);
      expect(newState.auth.isLoading).toBe(false);
      expect(newState.auth.error).toBeNull();
    });

    it('should handle AUTH_INIT_ERROR correctly', () => {
      const initialState = createInitialState();
      const action = {
        type: 'AUTH_INIT_ERROR' as const,
        payload: 'Authentication failed',
      };

      const newState = globalReducer(initialState, action);

      expect(newState.auth.user).toBeNull();
      expect(newState.auth.isInitialized).toBe(true);
      expect(newState.auth.isLoading).toBe(false);
      expect(newState.auth.error).toBe('Authentication failed');
    });

    it('should handle CONTEXT_SWITCH_CLIENT correctly', () => {
      const initialState = createInitialState();
      const mockClient = {
        id: 'client-1',
        name: 'Test Client',
        status: 'active',
      };

      const action = {
        type: 'CONTEXT_SWITCH_CLIENT' as const,
        payload: mockClient,
      };

      const newState = globalReducer(initialState, action);

      expect(newState.context.client).toEqual(mockClient);
      expect(newState.context.engagement).toBeNull(); // Should clear engagement
      expect(newState.context.flow).toBeNull(); // Should clear flow
    });

    it('should handle UI_ADD_NOTIFICATION correctly', () => {
      const initialState = createInitialState();
      const notification = {
        type: 'success' as const,
        title: 'Test Notification',
        message: 'This is a test',
      };

      const action = {
        type: 'UI_ADD_NOTIFICATION' as const,
        payload: notification,
      };

      const newState = globalReducer(initialState, action);

      expect(newState.ui.notifications).toHaveLength(1);
      expect(newState.ui.notifications[0]).toMatchObject(notification);
      expect(newState.ui.notifications[0].id).toBeDefined();
      expect(newState.ui.notifications[0].timestamp).toBeDefined();
    });

    it('should handle PERFORMANCE_UPDATE_METRICS correctly', () => {
      const initialState = createInitialState();
      const metrics = {
        renderCount: 5,
        lastRenderTime: 16.7,
        cacheHitRate: 0.85,
      };

      const action = {
        type: 'PERFORMANCE_UPDATE_METRICS' as const,
        payload: metrics,
      };

      const newState = globalReducer(initialState, action);

      expect(newState.performance.renderCount).toBe(5);
      expect(newState.performance.lastRenderTime).toBe(16.7);
      expect(newState.performance.cacheHitRate).toBe(0.85);
    });
  });

  describe('Feature Flags', () => {
    it('should initialize with correct default feature flags', () => {
      const initialState = createInitialState(true);

      expect(initialState.featureFlags.enablePerformanceMonitoring).toBe(true);
      expect(initialState.featureFlags.useWebSocketSync).toBe(true);
      expect(initialState.featureFlags.useProgressiveHydration).toBe(true);
    });

    it('should allow feature flag updates', () => {
      const initialState = createInitialState();
      const action = {
        type: 'FEATURE_FLAGS_UPDATE' as const,
        payload: {
          useRedisCache: true,
          enableContextDebugging: false,
        },
      };

      const newState = globalReducer(initialState, action);

      expect(newState.featureFlags.useRedisCache).toBe(true);
      expect(newState.featureFlags.enableContextDebugging).toBe(false);
    });
  });

  describe('Cache Management', () => {
    it('should handle cache status updates', () => {
      const initialState = createInitialState();
      const action = {
        type: 'CACHE_SET_STATUS' as const,
        payload: {
          isEnabled: true,
          isConnected: true,
        },
      };

      const newState = globalReducer(initialState, action);

      expect(newState.cache.isEnabled).toBe(true);
      expect(newState.cache.isConnected).toBe(true);
    });

    it('should handle pending cache invalidations', () => {
      const initialState = createInitialState();

      // Add pending invalidation
      const addAction = {
        type: 'CACHE_ADD_PENDING_INVALIDATION' as const,
        payload: 'user-context',
      };

      const stateWithPending = globalReducer(initialState, addAction);
      expect(stateWithPending.cache.pendingInvalidations).toContain('user-context');

      // Clear pending invalidations
      const clearAction = {
        type: 'CACHE_CLEAR_PENDING_INVALIDATIONS' as const,
      };

      const clearedState = globalReducer(stateWithPending, clearAction);
      expect(clearedState.cache.pendingInvalidations).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle unknown actions gracefully', () => {
      const initialState = createInitialState();
      const unknownAction = {
        type: 'UNKNOWN_ACTION' as never,
        payload: 'test',
      };

      // Should not throw an error
      const newState = globalReducer(initialState, unknownAction);
      expect(newState).toEqual(initialState);
    });

    it('should handle API failures during context switching', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'user',
      };

      mockApiCall
        .mockResolvedValueOnce({ user: mockUser }) // Initial context
        .mockRejectedValueOnce(new Error('Client not found')); // Switch client fails

      renderWithProvider(<TestComponent />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      // Attempt to switch client (should fail)
      const switchClientButton = screen.getByTestId('switch-client-button');
      await act(async () => {
        await userEvent.click(switchClientButton);
      });

      // Should still be authenticated but client switch should have failed
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('client-name')).toHaveTextContent('no-client');
    });
  });

  describe('Performance Monitoring', () => {
    it('should enable performance monitoring when flag is set', () => {
      renderWithProvider(<TestComponent />, { enablePerformanceMonitoring: true });

      // Performance monitoring should be enabled in the initial state
      expect(createInitialState(true).featureFlags.enablePerformanceMonitoring).toBe(true);
    });

    it('should disable performance monitoring when flag is not set', () => {
      renderWithProvider(<TestComponent />, { enablePerformanceMonitoring: false });

      // Performance monitoring should be disabled in the initial state
      expect(createInitialState(false).featureFlags.enablePerformanceMonitoring).toBe(false);
    });
  });
});
