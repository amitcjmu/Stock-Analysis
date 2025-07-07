import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import masterFlowServiceExtended from '../services/api/masterFlowService.extensions';

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
  flowId: string | null;
}

// Use extended master flow service for all API calls
const createUnifiedDiscoveryAPI = (clientAccountId: string, engagementId: string) => ({
  async getFlowStatus(flowId: string): Promise<UnifiedDiscoveryFlowState> {
    const response = await masterFlowServiceExtended.getFlowStatus(flowId, clientAccountId, engagementId);
    return response as any; // Cast to expected type
  },

  async initializeFlow(data: any): Promise<any> {
    return masterFlowServiceExtended.initializeDiscoveryFlow(clientAccountId, engagementId, data);
  },

  async executePhase(flowId: string, phase: string, data: any = {}): Promise<any> {
    // Now using the extended service with proper phase execution
    return masterFlowServiceExtended.executePhase(flowId, phase, data, clientAccountId, engagementId);
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
    // Use demo UUIDs as fallback
    const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
    const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
    return createUnifiedDiscoveryAPI(clientAccountId, engagementId);
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

      // Try to get from localStorage
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

  // Flow state query
  const {
    data: flowState,
    isLoading,
    error,
    refetch: refreshFlow,
  } = useQuery({
    queryKey: ['unifiedDiscoveryFlow', flowId],
    queryFn: () => flowId ? unifiedDiscoveryAPI.getFlowStatus(flowId) : null,
    enabled: !!flowId,
    refetchInterval: false, // DISABLED: No automatic polling - use manual refresh
    refetchIntervalInBackground: false,
    staleTime: 30000, // Consider data fresh for 30 seconds
  });

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
    mutationFn: unifiedDiscoveryAPI.initializeFlow,
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
    flowId,
  };
}; 