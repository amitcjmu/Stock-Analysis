/**
 * Discovery Flow V2 Hook
 * Comprehensive React hook for V2 API integration with state management and real-time tracking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { 
  unifiedDiscoveryService,
  UnifiedDiscoveryFlowRequest,
  UnifiedDiscoveryFlowResponse
} from '../../services/discoveryUnifiedService';

// Types
interface DiscoveryFlowV2 {
  id: string;
  flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  import_session_id?: string;
  data_import_id?: string;
  flow_name: string;
  flow_description?: string;
  status: string;
  progress_percentage: number;
  phases: Record<string, boolean>;
  crewai_persistence_id?: string;
  learning_scope: string;
  memory_isolation_level: string;
  assessment_ready: boolean;
  is_mock: boolean;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
  migration_readiness_score: number;
  next_phase?: string;
  is_complete: boolean;
}

interface DiscoveryAssetV2 {
  id: string;
  discovery_flow_id: string;
  client_account_id: string;
  engagement_id: string;
  asset_name: string;
  asset_type?: string;
  asset_subtype?: string;
  raw_data: Record<string, any>;
  normalized_data?: Record<string, any>;
  discovered_in_phase: string;
  discovery_method?: string;
  confidence_score?: number;
  migration_ready: boolean;
  migration_complexity?: string;
  migration_priority?: number;
  asset_status: string;
  validation_status: string;
  is_mock: boolean;
  created_at?: string;
  updated_at?: string;
}

interface FlowCompletionValidation {
  flow_id: string;
  is_ready: boolean;
  validation_checks: Record<string, any>;
  warnings: string[];
  errors: string[];
  asset_summary: Record<string, any>;
  readiness_score: number;
}

interface AssessmentPackage {
  package_id: string;
  generated_at: string;
  discovery_flow: Record<string, any>;
  assets: any[];
  summary: Record<string, any>;
  migration_waves: any[];
  risk_assessment: Record<string, any>;
  recommendations: Record<string, any>;
}

interface UseDiscoveryFlowV2Options {
  enableRealTimeUpdates?: boolean;
  pollInterval?: number;
  autoRefresh?: boolean;
}

interface UseDiscoveryFlowV2Return {
  // Flow data
  flow: DiscoveryFlowV2 | null;
  assets: DiscoveryAssetV2[];
  
  // Loading states
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isCompleting: boolean;
  
  // Error states
  error: Error | null;
  
  // Flow operations
  createFlow: (data: CreateFlowData) => Promise<DiscoveryFlowV2>;
  updatePhase: (phase: string, data: any) => Promise<DiscoveryFlowV2>;
  completeFlow: () => Promise<DiscoveryFlowV2>;
  
  // Asset operations
  getAssets: () => Promise<DiscoveryAssetV2[]>;
  createAssetsFromDiscovery: () => Promise<any>;
  
  // Flow completion
  validateCompletion: () => Promise<FlowCompletionValidation>;
  getAssessmentReadyAssets: (filters?: any) => Promise<any>;
  generateAssessmentPackage: (selectedAssetIds?: string[]) => Promise<AssessmentPackage>;
  completeWithAssessment: (selectedAssetIds?: string[]) => Promise<any>;
  
  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
  
  // Progress tracking
  progressPercentage: number;
  currentPhase: string | null;
  completedPhases: string[];
  nextPhase: string | null;
  
  // Utilities
  refresh: () => void;
  reset: () => void;
}

interface CreateFlowData {
  flow_id: string;
  raw_data: any[];
  metadata?: Record<string, any>;
  import_session_id?: string;
  user_id?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const V2_API_BASE = `${API_BASE_URL}/api/v2/discovery-flows`;

// Default headers for multi-tenant context
const getDefaultHeaders = () => ({
  'Content-Type': 'application/json',
  'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',
  'X-Engagement-Id': '22222222-2222-2222-2222-222222222222'
});

// API functions
const apiClient = {
  async createFlow(data: CreateFlowData): Promise<DiscoveryFlowV2> {
    const response = await fetch(`${V2_API_BASE}/flows`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getFlow(flowId: string): Promise<DiscoveryFlowV2> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}`, {
      headers: getDefaultHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async updatePhase(flowId: string, phase: string, data: any): Promise<DiscoveryFlowV2> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/phase`, {
      method: 'PUT',
      headers: getDefaultHeaders(),
      body: JSON.stringify({ phase, phase_data: data }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update phase: ${response.statusText}`);
    }
    
    return response.json();
  },

  async completeFlow(flowId: string): Promise<DiscoveryFlowV2> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/complete`, {
      method: 'POST',
      headers: getDefaultHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to complete flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getAssets(flowId: string): Promise<DiscoveryAssetV2[]> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/assets`, {
      headers: getDefaultHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get assets: ${response.statusText}`);
    }
    
    return response.json();
  },

  async createAssetsFromDiscovery(flowId: string): Promise<any> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/create-assets`, {
      method: 'POST',
      headers: getDefaultHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create assets: ${response.statusText}`);
    }
    
    return response.json();
  },

  async validateCompletion(flowId: string): Promise<FlowCompletionValidation> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/validation`, {
      headers: getDefaultHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to validate completion: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getAssessmentReadyAssets(flowId: string, filters?: any): Promise<any> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    
    const url = `${V2_API_BASE}/flows/${flowId}/assessment-ready-assets${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await fetch(url, {
      headers: getDefaultHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get assessment-ready assets: ${response.statusText}`);
    }
    
    return response.json();
  },

  async generateAssessmentPackage(flowId: string, selectedAssetIds?: string[]): Promise<AssessmentPackage> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/assessment-package`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify({ selected_asset_ids: selectedAssetIds }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to generate assessment package: ${response.statusText}`);
    }
    
    return response.json();
  },

  async completeWithAssessment(flowId: string, selectedAssetIds?: string[]): Promise<any> {
    const response = await fetch(`${V2_API_BASE}/flows/${flowId}/complete-with-assessment`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify({ selected_asset_ids: selectedAssetIds }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to complete with assessment: ${response.statusText}`);
    }
    
    return response.json();
  },
};

/**
 * Main hook for Discovery Flow V2 operations
 */
export function useDiscoveryFlowV2(
  flowId?: string,
  options: UseDiscoveryFlowV2Options = {}
): UseDiscoveryFlowV2Return {
  const {
    enableRealTimeUpdates = false,
    pollInterval = 30000,
    autoRefresh = false
  } = options;

  // 🚨 DEBUG: Check for problematic flow ID
  const PROBLEM_FLOW_ID = '11055bdf-5e39-4e0d-913e-0c7080f82e2c';
  if (flowId === PROBLEM_FLOW_ID) {
    console.error('🚨 PROBLEM FLOW ID DETECTED:', {
      flowId,
      stackTrace: new Error().stack,
      component: 'useDiscoveryFlowV2'
    });
    // Don't proceed with the problematic flow ID
    return {
      flow: null,
      assets: [],
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isCompleting: false,
      error: new Error(`Flow ID ${flowId} does not exist in database`),
      createFlow: async () => { throw new Error('Invalid flow ID'); },
      updatePhase: async () => { throw new Error('Invalid flow ID'); },
      completeFlow: async () => { throw new Error('Invalid flow ID'); },
      getAssets: async () => [],
      createAssetsFromDiscovery: async () => { throw new Error('Invalid flow ID'); },
      validateCompletion: async () => { throw new Error('Invalid flow ID'); },
      getAssessmentReadyAssets: async () => { throw new Error('Invalid flow ID'); },
      generateAssessmentPackage: async () => { throw new Error('Invalid flow ID'); },
      completeWithAssessment: async () => { throw new Error('Invalid flow ID'); },
      subscribeToUpdates: () => {},
      unsubscribeFromUpdates: () => {},
      progressPercentage: 0,
      currentPhase: null,
      completedPhases: [],
      nextPhase: null,
      refresh: () => {},
      reset: () => {}
    };
  }

  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const lastSuccessfulFetch = useRef<number>(0);
  const consecutiveErrors = useRef<number>(0);

  // Query keys
  const flowQueryKey = ['discoveryFlowV2', flowId];
  const assetsQueryKey = ['discoveryFlowV2Assets', flowId];

  // Anti-polling safeguards
  const shouldPoll = useCallback(() => {
    if (!autoRefresh || !flowId) return false;
    
    // Stop polling if too many consecutive errors
    if (consecutiveErrors.current >= 3) {
      console.warn(`🚫 Stopping polling for flow ${flowId} due to consecutive errors`);
      return false;
    }
    
    // Exponential backoff after errors
    const backoffDelay = Math.min(pollInterval * Math.pow(2, consecutiveErrors.current), 300000); // Max 5 minutes
    const timeSinceLastFetch = Date.now() - lastSuccessfulFetch.current;
    
    return timeSinceLastFetch >= backoffDelay;
  }, [autoRefresh, flowId, pollInterval]);

  // Flow query with intelligent polling
  const {
    data: flow,
    isLoading,
    error: flowError,
    refetch: refetchFlow
  } = useQuery({
    queryKey: flowQueryKey,
    queryFn: async () => {
      if (!flowId) return null;
      
      try {
        const result = await apiClient.getFlow(flowId);
        consecutiveErrors.current = 0; // Reset error count on success
        lastSuccessfulFetch.current = Date.now();
        return result;
      } catch (error) {
        consecutiveErrors.current += 1;
        console.error(`❌ Flow fetch error (attempt ${consecutiveErrors.current}):`, error);
        
        // Stop polling after 3 consecutive errors
        if (consecutiveErrors.current >= 3) {
          console.warn(`🚫 Disabling polling for flow ${flowId} after 3 consecutive failures`);
        }
        throw error;
      }
    },
    enabled: !!flowId,
    refetchInterval: (query) => {
      // Only poll if explicitly enabled and conditions are met
      if (!shouldPoll()) return false;
      
      // Stop polling if flow is completed or failed
      const flowData = query.state.data;
      if (flowData?.status === 'completed' || flowData?.status === 'failed') {
        return false;
      }
      
      return pollInterval;
    },
    staleTime: 60000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    retry: (failureCount, error) => {
      // Limit retries and implement exponential backoff
      if (failureCount >= 3) return false;
      
      // Don't retry 404 errors (flow doesn't exist)
      if (error && ('status' in error && error.status === 404)) {
        console.warn(`🚫 Flow ${flowId} not found, stopping retries`);
        return false;
      }
      
      // Don't retry if error message indicates flow not found
      if (error && error.message && error.message.includes('Discovery flow not found')) {
        console.warn(`🚫 Flow ${flowId} not found (from message), stopping retries`);
        return false;
      }
      
      // Don't retry if response indicates flow not found
      if (error && error.message && error.message.includes('Failed to get flow')) {
        console.warn(`🚫 Flow ${flowId} fetch failed, stopping retries`);
        return false;
      }
      
      return true;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Assets query
  const {
    data: assets = [],
    refetch: refetchAssets
  } = useQuery({
    queryKey: assetsQueryKey,
    queryFn: () => flowId ? apiClient.getAssets(flowId) : [],
    enabled: !!flowId,
    staleTime: 30000,
  });

  // Mutations
  const createFlowMutation = useMutation({
    mutationFn: apiClient.createFlow,
    onSuccess: (data) => {
      queryClient.setQueryData(['discoveryFlowV2', data.flow_id], data);
      toast.success('Discovery flow created successfully');
    },
    onError: (error: Error) => {
      setError(error);
      toast.error(`Failed to create flow: ${error.message}`);
    },
  });

  const updatePhaseMutation = useMutation({
    mutationFn: ({ phase, data }: { phase: string; data: any }) =>
      flowId ? apiClient.updatePhase(flowId, phase, data) : Promise.reject(new Error('No flow ID')),
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      toast.success(`Phase ${data.next_phase || 'updated'} completed`);
    },
    onError: (error: Error) => {
      setError(error);
      toast.error(`Failed to update phase: ${error.message}`);
    },
  });

  const completeFlowMutation = useMutation({
    mutationFn: () =>
      flowId ? apiClient.completeFlow(flowId) : Promise.reject(new Error('No flow ID')),
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      toast.success('Discovery flow completed successfully');
    },
    onError: (error: Error) => {
      setError(error);
      toast.error(`Failed to complete flow: ${error.message}`);
    },
  });

  const createAssetsMutation = useMutation({
    mutationFn: () =>
      flowId ? apiClient.createAssetsFromDiscovery(flowId) : Promise.reject(new Error('No flow ID')),
    onSuccess: () => {
      refetchAssets();
      toast.success('Assets created successfully');
    },
    onError: (error: Error) => {
      setError(error);
      toast.error(`Failed to create assets: ${error.message}`);
    },
  });

  const completeWithAssessmentMutation = useMutation({
    mutationFn: (selectedAssetIds?: string[]) =>
      flowId ? apiClient.completeWithAssessment(flowId, selectedAssetIds) : Promise.reject(new Error('No flow ID')),
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      toast.success('Flow completed with assessment package generated');
    },
    onError: (error: Error) => {
      setError(error);
      toast.error(`Failed to complete with assessment: ${error.message}`);
    },
  });

  // WebSocket for real-time updates
  const subscribeToUpdates = useCallback(() => {
    if (!enableRealTimeUpdates || !flowId) return;

    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/discovery-flow/${flowId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'flow_update') {
          queryClient.setQueryData(flowQueryKey, data.payload);
        } else if (data.type === 'assets_update') {
          queryClient.setQueryData(assetsQueryKey, data.payload);
        }
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [enableRealTimeUpdates, flowId, queryClient, flowQueryKey, assetsQueryKey]);

  const unsubscribeFromUpdates = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Effect for WebSocket management
  useEffect(() => {
    if (enableRealTimeUpdates) {
      subscribeToUpdates();
    }

    return () => {
      unsubscribeFromUpdates();
    };
  }, [enableRealTimeUpdates, subscribeToUpdates, unsubscribeFromUpdates]);

  // Derived state
  const progressPercentage = flow?.progress_percentage || 0;
  const currentPhase = flow?.next_phase || null;
  const completedPhases = flow?.phases 
    ? Object.entries(flow.phases).filter(([_, completed]) => completed).map(([phase]) => phase)
    : [];
  const nextPhase = flow?.next_phase || null;

  // Utility functions
  const refresh = useCallback(() => {
    refetchFlow();
    refetchAssets();
  }, [refetchFlow, refetchAssets]);

  const reset = useCallback(() => {
    setError(null);
    queryClient.removeQueries({ queryKey: flowQueryKey });
    queryClient.removeQueries({ queryKey: assetsQueryKey });
  }, [queryClient, flowQueryKey, assetsQueryKey]);

  // API wrapper functions
  const validateCompletion = useCallback(async (): Promise<FlowCompletionValidation> => {
    if (!flowId) throw new Error('No flow ID');
    return apiClient.validateCompletion(flowId);
  }, [flowId]);

  const getAssessmentReadyAssets = useCallback(async (filters?: any) => {
    if (!flowId) throw new Error('No flow ID');
    return apiClient.getAssessmentReadyAssets(flowId, filters);
  }, [flowId]);

  const generateAssessmentPackage = useCallback(async (selectedAssetIds?: string[]): Promise<AssessmentPackage> => {
    if (!flowId) throw new Error('No flow ID');
    return apiClient.generateAssessmentPackage(flowId, selectedAssetIds);
  }, [flowId]);

  return {
    // Flow data
    flow: flow || null,
    assets,

    // Loading states
    isLoading,
    isCreating: createFlowMutation.isPending,
    isUpdating: updatePhaseMutation.isPending,
    isCompleting: completeFlowMutation.isPending || completeWithAssessmentMutation.isPending,

    // Error states
    error: error || flowError,

    // Flow operations
    createFlow: createFlowMutation.mutateAsync,
    updatePhase: (phase: string, data: any) => updatePhaseMutation.mutateAsync({ phase, data }),
    completeFlow: completeFlowMutation.mutateAsync,

    // Asset operations
    getAssets: () => flowId ? apiClient.getAssets(flowId) : Promise.resolve([]),
    createAssetsFromDiscovery: createAssetsMutation.mutateAsync,

    // Flow completion
    validateCompletion,
    getAssessmentReadyAssets,
    generateAssessmentPackage,
    completeWithAssessment: completeWithAssessmentMutation.mutateAsync,

    // Real-time updates
    subscribeToUpdates,
    unsubscribeFromUpdates,

    // Progress tracking
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase,

    // Utilities
    refresh,
    reset,
  };
}

// Additional utility hooks
export function useDiscoveryFlowList() {
  return useQuery({
    queryKey: ['discoveryFlowsV2'],
    queryFn: async () => {
      const response = await fetch(`${V2_API_BASE}/flows`, {
        headers: getDefaultHeaders()
      });
      if (!response.ok) {
        throw new Error(`Failed to get flows: ${response.statusText}`);
      }
      return response.json();
    },
    staleTime: 60000,
  });
}

export function useDiscoveryFlowHealth() {
  return useQuery({
    queryKey: ['discoveryFlowV2Health'],
    queryFn: async () => {
      const response = await fetch(`${V2_API_BASE}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }
      return response.json();
    },
    staleTime: 30000,
    refetchInterval: 30000,
  });
} 