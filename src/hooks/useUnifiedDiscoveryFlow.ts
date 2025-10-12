import { useState } from 'react'
import { useCallback, useEffect, useMemo } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext';
import masterFlowServiceExtended from '../services/api/masterFlowService.extensions';
import type { FlowStatusResponse } from '../services/api/masterFlowService';
import { masterFlowService } from '../services/api/masterFlowService';
import type { FlowStatusResponse } from '../services/api/masterFlowService';
import type {
  FlowInitializationData,
  PhaseExecutionData,
  PhaseExecutionResult,
  DataRecord,
  AssetProperties
} from '../types/hooks/flow-types';
import SecureLogger from '../utils/secureLogger';
import SecureStorage from '../utils/secureStorage';

// Types for UnifiedDiscoveryFlow
interface CrewStatus {
  crew_id: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  last_activity?: string;
  error_message?: string;
}

interface RawDataItem {
  id: string;
  source: string;
  data: DataRecord;
  timestamp: string;
  validation_status?: 'pending' | 'valid' | 'invalid';
}

interface FieldMapping {
  source_field: string;
  target_field: string;
  mapping_type: 'direct' | 'transform' | 'calculated';
  transformation_rule?: string;
  confidence: number;
}

interface CleanedDataItem {
  id: string;
  original_id: string;
  cleaned_data: DataRecord;
  cleaning_rules_applied: string[];
  quality_score: number;
}

interface AssetInventoryItem {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  properties: AssetProperties;
  status: string;
  discovered_at: string;
}

interface DependencyRelation {
  source_asset: string;
  target_asset: string;
  dependency_type: 'network' | 'data' | 'service' | 'infrastructure';
  strength: 'weak' | 'medium' | 'strong';
  bidirectional: boolean;
}

interface TechnicalDebtItem {
  debt_id: string;
  category: 'security' | 'performance' | 'maintainability' | 'reliability';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_assets: string[];
  remediation_effort: number;
}

interface AgentInsight {
  insight_id: string;
  agent_name: string;
  insight_type: 'recommendation' | 'warning' | 'observation';
  content: string;
  confidence: number;
  relevant_assets: string[];
  timestamp: string;
}

interface UnifiedDiscoveryFlowState {
  flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  phase_state?: Record<string, unknown>;  // CC: Added for conflict resolution tracking
  crew_status: Record<string, CrewStatus>;
  raw_data: RawDataItem[];
  field_mappings: Record<string, FieldMapping>;
  cleaned_data: CleanedDataItem[];
  asset_inventory: Record<string, AssetInventoryItem>;
  dependencies: Record<string, DependencyRelation>;
  technical_debt: Record<string, TechnicalDebtItem>;
  agent_insights: AgentInsight[];
  status: string;
  progress_percentage: number;
  errors: string[];
  warnings: string[];
  created_at: string;
  updated_at: string;
  // Additional properties that might be present
  data_cleansing_results?: {
    quality_issues: unknown[];
    recommendations: unknown[];
    metadata?: {
      original_records: number;
    };
  };
  data_cleansing?: {
    quality_issues: unknown[];
    recommendations: unknown[];
    metadata?: {
      original_records: number;
    };
  };
  results?: {
    data_cleansing: {
      quality_issues: unknown[];
      recommendations: unknown[];
      metadata?: {
        original_records: number;
      };
    };
  };
  import_metadata?: {
    record_count: number;
  };
}

interface FlowInitializationData {
  data_sources?: string[];
  initial_configuration?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

interface PhaseExecutionData {
  phase_specific_data?: Record<string, unknown>;
  options?: Record<string, unknown>;
}

interface PhaseData {
  phase_name: string;
  data: DataRecord;
  completion_status: boolean;
  metadata?: Record<string, unknown>;
}

interface UseUnifiedDiscoveryFlowReturn {
  flowState: UnifiedDiscoveryFlowState | null;
  isLoading: boolean;
  error: Error | null;
  isHealthy: boolean;
  initializeFlow: (data: FlowInitializationData) => Promise<{ flow_id: string; status: string }>;
  executeFlowPhase: (phase: string, data?: PhaseExecutionData) => Promise<PhaseExecutionResult>;
  getPhaseData: (phase: string) => PhaseData | null;
  isPhaseComplete: (phase: string) => boolean;
  canProceedToPhase: (phase: string) => boolean;
  refreshFlow: () => Promise<void>;
  isExecutingPhase: boolean;
  flowId: string | null;
}

// Use discovery flow service for operational status (ADR-012)
const createUnifiedDiscoveryAPI = (clientAccountId: string, engagementId: string) => ({
  async getFlowStatus(flowId: string): Promise<UnifiedDiscoveryFlowState> {
    SecureLogger.debug(`useUnifiedDiscoveryFlow.getFlowStatus called`);

    // ADR-012: Use discovery flow service for operational status
    // This provides child flow status for operational decisions
    const response: FlowStatusResponse = await masterFlowService.getFlowStatus(flowId, clientAccountId, engagementId);

    SecureLogger.debug('Discovery flow API response received', {
      hasFieldMappings: !!response.field_mappings,
      fieldMappingsType: typeof response.field_mappings,
      fieldMappingsIsArray: Array.isArray(response.field_mappings),
      hasRawData: !!response.raw_data,
      rawDataType: typeof response.raw_data,
      rawDataIsArray: Array.isArray(response.raw_data)
    });

    // Map discovery flow response to frontend format
    // ADR-012: This now uses child flow status for operational decisions

    // Enhanced logging for debugging data mapping issues
    SecureLogger.debug('Processing discovery flow response for mapping', {
      responseKeysCount: Object.keys(response).length,
      rawDataType: typeof response.raw_data,
      rawDataLength: Array.isArray(response.raw_data) ? response.raw_data.length : 0,
      fieldMappingsType: typeof response.field_mappings,
      fieldMappingsCount: response.field_mappings ? Object.keys(response.field_mappings).length : 0,
      cleanedDataType: typeof response.cleaned_data,
      cleanedDataLength: Array.isArray(response.cleaned_data) ? response.cleaned_data.length : 0,
      hasSummary: !!response.summary
    });

    // Extract raw data from various possible locations in the response
    let rawData = [];
    if (Array.isArray(response.raw_data) && response.raw_data.length > 0) {
      rawData = response.raw_data;
      SecureLogger.debug(`Using direct raw_data: ${rawData.length} items`);
    } else if (response.data?.raw_data && Array.isArray(response.data.raw_data)) {
      rawData = response.data.raw_data;
      SecureLogger.debug(`Using nested data.raw_data: ${rawData.length} items`);
    } else if (response.summary?.total_records > 0) {
      // If we have a record count but no raw data, create placeholder entries for UI purposes
      const recordCount = response.summary.total_records;
      rawData = Array(Math.min(recordCount, 3)).fill(null).map((_, index) => ({
        id: `placeholder-${index}`,
        record_number: index + 1,
        status: 'processed',
        metadata: { source: 'discovery_flow', total_available: recordCount }
      }));
      SecureLogger.debug(`Created placeholder raw_data from summary: ${rawData.length} items for ${recordCount} total records`);
    }

    // Extract field mappings from various possible locations
    let fieldMappings = {};
    if (response.field_mappings && typeof response.field_mappings === 'object') {
      if (Array.isArray(response.field_mappings)) {
        // Convert array of field mappings to object format
        fieldMappings = response.field_mappings.reduce((acc, mapping) => {
          if (mapping.source_field && mapping.target_field) {
            acc[mapping.source_field] = {
              source_field: mapping.source_field,
              target_field: mapping.target_field,
              mapping_type: mapping.mapping_type || 'direct',
              transformation_rule: mapping.transformation_rule,
              confidence: mapping.confidence_score || mapping.confidence || 1.0
            };
          }
          return acc;
        }, {});
        SecureLogger.debug(`Converted array field_mappings to object: ${Object.keys(fieldMappings).length} mappings`);
      } else {
        fieldMappings = response.field_mappings;
        SecureLogger.debug(`Using direct field_mappings object: ${Object.keys(fieldMappings).length} mappings`);
      }
    } else if (response.data?.field_mappings) {
      fieldMappings = response.data.field_mappings;
      SecureLogger.debug(`Using nested data.field_mappings: ${Object.keys(fieldMappings).length} mappings`);
    }

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
      phase_state: response.phase_state || {},  // CC: Added for conflict resolution tracking
      crew_status: {}, // Will be populated by discovery flow service
      raw_data: rawData, // Enhanced raw data extraction
      field_mappings: fieldMappings, // Enhanced field mappings extraction
      cleaned_data: response.cleaned_data || [],
      asset_inventory: response.asset_inventory || {},
      dependencies: response.dependencies || {},
      // CRITICAL FIX: Map dependency_analysis data for Dependencies page
      dependency_analysis: response.dependency_analysis || response.dependencies || {},
      technical_debt: response.tech_debt_analysis || {},
      agent_insights: response.agent_insights || [],
      status: response.status || 'unknown',
      progress_percentage: response.progress_percentage || 0,
      errors: response.errors || [],
      warnings: response.warnings || [],
      created_at: response.created_at || '',
      updated_at: response.updated_at || '',
      // Additional fields from discovery flow with enhanced data extraction
      data_cleansing_results: response.cleaned_data ? { cleaned_data: response.cleaned_data } : {},
      inventory_results: response.asset_inventory || {},
      dependency_results: response.dependency_analysis || response.dependencies || {},
      tech_debt_results: response.tech_debt_analysis || {},
      // CRITICAL FIX: Add results object for compatibility with Dependencies page
      results: {
        dependency_analysis: response.dependency_analysis || response.dependencies || {},
        asset_inventory: response.asset_inventory || {},
        data_cleansing: response.cleaned_data ? { cleaned_data: response.cleaned_data } : {},
        tech_debt_analysis: response.tech_debt_analysis || {}
      },
      // Add import metadata for data availability detection
      import_metadata: response.summary ? {
        record_count: response.summary.total_records || 0,
        records_processed: response.summary.records_processed || 0,
        quality_score: response.summary.quality_score || 0
      } : {}
    };

    SecureLogger.debug('Mapped response field_mappings', {
      fieldMappingsCount: Object.keys(mappedResponse.field_mappings).length
    });
    SecureLogger.debug('Discovery flow response mapping completed', {
      flowId: mappedResponse.flow_id,
      currentPhase: mappedResponse.current_phase,
      status: mappedResponse.status,
      progressPercentage: mappedResponse.progress_percentage
    });

    return mappedResponse;
  },

  async initializeFlow(data: FlowInitializationData): Promise<{
    flow_id: string;
    status: string;
    message?: string;
  }> {
    return masterFlowServiceExtended.initializeDiscoveryFlow(clientAccountId, engagementId, data);
  },

  async executePhase(flowId: string, phase: string, data: PhaseExecutionData = {}): Promise<{
    success: boolean;
    phase: string;
    status: 'started' | 'completed' | 'failed';
    message?: string;
    data?: Record<string, unknown>;
    estimated_duration?: number;
    errors?: string[];
  }> {
    // ADR-012: Use discovery flow service for operational phase execution
    return masterFlowService.executePhase(flowId, phase, data, clientAccountId, engagementId);
  },

  async getHealthStatus(): Promise<{
    status: 'healthy' | 'unhealthy' | 'degraded';
    message?: string;
    checks?: Record<string, boolean>;
  }> {
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
      SecureLogger.warn('Missing client or engagement context for unified discovery flow');
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
      // Try to get from URL parameters with validation
      const urlParams = new URLSearchParams(window.location.search);
      const rawUrlFlowId = urlParams.get('flow_id') || urlParams.get('flowId');

      if (rawUrlFlowId) {
        const validatedUrlFlowId = SecureStorage.validateUrlFlowId(rawUrlFlowId);
        if (validatedUrlFlowId && SecureStorage.setFlowId(validatedUrlFlowId)) {
          return validatedUrlFlowId;
        }
      }

      // Extract from path with validation (e.g., /discovery/attribute-mapping/flow-123 or /discovery/attribute-mapping/uuid)
      const pathMatch = window.location.pathname.match(/\/discovery\/[^/]+\/([a-f0-9-]+)/);
      if (pathMatch) {
        const rawPathFlowId = pathMatch[1];
        const validatedPathFlowId = SecureStorage.validateUrlFlowId(rawPathFlowId);
        if (validatedPathFlowId && SecureStorage.setFlowId(validatedPathFlowId)) {
          return validatedPathFlowId;
        }
      }

      // Only use localStorage flow ID if we're on a page that expects a flow ID
      // Don't load flow status on cmdb-import page unless explicitly requested
      if (window.location.pathname.includes('/discovery/cmdb-import')) {
        return null;
      }

      // Try to get from localStorage for other pages
      const storedFlowId = SecureStorage.getFlowId();
      if (storedFlowId) {
        return storedFlowId;
      }

      return null;
    } catch (error) {
      SecureLogger.error('Error getting flow ID', error);
      return null;
    }
  }, [providedFlowId]);

  // Track polling attempts
  const [pollingAttempts, setPollingAttempts] = useState(0);
  const [pollingEnabled, setPollingEnabled] = useState(true);
  const MAX_POLLING_ATTEMPTS = 15; // 15 attempts * 5 seconds = 75 seconds max

  // Flow state query with 404 error handling
  const {
    data: flowState,
    isLoading,
    error,
    refetch: refreshFlow,
  } = useQuery({
    queryKey: ['unifiedDiscoveryFlow', flowId, client?.id, engagement?.id],
    queryFn: async () => {
      if (!flowId || !unifiedDiscoveryAPI) return null;

      // Simply return the API call result, handle errors in onError callback
      return await unifiedDiscoveryAPI.getFlowStatus(flowId);
    },
    enabled: !!flowId && !!unifiedDiscoveryAPI && !!client?.id && !!engagement?.id && flowId !== 'none' &&
             // Ensure flow ID is a valid UUID format (not an import ID)
             /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(flowId),
    refetchInterval: (query) => {
      // Stop polling if disabled or max attempts reached
      if (!pollingEnabled || pollingAttempts >= MAX_POLLING_ATTEMPTS) {
        return false;
      }

      const state = query.state.data as UnifiedDiscoveryFlowState | null;

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
    retry: (failureCount, error: Error | unknown) => {
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
    onError: (error: Error | unknown) => {
      // Stop polling on error
      setPollingEnabled(false);

      // Clear invalid flow ID from localStorage on 404 error
      const errorObj = error as { status?: number; response?: { status?: number }; message?: string };
      if (errorObj?.status === 404 || errorObj?.response?.status === 404 ||
          errorObj?.message?.includes('404') || errorObj?.message?.includes('Not Found')) {
        SecureLogger.warn(`Flow ${flowId} not found (404), clearing from storage`);

        // Clear from SecureStorage
        if (flowId) {
          SecureStorage.removeFlowId();
        }

        // Also clear all flow-related items from localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('currentFlowId');
          localStorage.removeItem('lastActiveFlowId');
          localStorage.removeItem('auth_flow');
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
    mutationFn: (data: FlowInitializationData) => {
      if (!unifiedDiscoveryAPI) throw new Error('No API instance available');
      return unifiedDiscoveryAPI.initializeFlow(data);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['unifiedDiscoveryFlow'] });

      // Store flow ID securely
      if (data.flow_id) {
        SecureStorage.setFlowId(data.flow_id);
      }
    },
  });

  // Execute phase mutation
  const executePhhaseMutation = useMutation({
    mutationFn: ({ phase, data }: { phase: string; data?: PhaseExecutionData }) => {
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
      SecureLogger.error('Phase execution failed', error);
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

  const executeFlowPhase = useCallback(async (phase: string, data?: PhaseExecutionData) => {
    return executePhhaseMutation.mutateAsync({ phase, data });
  }, [executePhhaseMutation]);

  const initializeFlow = useCallback(async (data: FlowInitializationData) => {
    return initializeFlowMutation.mutateAsync(data);
  }, [initializeFlowMutation]);

  return {
    flowState: flowState || null,
    isLoading,
    error: error,
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
