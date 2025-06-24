import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';

// Types for UnifiedDiscoveryFlow
interface UnifiedDiscoveryFlowState {
  flow_id: string;
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  crew_status: Record<string, any>;
  raw_data: any[];
  field_mappings: Record<string, any>;
  cleaned_data: any[];
  asset_inventory: Record<string, any>;
  dependencies: Record<string, any>;
  technical_debt: Record<string, any>;
  status: string;
  progress_percentage: number;
  errors: string[];
  warnings: string[];
  created_at: string;
  updated_at: string;
}

interface UseUnifiedDiscoveryFlowReturn {
  flowState: UnifiedDiscoveryFlowState | null;
  isLoading: boolean;
  error: Error | null;
  isHealthy: boolean;
  initializeFlow: (data: any) => Promise<any>;
  executeFlowPhase: (phase: string) => Promise<any>;
  getPhaseData: (phase: string) => any;
  isPhaseComplete: (phase: string) => boolean;
  canProceedToPhase: (phase: string) => boolean;
  refreshFlow: () => Promise<void>;
  isExecutingPhase: boolean;
}

// API functions for UnifiedDiscoveryFlow
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const unifiedDiscoveryAPI = {
  async getFlowStatus(sessionId: string): Promise<UnifiedDiscoveryFlowState> {
    const response = await fetch(`${API_BASE}/api/v1/discovery/flow/status/${sessionId}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': localStorage.getItem('user_id') || '',
        'X-Client-Account-ID': localStorage.getItem('client_account_id') || '',
        'X-Engagement-ID': localStorage.getItem('engagement_id') || '',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get flow status: ${response.statusText}`);
    }
    
    return response.json();
  },

  async initializeFlow(data: any): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/discovery/flow/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': localStorage.getItem('user_id') || '',
        'X-Client-Account-ID': localStorage.getItem('client_account_id') || '',
        'X-Engagement-ID': localStorage.getItem('engagement_id') || '',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to initialize flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async executePhase(phase: string, data: any = {}): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/discovery/flow/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': localStorage.getItem('user_id') || '',
        'X-Client-Account-ID': localStorage.getItem('client_account_id') || '',
        'X-Engagement-ID': localStorage.getItem('engagement_id') || '',
      },
      body: JSON.stringify({ phase, data }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to execute phase ${phase}: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getHealthStatus(): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/discovery/health`, {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': localStorage.getItem('user_id') || '',
        'X-Client-Account-ID': localStorage.getItem('client_account_id') || '',
        'X-Engagement-ID': localStorage.getItem('engagement_id') || '',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get health status: ${response.statusText}`);
    }
    
    return response.json();
  },
};

/**
 * Unified Discovery Flow Hook
 * 
 * This is the single source of truth for all discovery flow interactions.
 * Connects frontend to the UnifiedDiscoveryFlow CrewAI execution engine.
 */
export const useUnifiedDiscoveryFlow = (): UseUnifiedDiscoveryFlowReturn => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isExecutingPhase, setIsExecutingPhase] = useState(false);

  // Get current session ID from URL or localStorage
  const sessionId = useMemo(() => {
    // Try to get from URL first
    const urlParams = new URLSearchParams(window.location.search);
    const urlSessionId = urlParams.get('session_id');
    if (urlSessionId) return urlSessionId;

    // Try to get from localStorage
    const storedSessionId = localStorage.getItem('current_discovery_session_id');
    if (storedSessionId) return storedSessionId;

    // Extract from path (e.g., /discovery/attribute-mapping/session-123)
    const pathMatch = window.location.pathname.match(/\/discovery\/[^\/]+\/([^\/]+)/);
    if (pathMatch) return pathMatch[1];

    return null;
  }, []);

  // Flow state query
  const {
    data: flowState,
    isLoading,
    error,
    refetch: refreshFlow,
  } = useQuery({
    queryKey: ['unifiedDiscoveryFlow', sessionId],
    queryFn: () => sessionId ? unifiedDiscoveryAPI.getFlowStatus(sessionId) : null,
    enabled: !!sessionId,
    refetchInterval: 5000, // Poll every 5 seconds for real-time updates
    refetchIntervalInBackground: true,
    staleTime: 2000,
  });

  // Health check query
  const { data: healthStatus } = useQuery({
    queryKey: ['unifiedDiscoveryFlowHealth'],
    queryFn: unifiedDiscoveryAPI.getHealthStatus,
    refetchInterval: 30000, // Check health every 30 seconds
    staleTime: 15000,
  });

  // Initialize flow mutation
  const initializeFlowMutation = useMutation({
    mutationFn: unifiedDiscoveryAPI.initializeFlow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow'] });
      // Store session ID for future use
      if (data.session_id) {
        localStorage.setItem('current_discovery_session_id', data.session_id);
      }
    },
  });

  // Execute phase mutation
  const executePhhaseMutation = useMutation({
    mutationFn: ({ phase, data }: { phase: string; data?: any }) => 
      unifiedDiscoveryAPI.executePhase(phase, data),
    onMutate: () => {
      setIsExecutingPhase(true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow', sessionId] });
    },
    onError: (error) => {
      console.error('Phase execution failed:', error);
    },
    onSettled: () => {
      setIsExecutingPhase(false);
    },
  });

  // Helper functions
  const getPhaseData = useCallback((phase: string) => {
    if (!flowState) return null;
    
    switch (phase) {
      case 'field_mapping':
        return flowState.field_mappings;
      case 'data_cleansing':
        return flowState.cleaned_data;
      case 'asset_inventory':
        return flowState.asset_inventory;
      case 'dependency_analysis':
        return flowState.dependencies;
      case 'tech_debt_analysis':
        return flowState.technical_debt;
      default:
        return null;
    }
  }, [flowState]);

  const isPhaseComplete = useCallback((phase: string) => {
    return flowState?.phase_completion?.[phase] || false;
  }, [flowState]);

  const canProceedToPhase = useCallback((phase: string) => {
    if (!flowState) return false;
    
    // Define phase order
    const phaseOrder = [
      'data_import',
      'field_mapping', 
      'data_cleansing',
      'asset_inventory',
      'dependency_analysis',
      'tech_debt_analysis'
    ];
    
    const currentIndex = phaseOrder.indexOf(phase);
    if (currentIndex <= 0) return true; // First phase or unknown phase
    
    // Check if previous phase is complete
    const previousPhase = phaseOrder[currentIndex - 1];
    return isPhaseComplete(previousPhase);
  }, [flowState, isPhaseComplete]);

  const executeFlowPhase = useCallback(async (phase: string) => {
    return executePhhaseMutation.mutateAsync({ phase });
  }, [executePhhaseMutation]);

  const initializeFlow = useCallback(async (data: any) => {
    return initializeFlowMutation.mutateAsync(data);
  }, [initializeFlowMutation]);

  return {
    flowState: flowState || null,
    isLoading,
    error: error as Error | null,
    isHealthy: healthStatus?.status === 'healthy',
    initializeFlow,
    executeFlowPhase,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    refreshFlow: async () => {
      await refreshFlow();
    },
    isExecutingPhase,
  };
}; 