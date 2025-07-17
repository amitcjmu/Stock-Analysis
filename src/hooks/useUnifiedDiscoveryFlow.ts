import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import masterFlowServiceExtended from '../services/api/masterFlowService.extensions';
import type { FlowStatusResponse } from '../services/api/masterFlowService';
import { discoveryFlowService } from '../services/api/discoveryFlowService';
import type { DiscoveryFlowStatusResponse } from '../services/api/discoveryFlowService';

// Types for UnifiedDiscoveryFlow
interface UnifiedDiscoveryFlowState {
  flow_id: string;
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
  agent_insights: any[];
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
  executeFlowPhase: (phase: string, data?: any) => Promise<any>;
  getPhaseData: (phase: string) => any;
  isPhaseComplete: (phase: string) => boolean;
  canProceedToPhase: (phase: string) => boolean;
  refreshFlow: () => Promise<void>;
  isExecutingPhase: boolean;
  flowId: string | null;
}

// Use discovery flow service for operational status (ADR-012)
const createUnifiedDiscoveryAPI = (clientAccountId: string, engagementId: string) => ({
  async getFlowStatus(flowId: string): Promise<UnifiedDiscoveryFlowState> {
    console.log(`🔍 [DEBUG] useUnifiedDiscoveryFlow.getFlowStatus called for flowId: ${flowId}`);
    
    // ADR-012: Use discovery flow service for operational status
    // This provides child flow status for operational decisions
    const response: DiscoveryFlowStatusResponse = await discoveryFlowService.getOperationalStatus(flowId, clientAccountId, engagementId);
    
    console.log(`🔍 [DEBUG] Raw API response:`, response);
    console.log(`🔍 [DEBUG] Field mappings in response:`, response.field_mappings);
    console.log(`🔍 [DEBUG] Field mappings type:`, typeof response.field_mappings);
    console.log(`🔍 [DEBUG] Field mappings length:`, Array.isArray(response.field_mappings) ? response.field_mappings.length : 'not array');
    console.log(`🔍 [DEBUG] Raw data in response:`, response.raw_data);
    console.log(`🔍 [DEBUG] Raw data length:`, Array.isArray(response.raw_data) ? response.raw_data.length : 'not array');
    console.log(`🔍 [DEBUG] Raw data type:`, typeof response.raw_data);
    
    // Map discovery flow response to frontend format
    // ADR-012: This now uses child flow status for operational decisions
    const mappedResponse = {
      flow_id: response.flow_id || flowId,
      client_account_id: clientAccountId,
      engagement_id: engagementId || '',
      user_id: '',
      current_phase: response.current_phase || '',
      phase_completion: {
        data_import: response.summary?.data_import_completed || false,
        field_mapping: response.summary?.field_mapping_completed || false,
        data_cleansing: response.summary?.data_cleansing_completed || false,
        asset_inventory: response.summary?.asset_inventory_completed || false,
        dependency_analysis: response.summary?.dependency_analysis_completed || false,
        tech_debt_analysis: response.summary?.tech_debt_assessment_completed || false,
      },
      crew_status: {}, // Will be populated by discovery flow service
      raw_data: response.raw_data || [], // ADR-012: Use actual raw data from discovery flow response
      field_mappings: response.field_mappings || {},
      cleaned_data: response.cleaned_data || [],
      asset_inventory: response.asset_inventory || {},
      dependencies: response.dependencies || {},
      technical_debt: response.technical_debt || {},
      agent_insights: response.agent_insights || [],
      status: response.status || 'unknown',
      progress_percentage: response.progress_percentage || 0,
      errors: response.errors || [],
      warnings: response.warnings || [],
      created_at: response.created_at || '',
      updated_at: response.updated_at || '',
      // Additional fields from discovery flow
      data_cleansing_results: response.cleaned_data ? { cleaned_data: response.cleaned_data } : {},
      inventory_results: response.asset_inventory || {},
      dependency_results: response.dependencies || {},
      tech_debt_results: response.technical_debt || {}
    };
    
    console.log(`🔍 [DEBUG] Mapped response field_mappings:`, mappedResponse.field_mappings);
    console.log(`🔍 [DEBUG] Full mapped response:`, mappedResponse);
    
    return mappedResponse;
  },

  async initializeFlow(data: any): Promise<any> {
    return masterFlowServiceExtended.initializeDiscoveryFlow(clientAccountId, engagementId, data);
  },

  async executePhase(flowId: string, phase: string, data: any = {}): Promise<any> {
    // ADR-012: Use discovery flow service for operational phase execution
    return discoveryFlowService.executePhase(flowId, phase, data, clientAccountId, engagementId);
  },

  async getHealthStatus(): Promise<any> {
    return { status: 'healthy' }; // Mock for now
  },
});

/**
 * Unified Discovery Flow Hook
 * 
 * This is the single source of truth for all discovery flow interactions.
 * Connects frontend to the UnifiedDiscoveryFlow CrewAI execution engine.
 */
export const useUnifiedDiscoveryFlow = (providedFlowId?: string | null): UseUnifiedDiscoveryFlowReturn => {
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  const [isExecutingPhase, setIsExecutingPhase] = useState(false);
  
  // Create API instance with context
  const unifiedDiscoveryAPI = useMemo(() => {
    // Require proper client and engagement context
    if (!client?.id || !engagement?.id) {
      console.warn('Missing client or engagement context for unified discovery flow');
      return null;
    }
    
    return createUnifiedDiscoveryAPI(client.id, engagement.id);
  }, [client, engagement]);

  // Use provided flowId or try to get from URL/localStorage
  const flowId = useMemo((): string | null => {
    // If flowId is provided, use it
    if (providedFlowId) {
      return providedFlowId;
    }
    
    try {
      // Try to get from URL parameters
      const urlParams = new URLSearchParams(window.location.search);
      const urlFlowId = urlParams.get('flow_id') || urlParams.get('flowId');
      
      if (urlFlowId) {
        localStorage.setItem('currentFlowId', urlFlowId);
        return urlFlowId;
      }

      // Extract from path (e.g., /discovery/attribute-mapping/flow-123 or /discovery/attribute-mapping/uuid)
      const pathMatch = window.location.pathname.match(/\/discovery\/[^\/]+\/([a-f0-9-]+)/);
      if (pathMatch) {
        const pathFlowId = pathMatch[1];
        localStorage.setItem('currentFlowId', pathFlowId);
        return pathFlowId;
      }

      // Only use localStorage flow ID if we're on a page that expects a flow ID
      // Don't load flow status on cmdb-import page unless explicitly requested
      if (window.location.pathname.includes('/discovery/cmdb-import')) {
        return null;
      }

      // Try to get from localStorage for other pages
      const storedFlowId = localStorage.getItem('currentFlowId');
      if (storedFlowId) {
        return storedFlowId;
      }

      return null;
    } catch (error) {
      console.error('Error getting flow ID:', error);
      return null;
    }
  }, [providedFlowId]);

  // Track polling attempts
  const [pollingAttempts, setPollingAttempts] = useState(0);
  const [pollingEnabled, setPollingEnabled] = useState(true);
  const MAX_POLLING_ATTEMPTS = 15; // 15 attempts * 5 seconds = 75 seconds max

  // Flow state query
  const {
    data: flowState,
    isLoading,
    error,
    refetch: refreshFlow,
  } = useQuery({
    queryKey: ['unifiedDiscoveryFlow', flowId, client?.id, engagement?.id],
    queryFn: () => flowId && unifiedDiscoveryAPI ? unifiedDiscoveryAPI.getFlowStatus(flowId) : null,
    enabled: !!flowId && !!unifiedDiscoveryAPI && !!client?.id && !!engagement?.id && flowId !== 'none',
    refetchInterval: (query) => {
      // Stop polling if disabled or max attempts reached
      if (!pollingEnabled || pollingAttempts >= MAX_POLLING_ATTEMPTS) {
        return false;
      }

      const state = query.state.data as any;
      
      // Poll when flow is active AND not waiting for approval
      if ((state?.status === 'running' || state?.status === 'in_progress' || 
          state?.status === 'processing' || state?.status === 'active') &&
          state?.status !== 'waiting_for_approval' &&
          !state?.awaitingUserApproval) {
        setPollingAttempts(prev => prev + 1);
        return 90000; // Poll every 90 seconds when flow is active (increased from 60s to reduce load)
      }
      
      // Stop polling for terminal states or when waiting for approval
      if (state?.status === 'completed' || state?.status === 'failed' || 
          state?.status === 'cancelled' || state?.status === 'waiting_for_approval' ||
          state?.awaitingUserApproval) {
        setPollingEnabled(false);
        return false;
      }
      
      return false; // Stop polling for other states
    },
    refetchIntervalInBackground: false, // Don't poll in background
    refetchOnMount: false, // Don't refetch on mount if data exists
    refetchOnWindowFocus: false, // Don't refetch on window focus to reduce API calls
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes (increased from 30s)
    cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
    retry: (failureCount, error: any) => {
      // Max 2 retries with exponential backoff
      if (failureCount >= 2) {
        return false;
      }
      
      // Retry 429 errors and network failures
      if (error?.status === 429 || error?.message?.includes('network') || error?.message?.includes('fetch')) {
        return true;
      }
      
      return false;
    },
    retryDelay: (attemptIndex) => Math.min(2000 * Math.pow(2, attemptIndex), 8000), // 2s, 4s, 8s max
    onError: (error: any) => {
      // Stop polling on error
      setPollingEnabled(false);
      
      // Clear invalid flow ID from localStorage on 404 error
      if (error?.status === 404 || error?.message?.includes('404') || error?.message?.includes('Not Found')) {
        console.warn(`Flow ID ${flowId} not found, clearing from localStorage`);
        if (flowId) {
          localStorage.removeItem('currentFlowId');
        }
      }
    }
  });

  // Reset polling when flow ID changes
  useEffect(() => {
    setPollingAttempts(0);
    setPollingEnabled(true);
  }, [flowId]);

  // Health check query - DISABLED: endpoint doesn't exist
  const healthStatus = { status: 'healthy' }; // Mock healthy status
  /*
  const { data: healthStatus } = useQuery({
    queryKey: ['unifiedDiscoveryFlowHealth'],
    queryFn: unifiedDiscoveryAPI.getHealthStatus,
    refetchInterval: false, // DISABLED: No automatic health polling
    staleTime: 300000, // Consider health data fresh for 5 minutes
  });
  */

  // Initialize flow mutation
  const initializeFlowMutation = useMutation({
    mutationFn: (data: any) => {
      if (!unifiedDiscoveryAPI) throw new Error('No API instance available');
      return unifiedDiscoveryAPI.initializeFlow(data);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow'] });
      
      // Store flow ID
      if (data.flow_id) {
        localStorage.setItem('currentFlowId', data.flow_id);
      }
    },
  });

  // Execute phase mutation
  const executePhhaseMutation = useMutation({
    mutationFn: ({ phase, data }: { phase: string; data?: any }) => {
      if (!flowId) throw new Error('No flow ID available');
      if (!unifiedDiscoveryAPI) throw new Error('No API instance available');
      return unifiedDiscoveryAPI.executePhase(flowId, phase, data);
    },
    onMutate: () => {
      setIsExecutingPhase(true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow', flowId] });
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

  const executeFlowPhase = useCallback(async (phase: string, data?: any) => {
    return executePhhaseMutation.mutateAsync({ phase, data });
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
    flowId,
    pollingStatus: {
      enabled: pollingEnabled,
      attempts: pollingAttempts,
      maxAttempts: MAX_POLLING_ATTEMPTS,
      hasReachedMax: pollingAttempts >= MAX_POLLING_ATTEMPTS
    }
  };
}; 