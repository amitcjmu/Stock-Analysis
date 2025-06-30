import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { SessionToFlowMigration } from '../utils/migration/sessionToFlow';
import { FlowIdentifier, MigrationContext } from '../types/discovery';

// Types for UnifiedDiscoveryFlow
interface UnifiedDiscoveryFlowState {
  flow_id: string;
  session_id?: string; // @deprecated - Use flow_id instead
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
  // Migration helpers
  flowIdentifier: FlowIdentifier | null;
  migrationContext: MigrationContext;
}

// API functions for UnifiedDiscoveryFlow
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const unifiedDiscoveryAPI = {
  async getFlowStatus(flowId: string): Promise<UnifiedDiscoveryFlowState> {
    const response = await fetch(`${API_BASE}/api/v1/unified-discovery/flow/status/${flowId}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': '44444444-4444-4444-4444-444444444444',
        'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-ID': '22222222-2222-2222-2222-222222222222',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get flow status: ${response.statusText}`);
    }
    
    return response.json();
  },

  async initializeFlow(data: any): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/unified-discovery/flow/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': '44444444-4444-4444-4444-444444444444',
        'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-ID': '22222222-2222-2222-2222-222222222222',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to initialize flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async executePhase(phase: string, data: any = {}): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/unified-discovery/flow/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': '44444444-4444-4444-4444-444444444444',
        'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-ID': '22222222-2222-2222-2222-222222222222',
      },
      body: JSON.stringify({ phase, data }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to execute phase ${phase}: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getHealthStatus(): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/unified-discovery/health`, {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': '44444444-4444-4444-4444-444444444444',
        'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-ID': '22222222-2222-2222-2222-222222222222',
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

  // Initialize migration on component mount
  useEffect(() => {
    SessionToFlowMigration.initialize();
  }, []);

  // Get migration context
  const migrationContext = useMemo(() => {
    return SessionToFlowMigration.getMigrationContext();
  }, []);

  // Get current flow identifier from URL or localStorage with migration support
  const flowIdentifier = useMemo((): FlowIdentifier | null => {
    try {
      // Try to get from URL parameters (both flow_id and session_id for backward compatibility)
      const urlParams = new URLSearchParams(window.location.search);
      const urlFlowId = urlParams.get('flow_id') || urlParams.get('flowId');
      const urlSessionId = urlParams.get('session_id') || urlParams.get('sessionId');
      
      if (urlFlowId) {
        const identifier = SessionToFlowMigration.createFlowIdentifier(urlFlowId);
        SessionToFlowMigration.storeIdentifier(identifier.flowId, true);
        return identifier;
      }
      
      if (urlSessionId) {
        SessionToFlowMigration.logDeprecationWarning('useUnifiedDiscoveryFlow', urlSessionId);
        const identifier = SessionToFlowMigration.createFlowIdentifier(urlSessionId);
        SessionToFlowMigration.storeIdentifier(identifier.flowId, true);
        return identifier;
      }

      // Extract from path (e.g., /discovery/attribute-mapping/flow-123 or session-123)
      const pathMatch = window.location.pathname.match(/\/discovery\/[^\/]+\/([^\/]+)/);
      if (pathMatch) {
        const pathIdentifier = pathMatch[1];
        const identifier = SessionToFlowMigration.createFlowIdentifier(pathIdentifier);
        SessionToFlowMigration.storeIdentifier(identifier.flowId, true);
        return identifier;
      }

      // Try to get from localStorage using migration utility
      const currentIdentifier = SessionToFlowMigration.getIdentifier();
      if (currentIdentifier) {
        return SessionToFlowMigration.createFlowIdentifier(currentIdentifier);
      }

      return null;
    } catch (error) {
      console.error('Error getting flow identifier:', error);
      return null;
    }
  }, []);

  // Get the actual identifier to use for API calls
  const currentIdentifier = useMemo(() => {
    if (!flowIdentifier) return null;
    
    return migrationContext.useFlowId ? flowIdentifier.flowId : flowIdentifier.sessionId || flowIdentifier.flowId;
  }, [flowIdentifier, migrationContext]);

  // Flow state query
  const {
    data: flowState,
    isLoading,
    error,
    refetch: refreshFlow,
  } = useQuery({
    queryKey: ['unifiedDiscoveryFlow', currentIdentifier, migrationContext.useFlowId],
    queryFn: () => currentIdentifier ? unifiedDiscoveryAPI.getFlowStatus(currentIdentifier) : null,
    enabled: !!currentIdentifier,
    refetchInterval: false, // DISABLED: No automatic polling - use manual refresh
    refetchIntervalInBackground: false,
    staleTime: 30000, // Consider data fresh for 30 seconds
  });

  // Health check query
  const { data: healthStatus } = useQuery({
    queryKey: ['unifiedDiscoveryFlowHealth'],
    queryFn: unifiedDiscoveryAPI.getHealthStatus,
    refetchInterval: false, // DISABLED: No automatic health polling
    staleTime: 300000, // Consider health data fresh for 5 minutes
  });

  // Initialize flow mutation
  const initializeFlowMutation = useMutation({
    mutationFn: unifiedDiscoveryAPI.initializeFlow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow'] });
      
      // Store identifier using migration utility
      if (data.flow_id) {
        SessionToFlowMigration.storeIdentifier(data.flow_id, true);
      } else if (data.session_id) {
        // Legacy support
        SessionToFlowMigration.logDeprecationWarning('initializeFlow response', data.session_id);
        const flowId = SessionToFlowMigration.convertSessionToFlowId(data.session_id);
        SessionToFlowMigration.storeIdentifier(flowId, true);
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
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow', currentIdentifier, migrationContext.useFlowId] });
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
    // Migration helpers
    flowIdentifier,
    migrationContext,
  };
}; 